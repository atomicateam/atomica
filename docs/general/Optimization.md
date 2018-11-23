# Optimization

Atomica's optimization system is designed to be flexible and extensible. To support this, the philosophy underpinning the implementation is that the different aspects of optimization are separated out so that they can be combined in different ways, and easily extended. The most common optimization tasks will likely have their own API wrappers for easy usage.

## `Optimization` class

The key entry point to the optimization system is the `Optimization` class. Conceptually, an instance of this class contains a set of instructions for how to perform an optimization. The role of optimization is to make changes to a set of program instructions (such as changing the amount of spending on programs) in order to achieve some goal. Optimization takes in an unoptimized set of program instructions, and returns a set of program instructions that is optimal in some sense. An `Optimization` instance describes what changes can be made to the program instructions, and how to define 'optimality' for the purpose of the optimization.

There are three fundamental aspects for optimization:

- What elements of the program instructions should be changed, and how to change them
- What conditions the program instructions need to satisfy (e.g. the total amount of money spent is fixed)
- What aspects of the simulation output should be used for optimization in the objective function

An optimization thus contains

- A set of `Adjustments` that define the changes that can be made to the instructions. Conceptually, an 'Adjustment' represents terms that ASD will vary in the process of optimization
- A set of `Constraints` that rescale or otherwise change the program instructions as required. Conceptually, a 'Constraint' is a specification of some condition that the proposed instructions must satisfy.
- A set of `Measurables` that computes objective values based on the simulation output. Conceptually, a 'Measurable' represents a term in the objective function, so it is a specification of what quantities should be used to guide optimization

#### Performing an optimization

To use the optimization, the function `optimization.optimize` takes in a parset, progset, optimization, and unoptimized program instructions. It optimizes according to the specification given in the `Optimization` object provided, and returns optimized instructions. `Project.make_optimization` wraps the `Optimization` constructor for the API, and also automatically stores the `Optimization` object in the `Project`. `Project.run_optimization` wraps `optimization.optimize` for the API. It also automatically runs a simulation using the optimized instructions, and can optionally save that simulation to the project.

## Adjustments

The first component of an optimization is the set of changes that can be made to the program instructions. Typically, these changes focus on spending, but this is not necessarily the case. From the outset, we can identify an initial set of different adjustments users might want to make:

- Basic overwrite - all programs being optimized each have a single value for spending, which takes effect in the program start year
- Delayed overwrite - all programs being optimized each have a single value for spending, which takes effect some time _after_ the program start year. This could correspond to a delayed scale-up, for example
- Multiple time-dependent overwrites - A program specifies a different spending amount in different years, to be optimized separately. This could correspond to optimizing the size of a scale-up, or optimizing a reduction in spending in the future if prevalence is falling
- Parametric overwrite - Time-dependent program spending is a function of one or more variables, and it is those variables that are optimized rather than the actual spending value
- Non-spending overwrite - Optimization of a parameter like time

In the general case, an `Adjustment` represents a function that maps variables, referred to as `Adjustables`, to a change in the program instructions. This could be as simple as an `Adjustable` simply being a spending value, or it could be complex, where the `Adjustable` is a term in a function. In some cases, particularly with parametric adjustments, the adjustment may have more than one `Adjustable` associated with it. For example, a linear spending profile has a slope and an intercept, so two parameters could map to a time-varying allocation for a single program. There, we might have a single `Adjustment` representing `y=mx+b` and two `Adjustables` corresponding to `m` and `b` (the quantities being fitted). So that is the distinction between an `Adjustment` and an `Adjustable`.

In terms of interfacing with ASD, there is one element in the vector of ASD values for every `Adjustable` contained in the optimization. The `Adjustable` contains a specification of its upper and lower bounds, as well as the initial value. The `Adjustment` is able to initialize its `Adjustables` based on the program instructions, which allows initial values to be populated based on program instructions or based on the data in the program set, as well as for the lower and upper bounds to be specified as relative limits rather than absolute limits.

Since an `Adjustment` represents the function mapping its `Adjustables` to a change in the program instructions, different possible changes are stored in subclasses. Atomica currently contains the following

