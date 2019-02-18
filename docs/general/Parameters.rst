Parameters
##########

Types of parameter
******************

Parameters are all defined on the 'Parameters' sheet of the framework. Depending on the structure of the model defined in the framework, a parameter may have certain attributes or restrictions if used in a particular way. We therefore introduce three classifications to help refer to such parameters. These classifications are:

- **Transition parameter** - A parameter is referred to as a 'transition parameter' if it appears in the transition matrix and is thus *directly* associated with flow rates. 
- **Function parameter** - A parameter is referred to as a 'function parameter' if a function is provided in the Framework for the parameter
- **Output parameter** - A parameter is referred to as an 'output parameter' if it does not directly or indirectly contribute to transitions. A parameter contributes directly to transitions if it is an output parameter, but it can also contribute indirectly if it appears in a transition parameter's function (or even further back, if it appears in the function of any parameter that ends up affecting a transition parameter)

Functions
*********

In the framework, a parameter can have a function associated with it, which can compute the value of a parameter based on the values of other integration objects like compartments, characteristics, parameters, and links (flow rates). You can also refer to the simulation time as `t` and the time step as `dt`. Standard math operations can be performed, as well as common functions like ``max``, ``min``, ``exp`` etc. Valid functions can be found in ``function_parser.py``. 

Parameters are updated in the order in which they appear in the framework. This means that parameter functions can only refer to parameters that appear above them in the framework. Atomica will automatically validate this when the framework is loaded. This also means that any program overwrites that affect terms inside a parameter function will be performed prior to the function being evaluated. 

As mentioned above, it is possible to include actual flow rates in parameter functions. These can be specified in two ways

- You can append ``:flow`` to the name of any transition parameter which resolves to the sum of all transitions driven by that parameter. This means if a parameter drives multiple transitions (e.g. deaths from multiple compartments) they will also be included
- You can use the compartment syntax to specify flows between compartments e.g. ``sus:vac`` for flows between susceptible and vaccinated, ``sus:`` for all flows out of susceptible, and ``:vac`` for all flows into vaccinated. You can also use ``sus:vac:par_name`` to select only flows between compartments driven by a particular parameter, in the case where multiple parameters contribute independently to the same transition.

.. caution::

    All link values are automatically annualized inside the parameter function and are in units of 'people/year' - this prevents the values from changing relative to other parameters if the model step size is changed.

Finally, all parameters are updated prior to computing flow rates. This is because flow rates may need to be rescaled in order to prevent negative compartment sizes, and this rescaling can only take place after all parameters have been computed. Thus, flow rates cannot appear in any parameter that contributes directly or indirectly to transitions, as there would otherwise be a circular dependency.

.. caution::

    Links can only be used inside parameter functions for output parameters

Performance considerations
**************************

The structure of the parameters in the model can have a significant effect on performance. The root causes is that in Python, it is much faster to perform calculations with vectorized operations rather than repeated scalar operations. 

A vectorized operation is one that can be performed on all time points simultaneously, whereas a scalar operation operates on only one time point at a time. Operating one time point at a time is required if two conditions are met

- The parameter is required to directly or indirectly drive a transition, **and**
- The parameter depends on a compartment or characteristic

If a parameter depends on a compartment or characteristic, then it can only be evaluated after the compartment sizes have been computed. In the case of output parameters, this can be performed as a fast vector operation after integration is complete. If that same parameter drives transitions however, then it must be evaluated during integration using slower scalar operations. Similarly, if a parameter only depends on quantities in the databook (even if it depends on other parameters, as long as those parameters only depend on the databook) then the parameter can be evaluated in a fast vector operation either before or after integration, depending on whether it is needed for transitions.

Atomica will automatically select the fastest possible computation, but be aware that the inclusion of compartments and characteristics in parameter functions can have a significant effect on performance. 

Timescales
***********

Transitions in the model are driven by parameters. If the parameter is specified as a probability or a number of people, then there is an implicit time period associated with the flow. This is 1 year by default. So for example,

- A transition parameter in probability units is interpreted as 'probability (per year)'
- A transition parameter in number units is interpreted as 'number of people (per year)'
- A transition parameter in duration units is interpreted in years

However, working exclusively with years can be problematic for two reasons

1. The values entered in the databook are entered in the same units as the parameter. In some cases, it may be preferable for end users to enter values in different units. For example, for fast processes it may be clearer to enter values in days rather than years. Similarly, in some cases available data may list outcomes over different timescales e.g. probability of treatment success over a 1 month period. Although this can be inconvenient, it is possible to use formulas in the databook to work around this, or conversions in the framework. However, either option adds considerable complexity.
2. If models are run with very small timesteps, such as daily time steps (required for frameworks where the fastest processes are on this timescale - for example, the mosquito lifespan for malaria is on this scale) - then the rescaling of probabilities by repeated sampling can suffer from loss of numerical precision. This is particularly problematic when moving between daily and annual probabilities. This is a critical issue that can prevent implementation of a model.

To address this, it is possible to optionally specify a *timescale* associated with a parameter. The timescale specifies the period in years associated with a parameter. If not specified, parameters are treated as having a timescale of 1, which corresponds to annual units. If a different value is entered, the effect is to change the units of the parameter. For example, if the timescale was entered as :math:`1/365 = 0.00274`, then the parameter would be treated as a daily quantity. The exact units depend on the format of the quantity:

- If the transition parameter has timescale :math:`1/365` and format 'duration' then the units are 'days'
- If the transition parameter has timescale :math:`1/365` and format 'probability' then the units are 'probability per day'
- If the transition parameter has timescale :math:`1/365` and format 'number' then the units are 'number per day'

If a parameter has a timescale, then the units in the databook will automatically reflect the timescale. If a timescale is present in the databook, then the framework must have a matching timescale. So for example, if the framework declares that a parameter has timescale :math:`1/365` (days) then the databook *must* provide the value in days (i.e. users cannot change this in the databook by changing it to read 'weeks' without making a corresponding change to the framework).

The timescales affect simulations and plotting in two ways

1. During model integration, the parameter is in the units specified in the framework, but flows in the model (the values stored in ``Link`` objects) are *always* in 'number per timestep' units. If a parameter has a timescale, that timescale will affect the conversion
2. When constructing a ``PlotData`` object with time aggregation or accumulation, the timescale will be taken in to account. Where applicable, plots will be labelled including the timescale (e.g. a probability parameter with a timescale of :math:`1/52` would have an axis label of 'Probability (per week)' on plots). 

Thus, Parameter objects themselves always store values in the units specified in the framework. Conversion only takes place during computation of flow rates or computation of ``PlotData`` aggregations. 

.. note::

    Because Parameter timescales are only converted when computing flow rates, user-defined parameter functions always operate on parameters in their native units. 

This means that it is up to the modeller to explicitly handle any unit conversions required - for example, if combining a 'Number per day' and a 'Number per week' in a function, it would likely be necessary to explicitly introduce a factor of ``7``. This would be done in the Framework in conjunction with specification of the timescales for the relevant parameters. Users are unable to change the timescale in the databook by design because the conversion is an arbitrary operation and depends on the parameter timescale - the modeller has complete control in the Framework to define the format and units and construct the model accordingly, without having to deal with the possibility of the user entering different formats or units. 
