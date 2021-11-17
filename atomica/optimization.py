"""
Implements various Optimizations in Atomica

This module implements the :class:`Optimization` class, which contains the
information required to perform an optimization in Atomica. An Optimization
effectively serves as a mapping from one set of program instructions to another.

"""

import logging
import pickle
from collections import defaultdict

import numpy as np
import scipy.optimize

import sciris as sc
from .cascade import get_cascade_vals
from .model import Model, Link
from .parameters import ParameterSet
from .programs import ProgramSet, ProgramInstructions
from .results import Result
from .system import logger, NotFoundError
from .utils import NamedItem
from .utils import TimeSeries

__all__ = ["InvalidInitialConditions", "UnresolvableConstraint", "FailedConstraint", "Adjustable", "Adjustment", "SpendingAdjustment", "StartTimeAdjustment", "ExponentialSpendingAdjustment", "SpendingPackageAdjustment", "PairedLinearSpendingAdjustment", "Measurable", "MinimizeMeasurable", "MaximizeMeasurable", "AtMostMeasurable", "AtLeastMeasurable", "IncreaseByMeasurable", "DecreaseByMeasurable", "MaximizeCascadeStage", "MaximizeCascadeConversionRate", "Constraint", "TotalSpendConstraint", "Optimization", "optimize"]


class InvalidInitialConditions(Exception):
    """
    Invalid initial parameter values

    This error gets thrown if the initial conditions yield an objective value
    that is not finite

    """

    pass


class UnresolvableConstraint(Exception):
    """
    Unresolvable (ill-posed) constraint

    This error gets thrown if it is _impossible_ to satisfy the constraints. There are
    two modes of constraint failure
    - The constraint might not be satisfied on this iteration, but could be satisfied by other
      parameter values
    - The constraint is impossible to satisfy because it is inconsistent (for example, if the
      total spend is greater than the sum of the upper bounds on all the individual programs)
      in which case the algorithm cannot continue
    This error gets raised in the latter case, while the former should result in the iteration
    being skipped

    """

    pass


class FailedConstraint(Exception):
    """
    Not possible to apply constraint

    This error gets raised if a ``Constraint`` is unable to transform the instructions
    given the supplied parameter values (but other values may be acceptable). It signals
    that the algorithm should proceed immediately to the next iteration.

    """

    pass


class Adjustable:
    """
    Class to store single optimizable parameter

    An ``Adjustable`` represents a single entry in the ASD matrix. An ``Adjustment`` uses one or more
    ``Adjustables`` to make changes to the program instructions.

    :param name: The name of the adjustable
    :param limit_type: If bounds are provided, are they relative or absolute (``'abs'`` or ``'rel'``)
    :param lower_bound: Optionally specify minimum value
    :param upper_bound: Optionally specify maximum value
    :param initial_value: Optionally specify initial value. Most commonly, the initial value would be set by the ``Adjustment`` containing the ``Adjustable``

    """

    def __init__(self, name, limit_type="abs", lower_bound=-np.inf, upper_bound=np.inf, initial_value=None):
        self.name = name
        self.limit_type = limit_type
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.initial_value = initial_value

    def get_hard_bounds(self, x0: float = None) -> tuple:
        """
        Return hard bounds for the adjustable

        The hard bounds could be relative or absolute. If they are relative, then they are treated
        as being relative to the initial value for this adjustable. This is because not all adjustables
        can be directly drawn from the program instructions (e.g. parametric overwrites) in which case
        it would not be possible to extract initial values from the instructions alone. For consistency,
        all adjustables behave the same way with constraints relative to their initialization.

        :param x0: The reference value for relative constraints - only required if the limit type is not absolute
        :return: A tuple with ``(min,max)`` limits

        """

        self.lower_bound = self.lower_bound if self.lower_bound is not None else -np.inf
        self.upper_bound = self.upper_bound if self.upper_bound is not None else np.inf
        xmin = self.lower_bound if self.limit_type == "abs" else x0 * self.lower_bound
        xmax = self.upper_bound if self.limit_type == "abs" else x0 * self.upper_bound
        return xmin, xmax


class Adjustment:
    """
    Class to represent changes to instructions

    An ``Adjustment`` represents a change to program instructions, governed by one or more ``Adjustables``.
    This base class specifies the interface for all ``Adjustments``

    :param name: The name of the adjustment

    """

    def __init__(self, name):
        self.name = name
        self.adjustables = list()  #: A list of ``Adjustables``

    def get_initialization(self, progset: ProgramSet, instructions: ProgramInstructions) -> list:
        """
        Return initial values for ASD

        :param progset: The ``ProgramSet`` being used for the optimization
        :param instructions: The initial instructions
        :return: A list of initial values, one for each adjustable

        """
        return [x.initial_value for x in self.adjustables]

    def update_instructions(self, adjustable_values, instructions: ProgramInstructions):
        # adjustable_values contains the values for each adjustable in self.adjustables
        # at the current ASD iteration. This function updates the provided instructions in place
        return


class SpendingAdjustment(Adjustment):
    """
    Adjust program spending

    This adjustment class represents making a spending quantity adjustable. By default, the
    base class simply overwrites the spending value at a particular point in time
    A SpendingAdjustment has a separate Adjustable for each time reached (independently)

    :param prog_name: The code name of a program
    :param t: A single time, or list/array of times at which to make adjustments
    :param limit_type: Interpret ``lower`` and ``upper`` as absolute or relative limits (should be ``'abs'`` or ``'rel'``)
    :param lower: Lower bound (0 by default). A single value (used for all times) or a list/array the same length as ``t``
    :param upper: Upper bound (``np.inf`` by default). A single value (used for all times) or a list/array the same length as ``t``
    :param initial: Optionally specify the initial value, either as a scalar or list/array the same length as ``t``. If not specified,
                    the initial spend will be drawn from the program instructions, or the progset.
    """

    def __init__(self, prog_name, t, limit_type="abs", lower=0.0, upper=np.inf, initial=None):
        Adjustment.__init__(self, name=prog_name)
        self.prog_name = prog_name
        self.t = sc.promotetoarray(t)  # Time at which to apply the adjustment

        lower = sc.promotetolist(lower, keepnone=True)
        if len(lower) == 1:
            lower = lower * len(self.t)
        else:
            assert len(lower) == len(self.t), "If supplying lower bounds, you must either specify one, or one for every time point"

        upper = sc.promotetolist(upper, keepnone=True)
        if len(upper) == 1:
            upper = upper * len(self.t)
        else:
            assert len(upper) == len(self.t), "If supplying upper bounds, you must either specify one, or one for every time point"

        initial = sc.promotetolist(initial, keepnone=True)
        if len(initial) == 1:
            initial = initial * len(self.t)
        else:
            assert len(initial) == len(self.t), "If supplying initial values, you must either specify one, or one for every time point"

        self.adjustables = [Adjustable(prog_name, limit_type, lower_bound=lb, upper_bound=ub, initial_value=init) for lb, ub, init in zip(lower, upper, initial)]

    def update_instructions(self, adjustable_values, instructions: ProgramInstructions):
        # There is one Adjustable for each time point, so the adjustable_values
        # are a list of this same length, one value for each time point
        for i, t in enumerate(self.t):
            if self.prog_name not in instructions.alloc:
                instructions.alloc[self.prog_name] = TimeSeries(t=t, vals=adjustable_values[i])
            else:
                instructions.alloc[self.prog_name].insert(t, adjustable_values[i])

    def get_initialization(self, progset: ProgramSet, instructions: ProgramInstructions) -> list:
        """
        Return initial values for ASD

        The initial values correspond to either

        - The explicitly specified initial spend
        - The initial spend from the program set/instructions

        Note that the initial spend is NOT clipped to any bounds. This is because the initial spend is in turn used to compute
        relative spending constraints. If the initial spend is not consistent then an error will be subsequently raised
        at that point.

        :param progset: The ``ProgramSet`` being used for the optimization
        :param instructions: The initial instructions
        :return: A list of initial values, one for each adjustable

        """

        initialization = []
        for adjustable, t in zip(self.adjustables, self.t):
            if adjustable.initial_value is not None:
                initialization.append(adjustable.initial_value)
            else:
                alloc = progset.get_alloc(t, instructions)
                initialization.append(alloc[self.prog_name][0])  # The Adjustable's name corresponds to the name of the program being overwritten.
        return initialization


