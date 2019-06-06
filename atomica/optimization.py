"""
Implements various Optimizations in Atomica

This module implements the :class:`Optimization` class, which contains the
information required to perform an optimization in Atomica. An Optimization
effectively serves as a mapping from one set of program instructions to another.

"""

import sciris as sc
from .system import logger, NotFoundError
from .utils import NamedItem
import numpy as np
from .model import Model, Link
import pickle
import scipy.optimize
from collections import defaultdict
from .utils import TimeSeries
from .results import Result
from .cascade import get_cascade_vals
from .programs import ProgramInstructions


class InvalidInitialConditions(Exception):
    # This error gets thrown if the initial conditions yield an objective value
    # that is not finite
    pass


class UnresolvableConstraint(Exception):
    # This error gets thrown if it is _impossible_ to satisfy the constraints. There are
    # two modes of constraint failure
    # - The constraint might not be satisfied on this iteration, but could be satisfied by other
    #   parameter values
    # - The constraint is impossible to satisfy because it is inconsistent (for example, if the
    #   total spend is greater than the sum of the upper bounds on all the individual programs)
    #   in which case the algorithm cannot continue
    # This error gets raised in the latter case, while the former should result in the iteration
    # being skipped
    pass


class Adjustable(object):

    def __init__(self, name, limit_type='abs', lower_bound=-np.inf, upper_bound=np.inf, initial_value=None):
        self.name = name  # identify the adjustable
        self.limit_type = limit_type  # 'abs' or 'rel'
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.initial_value = initial_value  # This could be None, but if it is None, then `extract_from_instructions` cannot be None

    def get_hard_bounds(self, x0=None):
        # Return hard bounds based the limit type and specified bounds
        self.lower_bound = self.lower_bound if self.lower_bound is not None else -np.inf
        self.upper_bound = self.upper_bound if self.upper_bound is not None else np.inf
        xmin = self.lower_bound if self.limit_type == 'abs' else x0 * self.lower_bound
        xmax = self.upper_bound if self.limit_type == 'abs' else x0 * self.upper_bound
        return xmin, xmax


class Adjustment(object):
    def __init__(self, name):
        self.name = name
        self.adjustables = None

    def get_initialization(self, progset, instructions):
        # Return initial values for ASD
        return [x.initial_value for x in self.adjustables]

    def update_instructions(self, adjustable_values, instructions):
        # adjustable_values contains the values for each adjustable in self.adjustables
        # at the current ASD iteration. This function updates the provided instructions in place
        return


class SpendingAdjustment(Adjustment):
    # This adjustment class represents making a spending quantity adjustable. By default, the
    # base class simply overwrites the spending value at a particular point in time
    # A SpendingAdjustment has a separate Adjustable for each time reached (independently)
    def __init__(self, prog_name, t, limit_type='abs', lower=0.0, upper=np.inf, initial=None):
        Adjustment.__init__(self, name=prog_name)
        self.prog_name = prog_name
        self.t = sc.promotetoarray(t)  # Time at which to apply the adjustment

        lower = sc.promotetolist(lower,keepnone=True)
        if len(lower) == 1:
            lower = lower*len(self.t)
        else:
            assert len(lower) == len(self.t), "If supplying lower bounds, you must either specify one, or one for every time point"

        upper = sc.promotetolist(upper,keepnone=True)
        if len(upper) == 1:
            upper = upper*len(self.t)
        else:
            assert len(upper) == len(self.t), "If supplying upper bounds, you must either specify one, or one for every time point"

        initial = sc.promotetolist(initial,keepnone=True)
        if len(initial) == 1:
            initial = initial*len(self.t)
        else:
            assert len(initial) == len(self.t), "If supplying initial values, you must either specify one, or one for every time point"

        self.adjustables = [Adjustable(prog_name, limit_type, lower_bound=lb, upper_bound=ub, initial_value=init) for lb,ub,init in zip(lower,upper,initial)]

    def update_instructions(self, adjustable_values, instructions):
        # There is one Adjustable for each time point, so the adjustable_values
        # are a list of this same length, one value for each time point
        for i, t in enumerate(self.t):
            if self.prog_name not in instructions.alloc:
                instructions.alloc[self.prog_name] = TimeSeries(t=t, vals=adjustable_values[i])
            else:
                instructions.alloc[self.prog_name].insert(t, adjustable_values[i])

    def get_initialization(self, progset, instructions):
        initialization = []
        for adjustable, t in zip(self.adjustables, self.t):
            if adjustable.initial_value:
                initialization.append(adjustable.initial_value)
            else:
                alloc = progset.get_alloc(t, instructions)
                initialization.append(alloc[self.prog_name][0])  # The Adjustable's name corresponds to the name of the program being overwritten.
        return initialization


class StartTimeAdjustment(Adjustment):
    # Example of an Adjustment that does not target a spending value

    def __init__(self, name, lower, upper, initial):
        Adjustment.__init__(self, name=name)
        self.adjustables = [Adjustable('start_year', limit_type='abs', lower=lower, upper=upper, initial=initial)]

    def update_instructions(self, adjustable_values, instructions):
        instructions.start_year = adjustable_values[0]

    def get_initialization(self, progset, instructions):
        if self.initial_value:
            return self.initial_value
        else:
            return instructions.start_year