- `Adjustment` - the base class defining the interface for all `Adjustments`
- `SpendingAdjustment` - the most common type of adjustment - this `Adjustment` contains `Adjustables` that correspond to spending values for a single program at a single time. The `SpendingAdjustment` could contain multiple `Adjustables` corresponding to changing the amount of spending at multiple time points
- `PairedLinearSpendingAdjustment` - this is a demonstration of how to implement parametric adjustments. This adjustment represents a time-dependent transfer of funds from one program to another. It therefore simultaneously changes spending on two programs rather than one. It only has one `Adjustable` corresponding to the rate at which spending is changed. This also demonstrates how the `Adjustable` system works when the `Adjustable` does not correspond to a spending value
- `ExponentialSpendingAdjustment` - This is an incomplete demonstration implementation of the previously used timevarying alloc
- `StartTimeAdjustment` - This untested demonstration shows how an `Adjustment` can change something in the program instructions that is not a spending value - in this case, it is the start year for the programs. This is just an illustrative example - a more realistic case may be where meeting targets in 2030 can be most efficiently reached by delaying program scaleup, rather than only changing the scale up amount.

The code users write to construct and use these objects ends up being quite simple and readable. For example, adding

	au.SpendingAdjustment('Treatment 1', 2020, 'abs', 0., 100.)

to the optimization means that the optimization will change the allocation for 'Treatment 1' in 2020 and the spending value must be between 0 and 100.

#### Implementation specifics

An `Adjustment` contains

- A name to identify it
- If it affects spending on a program, it stores the name of that program, or a list of the program names. This allows constraints (see below) to identify programs that are being optimized, even in cases where the adjustables do not directly map to spending values.
- A list of adjustables
- Any other information specific to that particular type of adjustment - for example, for a linear spend `y=mx+b` maybe the intercept is fixed and only the gradient can be varied. In that case, `m` would be an `Adjustable`, while `b` would simply be stored as a member variable.

An `Adjustment` has the following methods

- `Adjustment.get_initialization(progset,instructions)` - this method returns a vector of initial values for each adjustable, which are the default initial values for ASD. There are several possible places where initial values can be stored. Consider spending values. In order of precedence, the places where default values could be defined are:
	- In the `Adjustable`. For example, the `SpendingAdjustment` in an optimization might wish to explictly store an initial value to start the optimization at
	- In the `ProgramInstructions` - the program instructions optionally contains a `TimeSeries` of spending values that overwrite the data spending values stored in the `ProgramSet`, which is the used to implementing budget scenarios
	- In the `ProgramSet`, each program by default has spending specified in the Progbook file

	Thus, `get_initialization` takes in both the `progset` and the `instructions`. By default, the `Adjustment` base class simply returns the values stored in the `Adjustable`. Otherwise, derived classes can implement this method to set the default values appropriately. For example, `SpendingAdjustment` implements the default spending precedence described above. It would also be possible to perform more sophisticated initialization - for example, a parametric adjustment could use `Adjustment.get_initialization` to fit the adjustables as part of the initialization.

- `Adjustment.update_instructions(adjustable_values,instructions)` - this method actually performs the overwrite. It takes in a list of adjustable values, which is a slice from the full ASD vector corresponding to just the adjustables contained in this adjustment. The function then changes the instructions in-place. For `SpendingAdjustment` this just means inserting the elements of `adjustable_values` into the instruction's alloc, but for a parametric adjustment, `update_instructions` would contain the actual code for the adjustment.

## Constraints

The second major component of an optimization is the constraints. Every adjustable has its own upper and lower bound. However, we may also want to provide constraints that apply to the Program Instructions as a whole (i.e. to the cumulative effect of all adjustments together). For example, this could be a constraint on total spending. A constraint on total spending cannot be implemented by considering each program independently. Therefore, it is implemented by the `Constraint` class that operates after all of the adjustments in the optimization have been made. There are two aspects to constraints

1. How to check whether a constraint is satisfied or not
2. How to change the adjustables or the program instructions to satisfy the constraint

For example, consider a simple single spending overwrite with a constraint on the total spending

1. The constraint is checked by summing the spending on all adjustable programs in the overwrite year
2. The constraint is satisfied by rescaling spending on all adjustable programs such that their sum matches the target value