class StartTimeAdjustment(Adjustment):
    """
    Optimize program start year

    This is an example of an Adjustment that does not target a spending value

    """

    def __init__(self, name, lower, upper, initial):
        Adjustment.__init__(self, name=name)
        self.adjustables = [Adjustable("start_year", limit_type="abs", lower=lower, upper=upper, initial=initial)]

    def update_instructions(self, adjustable_values, instructions: ProgramInstructions):
        instructions.start_year = adjustable_values[0]

    def get_initialization(self, progset, instructions: ProgramInstructions):
        if self.initial_value:
            return self.initial_value
        else:
            return instructions.start_year


class ExponentialSpendingAdjustment(Adjustment):
    """
    Parametric overwrite example

    This is an example of an Adjustment that uses a function of several variables to
    compute time-dependent spending.

    """

    # Example of a parametric time-varying budget where multiple parameters
    # are mapped to spending via a function

    def __init__(self, prog_name, t, t_0, t_end, p1, a1, a2):
        Adjustment.__init__(self, name=prog_name)
        self.prog_name = prog_name
        self.t = t  # Vector of time values instructions are updated at
        self.t_0 = t_0  # non-adjustable parameter
        self.t_end = t_end  # non_adjustable parameter
        self.adjustables = [Adjustable("p1", initial_value=p1), Adjustable("a1", initial_value=a1), Adjustable("a2", initial_value=a2)]  # Would need to specify initial values and limits for these parameters

    # Note - we can use get_initialization from the base class because all of the Adjustables
    # have explicit initial values. Note that it's essential to provide explicit initial values
    # for any Adjustable that does not explicitly appear in the instructions. Although in theory,
    # it would be possible to write a `get_initialization` function that fits the Adjustables
    # to the initial spending...

    def update_instructions(self, adjustable_values, instructions: ProgramInstructions):
        # p1*exp(a1*(t-t_0))*exp(b1*(t-t_end))
        instructions.alloc[self.prog_name][self.t] = adjustable_values[0] * np.exp(adjustable_values[1] * (self.t - self.t_0)) * np.exp(adjustable_values[2] * (self.t - self.t_end))


class SpendingPackageAdjustment(Adjustment):
    """
    Adjustment to set total spending on several programs

    This adjustment can be used when it is important to constrain the sum of spending on multiple programs. For example,
    a package could be defined for 'MDR short' and 'MDR standard' standard programs, where the adjustments would be the
    total spend on MDR, and the fraction spent on MDR short.
    """

    def __init__(self, package_name: str, t, prog_names: list, initial_spends, min_props: list = None, max_props: list = None, min_total_spend: float = 0.0, max_total_spend: float = np.inf):
        """

        :param package_name:
        :param t:
        :param prog_names:
        :param initial_spends:
        :param min_props: List of minimum proportion to spend on each program, same length as ``prog_names``
        :param max_props: List of maximum proportion to spend on each program, same length as ``prog_names``
        :param min_total_spend: Minimum total spend
        :param max_total_spend: Maximum total spend

        """

        #        super().__init__(self, name=package_name)
        self.name = package_name
        self.prog_name = prog_names
        self.t = t
        self.min_props = [0.0 for _ in self.prog_name] if min_props is None else min_props
        self.max_props = [1.0 for _ in self.prog_name] if max_props is None else max_props

        assert sum(min_props) <= 1, "Constraining fractions of an intervention package where the minimum total is >1 is impossible"
        assert sum(max_props) >= 1, "Constraining fractions of an intervention package where the maximum total is <1 is impossible"

        self.adjustables = []
        for pn, program in enumerate(self.prog_name):
            current_prop = initial_spends[pn] / sum(initial_spends)
            # set to the current proportion - note that the overall fractions won't end up being constrained so will have to be rescaled
            # Similarly, the upper and lower_bounds here will still need to be enforced later after scaling when updating instructions
            self.adjustables.append(Adjustable("frac_" + program, initial_value=current_prop, lower_bound=min_props[pn], upper_bound=max_props[pn]))

        # total spending can be adjusted as a single adjustable
        self.adjustables.append(Adjustable("package_spend", initial_value=sum(initial_spends), lower_bound=min_total_spend, upper_bound=max_total_spend))

    def update_instructions(self, adjustable_values, instructions):
        naive_frac_total = sum(adjustable_values[:-1])
        scaled_fracs = [av / naive_frac_total for av in adjustable_values[:-1]]  # an array with a sum of 1, scaling all fractions

        # rescale anything violating a lower bound
        scaled_fracs = [max(self.min_props[pn], min(self.max_props[pn], val)) for pn, val in enumerate(scaled_fracs)]
        difference = 1.0 - sum(scaled_fracs)

        # just progressively add or subtract the difference to the first program in the list - this is perhaps a bit biased as an algorithm and could be improved,
        # but if it produces a suboptimal outcome then an adjustment should exist to improve on it!
        pn = 0
        while not sc.approx(difference, 0.0):
            scaled_fracs[pn] = max(self.min_props[pn], min(self.max_props[pn], scaled_fracs[pn] + difference))
            difference = 1.0 - sum(scaled_fracs)
            pn += 1
        if difference != 0.0:  # e.g. if it's some trivial non-zero tiny fraction, let's not care if we're violating a constraint...
            scaled_fracs[-1] += difference
        assert sc.approx(sum(scaled_fracs), 1.0), "Need to fix the algorithm if not (difference %s)!" % (difference)

        # now that the scaled fractions total to 1 and don't violate any constraints, update the spending on each program
        total_spending = adjustable_values[-1]  # last on the list
        for pn, prog_name in enumerate(self.prog_name):
            this_prog_spend = [scaled_fracs[pn] * total_spending]
            if prog_name not in instructions.alloc:
                instructions.alloc[prog_name] = TimeSeries(t=self.t, vals=this_prog_spend)
            else:
                instructions.alloc[prog_name].insert(t=self.t, v=this_prog_spend)