class ExponentialSpendingAdjustment(Adjustment):
    # Example of a parametric time-varying budget where multiple parameters
    # are mapped to spending via a function

    def __init__(self, prog_name, t, t_0, t_end, p1, a1, a2):
        Adjustment.__init__(self, name=prog_name)
        self.prog_name = prog_name
        self.t = t  # Vector of time values instructions are updated at
        self.t_0 = t_0  # non-adjustable parameter
        self.t_end = t_end  # non_adjustable parameter
        self.adjustables = [Adjustable('p1', initial_value=p1), Adjustable('a1', initial_value=a1), Adjustable('a2', initial_value=a2)]  # Would need to specify initial values and limits for these parameters

    # Note - we can use get_initialization from the base class because all of the Adjustables
    # have explicit initial values. Note that it's essential to provide explicit initial values
    # for any Adjustable that does not explicitly appear in the instructions. Although in theory,
    # it would be possible to write a `get_initialization` function that fits the Adjustables
    # to the initial spending...

    def update_instructions(self, adjustable_values, instructions):
        # p1*exp(a1*(t-t_0))*exp(b1*(t-t_end))
        instructions.alloc[self.prog_name][self.t] = adjustable_values[0] * np.exp(adjustable_values[1] * (self.t - self.t_0)) * np.exp(adjustable_values[2] * (self.t - self.t_end))


class PairedLinearSpendingAdjustment(Adjustment):
    # This example shows a parametric time-varying budget reaching more than one program.
    # A single adjustable corresponding to the rate of change simultaneously acts on
    # two programs in opposite directions

    def __init__(self, prog_names, t):
        Adjustment.__init__(self, name=None)
        assert len(prog_names) == 2, 'PairedLinearSpendingAdjustment needs exactly two program names'
        self.prog_names = prog_names
        self.t = t  # [t_start,t_stop] for when to start/stop ramping
        self.adjustables = [Adjustable('ramp', initial_value=0.0)]

    def update_instructions(self, adjustable_values, instructions):

        gradient = adjustable_values[0]
        tspan = (self.t[1] - self.t[0])

        if gradient < 0:  # We are transferring money from program 2 to program 1
            available = -instructions.alloc[self.prog_names[1]].get(self.t[0])
            max_gradient = float(available) / tspan
            if gradient < max_gradient:
                gradient = max_gradient
        else:
            available = instructions.alloc[self.prog_names[0]].get(self.t[0])
            max_gradient = float(available) / tspan
            if gradient > max_gradient:
                gradient = max_gradient

        funding_change = gradient * tspan  # Amount transferred from program 1 to program 2

        # This does not change the amount of funds allocated in the initial year
        for prog in self.prog_names:
            instructions.alloc[prog].insert(self.t[0], instructions.alloc[prog].interpolate(self.t[0])[0])
            instructions.alloc[prog].remove_between(self.t)

        instructions.alloc[self.prog_names[0]].insert(self.t[1], instructions.alloc[self.prog_names[0]].get(self.t[0]) - funding_change)
        instructions.alloc[self.prog_names[1]].insert(self.t[1], instructions.alloc[self.prog_names[1]].get(self.t[0]) + funding_change)


class Measurable(object):

    def __init__(self, measurable_name, t, pop_names=None, weight=1.0, fcn=None):
        self.measurable_name = measurable_name
        self.t = sc.promotetoarray(t)  # Single year, or multiple years
        self.weight = weight
        self.pop_names = pop_names
        self.fcn = fcn  # transformation function to apply

    def eval(self, model):
        # This is the main interface with the optimization code - this function gets called
        # to return the transformed, weighted objective value from this Measurable for use in ASD
        # Only overload this if you want to customize the transformation and weighting
        val = self.get_objective_val(model)
        return self._transform_val(val)

    def get_objective_val(self, model):
        # This returns the base objective value, prior to any function transformation
        # or weighting. The function transformation and weighting are handled by this base
        # class - derived classes may wish to not expose things like the function mapping
        # in their constructors, if that wouldn't be appropriate. But otherwise, they can
        # inherit this behaviour for free. So derived classes should overload this method
        #
        # The base class has the default behaviour that the 'measurable name' is a model variable
        if len(self.t) == 1:
            t_filter = model.t == self.t  # boolean vector for whether to use the time point or not
        else:
            t_filter = (model.t >= self.t[0]) & (model.t < self.t[1])  # Don't include upper bound, so [2018,2019] will include exactly one year

        if self.measurable_name in model.progset.programs:
            alloc = model.progset.get_alloc(model.t, model.program_instructions)
            val = np.sum(alloc[self.measurable_name][t_filter])
        else:  # If the measurable is a model output...
            val = 0.0
            matched = False # Flag whether any variables were found
            for pop in model.pops:
                if not self.pop_names:
                    # If no pops were provided, then iterate over all pops but skip those where the measureable is not defined
                    # Use this approach rather than checking the pop type in the framework because user could be optimizating
                    # flow rates or transitions that don't appear in the framework
                    try:
                        vars = pop.get_variable(self.measurable_name)
                        matched = True
                    except NotFoundError:
                        continue
                elif pop not in self.pop_names:
                    continue
                else:
                    vars = pop.get_variable(self.measurable_name) # If variable is missing and the pop was explicitly defined, raise the error
                    matched = True

                for var in vars:
                    if isinstance(var, Link):
                        val += np.sum(var.vals[t_filter] / var.dt)  # Annualize link values - usually this won't make a difference, but it matters if the user mixes Links with something else in the objective
                    else:
                        val += np.sum(var.vals[t_filter])

            if not matched:
                # Raise an error if the measureable was not found in any populations
                raise Exception('"%s" not found in any populations' % (self.measurable_name))

        return val

    def _transform_val(self, val):
        # Apply function transformation and weight to the value
        if self.fcn:
            val = self.fcn(val)
        val *= self.weight
        return val


