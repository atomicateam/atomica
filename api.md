## Workflows

### Framework IO operations

Create empty Framework on the heap (i.e., one without a framework file uploaded)

Export Framework to storage/workbook (given instructions) from the heap

Export Framework to workbook from the heap

Import Framework from storage/workbook onto the heap

Import Framework from workbook onto the heap

Delete Framework from the heap

Edit Framework

#### Project preparations

Create empty Project (given Framework object) in storage

Export Project to storage

Import Project from storage

Delete Project from storage

Export Data to workbook (given instructions)

Import Data from workbook

#### Parameter preparations

Create new default ParameterSet

Delete ParameterSet

Manual calibration - set y-factor 
	
	parset.set_scaling_factor(par_name,pop_name,value)

Insert data point

	insertValuePair

Remove data point

	remove

	removeBetween

Autocalibrate ParameterSet

The inputs are

- `pars_to_modify` list of tuples `(pop_name,par_name)`
- `outputs_to_use` list of tuples

	proj.autocalibrate(parset_name,pars_to_modify,outputs_to_use) 


#### Program preparations

Create new default ProgramSet

Create Program in Data

Delete Program in Data

Create Program in ProgramSet

Delete Program in ProgramSet

Plot ProgramSet

Delete ProgramSet

Edit ProgramSet manually 

Autoreconcile ProgramSet (given instructions, perhaps two options; in-place and duplicated)

#### Model simulation

Create results, i.e. run simulation (given ParameterSet/ProgramSet objects and instructions)

Delete results

Plot results

#### Scenarios

Create unprocessed ParameterScenario (i.e. instructions for model run sans ProgramSet)

Create unprocessed ProgramScenario ( (i.e. instructions for model run for model run with ProgramSet)

Delete scenario

Add scenario override, i.e. Edit scenario (for ParScen specify par overwrite, for ProgScen specify 
budget/coverage/attribute overwrite)

Delete scenario override, i.e. edit scenario

Process scenarios

Plot scenarios

Export scenario

Import scenario

#### Optimisation

Create unprocessed optimisation (i.e. instructions)

Delete optimisation

Edit optimisation

Process optimisation

Plot optimisation

Export optimisation

Import optimisation


