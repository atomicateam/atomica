"""
Functions for running optimizations.
Version: 2018mar26
"""

import sciris.core as sc
from .system import AtomicaException, NotAllowedError
from .utils import NamedItem
import numpy as np
from .model import Model, Link
import pickle
import scipy.optimize
from collections import defaultdict
from .structure import TimeSeries
import logging
from .results import Result
from .cascade import get_cascade_vals

logger = logging.getLogger(__name__)

class Adjustable(object):

    def __init__(self,name,limit_type='abs',lower_bound=-np.inf,upper_bound=np.inf,initial_value=None):
        self.name = name # identify the adjustable
        self.limit_type = limit_type # 'abs' or 'rel'
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.initial_value = initial_value # This could be None, but if it is None, then `extract_from_instructions` cannot be None

    def get_hard_bounds(self,x0=None):
        # Return hard bounds based the limit type and specified bounds
        self.lower_bound = self.lower_bound if self.lower_bound is not None else -np.inf
        self.upper_bound = self.upper_bound if self.upper_bound is not None else np.inf
        xmin = self.lower_bound if self.limit_type == 'abs' else x0*self.lower_bound
        xmax = self.upper_bound if self.limit_type == 'abs' else x0*self.upper_bound
        return xmin, xmax

class Adjustment(object):
    def __init__(self,name):
        self.name = name
        self.adjustables = None

    def get_initialization(self,progset,instructions):
        # Return initial values for ASD
        return [x.initial_value for x in self.adjustables]

    def update_instructions(self,adjustable_values,instructions):
        # adjustable_values contains the values for each adjustable in self.adjustables
        # at the current ASD iteration. This function updates the provided instructions in place
        return

class SpendingAdjustment(Adjustment):
    # This adjustment class represents making a spending quantity adjustable. By default, the
    # base class simply overwrites the spending value at a particular point in time
    # A SpendingAdjustment has a separate Adjustable for each time reached (independently)
    def __init__(self,prog_name,t,limit_type='abs',lower=0.0,upper=np.inf,initial=None):
        Adjustment.__init__(self,name=prog_name)
        self.prog_name = prog_name
        self.t = sc.promotetoarray(t) # Time at which to apply the adjustment
        if isinstance(initial,list):
            assert len(initial)==len(self.t), "If supplying initial values, you must either specify one, or one for every time point"
        else:
            initial = [initial]*len(self.t)
        self.adjustables = [Adjustable(prog_name,limit_type,lower,upper,initial_value) for initial_value in initial]

    def update_instructions(self,adjustable_values,instructions):
        # There is one Adjustable for each time point, so the adjustable_values
        # are a list of this same length, one value for each time point
        for i,t in enumerate(self.t):
            if self.prog_name not in instructions.alloc:
                instructions.alloc[self.prog_name] = TimeSeries(t=t, vals=adjustable_values[i])
            else:
                instructions.alloc[self.prog_name].insert(t,adjustable_values[i])

    def get_initialization(self,progset,instructions):
        initialization = []
        for adjustable,t in zip(self.adjustables,self.t):
            if adjustable.initial_value:
                initialization.append(adjustable.initial_value)
            else:
                alloc = progset.get_alloc(instructions,t)
                initialization.append(alloc[self.prog_name][0]) # The Adjustable's name corresponds to the name of the program being overwritten.
        return initialization

class StartTimeAdjustment(Adjustment):
    # Example of an Adjustment that does not target a spending value

    def __init__(self,name,lower,upper,initial):
        Adjustment.__init__(self,name=name)
        self.adjustables = [Adjustable('start_year',limit_type='abs',lower=lower,upper=upper,initial=initial)]

    def update_instructions(self,adjustable_values,instructions):
        instructions.start_year = adjustable_values[0]

    def get_initialization(self,progset,instructions):
        if self.initial_value:
            return self.initial_value
        else:
            return instructions.start_year