class MinimizeMeasurable(Measurable):
    # Syntactic sugar for a measurable that minimizes its quantity
    def __init__(self, measurable_name, t, pop_names=None):
        Measurable.__init__(self, measurable_name, t=t, weight=1, pop_names=pop_names)


class MaximizeMeasurable(Measurable):
    # Syntactic sugar for a measurable that maximizes its quantity
    def __init__(self, measurable_name, t, pop_names=None):
        Measurable.__init__(self, measurable_name, t=t, weight=-1, pop_names=pop_names)


class AtMostMeasurable(Measurable):
    # A Measurable that impose a penalty if the quantity is larger than some threshold
    # The initial points should be 'valid' in the sense that the quantity starts out
    # below the threshold (and during ASD it will never be allowed to cross the threshold)
    def __init__(self, measurable_name, t, threshold, pop_names=None):
        Measurable.__init__(self, measurable_name, t=t, weight=np.inf, pop_names=pop_names)
        self.weight = 1.0
        self.threshold = threshold
        self.fcn = lambda x: np.inf if x > self.threshold else 0.0

    def __repr__(self):
        return 'AtMostMeasurable(%s < %f)' % (self.measurable_name, self.threshold)


class AtLeastMeasurable(Measurable):
    # A Measurable that impose a penalty if the quantity is smaller than some threshold
    # The initial points should be 'valid' in the sense that the quantity starts out
    # above the threshold (and during ASD it will never be allowed to cross the threshold)
    def __init__(self, measurable_name, t, threshold, pop_names=None):
        Measurable.__init__(self, measurable_name, t=t, weight=np.inf, pop_names=pop_names)
        self.weight = 1.0
        self.threshold = threshold
        self.fcn = lambda x: np.inf if x < self.threshold else 0.0

    def __repr__(self):
        return 'AtLeastMeasurable(%s > %f)' % (self.measurable_name, self.threshold)


class MaximizeCascadeStage(Measurable):
    # This Measurable will maximize the number of people in a cascade stage, whatever that stage is
    # e.g. `measurable = MaximizeCascadeStage('main',2020)
    # If multiple years are provided, they will be summed over
    # Could add option to weight specific years later on, if desired

    def __init__(self, cascade_name, t, pop_names='all', weight=1.0, cascade_stage=-1):
        # Instantiate thpop_names can be a single pop name (including all), or a list of pop names
        # aggregations are supported by setting pop_names to a dict e.g.
        # pop_names = {'foo':['0-4','5-14']}
        #
        # The cascade name is passed to `get_cascade_vals` so any cascade can be passed in
        # Usually this would be 'None' (fallback cascade, or first cascade) or the name of a
        # cascade
        #
        # - t : Can be a single time or array of times (as supposed by get_cascade_vals)
        # - cascade_stage specifies which stage(s) to include. It can be
        #   - An integer indexing the `cascade_vals` dict e.g. -1 is the last stage
        #   - The name of a cascade stage
        #   - A list of integers and/or names to include multiple stages

        Measurable.__init__(self, cascade_name, t=t, weight=-weight, pop_names=pop_names)
        if not isinstance(cascade_stage, list):
            cascade_stage = [cascade_stage]
        self.cascade_stage = cascade_stage
        if not isinstance(self.pop_names, list):
            self.pop_names = [self.pop_names]

    def get_objective_val(self, model):
        result = Result(model=model)
        val = 0
        for pop_name in self.pop_names:
            cascade_vals = get_cascade_vals(result, self.measurable_name, pop_name, self.t)
            for stage in self.cascade_stage:  # Loop over included stages
                val += np.sum(cascade_vals[0][stage])  # Add the values from the stage, summed over time
        return val


