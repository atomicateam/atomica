# Describe a Framework

Explain what an Atomica framework models: enumerate compartments, draw the flow diagram, and table the parameters driving each transition. Use when the user asks to describe, explain, or explore a framework file.

## Steps

1. **Get all variables** — call `list_variables(framework_path)` with no search terms.
   Organise the results by type: compartments (`comp`), characteristics (`charac`),
   parameters (`par`), and interactions (`interpop`).

2. **Summarise each type**:
   - *Compartments*: list code names and display names; these are the disease states
     people flow through.
   - *Characteristics*: aggregated quantities derived from compartments (e.g. prevalence,
     population size).
   - *Parameters*: transition rates and other quantities that drive model dynamics.
   - *Interactions*: cross-population parameters (only present in multi-population models).

3. **Map the compartment flow** — for each compartment, call `map_transitions(framework_path, code_name)`
   to find where people move. Build a plain-English description of the flow
   (e.g. "Susceptible → Latent driven by `foi`, Latent → Active driven by `v_rate`").

4. **Detail key parameters** — for parameters that appear in transitions, call
   `detail_parameter(framework_path, code_name)` to retrieve the parameter function and
   its dependencies. Note any parameters that depend on other variables.

5. **Write the summary** in this order:
   - One-paragraph overview of what the model represents.
   - Compartment flow diagram (plain text arrows).
   - Table of all parameters with display name, function (if any), and what transition it drives.
   - Any characteristics or interactions worth highlighting.