class PairedLinearSpendingAdjustment(Adjustment):
    """
    Parametric overwrite with multiple programs

    This example Adjustment demonstrates a parametric time-varying budget reaching more than one
    program. A single adjustable corresponding to the rate of change simultaneously acts on
    two programs in opposite directions

    """

    def __init__(self, prog_names, t):
        Adjustment.__init__(self, name=None)
        assert len(prog_names) == 2, "PairedLinearSpendingAdjustment needs exactly two program names"
        self.prog_name = prog_names  # Store names in the attribute 'prog_name' so that TotalSpendConstraint picks this up
        self.t = t  # [t_start,t_stop] for when to start/stop ramping
        self.adjustables = [Adjustable("ramp", initial_value=0.0)]

    def update_instructions(self, adjustable_values, instructions: ProgramInstructions):

        gradient = adjustable_values[0]
        tspan = self.t[1] - self.t[0]

        if gradient < 0:  # We are transferring money from program 2 to program 1
            available = -instructions.alloc[self.prog_name[1]].get(self.t[0])
            max_gradient = float(available) / tspan
            if gradient < max_gradient:
                gradient = max_gradient
        else:
            available = instructions.alloc[self.prog_name[0]].get(self.t[0])
            max_gradient = float(available) / tspan
            if gradient > max_gradient:
                gradient = max_gradient

        funding_change = gradient * tspan  # Amount transferred from program 1 to program 2

        # This does not change the amount of funds allocated in the initial year
        for prog in self.prog_name:
            instructions.alloc[prog].insert(self.t[0], instructions.alloc[prog].interpolate(self.t[0])[0])
            instructions.alloc[prog].remove_between(self.t)

        instructions.alloc[self.prog_name[0]].insert(self.t[1], instructions.alloc[self.prog_name[0]].get(self.t[0]) - funding_change)
        instructions.alloc[self.prog_name[1]].insert(self.t[1], instructions.alloc[self.prog_name[1]].get(self.t[0]) + funding_change)


class Measurable:
    """
    Optimization objective

    A ``Measurable`` is a class that returns an objective value based on a simulated
    ``Model`` object. It takes in a ``Model`` and returns a scalar value. Often, an optimization
    may contain multiple ``Measurable`` objects, and the objective value returned by each of them
    is summed together.

    :param measurable_name: The base measurable class accepts the name of a program (for spending) or a quantity supported by ``Population.get_variable()``
    :param t: Single year, or a list of two start/stop years. If specifying a single year, that year must appear in the simulation output.
              The quantity will be summed over all simulation time points
    :param pop_names: The base `Measurable` class takes in the names of the populations to use. If multiple populations are provided, the objective will be added across the named populations
    :param weight: The weight factor multiplies the quantity

    """

    def __init__(self, measurable_name, t, pop_names=None, weight=1.0):
        self.measurable_name = measurable_name
        self.t = sc.promotetoarray(t)
        assert len(self.t) <= 2, "Measurable time must either be a year, or the `[low,high)` values defining a period of time"
        self.weight = weight
        self.pop_names = pop_names

    def eval(self, model, baseline):
        # This is the main interface with the optimization code - this function gets called
        # to return the transformed, weighted objective value from this Measurable for use in ASD
        # Only overload this if you want to customize the transformation and weighting
        return self.weight * self.get_objective_val(model, baseline)

    def get_baseline(self, model):
        """
        Return cached baseline values

        Similar to ``get_hard_constraint``, sometimes a relative ``Measurable`` might be desired e.g. 'Reduce deaths by at least 50%'.
        In that case, we need to perform a procedure similar to getting a hard constraint, where the ``Measurable`` receives an initial
        ``Model`` object and extracts baseline data for subsequent use in ``get_objective_val``.

        Thus, the output of this function is paired to its usage in ``get_objective_val``.

        :param model:
        :return: The value to pass back to the ``Measurable`` during optimization
        """

        return None

    def get_objective_val(self, model: Model, baseline) -> float:
        """
        Return objective value

        This method should return the _unweighted_ objective value. Note that further transformation may occur

        :param model: A ``Model`` object after integration
        :param baseline: The baseline variable returned by this ``Measurable`` at the start of optimization
        :return: A scalar objective value

        """

        # This returns the base objective value, prior to any function transformation
        # or weighting. The function transformation and weighting are handled by this base
        # class - derived classes may wish to not expose things like the function mapping
        # in their constructors, if that wouldn't be appropriate. But otherwise, they can
        # inherit this behaviour for free. So derived classes should overload this method
        #
        # The base class has the default behaviour that the 'measurable name' is a model variable
        if len(self.t) == 1:
            t_filter = model.t == self.t  # boolean vector for whether to use the time point or not. This could be relaxed using interpolation if needed, but safer not to unless essential
        else:
            t_filter = (model.t >= self.t[0]) & (model.t < self.t[1])  # Don't include upper bound, so [2018,2019] will include exactly one year

        if self.measurable_name in model.progset.programs:
            alloc = model.progset.get_alloc(model.t, model.program_instructions)
            val = np.sum(alloc[self.measurable_name][t_filter])
        else:  # If the measurable is a model output...
            val = 0.0
            matched = False  # Flag whether any variables were found
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
                    vars = pop.get_variable(self.measurable_name)  # If variable is missing and the pop was explicitly defined, raise the error
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


class MinimizeMeasurable(Measurable):
    # Syntactic sugar for a measurable that minimizes its quantity
    def __init__(self, measurable_name, t, pop_names=None):
        Measurable.__init__(self, measurable_name, t=t, weight=1, pop_names=pop_names)


class MaximizeMeasurable(Measurable):
    # Syntactic sugar for a measurable that maximizes its quantity
    def __init__(self, measurable_name, t, pop_names=None):
        Measurable.__init__(self, measurable_name, t=t, weight=-1, pop_names=pop_names)