class MaximizeCascadeConversionRate(Measurable):
    """
    Maximize overall conversion rate

    Maximize conversion summed over all cascade stages

    :param cascade_name: The name of one of the cascades in the Framework
    :param t: A single time value e.g. 2020
    :param pop_names: A single pop name (including 'all'), a list of populations,
                  or a dict/list of dicts, each with a single aggregation e.g. ``{'foo':['0-4','5-14']}``
    :param weight: Weighting factor for this Measurable in the overall objective function

    """

    def __init__(self, cascade_name, t:float, pop_names='all', weight=1.0):
        Measurable.__init__(self, cascade_name, t=t, weight=-weight, pop_names=pop_names)
        if not isinstance(self.pop_names, list):
            self.pop_names = [self.pop_names]

    def get_objective_val(self, model):
        if self.t < model.t[0] or self.t > model.t[-1]:
            raise Exception('Measurable year for optimization (%d) is outside the simulation range (%d-%d)' % (self.t,model.t[0],model.t[-1]))
        result = Result(model=model)
        val = 0
        for pop_name in self.pop_names:
            cascade_vals = get_cascade_vals(result, self.measurable_name, pop_name, self.t)[0]
            cascade_array = np.hstack(cascade_vals.values())
            conversion = cascade_array[1:] / cascade_array[0:-1]
            val += np.sum(conversion)
        return val


class Constraint(object):
    # A Constraint represents a condition that must be satisfied by the Instructions
    # after the cumulative effect of all adjustments. The Instructions are rescaled to
    # satisfy the constraint directly (rather than changing the value of the Adjustables)
    # although this distinction really only matters in the context of parametric spending

    def get_hard_constraint(self, optimization, instructions):
        return

    def constrain_instructions(self, instructions, hard_constraints):
        # Constrains the instructions, returns a metric penalizing the constraint
        # If there is no penalty associated with adjusting (perhaps if all of the Adjustments are
        # parametric?) then this would be 0.0
        return 0.0