class ExponentialSpendingAdjustment(Adjustment):
    # Example of a parametric time-varying budget where multiple parameters
    # are mapped to spending via a function

    def __init__(self,prog_name,t,t_0,t_end,p1,a1,a2):
        Adjustment.__init__(self,name=prog_name)
        self.prog_name = prog_name
        self.t = t # Vector of time values instructions are updated at
        self.t_0 = t_0 # non-adjustable parameter
        self.t_end = t_end # non_adjustable parameter
        self.adjustables = [Adjustable('p1',initial_value=p1),Adjustable('a1',initial_value=a1),Adjustable('a2',initial_value=a2)] # Would need to specify initial values and limits for these parameters

    # Note - we can use get_initialization from the base class because all of the Adjustables
    # have explicit initial values. Note that it's essential to provide explicit initial values
    # for any Adjustable that does not explicitly appear in the instructions. Although in theory,
    # it would be possible to write a `get_initialization` function that fits the Adjustables
    # to the initial spending...

    def update_instructions(self,adjustable_values,instructions):
        # p1*exp(a1*(t-t_0))*exp(b1*(t-t_end))
        instructions.alloc[self.prog_name][self.t] = adjustable_values[0]*np.exp(adjustable_values[1]*(self.t-self.t_0))*np.exp(adjustable_values[2]*(self.t-self.t_end))

class PairedLinearSpendingAdjustment(Adjustment):
    # This example shows a parametric time-varying budget reaching more than one program.
    # A single adjustable corresponding to the rate of change simultaneously acts on
    # two programs in opposite directions

    def __init__(self, prog_names, t):
        Adjustment.__init__(self, name=None)
        assert len(prog_names) == 2, 'PairedLinearSpendingAdjustment needs exactly two program names'
        self.prog_names = prog_names
        self.t = t  # [t_start,t_stop] for when to start/stop ramping
        self.adjustables = [Adjustable('ramp',initial_value=0.0)]

    def update_instructions(self, adjustable_values, instructions):

        gradient = adjustable_values[0]
        tspan = (self.t[1] - self.t[0])

        if gradient < 0: # We are transferring money from program 2 to program 1
            available = -instructions.alloc[self.prog_names[1]].get(self.t[0])
            max_gradient = float(available) / tspan
            if gradient < max_gradient:
                gradient = max_gradient
        else:
            available = instructions.alloc[self.prog_names[0]].get(self.t[0])
            max_gradient = float(available) / tspan
            if gradient > max_gradient:
                gradient = max_gradient

        funding_change = gradient*tspan # Amount transferred from program 1 to program 2

        # This does not change the amount of funds allocated in the initial year
        for prog in self.prog_names:
            instructions.alloc[prog].insert(self.t[0],instructions.alloc[prog].interpolate(self.t[0])[0])
            instructions.alloc[prog].remove_between(self.t)

        instructions.alloc[self.prog_names[0]].insert(self.t[1],instructions.alloc[self.prog_names[0]].get(self.t[0])-funding_change)
        instructions.alloc[self.prog_names[1]].insert(self.t[1],instructions.alloc[self.prog_names[1]].get(self.t[0])+funding_change)


