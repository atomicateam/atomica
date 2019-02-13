Model objects
#################

Atomica uses a network or graph of interconnected objects to carry out the integration, rather than a transition matrix. This design choice trades performance against flexibility, and makes it easy to heavily customize models via the Framework file, as well as facilitating accessing outputs from the model and reasoning untuitively about how parts of the model interact. 

A model run is stored in the `Model` object. There are four types of fundamental building blocks that make up the model - `Compartments`, `Characteristics`, `Parameters`, and `Links`. Each of these is implemented as a class. Where applicable, member variables store references to other objects - these are Python variables passed by reference, and can thus be interacted with directly.

Variable (base class)
***********************************************************************************************

All of the 4 fundamental units are derived from the `Variable` object. A variable contains

- A `id` which is an tuple that uniqiely identifies this `Variable` within a `Model`. The last entry of the tuple is the code name for the object (the code name entered in the Framework)
- A `name` property method, which is a shortcut to the code name for the variable
- A `vals` array, which is an array of numbers with as many entries as there are time points in the simulation. All of the fundamental objects have a value associated with them, but the quantity that these values represent depends on the type of object
- A `t` array, which stores the time values that correspond to the `vals` array. This facilitates plotting the variable. The `t` array is a reference to `Model.t` so it is shared by all variables in the `Model` to save memory 
- A `dt` property, which stores the timestep to faciliate annualization
- A `units` property which is used for labelling when plotting, and to validate aggregations when aggregating plot data

The key methods for `Variable` objects are:

- `preallocate` which takes in a time vector, and initializes the `vals` array to be NaNs with the same shape
- `update` which is called at every time step, and overloaded by the derived classes
- `set_dependent` which flags a variable as a dependency - this is mainly relevant for `Parameters` but is also used by `Links`
- `plot` this will make a basic time series plot of the variable, which is mainly useful for diagnostic and debugging purposes

Compartment
***********************************************************************************************

[[graphics/Compartment.png]]

A `Compartment`  represents one of the compartments specified in the 'Compartments' sheet of the framework. A compartment stores people in a particular state (e.g., susceptible, infected). For each population, there is one `Compartment` for every entry in that sheet. `Compartments` have the following key features:

- The `vals` attribute for the compartment object represents the number of people in that compartment
- The `name` attribute matches the 'Code Label' in the framework
- Boolean flags for birth, death, and junction compartments (`tag_birth`,`tag_dead`, and `is_junction`, respectively)
- A list of Link objects, `inlinks`, that represents flows into the compartment
- A list of Link objects, `outlinks`, that represents flows out of the compartment

A junction is a special type of compartment that is emptied at every time step, so the `vals` attribute should be 0 at all times. 

Compartments have a number of helper methods

- `outflow` which is the sum of all outgoing links at a given point in time. This can also be used as a proxy for the 'value' of a junction, because it corresponds to how many people had arrived in the junction at that time step. 
- `expected_duration` this returns the time in years that an individual would be expected to remain in the compartment if the outflow probabilities and the compartment size remained the same going into the future (i.e. in a steady state approximation)
- `expected_outflow` this returns a dict showing where people in the compartment would be expected to be after 1 year, on the assumption that the outflows at each time step are probabilistic and constant

The last two methods `expected_duration` and `expected_outflow` are mainly for application diagnostic purposes.

Link
***********************************************************************************************

[[graphics/Link.png]]

A link represents one of the transitions specified in the 'Transitions' sheet of the cascade workbook. For each population, there is one `Link` for every entry in the transition matrix - note that this means there are separate instances of a `Link` object for any repeated tags. There is also an instance of a `Link` object between corresponding pairs of compartments between any two populations that have transfers between them. The transfer links are stored in the source population. A `Link` draws its value from a `Parameter` object. A `Link` has the following key features:

- The `vals` attribute for the link represents how many people are being moved from one compartment to another at a given time. The rule is `popsize[ti+1]=popsize[t]+link_value[t]`. To apply a link, the link value is subtracted from the source compartment, and added to the destination compartment. These values correspond to the actual number of people moved at each time step (after incorporation of any constraints to prevent negative compartment sizes). Note that this means that the values are _not_ annualized. This greatly improves consistency and usability when working with the raw matrices, generally output to a user goes via helper methods such as plotting or exporting, and these take care of annualization where required.
- The `name` attribute of the `Link` is the name of the `Parameter` object that the link obtains its value from, with `:flow` appended to it
- The `source` attribute is an instance of a `Compartment` object, corresponding to the source compartment
- The `dest` attribute is an instance of a `Compartment` object, corresponding to the destination compartment
- The `parameter` attribute is an instance of a `Parameter` object, corresponding to the `Parameter` supplying values for the link