class TotalSpendConstraint(Constraint):
    # This class implements a constraint on the total spend at every time point when a program
    # is optimizable. A program is considered optimizable if an Adjustment reaches that program
    # at the specified time. Spending is constrained independently at all times when any program
    # is adjustable.
    #
    # Important - this constraint only acts on program spending that is reached by an Adjustment.

    def __init__(self, total_spend=None, t=None, budget_factor=1.0):
        # total_spend allows the total spending in a particular year to be explicitly specified
        # rather than drawn from the initial allocation. This could be useful when using parametric
        # programs.
        # This constraint can be set to only apply in certain years.
        # The budget_factor multiplies the total spend at the time the hard_constraint is assigned
        # Typically this is to scale up the available spending when that spending is being drawn from
        # the instructions/progset (otherwise the budget_factor could already be part of the specified total spend)
        #
        # INPUTS
        # - t : A time, or list of times, at which to apply the total spending constraint. If None, it will
        #       automatically be set to all years in which spending adjustments are being made
        # - total_spend: A list of spending amounts the same size as t (can contain Nones), or None.
        #                For times in which the total spend is None, it will be automatically set to the sum of
        #                spending on optimizable programs in the corresponding year
        # - budget_factor: The budget factor multiplies whatever the total_spend is. This can either be a single value, or
        #                  a year specific value
        #
        # Note that if no times are specified, the budget factor should be a scalar but no explicit
        # spending values can be specified. This is because in the case where different programs are
        # optimized in different years, an explicit total spending constraint applying to all
        # times is unlikely to be a sensible choice (so we just ask the user to specify the time as well)
        self.total_spend = sc.promotetoarray(total_spend) if total_spend is not None else ()
        self.t = sc.promotetoarray(t) if t is not None else ()
        self.budget_factor = sc.promotetoarray(budget_factor)

        if t is None:
            assert total_spend is None, 'If no times are specified, no total spend values can be specified either'
            assert len(self.budget_factor) == 1, 'If no times are specified, the budget factor must be scalar'

        if t is not None and total_spend is not None:
            assert len(self.total_spend) == len(self.t), 'If specifying both the times and values for the total spending constraint, their lengths must be the same'
        if len(self.budget_factor) > 1:
            assert len(self.budget_factor) == len(self.t), 'If specifying multiple budget factors, you must also specify the years in which they are used'

    def get_hard_constraint(self, optimization, instructions):
        # First, at each time point where a program overwrite exists, we need to store
        # the names of all of the programs being overwritten
        # e.g.
        # hard_constraints['programs'][2020] = ['Program 1','Program 2']
        # hard_constraints['programs'][2030] = ['Program 2','Program 3']
        # By convention, an Adjustable affecting a program should store the program's name in the
        # `prog_name` attribute. If a program reaches multiple programs, then `prog_name` will be a list

        # First, we make a dictionary storing the years in which any adjustments are made
        # as well as the upper and lower bounds in that year. This is only done for spending
        # adjustments (i.e. those where `adjustment.prog_name` is defined)
        hard_constraints = {}
        hard_constraints['programs'] = defaultdict(set)  # It's a set so that it will work properly if multiple Adjustments reach the same parameter at the same time. However, this would a bad idea and nobody should do this!
        for adjustment in optimization.adjustments:
            if hasattr(adjustment, 'prog_name'):
                for t in list(adjustment.t):
                    if isinstance(adjustment.prog_name, list):
                        hard_constraints['programs'][t].update(adjustment.prog_name)
                    else:
                        hard_constraints['programs'][t].add(adjustment.prog_name)

        if len(self.t):
            # Check that every explictly specified time has
            # corresponding spending adjustments available for use
            missing_times = set(self.t) - set(hard_constraints['programs'].keys())
            if missing_times:
                raise Exception('Total spending constraint was specified in %s but the optimization does not have any adjustments at those times' % (missing_times))

        # Now we have a set of times and programs for which we need to get total spend, and
        # also which programs should be included in the total for that year
        #
        # hard_constraints['total_spend'][2020] = 300
        # hard_constraints['total_spend'][2030] = 400
        hard_constraints['total_spend'] = {}
        for t, progs in hard_constraints['programs'].items():
            # For every time at which programs are optimizable...
            if len(self.t) and t not in self.t:
                # If we are not wanting to constrain spending in this year, then
                # continue
                continue
            elif len(self.t):
                idx = np.where(self.t == t)[0][0]  # This is the index for the constraint year
            else:
                idx = None

            if not len(self.total_spend) or self.total_spend[idx] is None:
                # Get the total spend from the allocation in this year
                total_spend = 0.0
                for prog in progs:
                    total_spend += instructions.alloc[prog].get(t)
            else:
                total_spend = self.total_spend[idx]

            # Lastly, apply the budget factor
            if len(self.budget_factor) == 1:
                hard_constraints['total_spend'][t] = total_spend * self.budget_factor
            else:
                hard_constraints['total_spend'][t] = total_spend * self.budget_factor[idx]

        # Finally, for each adjustable, we need to store its upper and lower bounds
        # _in the year that the adjustment is being made_
        #
        # This is because in the case where we have an multiple adjustables targeting the same Program at different
        # time points, the upper/lower bounds might be different. For example, suppose we have spending on
        # Program 1 specified somehow as 2020=$20 and 2030=$30. Then suppose we add an Adjustment for Program 1 in
        # 2020 *and* 2030 with relative bounds of [0.5,2.0]. Then, in 2020 spending on Program 1 is limited to
        # $10-40 while in 2030 it's limited to $15-$60. Thus the spending constraint could also be time-varying.
        # In the case of a parametric overwrite, there will be no direct spending bounds based on the Adjustable. Then,
        # the spending should only be restricted to a positive value.

        hard_constraints['bounds'] = dict()

        for t, progs in hard_constraints['programs'].items():  # For each time point being constrained, and for each program
            if t not in hard_constraints['total_spend']:
                # If the time is not one where the total spending constraint is being applied, then
                # just skip it
                continue

            hard_constraints['bounds'][t] = dict()
            # If there is an Adjustable that reaches this Program in the appropriate year:

            # Keep track of the absolute lower and upper bounds on spending permitted by the program constraints
            minimum_spend = 0.0
            maximum_spend = 0.0

            for adjustment in optimization.adjustments:
                if hasattr(adjustment, 'prog_name') and adjustment.prog_name in progs and t in adjustment.t:
                    if isinstance(adjustment, SpendingAdjustment):
                        idx = np.where(adjustment.t == t)[0][0]  # If it is a SpendingAdjustment then set bounds from the appropriate Adjustable
                        adjustable = adjustment.adjustables[idx]
                        hard_constraints['bounds'][t][adjustment.prog_name] = adjustable.get_hard_bounds(instructions.alloc[adjustment.prog_name].get(t))  # The instructions should already have the initial spend on this program inserted. This may be inconsistent if multiple Adjustments reach the same program...!
                    else:
                        hard_constraints['bounds'][t][adjustment.prog_name] = (0.0, np.inf)  # If the Adjustment reaches spending but is not a SpendingAdjustment then do not constrain the alloc

                    minimum_spend += hard_constraints['bounds'][t][adjustment.prog_name][0]
                    maximum_spend += hard_constraints['bounds'][t][adjustment.prog_name][1]

            if minimum_spend > hard_constraints['total_spend'][t]:
                raise UnresolvableConstraint('The total spend in %.2f is constrained to %.2f but the individual programs have a total minimum spend of %.2f which is impossible to satisfy. Please either raise the total spending, or lower the minimum spend on one or more programs' % (t, hard_constraints['total_spend'][t], minimum_spend))

            if maximum_spend < hard_constraints['total_spend'][t]:
                raise UnresolvableConstraint('The total spend in %.2f is constrained to %.2f but the individual programs have a total maximum spend of %.2f which is impossible to satisfy. Please either lower the total spending, or raise the maximum spend on one or more programs' % (t, hard_constraints['total_spend'][t], maximum_spend))

        return hard_constraints

    def constrain_instructions(self, instructions, hard_constraints):

        penalty = 0.0

        for t, total_spend in hard_constraints['total_spend'].items():

            x0 = sc.odict()  # Order matters here
            bounds = []
            progs = hard_constraints['programs'][t]  # Programs eligible for constraining at this time
            LinearConstraint = [{'type': 'eq', 'fun': lambda x: np.sum(x) - total_spend, 'jac': lambda x: np.ones(x.shape)}]  # Constrain spend

            for prog in progs:
                x0[prog] = instructions.alloc[prog].get(t)
                bounds.append(hard_constraints['bounds'][t][prog])

            x0_array = np.array(x0.values()).ravel()
            x0_array_scaled = x0_array / sum(x0_array) * total_spend  # Multiplicative rescaling to match the total spend

            def jacfcn(x):
                dist = np.linalg.norm(x - x0_array_scaled)
                if dist == 0:
                    return np.zeros(x.shape)
                else:
                    return (x-x0_array_scaled)/dist

            res = scipy.optimize.minimize(lambda x: np.linalg.norm(x - x0_array_scaled), x0_array_scaled, jac=jacfcn, bounds=bounds, constraints=LinearConstraint, options={'maxiter': 500})

            if not res['success']:
                logger.error('TotalSpendConstraint failed - rejecting these proposed parameters with an objective value of np.inf')
                penalty = np.inf
            else:
                penalty += np.linalg.norm(res['x'] - x0_array)  # Penalty is the distance between the unconstrained budget and the constrained budget
                for name, val in zip(x0.keys(), res['x']):
                    instructions.alloc[name].insert(t, val)
        return penalty