class Measurable(object):

    def __init__(self,measurable_name,t,pop_names=None,weight=1.0,fcn=None):
        self.measurable_name = measurable_name
        self.t = sc.promotetoarray(t) # Single year, or multiple years
        self.weight = weight
        self.pop_names = pop_names
        self.fcn = fcn # transformation function to apply

    def eval(self,model):
        # This is the main interface with the optimization code - this function gets called
        # to return the transformed, weighted objective value from this Measurable for use in ASD
        # Only overload this if you want to customize the transformation and weighting
        val = self.get_objective_val(model)
        return self._transform_val(val)

    def get_objective_val(self,model):
        # This returns the base objective value, prior to any function transformation
        # or weighting. The function transformation and weighting are handled by this base
        # class - derived classes may wish to not expose things like the function mapping
        # in their constructors, if that wouldn't be appropriate. But otherwise, they can
        # inherit this behaviour for free. So derived classes should overload this method
        #
        # The base class has the default behaviour that the 'measurable name' is a model variable
        if len(self.t) == 1:
            t_filter = model.t==self.t # boolean vector for whether to use the time point or not
        else:
            t_filter = (model.t >= self.t[0]) & (model.t < self.t[1]) # Don't include upper bound, so [2018,2019] will include exactly one year

        if self.measurable_name in model.progset.programs:
            alloc = model.progset.get_alloc(model.program_instructions,model.t)
            val =  np.sum(alloc[self.measurable_name][t_filter])
        else: # If the measurable is a model output...
            val = 0.0
            for pop in model.pops:
                if not self.pop_names or pop in self.pop_names:
                    vars = pop.get_variable(self.measurable_name)
                    for var in vars:
                        if isinstance(var, Link):
                            val += np.sum(var.vals[t_filter] / var.dt)  # Annualize link values - usually this won't make a difference, but it matters if the user mixes Links with something else in the objective
                        else:
                            val += np.sum(var.vals[t_filter])
        return val

    def _transform_val(self,val):
        # Apply function transformation and weight to the value
        if self.fcn:
            val = self.fcn(val)
        val *= self.weight
        return val

class MinimizeMeasurable(Measurable):
    # Syntactic sugar for a measurable that minimizes its quantity
    def __init__(self,measurable_name, t,pop_names=None):
        Measurable.__init__(self,measurable_name,t=t,weight=1,pop_names=pop_names)

class MaximizeMeasurable(Measurable):
    # Syntactic sugar for a measurable that maximizes its quantity
    def __init__(self,measurable_name, t,pop_names=None):
        Measurable.__init__(self,measurable_name,t=t,weight=-1,pop_names=pop_names)

class AtMostMeasurable(Measurable):
    # A Measurable that impose a penalty if the quantity is larger than some threshold
    # The initial points should be 'valid' in the sense that the quantity starts out
    # below the threshold (and during ASD it will never be allowed to cross the threshold)
    def __init__(self,measurable_name, t, threshold,pop_names=None):
        Measurable.__init__(self,measurable_name,t=t,weight=np.inf,pop_names=pop_names)
        self.weight = 1.0
        self.threshold = threshold
        self.fcn = lambda x: np.inf if x>threshold else 0.0

class AtLeastMeasurable(Measurable):
    # A Measurable that impose a penalty if the quantity is smaller than some threshold
    # The initial points should be 'valid' in the sense that the quantity starts out
    # above the threshold (and during ASD it will never be allowed to cross the threshold)
    def __init__(self,measurable_name, t, threshold,pop_names=None):
        Measurable.__init__(self,measurable_name,t=t,weight=np.inf,pop_names=pop_names)
        self.weight = 1.0
        self.threshold = threshold
        self.fcn = lambda x: np.inf if x<threshold else 0.0

class MaximizeCascadeFinalStage(Measurable):
    # This Measurable will maximize the number of people in the final cascade stage, whatever that stage is
    # e.g. `measurable = MaximizeCascadeFinalStage('main',2020)
    # If multiple years are provided, they will be summed over
    # Could add option to weight specific years later on, if desired
    def __init__(self,cascade_name,t,pop_names='all',weight=-1.0):
        # pop_names can be a single pop name (including all), or a list of pop names
        # aggregations are supported by setting pop_names to a dict e.g.
        # pop_names = {'foo':['0-4','5-14']}
        Measurable.__init__(self,cascade_name,t=t,weight=weight,pop_names=pop_names)
        if not isinstance(self.pop_names, list):
            self.pop_names = [self.pop_names]

    def get_objective_val(self,model):
        result = Result(model=model)
        val = 0
        for pop_name in self.pop_names:
            cascade_vals = get_cascade_vals(result,self.measurable_name, pop_name, self.t)
            val += np.sum(cascade_vals[0][-1]) # The sum of final cascade stage values
        return val