Characteristic
***********************************************************************************************

[[graphics/Characteristic.png]]

A characteristic represents a grouping of compartments, with optional normalization. In each population, there is one `Characteristic` object for every entry in the 'Characteristics' sheet in the cascade workbook. A characteristic may be used within other characteristics and in parameter computation. A `Characteristic` has the following key features:

- The `vals` property attribute represents either a number of people, or a fraction of people (depending on whether the denominator is set or not)
- The `includes` attribute is a list whose elements are either `Characteristic` or `Compartment` objects. At each timepoint, the `vals` attribute of the objects in the `includes` list are summed together to calculate the value of the current `Characteristic`
- The `denominator` attribute is optionally provided as a `Characteristic` or `Compartment` object. If provided, at each timepoint the sum of the `includes` objects will be divided by the `vals` attribute of the `denominator`. The most common usage scenario for this is to define a characteristic corresponding to a prevalance (e.g., where the `includes` list sums up the number of infector people, and the denominator is a characteristic including all people in the population). If a `denominator` is supplied, then the `is_fraction` flag is `True` for the `Characteristic`
- The `update(ti)` method is called during integration, and computes the `vals` attribute at time index `ti` based on the `includes` and `denominator` objects
- The `dependency` flag indicates whether the value of the characteristic needs to be computed during integration or not. A `Characteristic` is dependent if it is used in a `Parameter` function. If `False`, then the value of the characteristic will be computed at the end of integration using vectorized operations for efficiency.

To save storage space after the simulation is complete, the values for characteristics are not generally stored. Instead, the `vals` property attribute dynamically computes the characteristic value based on the compartment sizes, which are retained. This is useful because there are often more characteristics than compartments, and all characteristics can be computed based on compartment values. However, to avoid the computational overhead during model integration, the characteristic contains a `_internal_vals` member variable that actually stores the characteristic value during integration. If this is not `None`, then the `vals` method will simply return the `_internal_vals` array.

Parameter
***********************************************************************************************

[[graphics/Parameter.png]]

A parameter object provides a way to compute variables based on the value of other variables, either for use as simulation outputs, or to dynamically compute transition rates (i.e. `Link` values) during integration. There is one `Parameter` object for every entry listed in the 'Parameters' sheet of the cascade workbook, plus an additional `Parameter` for every pair of populations that has a transfer between them. Note that there is only one transfer `Parameter` for every pair of populations, but there is a `Link` between every corresponding compartment within those populations - so for example, aging from `0-4` to `5-14` will have a single `Parameter` representing the total number of people changing populations, and there would be links between `[0-4 Sus]->[5-14 Sus]` and `[0-4 Vac]->[5-14 Vac]`. 

A `Parameter` has the following key features:

- The `links` attribute stores a list of `Links` that derive their value from the `Parameter` object. If this list is empty, then the `Parameter` is either a dependency for another `Parameter`, or an `Output` object.
- The `vals` attribute represents either a transition rate (in units of fraction/probability or number of people) or otherwise a quantity with unknown units. If a parameter represents a transition rate, its units are assumed to be annualized, and will be converted to timestep-based values during integration (the method for conversion depends on `units` attribute of the `Parameter`). At construction, the `Parameter` is loaded in with values supplied from the `parset` if values are available
- The `fcn_str` optionally specifies a formula that is used to compute the value of the `Parameter` dynamically
- If an `fcn_str` is provided, the `deps` list contains a list of objects whose values are used in the `fcn_str` formula. Allowed objects are `Compartments`, `Characteristics`, `Parameters`, and `Links`. A `Characteristic` or `Parameter` that appears in a `deps` list is considered a dependency and the value of that object needs to be computed during integration. If a `Parameter` is used to supply values for a transition, then it is considered a dependency, and it, together with all of the variables in the `deps` list, needs to be computed during integration. Otherwise, ths parameter is only used for output, and it is computed using vector operations at the end of the simulation. Because parameters are used to compute values for links, the inclusion of `Links` in parameter functions is only permitted if the parameter is not a dependency (i.e., if it is an output).
- The `dependency` flag indicates whether the value of the parameter needs to be computed during integration or not. A `Parameter` is dependent if it appears in the `deps` list of another `Parameter`, or if the `links` list is not empty (which indicates the parameter value is required during integration to supply the flow rates for the links).
- The `scale_factor` rescales the parameter value - this is the calibration y-factor
- The `limits` property optionally specifies lower and upper bounds for the parameter value. These are hard limits that are applied right before the `Link` values are computed, so they are implemented after any programs or special operations (i.e. interactions) are computed
- The `pop_aggregation` flag specifies whether the parameter value will be computed in `Model.update_pars` or in `Parameter.update()`. Parameter aggregation across populations (e.g. for cross-population disease transmission) is governed by the special functions `SRC_POP_AVG` and `TGT_POP_AVG` and these calculations are implemented in `Model.update_pars` because they require multiple `Parameter` objects.
- The `update(ti)` method is called during integration, and computes the `vals` attribute at time index `ti` based on the `fcn_str` if it is not `None`
- The `source_popsize(ti)` method is used to compute the number of people reached by this `Parameter` at time index `ti`, which is required when computing `Program` disaggregations if the `Parameter` is in number units. The `source_popsize` is defined as the sum of the source compartment sizes for every `Link` whose parameter is supplied by this `Parameter` i.e., it is `sum([Link.source.vals[ti] for Link in Parameter.links])`. As this value may be accessed multiple times when computing programs, it is internally cached for efficiency.
- The 
Note that transfer parameters currently do not support having a function - instead, they only draw their values directly from interpolated data. This is because transfer parameters link populations, and as such they are specified in the databook rather than in the framework.