class OptimInstructions(NamedItem):
    def __init__(self, json=None):
        self.name = json['name']
        self.json = json

    def make(self, project=None):
        proj = project
        name = self.json['name']
        parset_name = self.json['parset_name']  # WARNING, shouldn't be unused
        progset_name = self.json['progset_name']
        adjustment_year = self.json['start_year']  # The year when adjustments get made
        end_year = self.json['end_year']  # For cascades, this is the evaluation year. For other measurables, it is optimized from the adjustment year to the end year
        budget_factor = self.json['budget_factor']
        objective_weights = self.json['objective_weights']
        prog_spending = self.json['prog_spending']
        maxtime = self.json['maxtime']
        optim_type = self.json['optim_type']
        tool = self.json['tool']
        method = self.json.get('method', None)
        start_year = project.data.end_year  # The year when programs turn on

        if tool == 'cascade' and optim_type == 'money':
            raise NotImplementedError('Money minimization not yet implemented for Cascades tool')

        progset = proj.progsets[progset_name]  # Retrieve the progset

        # Set up the initial allocation and program instructions
        progset_instructions = ProgramInstructions(alloc=progset, start_year=start_year)  # passing in the progset means we fix the spending in the start year

        # Add a spending adjustment in the start/optimization year for every program in the progset, using the lower/upper bounds
        # passed in as arguments to this function
        adjustments = []
        default_spend = progset.get_alloc(tvec=adjustment_year, instructions=progset_instructions)  # Record the default spend for scale-up in money minimization
        for prog_name in progset.programs:
            limits = list(sc.dcp(prog_spending[prog_name]))
            if limits[0] is None:
                limits[0] = 0.0
            if limits[1] is None and optim_type == 'money':
                # Money minimization requires an absolute upper bound. Limit it to 5x default spend by default
                limits[1] = 5 * default_spend[prog_name]
            adjustments.append(SpendingAdjustment(prog_name, t=adjustment_year, limit_type='abs', lower=limits[0], upper=limits[1]))

            if optim_type == 'money':
                # Modify default spending to see if more money allows target to be met at all
                if limits[1] is not None and np.isfinite(limits[1]):
                    progset_instructions.alloc[prog_name].insert(adjustment_year, limits[1])
                else:
                    progset_instructions.alloc[prog_name] = TimeSeries(adjustment_year, 5 * default_spend[prog_name])

        if optim_type == 'outcome':
            # Add a total spending constraint with the given budget scale up
            # For money minimization we do not need to do this
            constraints = [TotalSpendConstraint(budget_factor=budget_factor)]
        else:
            constraints = None

        # Add all of the terms in the objective
        measurables = []
        for mname, mweight in objective_weights.items():

            if not mweight:
                continue

            if tool == 'cascade':
                tokens = mname.split(':')
                if tokens[0] == 'cascade_stage':  # Parse a measurable name like 'cascade_stage:Default:All diagnosed'
                    measurables.append(MaximizeCascadeStage(cascade_name=tokens[1], t=[end_year], pop_names='all', cascade_stage=tokens[2], weight=mweight))
                elif tokens[0] == 'conversion':  # Parse a measurable name like 'conversions:Default'
                    measurables.append(MaximizeCascadeConversionRate(cascade_name=tokens[1], t=[end_year], pop_names='all', weight=mweight))
                else:
                    raise Exception('Unknown measurable "%s"' % (mname))
            else:
                if optim_type == 'money':
                    # For money minimization, use at AtMostMeasurable to meet the target by the end year.
                    # The weight stores the threshold value
                    measurables.append(AtMostMeasurable(mname, t=end_year, threshold=mweight))
                else:
                    measurables.append(Measurable(mname, t=[adjustment_year, end_year], weight=mweight))

        if optim_type == 'money':
            # Do a prerun to convert the optimization targets into absolute units
            result = proj.run_sim(proj.parsets[parset_name], progset=progset, progset_instructions=progset_instructions, store_results=False)
            for measurable in measurables:
                val = measurable.get_objective_val(result.model)  # This is the baseline value for the quantity being thresholded
                assert measurable.threshold <= 100 and measurable.threshold >= 0
                measurable.threshold = val * (1 - measurable.threshold / 100.)

            # Then, add extra measurables for program spending
            for prog in progset.programs.values():
                measurables.append(MinimizeMeasurable(prog.name, adjustment_year))  # Minimize 2020 spending on Treatment 1

        # Create the Optimization object
        optim = Optimization(name=name, parsetname=parset_name, progsetname=progset_name, adjustments=adjustments, measurables=measurables, constraints=constraints, maxtime=maxtime)

        # Set the method used for optimization
        if method is not None:
            optim.method = method
        elif optim_type == 'money':
            optim.method = 'pso'

        return optim, progset_instructions


