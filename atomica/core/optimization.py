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

class Optimization(NamedItem):
	""" An object for storing an optimization """

	def __init__(self,  name='default', adjustables=None, measurables = None, year_opt = None, year_eval = None, constraints = None,  maxtime = 10, maxiters=None):
		# INPUTS
		# - adjustables : A specification of what to change in the ProgramInstructions (upper/lower bounds, same length and order as the ASD vector)
		# - measurables : A specification of what to include in the objective function and what weight to use
		# - year_opt : Insert the adjustables into the ProgramInstructions at this year (if relevant)
		# - year_eval : Specification of which years to use in the objective function
		#
		NamedItem.__init__(self, name)

		self.year_opt = year_opt # Year to insert modifications to the instructions (for time-varying adjustables)
		self.year_eval = year_eval # Optionally specify time span for evaluation
		self.maxiters = maxiters # Not snake_case to match ASD
		self.maxtime = maxtime # Not snake_case to match ASD
		self.adjustables = adjustables # (prog_name/quantity,limit_type,lower_limit,upper_limit) - Input for self.update_instructions(), information needed to map ASD array entry to instructions. Limit type is 'rel' or 'abs'
		self.measurables = measurables # (variable_name,weight,pops=None) - vals for these are summed and summed

		if constraints is None:
			self.constraints = {'total_spend':None}  # Data required to calculate the hard constraints
		else:
			self.constraints = constraints # Data required to construct the constraint dict

	def __repr__(self):
		return sc.desc(self)

	def update_instructions(self,instructions,asd_values,hard_constraints):
		# This is the core of the Optimization class - it maps an array of ASD values into an
		# updated ProgramInstructions instance which in turn changes the outcome of the simulation
		#
		# Take in some ProgramInstructions and a vector of ASD values, insert them into the instructions
		# In the base case, instructions.alloc is an odict with one spending value per program defined,
		# and the ASD values are a vector the same length as instructions.alloc

		if not instructions.alloc:
			instructions.alloc = dict()

		for adjustable,val in zip(self.adjustables,asd_values):
			if adjustable[0] == 'start_year':
				raise NotImplementedError
			else: # Deal with other special cases above, as with start year
				# TODO - Could store additional information on how to insert a time-varying alloc here
				if adjustable[0] in instructions.alloc and isinstance(instructions.alloc[adjustable[0]],np.ndarray):
					raise NotImplementedError # Time varying allocs not yet supported in ProgramInstructions although they are hooked into ProgramSet.get_alloc()
				else:
					instructions.alloc[adjustable[0]] = val

		print('BEFORE')
		print(instructions.alloc)
		self.constrain_instructions(instructions,hard_constraints)
		print('AFTER')
		print(instructions.alloc)


	def get_hard_constraints(self,progset,instructions):
		# Compute the hard constraints used by optimization.constrain_instructions based on
		# the constraint specification in optimization.constraints
		#
		# For example, optimization.constraints might specify that total spending needs to be constrained,
	    # in which case this method will return the actual amount of total spending for the given instructions
		#

		hard_constraints = {}

		if not self.constraints:
			return hard_constraints

		initial_spending = progset.get_alloc(instructions, self.year_opt)
		for constraint_name,val in self.constraints.items():
			if constraint_name == 'total_spend' and val is None:
				# Note - this is a constraint only on **adjustable** programs
				hard_constraints[constraint_name] = 0.0
				if val: # If total spend is to be calculated over some time period
					raise NotImplementedError
				else:
					for adjustable in self.adjustables:
						if adjustable[0] in initial_spending:
							hard_constraints[constraint_name] += initial_spending[adjustable[0]][0]

		# Constraints on upper/lower bounds that need to also be enforced when rescaling
		_, xmin, xmax = self.get_initialization(progset,instructions)
		for i, (name, limit_type, lower_limit, upper_limit) in enumerate(self.adjustables):
			if name in initial_spending:
				hard_constraints[name] = (xmin[i],xmax[i])

		return hard_constraints


	def constrain_instructions(self,instructions,hard_constraints):
		# The hard_constraint passed in here is NOT optimization.constraints, it is
		# hard_constraint = optimization.get_hard_constraints(instructions)
		# This is because the constraint may depend on the initialization. For example
		# optimization.constraints = [('total_spend',[2020,np.inf])] # specify how to calculate the hard constraint from initial instructions
		# hard_constraint = optimization.get_hard_constraint(instructions) = {'total_spend':$100000} # the actual constraint corresponding to the actual initialization
		# optimization.constrain_instructions(instructions,hard_constraint) # rescale 'total_spend' (from optimization.constraints) such that total spend from 2020-np.inf is equal to $100000

		# At the moment - only support standard time-invariant constraints
		# We *could* probably do this directly based on x0 but we are not guaranteed that everything in x0 is a spending value
		# For instance, x0 could mix spending value and start year, that's why we map via the dict keys

		# First, form the vector of adjustable spends

		# If no constraints, no need to do anything. Note that bounds are already handled by ASD
		# but they need to be included here too when rescaling
		if not hard_constraints:
			return

		x0 = sc.odict()
		bounds = []
		constraints = [] # List of constraints used by scipy.optimize.minimize

		for name in hard_constraints:
			if name in instructions.alloc: # Note - if a spending amount is being optimized, then it will appear in the alloc during iteration, even if it wasn't originally there
				x0[name] = instructions.alloc[name]
				bounds.append(hard_constraints[name])
			elif name == 'total_spend':
				total_spend = hard_constraints[name]
				if len(sc.promotetoarray(total_spend)) == 1:
					constraints.append({'type': 'eq', 'fun': lambda x: np.sum(x) - total_spend}) # It must be equal to the total spend
				else:
					constraints.append({'type': 'ineq', 'fun': lambda x: total_spend[0] <= np.sum(x) <= total_spend[1]})  # It must be within the spending range (typically would be 0 to upper bound)

		x0_array = np.array(list(x0.values()))
		res = scipy.optimize.minimize(lambda x: np.sqrt(np.sum((x - x0_array) ** 2)), x0_array, bounds=bounds, constraints=constraints)

		for name,val in zip(x0.keys(),res['x']):
			instructions.alloc[name] = val

	def compute_objective(self,model):
		# Take in a completed model run
		# Compute the objective based on the settings in self.objective
		# Program name will map to spending array for that program

		# Reconstruct the alloc
		alloc = model.progset.get_alloc(model.program_instructions, model.t)

		objective = 0.0

		if self.year_eval:
			year_eval = sc.promotetoarray(self.year_eval)
			if len(year_eval) == 2:
				t_filter = ((year_eval[0] <= model.t) & (model.t <= year_eval[1]))
			elif len(year_eval) == 1:
				t_filter = (model.t == year_eval[0])
			else:
				raise NotAllowedError('Optimization objective year_eval must be a scalar or have two elements')
		else:
			t_filter = np.full(model.t.shape, True)

		for var_name,weight,*pop_names in self.measurables:
			# measurable is a tuple (variable_name,weight,pops=None)
			if not callable(weight):
				weightfun = lambda x: x*weight
			else:
				weightfun = weight

			if var_name in model.vars_by_pop:
				vars = model.vars_by_pop[var_name]
				contribution = 0.0
				for var in vars:
					if not pop_names[0] or var.pop.name in pop_names: # If we are using this pop in the objective
						if isinstance(var,Link):
							contribution += np.sum(var.vals[t_filter]/var.dt) # Annualize link values - usually this won't make a difference, but it matters if the user mixes Links with something else in the objective
						else:
							contribution += np.sum(var.vals[t_filter])
				print(contribution)
				objective += weightfun(contribution)
			else:
				objective += weightfun(np.sum(alloc[var_name][t_filter]))

		return objective

	def get_initialization(self,progset,instructions):
		# This is the default initial ASD values - typically these would be spending but in theory
		# they could be anything supported by self.update_instructions() (e.g. start year)
		#
		# Returns xmin and xmax as absolute values - they will persist in parallel optimization
		# or resumed/continued optimization whereas x0 might change (important because relative
		# bounds are assumed to be relative to the initial values fed in)

		x0   = np.zeros((len(self.adjustables,)))
		xmin = np.zeros((len(self.adjustables,)))
		xmax = np.zeros((len(self.adjustables,)))

		# First, get the spending values on all programs in `year_opt`
		# This allows the Progset to supply the initial values for programs that are set to
		# be optimized but where the initial value is the Program data value, rather than an
		# an existing overwrite in the instructions
		assert self.year_opt is None or len(sc.promotetoarray(self.year_opt)) == 1 # Only return 1 spending value
		initial_spending = progset.get_alloc(instructions, self.year_opt)

		for i,(name,limit_type,lower_limit,upper_limit,*initial) in enumerate(self.adjustables): # For each quantity we are adjusting
			if initial:
				x0[i] = initial
			elif name in initial_spending:
				x0[i] = initial_spending[name][0]
			else:
				raise NotImplemented # This could be other things like changing the start year or even year_opt - need to define allowed adjustable names e.g. 'start_year'

			if limit_type == 'rel':
				xmin[i] = x0[i]*lower_limit if lower_limit else 0.0
				xmax[i] = x0[i]*upper_limit if upper_limit else np.inf
			elif limit_type == 'abs':
				xmin[i] = lower_limit if lower_limit else 0.0
				xmax[i] = upper_limit if upper_limit else np.inf
			else:
				raise NotAllowedError('limit_type must be "rel" or "abs"')

		return x0,xmin,xmax


def _asd_objective(asd_values, pickled_model=None, optimization=None, hard_constraints = None):
	# Compute the objective in ASD

	# Unpickle model
	model = pickle.loads(pickled_model)

	# Inject the ASD vector into the instructions
	optimization.update_instructions(model.program_instructions, asd_values, hard_constraints)

	# Use the updated instructions to run the model
	model.process()

	# Compute the objective function based on the model calculated values and return it
	return optimization.compute_objective(model)


def optimize(project,optimization,parset,progset,instructions,x0=None,xmin=None,xmax=None):
	# The ASD initialization, xmin and xmax values can optionally be

	model = Model(project.settings, project.framework, parset, progset, instructions)
	pickled_model = pickle.dumps(model)

	initialization = optimization.get_initialization(progset,model.program_instructions)
	x0 = x0 if x0 is not None else initialization[0]
	xmin = xmin if xmin is not None else initialization[1]
	xmax = xmax if xmax is not None else initialization[2]

	hard_constraints = optimization.get_hard_constraints(progset,model.program_instructions) # The optimization passed in here knows how to calculate the hard constraints based on the program instructions

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
	optimization.update_instructions(model.program_instructions,x_opt,hard_constraints)
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