class AtMostMeasurable(Measurable):
    """
    Enforce quantity is below a value

    This Measurable imposes a penalty if the quantity is larger than some threshold
    The initial points should be 'valid' in the sense that the quantity starts out
    below the threshold (and during optimization it will never be allowed to cross
    the threshold).

    Typically, this Measurable would be used in conjunction with other measurables -
    for example, optimizing one quantity while ensuring another quantity does not
    cross a threshold.

    The measurable returns ``np.inf`` if the condition is violated, and ``0.0`` otherwise.

    """

    def __init__(self, measurable_name, t, threshold, pop_names=None):
        Measurable.__init__(self, measurable_name, t=t, weight=np.inf, pop_names=pop_names)
        self.weight = 1.0
        self.threshold = threshold

    def get_objective_val(self, model, baseline):
        val = Measurable.get_objective_val(self, model, baseline)
        return np.inf if val > self.threshold else 0.0

    def __repr__(self):
        return "AtMostMeasurable(%s < %f)" % (self.measurable_name, self.threshold)


class AtLeastMeasurable(Measurable):
    """
    Enforce quantity exceeds a value

    This Measurable imposes a penalty if the quantity is smaller than some threshold
    The initial points should be 'valid' in the sense that the quantity starts out
    above the threshold (and during optimization it will never be allowed to cross
    the threshold)

    Typically, this Measurable would be used in money minimization in conjunction
    with measurables that aim to minimize spending.

    The measurable returns ``np.inf`` if the condition is violated, and ``0.0`` otherwise.

    """

    def __init__(self, measurable_name, t, threshold, pop_names=None):
        Measurable.__init__(self, measurable_name, t=t, weight=np.inf, pop_names=pop_names)
        self.weight = 1.0
        self.threshold = threshold

    def get_objective_val(self, model, baseline):
        val = Measurable.get_objective_val(self, model, baseline)
        return np.inf if val < self.threshold else 0.0

    def __repr__(self):
        return "AtLeastMeasurable(%s > %f)" % (self.measurable_name, self.threshold)


class IncreaseByMeasurable(Measurable):
    """
    Increase quantity by percentage

    This Measurable stores the value of a quantity using the original instructions.
    It then requires that there is a minimum increase in the value of the quantity
    during optimization. For example

    >>> IncreaseByMeasurable('alive',2030,0.05)

    This Measurable would correspond to an increase of 5% in the number of people
    alive in 2030.

    The measurable returns ``np.inf`` if the condition is violated, and ``0.0`` otherwise.

    :param measurable_name: The base measurable class accepts the name of a program (for spending) or a quantity supported by ``Population.get_variable()``
    :param t: Single year, or a list of two start/stop years. If specifying a single year, that year must appear in the simulation output.
              The quantity will be summed over all simulation time points
    :param increase: The amount by which to increase the measurable (e.g. 0.05 for a 5% increase). Use ``target_type='abs'`` to specify an absolute increase
    :param pop_names: The base `Measurable` class takes in the names of the populations to use. If multiple populations are provided, the objective will be added across the named populations
    :param target_type: Specify fractional 'frac' or absolute 'abs' increase (default is fractional)

    """

    def __init__(self, measurable_name, t, increase, pop_names=None, target_type="frac"):

        Measurable.__init__(self, measurable_name, t=t, weight=np.inf, pop_names=pop_names)
        assert increase >= 0, "Cannot set negative increase"
        self.weight = 1.0
        self.increase = increase  # Required increase
        self.target_type = target_type

    def get_baseline(self, model) -> float:
        return Measurable.get_objective_val(self, model, None)  # Get the baseline value using the underlying Measurable

    def get_objective_val(self, model: Model, baseline: float) -> float:
        val = Measurable.get_objective_val(self, model, None)
        if self.target_type == "frac":
            return np.inf if (val / baseline) < (1 + self.increase) else 0.0
        elif self.target_type == "abs":
            return np.inf if val < (baseline + self.increase) else 0.0
        else:
            raise Exception("Unknown target type")


class DecreaseByMeasurable(Measurable):
    """
    Decrease quantity by percentage

    This Measurable stores the value of a quantity using the original instructions.
    It then requires that there is a minimum increase in the value of the quantity
    during optimization. For example

    >>> DecreaseByMeasurable('deaths',2030,0.05)

    This Measurable would correspond to an decrease of 5% in the number of deaths in 2030.

    The measurable returns ``np.inf`` if the condition is violated, and ``0.0`` otherwise.

    :param measurable_name: The base measurable class accepts the name of a program (for spending) or a quantity supported by ``Population.get_variable()``
    :param t: Single year, or a list of two start/stop years. If specifying a single year, that year must appear in the simulation output.
              The quantity will be summed over all simulation time points
    :param decrease: The amount by which to decrease the measurable (e.g. 0.05 for a 5% decrease). Use ``target_type='abs'`` to specify an absolute decrease
    :param pop_names: The base `Measurable` class takes in the names of the populations to use. If multiple populations are provided, the objective will be added across the named populations
    :param target_type: Specify fractional 'frac' or absolute 'abs' decrease (default is fractional)

    """

    def __init__(self, measurable_name, t, decrease, pop_names=None, target_type="frac"):

        Measurable.__init__(self, measurable_name, t=t, weight=np.inf, pop_names=pop_names)
        self.weight = 1.0
        assert decrease >= 0, "Set positive value for magnitude of decrease e.g. 0.05 for a 5%% decrease"
        assert target_type == "abs" or decrease <= 1, "Cannot decrease by more than 100%% - fractional decrease should be a value between 0 and 1"
        self.decrease = decrease
        self.target_type = target_type

    def get_baseline(self, model) -> float:
        return Measurable.get_objective_val(self, model, None)  # Get the baseline value using the underlying Measurable

    def get_objective_val(self, model: Model, baseline: float) -> float:
        val = Measurable.get_objective_val(self, model, None)
        if self.target_type == "frac":
            return np.inf if (val / baseline) > (1 - self.decrease) else 0.0
        elif self.target_type == "abs":
            return np.inf if val > (baseline - self.decrease) else 0.0
        else:
            raise Exception("Unknown target type")


class MaximizeCascadeStage(Measurable):
    # This Measurable will maximize the number of people in a cascade stage, whatever that stage is
    # e.g. `measurable = MaximizeCascadeStage('main',2020)
    # If multiple years are provided, they will be summed over
    # Could add option to weight specific years later on, if desired

    def __init__(self, cascade_name, t, pop_names="all", weight=1.0, cascade_stage=-1):
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

    def get_objective_val(self, model, baseline):
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

    def __init__(self, cascade_name, t: float, pop_names="all", weight=1.0):
        Measurable.__init__(self, cascade_name, t=t, weight=-weight, pop_names=pop_names)
        if not isinstance(self.pop_names, list):
            self.pop_names = [self.pop_names]

    def get_objective_val(self, model, baseline):
        if self.t < model.t[0] or self.t > model.t[-1]:
            raise Exception("Measurable year for optimization (%d) is outside the simulation range (%d-%d)" % (self.t, model.t[0], model.t[-1]))
        result = Result(model=model)
        val = 0
        for pop_name in self.pop_names:
            cascade_vals = get_cascade_vals(result, self.measurable_name, pop_name, self.t)[0]
            cascade_array = np.hstack(cascade_vals.values())
            conversion = cascade_array[1:] / cascade_array[0:-1]
            val += np.sum(conversion)
        return val