class Optimization(NamedItem):
    """
    Instructions on how to perform an optimization

    The Optimization object stores the information that defines an optimization operation.
    Optimization can be thought of as a function mapping one set of program instructions
    to another set of program instructions. The parameters of that function are stored in the
    Optimization object, and amount to

    - A definition of optimality
    - A specification of allowed changes to the program instructions
    - Any additional information required by a particular optimization algorithm e.g. ASD

    """

    def __init__(self, name=None, parsetname=None, progsetname=None, adjustments=None, measurables=None, constraints=None, maxtime=None, maxiters=None, method='asd'):

        # Get the name
        if name is None:
            name = 'default'
        NamedItem.__init__(self, name)

        self.parsetname = parsetname
        self.progsetname = progsetname
        self.maxiters = maxiters  # Not snake_case to match ASD
        self.maxtime = maxtime  # Not snake_case to match ASD
        self.method = method  # This gets passed to optimize() to select the algorithm

        assert adjustments is not None, 'Must specify some adjustments to carry out an optimization'
        assert measurables is not None, 'Must specify some measurables to carry out an optimization'
        self.adjustments = sc.promotetolist(adjustments)
        self.measurables = sc.promotetolist(measurables)

        if constraints:
            self.constraints = [constraints] if not isinstance(constraints, list) else constraints
        else:
            self.constraints = None

        if adjustments is None or measurables is None:
            raise Exception('Must supply either a json or an adjustments+measurables')
        return

    def __repr__(self):
        return sc.prepr(self)

    def get_initialization(self, progset, instructions):
        # Return arrays of lower and upper bounds for each adjustable
        x0 = []
        for adjustment in self.adjustments:
            x0 += adjustment.get_initialization(progset, instructions)
        x0 = np.array(x0)
        xmin = np.zeros(x0.shape)
        xmax = np.zeros(x0.shape)

        ptr = 0
        for adjustment in self.adjustments:
            for adjustable in adjustment.adjustables:
                bounds = adjustable.get_hard_bounds(x0[ptr])
                xmin[ptr] = bounds[0]
                xmax[ptr] = bounds[1]
                ptr += 1

        return x0, xmin, xmax

    def update_instructions(self, asd_values, instructions):
        idx = 0
        for adjustment in self.adjustments:
            adjustment.update_instructions(asd_values[idx:idx + len(adjustment.adjustables)], instructions)
            idx += len(adjustment.adjustables)

    def get_hard_constraints(self, x0, instructions):
        # Return hard constraints based on the starting initialization
        instructions = sc.dcp(instructions)
        self.update_instructions(x0, instructions)
        if not self.constraints:
            return None
        else:
            return [x.get_hard_constraint(self, instructions) for x in self.constraints]

    def constrain_instructions(self, instructions, hard_constraints):
        constraint_penalty = 0.0
        if self.constraints:
            for constraint, hard_constraint in zip(self.constraints, hard_constraints):
                constraint_penalty += constraint.constrain_instructions(instructions, hard_constraint)
        return constraint_penalty

    def compute_objective(self, model):
        # Take in a completed model run
        # Compute the objective based on the measurables
        # Program name will map to spending array for that program
        objective = 0.0
        for measurable in self.measurables:
            objective += measurable.eval(model)
        return objective


def _objective_fcn(asd_values, pickled_model=None, optimization=None, hard_constraints=None):
    # Compute the objective in ASD

    # Unpickle model
    model = pickle.loads(pickled_model)

    # Inject the ASD vector into the instructions
    optimization.update_instructions(asd_values, model.program_instructions)

    # Constrain the alloc - a penalty of `np.inf` signifies that the constraint could not be satisfied
    # In which case we can reject the proposed parameters _before_ processing the model
    constraint_penalty = optimization.constrain_instructions(model.program_instructions, hard_constraints)
    if np.isinf(constraint_penalty):
        return constraint_penalty

    # Use the updated instructions to run the model
    model.process()

    # Compute the objective function based on the model calculated values and return it
    # TODO - constraint_penalty is an interesting idea but need to make sure it doesn't dominate the actual objective
    # Using it directly seems to prioritize meeting the constraint and with ASD's single-parameter stepping this prevents convergence
    obj_val = 0.0 * constraint_penalty + optimization.compute_objective(model)

    return obj_val