In the case of constraining a basic spending overwrite, we are effectively rescaling the adjustables. However, in the case of parametric overwrites, the spending values produced by the overwrite are what gets rescaled, rather than the parameters themselves (for example, if the parametric overwrite was `y=mx+b` then the constraint would adjust the value of `y` after the function was evaluated, rather than trying to achieve a particular value of `y` by changing `m` and `b`). Note that in the case where the quantity being adjusted directly corresponds to an `Adjustable` (such as a spending value), then we have to also respect the upper and lower bounds specified for that adjustable.

Finally, at the point where the user declares that they want to constrain total spending, they may not know what the total spend is, because it depends on the combination of

- ProgramSet spending data
- ProgramInstructions alloc
- Optimization adjustable initial values

For example, the user might want to define an `Optimization` that fixes total spending, and then reuse that `Optimization` for several different proposed `ProgramInstructions` with different initial allocations. Alternatively, they may know what total spend they want, but they might not know the total spend associated with the initial values for the adjustables. For example, if a program is made time-varying using a parametric overwrite, the user might specify initial values for the parameters, but they might not know what the resulting sum of spending on all programs is.

**Caution - Constraining spending in conjunction with parametric time-varying programs means that spending on programs will in general _not_ match the requested parametric function. That is, the effect of rescaling will likely be that the constrained spending does not match the spending function. If using parametric functions with a separate constraint, it is important to check the optimized spending temporal profile in order to monitor this. It may be preferable for the parametric adjustment to implement the constraint itself within its function, as demonstrated in `PairedLinearSpendingAdjustment`**

#### Implementation specifics

There are two stages for constraints

- As part of optimization pre-processing, any relative constraints need to be converted into absolute constraints. For example, the actual value for total spending needs to be calculate based on the initial instructions, and relative bounds on attributes or spending need to be converted to absolute values. These values are referred to as **hard constraints**. Each `Constraint` has a 'hard constraint' dictionary associated with it. The `Constraint` generates it based on the program instructions and optimization using `Constraint.get_hard_constraint(self,optimization, instructions)` (which is generally overloaded in derived classes). The resulting dictionary is stored by `optimization.optimize` and passed back into `Constraint.constrain_instructions` during ASD optimization
- The actual constraining is performed by `Constraint.constrain_instructions(instructions,hard_constraints)`. This is called within `_asd_objective`. The `instructions` are passed in _after_ they have been updated by the adjustments, and the `hard_constraints` are simply the same dict that was generated by the `Constraint` object during initialization. `Constraint.constrain_instructions` modifies the instructions in-place in order to satisfy the constraint. So for example, if we are constraining the total spend, then `constrain_instructions` will contain all of the code to actually perform any required rescaling

### Total spending constraint

In considering the implementation for `Constraints`, it became evident that there were many different possible constraints. To support this, the system for defining constraints is very flexible and extensible. However, designing a one-size-fits-all `Constraint` is complex due to the range of different possibilities. As with `Adjustments`, it is expected that `Constraints` will be subclassed to define specific, detailed constraints. At the moment, Atomica only contains an implementation for the most commonly-used total spending constraint, and it is envisaged that more constraint types will be added as development continues.

The included basic constraint on total spending is implemented by the `TotalSpendConstraint` class. This constraint behaves as follows: total spending is constrained independently at each time point where at least one program is reached by an Adjustment. Rescaling is performed by constrained minimization using `scipy.optimize.minimize`. Specifically, this returns spending values that satisfy the total spending constraint, and also minimize the 'distance' between the ASD-requested spending and the valid constrained spending. `scipy.optimize.minimize` also accounts for the upper and lower bounds on individual programs, if they exist. This implementation is compact (requires minimal code on our end) and the optimal rescaled solution is also likely unique.

`TotalSpendConstraint` applies this constraint at each time point for all programs that are being reached at that time point, or alternatively it can only perform the rescaling in user-specified years. For the majority of optimizations, the optimal spending is computed for all programs at only one time point, so this is sufficient. However, some complications can arise if there are complex time-dependent adjustments. In those cases, it may be necessary to define a new constraint tailored to that optimization, or otherwise to incorporate the constraint into the adjustment itself, as mentioned above.

## Measurables

After applying proposed changes to the program instructions and running the model, the final aspect of optimization is computing the objective value. There are a number of different metrics that users may wish to use. For example, users may need to:

- Maximize people alive in a certain year
- Minimize infections/deaths in a certain year
- Minimize/maximize variables aggregated over a time period
- Minimize spending over a time period
- Use different time periods for each term in the objective
- Apply a transformation to the quantity prior to including in objective (e.g. weighting, non-linear penalty)
- Require that a condition must be met by the simulation

The implementation of this is as follows: a `Measurable` represents a single term in the objective. It takes in a `model` object after integration, and returns an objective value. An `Optimization` can contain multiple `Measurables`, and the values computed by each `Measureable` are added together and used as the final scalar objective returned to ASD.

A `Measurable` contains

- The name of the quantity being examined. This could be the name of an integration object (e.g. a characteristic), or the name of a program (to retrieve spending). Subclasses of `Measurable` can be written to extract other quantities from the model (e.g. from `model.progset`). Similarly, a subclass could ignore this entirely. But all of the basic included `Measurables` use the name to identify a model output or a program
- A weight factor
- A list of population names, which is used to filter model outputs by population (by default, all populations are included)
- A time index, or range of times, specifying the range of times to include when computing the value of the `Measurable` (by default, all times are included)
- A function that transforms the objective value before returning it. For example, you could take the absolute value, or apply some sort of threshold. Examples are described below

For convenience and readability, several subclasses of `Measurable` are provided with Atomica. These are

- `MinimizeMeasurable` - this has a built-in weight of `1.0` that results in the quantity being minimized by ASD
- `MaximizeMeasurable` - this has a built-in weight of `-1.0` that results in the quantity being maximized ASD
- `AtMostMeasurable` - this has a thresholding function such that the objective is `np.inf` if the quantity exceeds the specified limit, and `0.0` otherwise
- `AtLeastMeasurable` - this has a thresholding function such that the objective is `np.inf` if the quantity is less than the specified limit, and `0.0` otherwise

So for instance

	au.MaximizeMeasurable('ch_all',[2020,np.inf])

would mean that the characteristic `ch_all` should be maximized in all populations from 2020 to the end of the simulation. Similarly

	au.AtLeastMeasurable('ch_all',2030,728.01)

would mean that the simulation must have at least 728.01 people alive in 2030.

### Measurables vs. constraints

The threshold measurables described above effectively function as constraints. However the fundamental difference in usage is that a `Constraint` adjusts the `ProgramInstructions` so that the proposed ASD values still produce output. In contrast, a measurable that returns `np.inf` if a condition isn't satisfied will result in those ASD values being rejected outright. In general, it is simpler and clearer to implement constraints as measurables that reject values. However, some constraints cannot be satisfied by simply trying different parameters - ASD changes one parameter at a time, so if total spending must be fixed, then _any_ ASD step will violate that condition. In that case, it may be necessary to write a `Constraint`.

As discussed above, a third option would be to redesign the adjustable such that the constraint is guaranteed to be satisfied. For example, suppose spending on Program 2 had to have at most 50% of the budget of Program 1. Thus three approaches for incorporating this are:

1. The simplest approach would be to specify a `Measurable` that rejects cases where spending on Program 2 is too high. Although simple, this approach is less efficient because the measurable is only evaluated after the simulation has been run, thus wasting simulation time on parameters that will be rejected. On the other hand, because this `Measurable` is evaluated after all `Constraints` are resolved, it is guaranteed to produce a valid solution even after any total spending constraints are taken into account.
2. A more efficient approach could be to specify a parametric adjustment, where the first adjustable is spending on Program 1, and the second adjustable is the fraction of that spend allocated to Program 2. The bounds on the second adjustable would be `[0,0.5]` thus ensuring that Program 2 never received more than half of the funding of Program 1. This approach would be more efficient, but involves writing more code, and also does not guarantee that a `Constraint` won't cause the condition to be violated.
3. Finally, a constraint-based approach could work by taking capping Program 2 at half of Program 1's funding, and then redistributing that funding to all of the other programs. This approach would also have to respect the upper bounds on any `SpendingAdjustments` that are present, so it would have to contain logic to satisfy those limits as well.

Notice that the `Measurable` based approach will reject bad parameters, the `Adjustment` approach doesn't propose bad parameters, and the `Constraint` approach corrects bad parameters. The optimal approach to use depends on the specific problem at hand.

## Optimization examples

