"""
Functions for running optimizations.
Version: 2018mar26
"""

import sciris.core as sc
from .system import AtomicaException, NotAllowedError
from .utils import NamedItem
from .asd import asd
from copy import deepcopy as dcp
import numpy as np
from .model import Model, Link
import pickle
import scipy.optimize
from collections import defaultdict
import logging
logger = logging.getLogger(__name__)

# TODO
#
# - time varying allocs
#   - modify ProgramInstructions.alloc to support time-value pairs, probably using the TimeSeries object
#   - modify ProgramSet.get_alloc() to read time-varying allocs from the instructions
#   - modify Optimization.update_instructions to use `Optimization.year_opt` to insert overwrites in the correct year
#	- modify Optimization.get_hard_constraints() to extract hard constraint from correct years
#   - modify Optimization.constrain_instructions() to check the correct years when constraining
#
# - money optimization
#   - modify Optimization.compute_objective to threshold model output objective based on meeting/failing target
#   - decide whether differences in money optimization (e.g. initializing or checking 100% spending) warrant a separate derived class
#
# - performance
#	- after time-varying optimization is finalized, partially integrate model prior to pickling
#		- modify `model.py` to abort the integration loop in a specific year

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
			# TODO - Make this overwrite time specific by adjusting the
			# LHS to correctly index time
			instructions.alloc[self.prog_name] = adjustable_values[i]

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
	#
	# Time-varying spending using an exponential form
	# The fact that this is a subclass of SpendingAdjustment means that
	# the `prog_name` attribute is defined. For checking constraints, it's sufficient
	# to check whether an adjustment is a SpendingAdjustment to decide whether
	# a particular program is optimizable
		def __init__(self,prog_name,t,t_0,t_end,p1,a1,a2):
			Adjustment.__init__(self,name=prog_name)
			self.prog_name = prog_name
			self.t = t # Vector of time values instructions are updated at
			self.t_0 = t_0# non-adjustable parameter
			self.t_end = t_end # non_adjustable parameter
			self.adjustables = [Adjustable('p1',initial=p1),Adjustable('a1',initial=a1),Adjustable('a2',initial=a2)] # Would need to specify initial values and limits for these parameters

		# Note - we can use get_initialization from the base class because all of the Adjustables
		# have explicit initial values. Note that it's essential to provide explicit initial values
		# for any Adjustable that does not explicitly appear in the instructions. Although in theory,
		# it would be possible to write a `get_initialization` function that fits the Adjustables
		# to the initial spending...

		def update_instructions(self,adjustable_values,instructions):
			# p1*exp(a1*(t-t_0))*exp(b1*(t-t_end))
			instructions.alloc[self.prog_name][self.t] = adjustable_values[0]*np.exp(adjustable_values[1]*(self.t-self.t_0))*np.exp(adjustable_values[2]*(self.t-self.t_end))