class MaximizeCascadeConversionRate(Measurable):
    # This Measurable will maximize the conversion rate, summed over all cascade stages
    def __init__(self,cascade_name,t,pop_names='all',weight=-1.0):
        # pop_names can be a single pop name (including all), or a list of pop names
        # aggregations are supported by setting pop_names to a dict e.g.
        # pop_names = {'foo':['0-4','5-14']}
        Measurable.__init__(self,cascade_name,t=t,weight=weight,pop_names=pop_names)
        if not isinstance(self.pop_names,list):
            self.pop_names = [self.pop_names]

    def get_objective_val(self,model):
        result = Result(model=model)
        val = 0
        for pop_name in self.pop_names:
            cascade_vals = get_cascade_vals(result,self.measurable_name, pop_name, self.t)[0]
            cascade_array = np.hstack(cascade_vals.values())
            conversion = cascade_array[1:] / cascade_array[0:-1]
            val += np.sum(conversion)
        return val


class Constraint(object):
    # A Constraint represents a condition that must be satisfied by the Instructions
    # after the cumulative effect of all adjustments. The Instructions are rescaled to
    # satisfy the constraint directly (rather than changing the value of the Adjustables)
    # although this distinction really only matters in the context of parametric spending

    def get_hard_constraint(self,optimization, instructions):
        return

    def constrain_instructions(self,instructions,hard_constraints):
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

    def __init__(self, total_spend = None, t = None, budget_factor = 1.0):
        # total_spend allows the total spending in a particular year to be explicitly specified
        # rather than drawn from the initial allocation. This could be useful when using parametric
        # programs.
        # This constraint can be set to only apply in certain years.
        # The budget_factor multiplies the total spend at the time the hard_constraint is assigned
        # Typically this is to scale up the available spending when that spending is being drawn from
        # the instructions/progset (otherwise the budget_factor could already be part of the specified total spend)
        self.total_spend = total_spend  # Optionally a number, or a list of tuples of time-spending pairs e.g. [(2018,10000),(2020,200000)]
        self.t = sc.promotetoarray(t) if t is not None else ()
        self.budget_factor = budget_factor

    def get_hard_constraint(self,optimization, instructions):
        # First, at each time point where a program overwrite exists, we need to store
        # the names of all of the programs being overwritten
        # e.g.
        # hard_constraints['programs'][2020] = ['Program 1','Program 2']
        # hard_constraints['programs'][2030] = ['Program 2','Program 3']
        # By convention, an Adjustable affecting a program should store the program's name in the
        # `prog_name` attribute. If a program reaches multiple programs, then `prog_name` will be a list

        hard_constraints = {}
        hard_constraints['programs'] = defaultdict(set)  # It's a set so that it will work properly if multiple Adjustments reach the same parameter at the same time. However, this would a bad idea and nobody should do this!
        for adjustment in optimization.adjustments:
            if hasattr(adjustment, 'prog_name'):
                for t in list(adjustment.t):
                    if isinstance(adjustment.prog_name,list):
                        hard_constraints['programs'][t].update(adjustment.prog_name)
                    else:
                        hard_constraints['programs'][t].add(adjustment.prog_name)

        # Now we have a set of times and programs for which we need to get total spend, and
        # also which programs should be included in the total for that year
        #
        # hard_constraints['total_spend'][2020] = 300
        # hard_constraints['total_spend'][2030] = 400
        hard_constraints['total_spend'] = {}
        for t, progs in hard_constraints['programs'].items():
            if isinstance(self.total_spend, list):
                for spend in self.total_spend:
                    if t == spend[0]:
                        hard_constraints['total_spend'][t] = spend[1]*self.budget_factor
            elif self.total_spend:
                hard_constraints['total_spend'][t] = self.total_spend*self.budget_factor
            else:
                total_spend = 0.0
                for prog in progs:
                    total_spend += instructions.alloc[prog].get(t)
                hard_constraints['total_spend'][t] = total_spend*self.budget_factor

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
            hard_constraints['bounds'][t] = dict()
            # If there is an Adjustable that reaches this Program in the appropriate year:
            for adjustment in optimization.adjustments:
                if hasattr(adjustment, 'prog_name') and adjustment.prog_name in progs and t in adjustment.t:
                    if isinstance(adjustment, SpendingAdjustment):
                        idx = np.where(adjustment.t == t)[0][0] # If it is a SpendingAdjustment then set bounds from the appropriate Adjustable
                        adjustable = adjustment.adjustables[idx]
                        hard_constraints['bounds'][t][adjustment.prog_name] = adjustable.get_hard_bounds(instructions.alloc[adjustment.prog_name].get(t)) # The instructions should already have the initial spend on this program inserted. This may be inconsistent if multiple Adjustments reach the same program...!
                    else:
                        hard_constraints['bounds'][t][adjustment.prog_name] = (0.0, np.inf) # If the Adjustment reaches spending but is not a SpendingAdjustment then do not constrain the alloc

        return hard_constraints

    def constrain_instructions(self,instructions, hard_constraints):

        penalty = 0.0

        for t, total_spend in hard_constraints['total_spend'].items():
            if self.t and not t in self.t:
                continue

            x0 = sc.odict()  # Order matters here
            bounds = []
            progs = hard_constraints['programs'][t]  # Programs eligible for constraining at this time
            LinearConstraint = [{'type': 'eq', 'fun': lambda x: np.sum(x) - total_spend,'jac':lambda x: np.ones(x.shape)}]  # Constrain spend

            for prog in progs:
                x0[prog] = instructions.alloc[prog].get(t)
                bounds.append(hard_constraints['bounds'][t][prog])

            x0_array = np.array(x0.values()).ravel()
            res = scipy.optimize.minimize(lambda x: np.sqrt(np.sum((x - x0_array) ** 2)), x0_array, bounds=bounds,constraints=LinearConstraint)

            if not res['success']:
                logger.error('TotalSpendConstraint failed - how to handle this is yet to be determined')

            penalty += np.sqrt(np.sum((res['x'] - x0_array)**2)) # Penalty is the distance between the unconstrained budget and the constrained budget

            for name, val in zip(x0.keys(), res['x']):
                instructions.alloc[name].insert(t,val)

        return penalty
    