def optimize(project, optimization, parset, progset, instructions, x0=None, xmin=None, xmax=None, hard_constraints=None):
    """
    Main user entry point for optimization

    The optional inputs `x0`, `xmin`, `xmax` and `hard_constraints` are used when
    performing parallel optimization (implementation not complete yet), in which case
    they are computed by the parallel wrapper to `optimize()`. Normally these variables
    would not be specified by users, because they are computed from the `Optimization`
    together with the instructions (because relative constraints in the Optimization are
    interpreted as being relative to the allocation in the instructions).

    :param project: A :class:`Project` instance
    :param optimization: An :class:`Optimization` instance
    :param parset: A :class:`ParameterSet` instance or name of a parset
    :param progset: A :class:`ProgramSet` instance or name of a progset
    :param instructions: A :class:`ProgramInstructions` instance
    :param x0: Not for manual use - override initial values
    :param xmin: Not for manual use - override lower bounds
    :param xmax: Not for manual use - override upper bounds
    :param hard_constraints: Not for manual use - override hard constraints
    :return: A :class:`ProgramInstructions` instance representing optimal instructions

    """
    # The ASD initialization, xmin and xmax values can optionally be
    # method can be one of
    # - asd (to use normal ASD)
    # - pso (to use particle swarm optimization from pyswarm)
    # - hyperopt (to use hyperopt's Bayesian optimization function)

    assert optimization.method in ['asd', 'pso', 'hyperopt']

    model = Model(project.settings, project.framework, parset, progset, instructions)
    pickled_model = pickle.dumps(model)

    initialization = optimization.get_initialization(progset, model.program_instructions)
    x0 = x0 if x0 is not None else initialization[0]
    xmin = xmin if xmin is not None else initialization[1]
    xmax = xmax if xmax is not None else initialization[2]

    if not hard_constraints:
        hard_constraints = optimization.get_hard_constraints(x0, model.program_instructions)  # The optimization passed in here knows how to calculate the hard constraints based on the program instructions

    # Prepare additional arguments for the objective function
    args = {
        'pickled_model': pickled_model,
        'optimization': optimization,
        'hard_constraints': hard_constraints,
    }

    # Check that the initial conditions are OK
    initial_objective = _objective_fcn(x0, **args)
    if not np.isfinite(initial_objective):
        raise InvalidInitialConditions('Optimization cannot begin because the objective function was NaN for the specified initialization')

    if optimization.method == 'asd':
        optim_args = {
            # 'stepsize': proj.settings.autofit_params['stepsize'],
            'maxiters': optimization.maxiters,
            'maxtime': optimization.maxtime,
            # 'sinc': proj.settings.autofit_params['sinc'],
            # 'sdec': proj.settings.autofit_params['sdec'],
            'fulloutput': False,
            'xmin': xmin,
            'xmax': xmax,
        }
        x_opt = sc.asd(_objective_fcn, x0, args, **optim_args)[0]
    elif optimization.method == 'pso':

        import pyswarm

        optim_args = {
            'maxiter': 3,
            'lb': xmin,
            'ub': xmax,
            'minstep': 1e-3,
            'debug': True
        }
        if np.any(~np.isfinite(xmin)) or np.any(~np.isfinite(xmax)):
            errormsg = 'PSO optimization requires finite upper and lower bounds to specify the search domain (i.e. every Adjustable needs to have finite bounds)'
            raise Exception(errormsg)

        x_opt, _ = pyswarm.pso(_objective_fcn, kwargs=args, **optim_args)
    elif optimization.method == 'hyperopt':

        import hyperopt
        import functools

        if np.any(~np.isfinite(xmin)) or np.any(~np.isfinite(xmax)):
            errormsg = 'hyperopt optimization requires finite upper and lower bounds to specify the search domain (i.e. every Adjustable needs to have finite bounds)'
            raise Exception(errormsg)

        space = []
        for i, (lower, upper) in enumerate(zip(xmin,xmax)):
            space.append(hyperopt.hp.uniform(str(i),lower,upper))
        fcn = functools.partial(_objective_fcn,**args) # Partial out the extra arguments to the objective

        optim_args = {
            'max_evals': optimization.maxiters if optimization.maxiters is not None else 100,
            'algo': hyperopt.tpe.suggest
        }

        x_opt = hyperopt.fmin(fcn, space, **optim_args)
        x_opt = np.array([x_opt[str(n)] for n in range(len(x_opt.keys()))])

    optimization.update_instructions(x_opt, model.program_instructions)
    optimization.constrain_instructions(model.program_instructions, hard_constraints)
    return model.program_instructions  # Return the modified instructions

# def parallel_optimize(project,optimization,parset,progset,program_instructions):
#
#    raise NotImplementedError
#
#    initialization = optimization.get_initialization(progset, program_instructions)
#    xmin = initialization[1]
#    xmax = initialization[2]
#
#    initial_instructions = program_instructions
#    for i in range(0,n_rounds):
#        for i in range(0,n_threads):
#            optimized_instructions[i] = optimize(optimization, parset, progset, initial_instructions, x0=None, xmin=xmin, xmax=xmax)
#        initial_instructions = pick_best(optimized_instructions)
#    return initial_instructions # Best one from the last round