Population
***********************************************************************************************

[[graphics/Population.png]]

A `Population` stores lists the base objects listed above, all associated with a single population. It has the following key features:

- `comps` is a list of `Compartment` objects
- `characs` is a list of `Characteristic` objects
- `links` is a list of `Link` objects
- `pars` is a list of `Parameter` objects
- The `get_comp(name)`,  `get_links(name)`, `get_charac(name)`, and `get_par(name)` methods return their respective objects based on the `name` attribute, which allows objects to be located within a population based on their name. This is implemented as a dictionary lookup to improve performance
- The `get_variable(name)` will return a list of variables with that name, regardless of their type. It also supports looking up links based on `source_name:dest_name:par_name` syntax where each of those quantities is optional. For example, `sus:vac` returns all links between compartments `sus` and `vac`.
- The `popsize(ti)` method returns the number of people in all compartments (except birth and death) at timepoint `ti`. However, typically this value is accessed via a `Characteristic` which improves efficiency (such a `Characteristic` is typically defined anyway, so that it can be used as an output or in a `Parameter` function). 
- The `gen_cascade` function takes in a `settings` object, and constructs and wires together all of the compartments, characteristics, links, and parameters required. It is called automatically by the `Population` constructor. 
- The `initialize_compartments` method assigns the initial compartment values based on the characteristics provided in the parset. 

Model
***********************************************************************************************

The `Model` object is a class that contains all of the `Populations` for a simulation, and has methods to perform integration. Its key attributes are:

- `pops` a list of population groups that this model subdivides into.
- `interactions` stores the data associated with inter-population interactions
- `par_list` is a list of all parameters code names in the model for use during integration
- `programs_active` is True or False depending on whether programs will be used or not
- `progset` is a copy of the progset (containing the program-related parameters) used for this run
- `program_instructions` is a copy of the program instructions used for this simulation run
- `t` is the simulation time vector, shared by all variables within this model
- `dt` is the simulation time step
- `framework` is a copy of the framework which stores metadata associated with all of the integration objects (these may be user-customized if the user has added extra columns to the framework file) as well as stores the cascades and plot information used by the `Result` object for plotting and exporting
- `_vars_by_pop` a cache to look up lists of variables by name across populations
- `_t_index` keeps track of array index for current timepoint data within all compartments.
- `_program_cache` caches some program values for use during integration

The key methods are

- `build` which constructs required populations. As noted above, the `Population` constructor instantiates objects representing the cascade within a population. However, if transfers are present, then there are also `Parameters` and `Links` representing cross-population interactions. These are stored in the source `Population` so that they can be treated the same as all other `Parameters` and `Links` during integration, but they are instantiated by `model.build()` because they are intrinsically properties that intrinsically span populations. 
- `process` which actually integrates the simulation
- The `run_model` which wraps building, processing, and computing results. The input consists of settings, a `parset`, and optionally a `progset` and `ProgramInstructions`, and the output is a `Result`

Note that the `Model` forms the primary storage of the `Result` object, and thus it is possible to retrieve detailed output from the model run by querying the `Result` object. This also means that there is minimal post-processing time to reorganize the model outputs, because they are generally accessed in-place.

#Building
***********************************************************************************************

Building the model proceeds in the following stages

1. `Population` objects are instantiated
2. Initial characteristic values used to compute the initial compartment sizes, which are loaded into the `Compartment` objects
3. Populate the `Parameter` objects with interpolated data values, for all data that is present
4. Instantiate the `Parameter` and `Link` objects associated with transfers, and populate these `Parameter` objects with the transfer data values