class OptimInstructions(NamedItem):
    def __init__(self, json=None):
        self.name = json['name']
        self.json = json
    
    def make(self, project=None):
        proj = project
        name              = self.json['name']
        parset_name       = self.json['parset_name'] # WARNING, shouldn't be unused
        progset_name      = self.json['progset_name']
        start_year        = self.json['start_year']
        end_year          = self.json['end_year']
        budget_factor     = self.json['budget_factor']
        objective_weights = self.json['objective_weights']
        prog_spending     = self.json['prog_spending']
        maxtime           = self.json['maxtime']
    
        progset = proj.progsets[progset_name] # Retrieve the progset
    
        # Add a spending adjustment in the program start year for every program in the progset, using the lower/upper bounds
        # passed in as arguments to this function
        adjustments = []
        for prog_name in progset.programs:
            limits = prog_spending[prog_name]
            adjustments.append(SpendingAdjustment(prog_name,t=start_year,limit_type='abs',lower=limits[0],upper=limits[1]))
    
        # Add a total spending constraint with the given budget scale up
        constraints = [TotalSpendConstraint(budget_factor=budget_factor)]
    
        # Add all of the terms in the objective
        measurables = []
        for mname,mweight in objective_weights.items():

            if mname == 'finalstage' and mweight:
                measurables = MaximizeCascadeFinalStage('main',[end_year],pop_names='all')
                break
            elif mname == 'conversion' and mweight:
                measurables = MaximizeCascadeConversionRate('main',[end_year],pop_names='all')
                break
            else:
                measurables.append(Measurable(mname,t=[start_year,end_year],weight=mweight))
                
        # Create the Optimization object
        optim = Optimization(name=name, parsetname=parset_name, progsetname=progset_name, adjustments=adjustments, measurables=measurables, constraints=constraints, maxtime=maxtime)
        
        return optim
    
    