class Measurable(object):

	def __init__(self,measurable_name,t,pop_names=None,weight=1.0,fcn=None):
		self.measurable_name = measurable_name
		self.t = sc.promotetoarray(t) # Single year, or multiple years
		self.weight = weight
		self.pop_names = pop_names
		self.fcn = fcn # transformation function to apply

	def eval(self,model):
		if len(self.t) == 1:
			t_filter = model.t==self.t # boolean vector for whether to use the time point or not
		else:
			t_filter = (model.t >= self.t[0]) & (model.t < self.t[1]) # Don't include upper bound, so [2018,2019] will include exactly one year
		if self.measurable_name in model.vars_by_pop: # If the measurable is a model output...
			val = 0.0
			for var in model.vars_by_pop[self.measurable_name]:
				if not self.pop_names or var.pop.name in self.pop_names:  # If we are using this pop in the objective
					if isinstance(var, Link):
						val += np.sum(var.vals[t_filter] / var.dt)  # Annualize link values - usually this won't make a difference, but it matters if the user mixes Links with something else in the objective
					else:
						val += np.sum(var.vals[t_filter])
		else: # For now, only other possibility is that it's a spending amount
			alloc = model.progset.get_alloc(model.program_instructions,model.t)
			val =  alloc[self.measurable_name][t_filter]
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

	def __init__(self, total_spend = None):
		# total_spend allows the total spending in a particular year to be explicitly specified
		# rather than drawn from the initial allocation. This could be useful when using parametric
		# programs.
		self.total_spend = total_spend  # Optionally a number, or a list of tuples of time-spending pairs e.g. [(2018,10000),(2020,200000)]

	def get_hard_constraint(self,optimization, instructions):
		# First, at each time point where a program overwrite exists, we need to store
		# the names of all of the programs being overwritten
		# e.g.
		# hard_constraints['programs'][2020] = ['Program 1','Program 2']
		# hard_constraints['programs'][2030] = ['Program 2','Program 3']
		# By convention, an Adjustable affecting a program should store the program's name in the
		# `prog_name` attribute

		hard_constraints = {}
		hard_constraints['programs'] = defaultdict(set)  # It's a set so that it will work properly if multiple Adjustments reach the same parameter at the same time. However, this would a bad idea and nobody should do this!
		for adjustment in optimization.adjustments:
			if hasattr(adjustment, 'prog_name'):
				for t in list(adjustment.t):
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
						hard_constraints['total_spend'][t] = spend[1]
			elif self.total_spend:
				hard_constraints['total_spend'][t] = self.total_spend
			else:
				total_spend = 0.0
				for prog in progs:
					total_spend += instructions.alloc[prog] # TODO - index the time correctly here
				hard_constraints['total_spend'][t] = total_spend

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
						hard_constraints['bounds'][t][adjustment.prog_name] = adjustable.get_hard_bounds(instructions.alloc[adjustment.prog_name])  # TODO - Add time index to alloc # The instructions should already have the initial spend on this program inserted. This may be inconsistent if multiple Adjustments reach the same program...!
					else:
						hard_constraints['bounds'][t][adjustment.prog_name] = (0.0, np.inf) # If the Adjustment reaches spending but is not a SpendingAdjustment then do not constrain the alloc

		return hard_constraints

	def constrain_instructions(self,instructions, hard_constraints):

		penalty = 0.0

		for t, total_spend in hard_constraints['total_spend'].items():
			x0 = sc.odict()  # Order matters here
			bounds = []
			progs = hard_constraints['programs'][t]  # Programs eligible for constraining at this time
			LinearConstraint = [{'type': 'eq', 'fun': lambda x: np.sum(x) - total_spend}]  # Constrain spend

			for prog in progs:
				x0[prog] = instructions.alloc[prog] # TODO - Add time index to alloc
				bounds.append(hard_constraints['bounds'][t][prog])

			x0_array = np.array(x0.values()).ravel()
			res = scipy.optimize.minimize(lambda x: np.sqrt(np.sum((x - x0_array) ** 2)), x0_array, bounds=bounds,constraints=LinearConstraint)
			# TODO - If there's a failure to constrain, return np.inf here

			# TODO - If the penalty below doesn't seem to work properly, just return 0.0 to disable
			penalty += np.sqrt(np.sum((res['x'] - x0_array)**2)) # Penalty is the distance between the unconstrained budget and the constrained budget

			for name, val in zip(x0.keys(), res['x']):
				instructions.alloc[name] = val # TODO - Add time index to alloc

		return penalty

class Optimization(NamedItem):
	""" An object that defines an Optimization to perform """

	def __init__(self,  name='default', adjustments=None, measurables = None, constraints = None,  maxtime = 10, maxiters=None):

		NamedItem.__init__(self, name)

		assert adjustments is not None
		assert measurables is not None

		self.maxiters = maxiters # Not snake_case to match ASD
		self.maxtime = maxtime # Not snake_case to match ASD
		self.adjustments = [adjustments] if not isinstance(adjustments,list) else adjustments
		self.measurables = [measurables] if not isinstance(measurables,list) else measurables
		self.constraints = [constraints] if constraints and not isinstance(constraints,list) else constraints

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
		instructions = dcp(instructions)
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
	# obj_val = constraint_penalty + optimization.compute_objective(model)
	obj_val = optimization.compute_objective(model)

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

	x_opt = asd(_asd_objective,x0,args,**optim_args)[0]
	optimization.update_instructions(x_opt,model.program_instructions)
	optimization.constrain_instructions(model.program_instructions,hard_constraints)
	return model.program_instructions # Return the modified instructions

def parallel_optimize(project,optimization,parset,progset,program_instructions):

	raise NotImplementedError

	initialization = optimization.get_initialization(progset, program_instructions)
	xmin = initialization[1]
	xmax = initialization[2]

	initial_instructions = program_instructions
	for i in range(0,n_rounds):
		for i in range(0,n_threads):
			optimized_instructions[i] = optimize(optimization, parset, progset, initial_instructions, x0=None, xmin=xmin, xmax=xmax)
		initial_instructions = pick_best(optimized_instructions)
	return initial_instructions # Best one from the last round