class Constraint:
    """
    Store conditions to satisfy during optimization

    A Constraint represents a condition that must be satisfied by the Instructions
    after the cumulative effect of all adjustments. The Instructions are rescaled to
    satisfy the constraint directly (rather than changing the value of the Adjustables)
    although this distinction really only matters in the context of parametric spending.

    """

    def get_hard_constraint(self, optimization, instructions: ProgramInstructions):
        """
        Return hard constraint from initial instructions

        Often constraints can be specified relative to the initial conditions. For example,
        fixing total spend regardless of what the total spend is in the initial instructions.
        Therefore, during ``constrain_instructions``, it is necessary to examine properties
        from the initial instructions in order to perform the constraining.

        This method is called at the very start of optimization, passing in the initial instructions.
        It then returns an arbitrary value that is passed back to the instance's ``constrain_instructions``
        during optimization. For example, consider the total spending constraint

        - ``get_hard_constraint`` would extract the total spend from the initial instructions
        - This value is passed to ``constrain_instructions`` where it is used to rescale spending

        Because subclasses implement both ``get_hard_constraint`` and ``constrain_instructions``
        no assumptions need to be made about the value returned by this method - it simply needs
        to be paired to ``constrain_instructions``.

        :param optimization: An ``Optimization``
        :param instructions: A set of initial instructions to extract absolute constraints from
        :return: Arbitrary variable that will be passed back during ``constrain_instructions``
        """

        return

    def constrain_instructions(self, instructions: ProgramInstructions, hard_constraints) -> float:
        """
        Apply constraint to instructions

        Constrains the instructions, returns a metric penalizing the constraint
        If there is no penalty associated with adjusting (perhaps if all of the Adjustments are
        parametric?) then this would be 0.0. The penalty represents in some sense the quality
        of the constraint. For example, the default ``TotalSpendConstraint`` rescales spending
        such that the total spend matches a target value. The penalty reflects the distance between
        the requested spend and the constrained spend, so it is desirable to minimize it.

        If it is not possible to constrain the instructions, raise ``FailedConstraint``.

        :param instructions: The ``ProgramInstructions`` instance to constrain (in place)
        :param hard_constraints: The hard constraint returned by ``get_hard_constraint``
        :return: A numeric penalty value. Return `np.inf` if constraint penalty could not be computed
        :raises: :class:`FailedConstraint` if the instructions could not be constrained

        """

        return 0.0