#Integrating
***********************************************************************************************

[[graphics/Integration_workflow.png]]

The integration workflow is an interative process, alternating between updating the compartment sizes, and updating the link values. The main integration loop is in `Model.process()`. The stages are as follows

	self.update_comps() # This writes values to comp.vals[ti+1] so this will be out of bounds if self._t_index == self.t.size-1
	self._t_index += 1  # Step the simulation forward
	self.update_pars()
	self.update_links()
	self.update_junctions()

- In the first stage, `Model.update_comps()` updates the compartment values using the values contained in the `Links`. The link values will have been set at the end of the previous time step. Junction compartment sizes are skipped because they are always zero and dealt with separately.
- In the second stage, `Model.update_pars()` updates the parameter values. The parameter update proceeds as follows:
	1. First, if a program has a function, that function is evaluated
	2. If programs are active, the parameter value is overwritten using the program set
	3. If averaging over populations is required, this is performed now and the parameter values are again updated
	4. If the program has limits, the value is clipped to the allowed range
- In the third stage, `Model.update_links()`, the parameter values are propagated into the link objects. This proceeds as follows:
	1. The proposed link values are computed as a number of people. This involves rescaling the parameter value onto the simulation time step, and converting it to a number of people. This conversion depends on the units that the parameter is in, and is performed here. Note that if a parameter is in units of number of people, the outflow is disaggregated proportionately over all of the links at this step, depending on what fraction of the total number of people reached by the parameter are attributable to each link.
	2. If a compartment would become negative because the proposed link values flowing out of a compartment exceed the number of people in that compartment, all of the outgoing links for that compartment are rescaled such that the total number of people leaving matches the compartment's size. Note that only people currently in the compartment are eligible to leave the compartment, so it is not possible for new inflows to contribute to outflows.

	This update is only performed for links that flow out of non-junction compartments. This is because outflows from junctions are resolved in the next step.
- In the final stage, `Model.update_junctions()` computes the junction outflows. This is performed at this point in order to ensure that junction outflow links have a non-NaN value at the last timestep. To resolve the junction outflows:
	1. The number of people in the junction is determined by adding up the value of all of the incoming links
	2. The outflow links are calculated based on the parameters governing transitions out of junctions - these must be in 'proportion' units so no timestep rescaling is necessary
	3. If the outflow is into a non-junction compartment, then nothing further needs to be done, because the downstream compartment will be updated by `Model.update_comps()` at the next timestep. However, if the outflow is into another junction, that junction's value is updated, and the junction calculation is re-run to flush those people as well. 
	4. The calculation proceeds until all people have left the junctions. An infinite loop can occur if there is a cycle between junctions, without any normal compartments between them. In that case, the loop will be aborted with an error. 

	Note that the initialization might result in junctions having a nonzero number of people at the first time step. Therefore, the junctions need to be flushed prior to the simulation starting. This is performed by updating the parameters and junctions, and then updating the parameters, links, and junctions again. For the initial flush, a special flag is passed to `update_junctions` which tells it to use the junction's current nonzero initial value, instead of summing over incoming links

At the end of integration, the values for non-dependent parameters need to be computed - this is also performed in `model.process()`.

Linking and unlinking
***********************************************************************************************

The network of integration objects makes it easy to traverse the graph to trace back quantities. For example, `link.source.outlinks` would be a list of all of the outgoing links for the source compartment given an initial link. Because cyclical references are common (e.g, a `link` has a `source` which has that `link` in `source.outlinks`) an additional step is needed in order to be able to pickle and unpickle `Model` objects. This step recursively replaces all of the references with IDs. It proceeds as follows

- `Model.unlink` replaces references with IDs in all of it's properties. Then it calls `Population.unlink()` on every population. `Population.unlink()` replaces all of its references, and then calls `Variable.unlink()` on all of its variables. This allows variables to control how they unlink themselves, which is important because some variables have references that others do not (e.g., `Characteristics` have `includes` while `Parameters` have `deps`). At the end of this process, the variables are only stored once in the `Population` lists e.g. `Population.comps()`
- `Model.relink` reverses this. First it assembles a dict mapping ID to objects. Then it calls `relink` on all populations, passing in this dict of objects. In turn, `Variables` can `relink` themselves using this dict. The dict needs to be constructed at the `Model` level so that `Population` objects can `relink` transfers that span populations

The whole process is transparent to the user, because it is controlled by the `__getstate__`, `__setstate__` and `__deepcopy__` methods, so users generally will never see a `Model` object in an unlinked state. 