class Optimization(NamedItem):
    """ An object that defines an Optimization to perform """

    def __init__(self,  name=None, parsetname=None, progsetname=None, adjustments=None, measurables=None, constraints=None,  maxtime=None, maxiters=None):

        # Get the name
        if name is None:
            name = 'default'
        NamedItem.__init__(self, name)

        self.parsetname = parsetname
        self.progsetname = progsetname
        self.maxiters = maxiters # Not snake_case to match ASD
        self.maxtime = maxtime # Not snake_case to match ASD

        assert adjustments is not None, 'Must specify some adjustments to carry out an optimization'
        assert measurables is not None, 'Must specify some measurables to carry out an optimization'
        print('warning, replace with promotetolist()')
        self.adjustments = [adjustments] if not isinstance(adjustments,list) else adjustments
        self.measurables = [measurables] if not isinstance(measurables,list) else measurables

        if constraints:
            self.constraints = [constraints] if not isinstance(constraints,list) else constraints
        else:
            self.constraints = None
        
        if adjustments is None or measurables is None:
            raise AtomicaException('Must supply either a json or an adjustments+measurables')
        return
    
    
    def __repr__(self):
        return sc.desc(self)
    
    def get_initialization(self,progset,instructions):
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

    def get_hard_constraints(self,x0,instructions):
        # Return hard constraints based on the starting initialization
        instructions = sc.dcp(instructions)
        self.update_instructions(x0,instructions)
        if not self.constraints:
            return None
        else:
            return [x.get_hard_constraint(self,instructions) for x in self.constraints]

    def constrain_instructions(self,instructions,hard_constraints):
        constraint_penalty = 0.0
        if self.constraints:
            for constraint,hard_constraint in zip(self.constraints,hard_constraints):
                constraint_penalty += constraint.constrain_instructions(instructions,hard_constraint)
        return constraint_penalty

    def compute_objective(self,model):
        # Take in a completed model run
        # Compute the objective based on the measurables
        # Program name will map to spending array for that program
        objective = 0.0
        for measurable in self.measurables:
            objective += measurable.eval(model)
        return objective


def _asd_objective(asd_values, pickled_model=None, optimization=None, hard_constraints=None):
    # Compute the objective in ASD

    # Unpickle model
    model = pickle.loads(pickled_model)

    # Inject the ASD vector into the instructions
    optimization.update_instructions(asd_values,model.program_instructions)

    # Constrain the alloc
    constraint_penalty = optimization.constrain_instructions(model.program_instructions,hard_constraints)
    # Use the updated instructions to run the model
    model.process()

    # Compute the objective function based on the model calculated values and return it
    # TODO - constraint_penalty is an interesting idea but need to make sure it doesn't dominate the actual objective
    # Using it directly seems to prioritize meeting the constraint and with ASD's single-parameter stepping this prevents convergence
    obj_val = 0.0*constraint_penalty + optimization.compute_objective(model)

    return obj_val

def optimize(project,optimization,parset,progset,instructions,x0=None,xmin=None,xmax=None,hard_constraints=None):
    # The ASD initialization, xmin and xmax values can optionally be

    model = Model(project.settings, project.framework, parset, progset, instructions)
    pickled_model = pickle.dumps(model)

    initialization = optimization.get_initialization(progset,model.program_instructions)
    x0 = x0 if x0 is not None else initialization[0]
    xmin = xmin if xmin is not None else initialization[1]
    xmax = xmax if xmax is not None else initialization[2]

    if not hard_constraints:
        hard_constraints = optimization.get_hard_constraints(x0,model.program_instructions) # The optimization passed in here knows how to calculate the hard constraints based on the program instructions

    args = {
        'pickled_model': pickled_model,
        'optimization': optimization,
        'hard_constraints': hard_constraints,
    }

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

    x_opt = sc.asd(_asd_objective,x0,args,**optim_args)[0]
    optimization.update_instructions(x_opt,model.program_instructions)
    optimization.constrain_instructions(model.program_instructions,hard_constraints)
    return model.program_instructions # Return the modified instructions

#def parallel_optimize(project,optimization,parset,progset,program_instructions):
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