Putting it all together, here are some examples of common optimizations. Suppose we have 5 programs defined, with

	alloc = sc.odict([('Risk avoidance',0.),
	                 ('Harm reduction 1',0.),
	                 ('Harm reduction 2',0.),
	                 ('Treatment 1',50.),
	                 ('Treatment 2',1.)])
	instructions = au.ProgramInstructions(alloc=alloc,start_year=2020) # Instructions for default spending

We want to optimize spending on Treatment 1 and Treatment 2 while keeping the remaining programs at fixed spending.

#### Maximize people alive

	adjustments = []
	adjustments.append(au.SpendingAdjustment('Treatment 1',2020,'abs',0.,100.))
	adjustments.append(au.SpendingAdjustment('Treatment 2',2020,'abs',0.,100.))
	measurables = au.MaximizeMeasurable('ch_all',[2020,np.inf])
	constraints = au.TotalSpendConstraint()
	P.make_optimization(name='default', adjustments=adjustments, measurables=measurables,constraints=constraints)

Notice how

- A `SpendingAdjustable` is instantiated for each program being adjusted. If a program does not appear in any of the adjustments, then it will have fixed spending drawn either from the program instructions or the program set data
- The fact that we want to change spending in 2020 is a property of the adjustment. This could be separate to the base allocation year in the program instructions, in which case the resulting alloc will be timevarying. The fact that we want to maximize people alive from 2020 onwards is reflected in the range of times in the `Measurable`

#### Minimize deaths

Suppose instead of maximizing the number of people alive from 2020 onwards, we wanted to minimize the number of people dying in 2030. Then, we could use the following:

	adjustments = []
	adjustments.append(au.SpendingAdjustment('Treatment 1',2020,'abs',0.,100.))
	adjustments.append(au.SpendingAdjustment('Treatment 2',2020,'abs',0.,100.))
	measurables = au.MinimizeMeasurable(':dead',2030)
	constraints = au.TotalSpendConstraint()
	P.make_optimization(name='default', adjustments=adjustments, measurables=measurables,constraints=constraints)

Notice how this is exactly the same as before, except the measurable is different:

- The characteristic label `ch_all` has been replaced with the lookup string `:dead`. This is the same standard syntax for accessing integration variables used everywhere else (e.g. in `Population.get_variable()` or in plotting) and indeed anything supported by `Population.get_variable()` can be used in the `Measurable`
- The range of years `[2020,np.inf]` has been replaced by a single time value

For more examples, including time varying optimizations, see `test_optimization.py`

#### Minimize spending

This optimization is quite different to the others, in that the total spending value is not fixed, and instead we wish to minimize the program budgets subject to meeting some criterion (in this case, that a minimum number of people need to be alive in 2030).


	adjustments = []
	adjustments.append(au.SpendingAdjustment('Treatment 1', 2020, 'abs', 0., 100.))
	adjustments.append(au.SpendingAdjustment('Treatment 2', 2020, 'abs', 0., 100.))

	measurables = []
	measurables.append(au.AtLeastMeasurable('ch_all',2030,728.01))
	measurables.append(au.MinimizeMeasurable('Treatment 1',2020))
	measurables.append(au.MinimizeMeasurable('Treatment 2',2020))

	constraints = None

	P.make_optimization(name='default', adjustments=adjustments, measurables=measurables,constraints=constraints)

Notice how

- The `adjustments` are exactly the same as before, because we are still changing spending on the same programs as before with the same upper/lower bounds
- There are now three `Measurables` instead of one. The first measurable ensures that the proposed solution satisfies the condition that there are enough people alive in 2030. The second and third measurables correspond to minimizing spending on the programs being adjusted
- We no longer want to constrain the total spending, so `constraints` is set to `None`

## Optimization calling structure

- `optimize`
	- Calls `optimization.get_initialization`
		- Calls `adjustment.get_initialization` and reads lower/upper bounds from adjustables
	- Calls `ASD` with `_asd_objective` as the function
	- Calls `update_instructions` and `constrain_instructions` using the ASD-optimized values to prepare and return the optimized instructions

- `parallel_optimize`
	- Calls `optimization.get_initialization` once to get the upper/lower bounds as absolute limits based on the original initialization (this is essentially the same as how `orig_alloc` was previously used to allow the limits to be computed based on the original values)
	- Calls `optimize` but passes in the hard upper/lower bounds. Each worker starts with different initial conditions (not yet implemented)