class TotalSpendConstraint(Constraint):
    """
    Fix total spending

    This class implements a constraint on the total spend at every time point when a program
    is optimizable. A program is considered optimizable if an Adjustment reaches that program
    at the specified time. Spending is constrained independently at all times when any program
    is adjustable.

    The ``total_spend`` argument allows the total spending in a particular year to be explicitly specified
    rather than drawn from the initial allocation. This can be useful when using parametric programs where
    the adjustables do not directly correspond to spending value. If the total spend is not provided, it will
    automatically be computed from the first ASD step. Note that it is computed based on the initial instructions
    *after* the initial ASD values have been applied. This is because relative constraints on all adjustables are
    interpreted relative to the initial value of the adjustable, since not all adjustables map directly to values
    in the instructions. Since the adjustable hard upper and lower bounds are used as part of the constraint, for
    consistency, the total spend constraint itself is drawn from the same set of instructions (i.e. after the initial
    value has been applied). In cases where this is not the desired behaviour, the cause would likely be that the
    default value does not agree with a known desired total spend value. In that case, the desired total spend should
    simply be specified here explicitly as an absolute value.

    This constraint can also be set to only apply in certain years.

    The ``budget_factor`` multiplies the total spend at the time the ``hard_constraint`` is assigned
    Typically this is to scale up the available spending when that spending is being drawn from
    the instructions/progset (otherwise the budget_factor could already be part of the specified total spend)

    Note that if no times are specified, the budget factor should be a scalar but no explicit
    spending values can be specified. This is because in the case where different programs are
    optimized in different years, an explicit total spending constraint applying to all
    times is unlikely to be a sensible choice (so we just ask the user to specify the time as well).

    :param total_spend: A list of spending amounts the same size as ``t`` (can contain Nones), or ``None``.
                        For times in which the total spend is ``None``, it will be automatically set to the sum of
                        spending on optimizable programs in the corresponding year
    :param t: A time, or list of times, at which to apply the total spending constraint. If None, it will automatically be set to all years in which spending adjustments are being made
    :param budget_factor: The budget factor multiplies whatever the ``total_spend`` is. This can either be a single value, or a year specific value

    """

    def __init__(self, total_spend=None, t=None, budget_factor=1.0):
        self.total_spend = sc.promotetoarray(total_spend) if total_spend is not None else ()
        self.t = sc.promotetoarray(t) if t is not None else ()
        self.budget_factor = sc.promotetoarray(budget_factor)

        if t is None:
            assert total_spend is None, "If no times are specified, no total spend values can be specified either"
            assert len(self.budget_factor) == 1, "If no times are specified, the budget factor must be scalar"

        if t is not None and total_spend is not None:
            assert len(self.total_spend) == len(self.t), "If specifying both the times and values for the total spending constraint, their lengths must be the same"
        if len(self.budget_factor) > 1:
            assert len(self.budget_factor) == len(self.t), "If specifying multiple budget factors, you must also specify the years in which they are used"

    def get_hard_constraint(self, optimization, instructions: ProgramInstructions) -> dict:
        """
        Return hard constraint dictionary

        :param optimization: ``Optimization`` instance
        :param instructions: Initial ``ProgramInstructions``
        :return:
        """

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
        hard_constraints["programs"] = defaultdict(set)  # It's a set so that it will work properly if multiple Adjustments reach the same parameter at the same time. However, this would a bad idea and nobody should do this!
        for adjustment in optimization.adjustments:
            if hasattr(adjustment, "prog_name"):
                for t in list(adjustment.t):
                    if isinstance(adjustment.prog_name, list):
                        hard_constraints["programs"][t].update(adjustment.prog_name)
                    else:
                        hard_constraints["programs"][t].add(adjustment.prog_name)

        if len(self.t):
            # Check that every explictly specified time has
            # corresponding spending adjustments available for use
            missing_times = set(self.t) - set(hard_constraints["programs"].keys())
            if missing_times:
                raise Exception("Total spending constraint was specified in %s but the optimization does not have any adjustments at those times" % (missing_times))

        # Now we have a set of times and programs for which we need to get total spend, and
        # also which programs should be included in the total for that year
        #
        # hard_constraints['total_spend'][2020] = 300
        # hard_constraints['total_spend'][2030] = 400
        hard_constraints["total_spend"] = {}
        for t, progs in hard_constraints["programs"].items():
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
                hard_constraints["total_spend"][t] = total_spend * self.budget_factor
            else:
                hard_constraints["total_spend"][t] = total_spend * self.budget_factor[idx]

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

        hard_constraints["bounds"] = dict()

        for t, progs in hard_constraints["programs"].items():  # For each time point being constrained, and for each program
            if t not in hard_constraints["total_spend"]:
                # If the time is not one where the total spending constraint is being applied, then
                # just skip it
                continue

            hard_constraints["bounds"][t] = dict()
            # If there is an Adjustable that reaches this Program in the appropriate year:

            # Keep track of the absolute lower and upper bounds on spending permitted by the program constraints
            minimum_spend = 0.0
            maximum_spend = 0.0

            for adjustment in optimization.adjustments:
                if hasattr(adjustment, "prog_name") and np.array([prog in progs for prog in sc.promotetolist(adjustment.prog_name)]).all() and t in adjustment.t:
                    if isinstance(adjustment, SpendingAdjustment):
                        idx = np.where(adjustment.t == t)[0][0]  # If it is a SpendingAdjustment then set bounds from the appropriate Adjustable
                        adjustable = adjustment.adjustables[idx]
                        hard_constraints["bounds"][t][adjustment.prog_name] = adjustable.get_hard_bounds(instructions.alloc[adjustment.prog_name].get(t))  # The instructions should already have the initial spend on this program inserted. This may be inconsistent if multiple Adjustments reach the same program...!
                    elif isinstance(adjustment, SpendingPackageAdjustment):
                        spend_bounds = adjustment.adjustables[-1].get_hard_bounds()
                        for pn, prog in enumerate(sc.promotetolist(adjustment.prog_name)):
                            frac_bounds = adjustment.adjustables[pn].get_hard_bounds(instructions.alloc[prog].get(t))
                            #                            print (total_spend_bound, '\n...', adjustable.get_hard_bounds())
                            hard_constraints["bounds"][t][prog] = (spend_bounds[0] * frac_bounds[0], spend_bounds[1] * frac_bounds[1])
                    else:
                        for prog in sc.promotetolist(adjustment.prog_name):
                            hard_constraints["bounds"][t][prog] = (0.0, np.inf)  # If the Adjustment reaches spending but is not a SpendingAdjustment then do not constrain the alloc

                    for prog in sc.promotetolist(adjustment.prog_name):
                        minimum_spend += hard_constraints["bounds"][t][prog][0]
                        maximum_spend += hard_constraints["bounds"][t][prog][1]

            if minimum_spend > hard_constraints["total_spend"][t]:
                raise UnresolvableConstraint("The total spend in %.2f is constrained to %.2f but the individual programs have a total minimum spend of %.2f which is impossible to satisfy. Please either raise the total spending, or lower the minimum spend on one or more programs" % (t, hard_constraints["total_spend"][t], minimum_spend))

            if maximum_spend < hard_constraints["total_spend"][t]:
                raise UnresolvableConstraint("The total spend in %.2f is constrained to %.2f but the individual programs have a total maximum spend of %.2f which is impossible to satisfy. Please either lower the total spending, or raise the maximum spend on one or more programs" % (t, hard_constraints["total_spend"][t], maximum_spend))

        return hard_constraints

    def constrain_instructions(self, instructions: ProgramInstructions, hard_constraints: dict) -> float:
        """
        Apply total spend constraint

        :param instructions: The ``ProgramInstructions`` instance to constrain
        :param hard_constraints: Dictionary of hard constraints
        :return: Distance-like difference between initial spending and constrained spending, `np.inf` if constraint failed

        """

        penalty = 0.0

        for t, total_spend in hard_constraints["total_spend"].items():

            total_spend = sc.promotetoarray(total_spend).ravel()[0]  # Make sure total spend is a scalar
            x0 = sc.odict()  # Order matters here
            bounds = []
            progs = hard_constraints["programs"][t]  # Programs eligible for constraining at this time

            for prog in progs:
                x0[prog] = instructions.alloc[prog].get(t)
                bound = hard_constraints["bounds"][t][prog]
                bounds.append((bound[0] / total_spend, bound[1] / total_spend))
            x0_array = np.array(x0.values()).ravel()
            x0_array_scaled = x0_array / sum(x0_array)

            def jacfcn(x):
                dist = np.linalg.norm(x - x0_array_scaled)
                if dist == 0:
                    return np.zeros(x.shape)
                else:
                    return (x - x0_array_scaled) / dist

            # If x0_array_scaled satisfies all of the individual constraints, then we don't actually need to adjust the spending
            # at all. So first, check whether any of the individual constraints are being violated, if everything is OK,
            # then insert x0_array_scaled straight into the instructions
            for v, (low, high) in zip(x0_array_scaled, bounds):
                if v < low or v > high:
                    break
            else:
                for name, val in zip(x0.keys(), x0_array_scaled):
                    instructions.alloc[name].insert(t, val * total_spend)
                continue

            LinearConstraint = [{"type": "eq", "fun": lambda x: np.sum(x) - 1, "jac": lambda x: np.ones(x.shape)}]  # Constrain spend
            res = scipy.optimize.minimize(lambda x: np.linalg.norm(x - x0_array_scaled), x0_array_scaled, jac=jacfcn, bounds=bounds, constraints=LinearConstraint, method="SLSQP", options={"ftol": 1e-5, "maxiter": 1000})

            if not res["success"]:
                logger.warning("TotalSpendConstraint failed - rejecting proposed parameters")
                raise FailedConstraint()
            else:
                # TODO - disable this check for performance later on - this is just double checking to make check sure the constraint worked
                for v, (low, high) in zip(res["x"], bounds):
                    if v < low or v > high:
                        raise Exception("Rescaling algorithm did not return a valid result")

                penalty += total_spend * np.linalg.norm(res["x"] * total_spend - x0_array * total_spend)  # Penalty is the distance between the unconstrained budget and the constrained budget
                for name, val in zip(x0.keys(), res["x"]):
                    instructions.alloc[name].insert(t, val * total_spend)
        return penalty


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

    :param name:
    :param adjustments: An `Adjustment` or list of `Adjustment` objects
    :param measurables: A `Measurable` or list of `Measurable` objects
    :param constraints: Optionally provide a `Constraint` or list of `Constraint` objects
    :param maxtime: Optionally specify maximum ASD time
    :param maxiters: Optionally specify maximum number of ASD iterations or hyperopt evaluations
    :param method: One of ['asd','pso','hyperopt'] to use
                        - asd (to use normal ASD)
                        - pso (to use particle swarm optimization from pyswarm)
                        - hyperopt (to use hyperopt's Bayesian optimization function)

    """

    def __init__(self, name=None, adjustments=None, measurables=None, constraints=None, maxtime=None, maxiters=None, method="asd"):
        # Get the name
        if name is None:
            name = "default"
        NamedItem.__init__(self, name)

        self.maxiters = maxiters  #: Maximum number of ASD iterations or hyperopt evaluations
        self.maxtime = maxtime  #: Maximum ASD time
        self.method = method  #: Optimization method name

        assert adjustments is not None, "Must specify some adjustments to carry out an optimization"
        assert measurables is not None, "Must specify some measurables to carry out an optimization"
        self.adjustments = sc.promotetolist(adjustments)
        self.measurables = sc.promotetolist(measurables)

        if constraints:
            self.constraints = [constraints] if not isinstance(constraints, list) else constraints
        else:
            self.constraints = None

        if adjustments is None or measurables is None:
            raise Exception("Must supply either a json or an adjustments+measurables")
        return

    def __repr__(self):
        return sc.prepr(self)

    def get_initialization(self, progset: ProgramSet, instructions: ProgramInstructions) -> tuple:
        """
        Get initial values for each adjustment

        The initial conditions depend nontrivially on both the progset and the instructions. Spending is
        present in the progset and optionally overwritten in the instructions. Therefore, it is necessary
        to check both when determining initial spending. Extraction of the initial values for each
        ``Adjustment`` is delegated to the ``Adjustment`` itself.

        Note also that the return arrays have length equal to the number of ``Adjustables``
        (since an ``Adjustment`` may contain several ``Adjustables``).

        :param progset: The program set to extract initial conditions from
        :param instructions: Instructions to extract initial conditions from
        :return: Tuple containing ``(initial,low,high)`` with arrays for
            - The initial value of each adjustable
            - The lower limit for each adjustable
            - The upper limit for each adjustable
        """

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
                if x0[ptr] > xmax[ptr]:
                    raise InvalidInitialConditions('Adjustment "%s" has an adjustable with initial value of %.2f but an upper bound of %.2f' % (adjustment.name, x0[ptr], xmax[ptr]))
                elif x0[ptr] < xmin[ptr]:
                    raise InvalidInitialConditions('Adjustment "%s" has an adjustable with initial value of %.2f but a lower bound of %.2f' % (adjustment.name, x0[ptr], xmax[ptr]))
                ptr += 1

        return x0, xmin, xmax

    def update_instructions(self, asd_values, instructions: ProgramInstructions) -> None:
        """
        Apply all Adjustments

        This method takes in a list of values (same length as number of adjustables) and iteratively
        calls each ``Adjustment`` in the optimization to update the instructions (in place)

        :param asd_values: A list of values
        :param instructions: The ``ProgramInstructions`` instance to update

        """

        idx = 0
        for adjustment in self.adjustments:
            adjustment.update_instructions(asd_values[idx : idx + len(adjustment.adjustables)], instructions)
            idx += len(adjustment.adjustables)

    def get_hard_constraints(self, x0, instructions: ProgramInstructions) -> list:
        """
        Get hard constraints

        This method calls ``get_hard_constraint`` on each ``Constraint`` in the ``Optimization``
        iteratively, and returns them as a list.

        Note that the initial optimization values ``x0`` are applied _before_ the hard constraint is computed.
        This ensures that the hard constraints are relative to the initial conditions in the optimization, not
        the initial instructions. For example, if a parametric overwrite is present, the hard constraint will
        be relative to whatever spending is produced by the initial values of the parametric overwrite.

        :param x0: The initial values for optimization - these are applied to the instructions prior to extracting hard constraints
        :param instructions: The initial instructions
        :return: A list of hard constraints, as many items as there are constraints

        """
        # Return hard constraints based on the starting initialization
        instructions = sc.dcp(instructions)
        self.update_instructions(x0, instructions)
        if not self.constraints:
            return list()
        else:
            return [x.get_hard_constraint(self, instructions) for x in self.constraints]

    def get_baselines(self, pickled_model) -> list:
        """
        Return Measurable baseline values

        This method is run at the start of the `optimize` script, and is used to
        retrieve the baseline values for the Measurable. Note that the baseline values are obtained
        based on the original instructions (stored in the pickled model), independent of the initial
        parameters used for optimization. The logic is that the initial parameters for the optimization
        are a choice dictated by the numerics of optimization (e.g. needing to start from a particular
        part of the parameter space) rather than anything intrinsic to the problem, whereas the
        initial instructions reflect the actual baseline conditions.

        :param pickled_model:
        :param x0: The initial parameter values
        :param hard_constraints: List of hard constraint values
        :return: A list of Measurable baseline values

        """

        model = pickle.loads(pickled_model)
        model.process()
        baselines = [m.get_baseline(model) for m in self.measurables]
        return baselines

    def constrain_instructions(self, instructions: ProgramInstructions, hard_constraints: list) -> float:
        """
        Apply all constraints in-place, return penalty

        This method takes in the proposed instructions, and a list of hard constraints. Each constraint is
        applied to the instructions iteratively, passing in that constraint's own hard constraint, and the
        penalty is accumulated and returned.

        :param instructions: The current proposed ``ProgramInstructions``
        :param hard_constraints: A list of hard constraints the same length as the number of constraints
        :return: The total penalty value (if not finite, model integration will be skipped and the parameters will be rejected)

        """

        constraint_penalty = 0.0
        if self.constraints:
            for constraint, hard_constraint in zip(self.constraints, hard_constraints):
                constraint_penalty += constraint.constrain_instructions(instructions, hard_constraint)
        return constraint_penalty

    def compute_objective(self, model, baselines: list) -> float:
        """
        Return total objective function

        This method accumulates the objective values returned by each ``Measurable``, passing in
        the corresponding baseline values where required.

        :param model: A simulated ``Model`` object
        :param baselines: List of baseline values the same length as the number of ``Measurables``
        :return: The total/net objective value

        """

        # TODO - This method just adds the objective from each Measurable
        # It might be desirable in future to have more complex functions of the Measurable e.g.
        # sqrt of sum of squares. It's not clear yet whether this would be better as a transformation
        # applied here, or as a kind of meta-measurable. The former is probably simpler
        # to implement. But since there is no immediate need, this can be implemented later

        objective = 0.0
        for measurable, baseline in zip(self.measurables, baselines):
            objective += measurable.eval(model, baseline)
        return objective


def _objective_fcn(x, pickled_model, optimization, hard_constraints: list, baselines: list):
    """
    Return objective value

    This wrapper function takes in a vector of proposed parameters and returns the objective value.
    It is typically not called directly - instead, it is partialled to bind all arguments except ``x``
    and then passed to whichever optimization algorithm is used to optimize ``x``

    :param x: Vector of proposed parameter values
    :param pickled_model: A pickled ``Model`` - should contain a set of instructions
    :param optimization: An ``Optimization``
    :param hard_constraints: A list of hard constraints (should be the same length as ``optimization.constraints``)
    :param baselines: A list of measurable baselines (should be the same length as ``optimization.measurables``)
    :return:


    """

    try:
        model = pickle.loads(pickled_model)
        optimization.update_instructions(x, model.program_instructions)
        optimization.constrain_instructions(model.program_instructions, hard_constraints)
        model.process()
    except FailedConstraint:
        return np.inf  # Return an objective of `np.inf` if the constraints could not be satisfied by ``x``

    obj_val = optimization.compute_objective(model, baselines)

    # TODO - use constraint penalty somehow
    # The idea is to keep the optimization in a parameter regime where large corrections to the instructions
    # are not required. However, using ths constraint penalty directly can lead to it dominating the objective,
    # and with ASD's single-parameter stepping this prevents convergence. So needs some further work
    #
    # constaint_penalty = optimization.constrain_instructions(...)
    # obj_val += 0.0 * constraint_penalty

    return obj_val


def optimize(project, optimization, parset: ParameterSet, progset: ProgramSet, instructions: ProgramInstructions, x0=None, xmin=None, xmax=None, hard_constraints=None, baselines=None):
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
    :param parset: A :class:`ParameterSet` instance
    :param progset: A :class:`ProgramSet` instance
    :param instructions: A :class:`ProgramInstructions` instance
    :param x0: Not for manual use - override initial values
    :param xmin: Not for manual use - override lower bounds
    :param xmax: Not for manual use - override upper bounds
    :param hard_constraints: Not for manual use - override hard constraints
    :param baselines: Not for manual use - override Measurable baseline values (for relative Measurables)
    :return: A :class:`ProgramInstructions` instance representing optimal instructions

    """

    assert optimization.method in ["asd", "pso", "hyperopt"]

    model = Model(project.settings, project.framework, parset, progset, instructions)
    pickled_model = pickle.dumps(model)  # Unpickling effectively makes a deep copy, so this _should_ be faster

    initialization = optimization.get_initialization(progset, model.program_instructions)
    x0 = x0 if x0 is not None else initialization[0]
    xmin = xmin if xmin is not None else initialization[1]
    xmax = xmax if xmax is not None else initialization[2]

    if not hard_constraints:
        hard_constraints = optimization.get_hard_constraints(x0, model.program_instructions)  # The optimization passed in here knows how to calculate the hard constraints based on the program instructions

    if not baselines:
        baselines = optimization.get_baselines(pickled_model)  # The optimization passed in here knows how to calculate the hard constraints based on the program instructions

    # Prepare additional arguments for the objective function
    args = {
        "pickled_model": pickled_model,
        "optimization": optimization,
        "hard_constraints": hard_constraints,
        "baselines": baselines,
    }

    # Check that the initial conditions are OK
    # Note that this cannot be done by `optimization.get_baselines` because the baselines need to be computed against the
    # initial instructions which might be different to the initial conditions (e.g. baseline spending vs the scaled-up
    # initialization used when minimizing spending)
    initial_objective = _objective_fcn(x0, **args)
    if not np.isfinite(initial_objective):
        raise InvalidInitialConditions("Optimization cannot begin because the objective function was %s for the specified initialization" % (initial_objective))

    if optimization.method == "asd":
        optim_args = {
            # 'stepsize': proj.settings.autofit_params['stepsize'],
            "maxiters": optimization.maxiters,
            "maxtime": optimization.maxtime,
            # 'sinc': proj.settings.autofit_params['sinc'],
            # 'sdec': proj.settings.autofit_params['sdec'],
            "xmin": xmin,
            "xmax": xmax,
        }

        # Set ASD verbosity based on Atomica logging level
        log_level = logger.getEffectiveLevel()
        if log_level < logging.WARNING:
            optim_args["verbose"] = 2
        else:
            optim_args["verbose"] = 0

        opt_result = sc.asd(_objective_fcn, x0, args, **optim_args)
        x_opt = opt_result["x"]

    elif optimization.method == "pso":

        import pyswarm

        optim_args = {"maxiter": 3, "lb": xmin, "ub": xmax, "minstep": 1e-3, "debug": True}
        if np.any(~np.isfinite(xmin)) or np.any(~np.isfinite(xmax)):
            errormsg = "PSO optimization requires finite upper and lower bounds to specify the search domain (i.e. every Adjustable needs to have finite bounds)"
            raise Exception(errormsg)

        x_opt, _ = pyswarm.pso(_objective_fcn, kwargs=args, **optim_args)
    elif optimization.method == "hyperopt":

        import hyperopt
        import functools

        if np.any(~np.isfinite(xmin)) or np.any(~np.isfinite(xmax)):
            errormsg = "hyperopt optimization requires finite upper and lower bounds to specify the search domain (i.e. every Adjustable needs to have finite bounds)"
            raise Exception(errormsg)

        space = []
        for i, (lower, upper) in enumerate(zip(xmin, xmax)):
            space.append(hyperopt.hp.uniform(str(i), lower, upper))
        fcn = functools.partial(_objective_fcn, **args)  # Partial out the extra arguments to the objective

        optim_args = {"max_evals": optimization.maxiters if optimization.maxiters is not None else 100, "algo": hyperopt.tpe.suggest}

        x_opt = hyperopt.fmin(fcn, space, **optim_args)
        x_opt = np.array([x_opt[str(n)] for n in range(len(x_opt.keys()))])

    # Use the optimal parameter values to generate new instructions
    optimization.update_instructions(x_opt, model.program_instructions)
    optimization.constrain_instructions(model.program_instructions, hard_constraints)
    return model.program_instructions  # Return the modified instructions
    # Note that we do not return the value of the objective here because *in general* the objective isn't required
    # or expected to have a meaningful interpretation because it may arbitrarily combine quantities (e.g. spending
    # and epi outcomes) or is otherwise subject to the choice of weighting (e.g. impact vs equity). Therefore,
    # it is recommended that an _absolute_ metric be computed from the returned optimized instructions rather than
    # capturing the optimization objective. For example, in an optimization trading off equity against impact,
    # the deaths averted could be computed using the optimized instructions and returned as an absolute measure of quality.


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
