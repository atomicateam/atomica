"""
Version:
"""

import atomica.ui as au
import sciris.core as sc
import numpy as np

def rpc_optimize(proj,parset_name,progset_name,optimization_name,start_year,end_year,budget_factor,objective_weights,prog_spending,maxtime=10):
    # RPC call for TB optimization
    # INPUTS
    # - parset_name : A string with the name of the parset to use. This parset should already exist in the project
    # - progset_name : A string with the name of the progset to use. This progset should already exist in the project
    # - optimization_name : A string that will name this optimization
    # - start_year : The year of program onset and when spending will be applied
    # - end_year : The end year for the simulation. Programs run up to this year, and the objective will be evaluated from start_year to end_year
    # - budget_factor : This will rescale total spending
    # - objective_weights : This is a dict/odict mapping {variable_name:weight}. Available variables are determined by the FE
    # - prog_spending : This is a dict/odict mapping {program_name:(minspend,maxspend)}. It is assumed that the FE will provide absolute values for
    #                   both quantities for every program (these could default to minspend=0 and maxspend=np.inf but those defaults should be assigned
    #                   before this function is called
    # - maxtime : Set ASD's maxtime, this might default to np.inf for the actual FE but useful to make it shorter when testing
    #
    # OUTPUTS
    # - Optimized Result, for addition to the database and project by the FE code
    #   The optimized program instructions are available in `Result.model.program_instructions`. Note that the Project will also have a new
    #   Optimization object, so the Project will probably need to be saved after calling this function too

    instructions = au.ProgramInstructions(alloc=None,start_year=start_year) # Set up default ProgramInstructions with no alloc because we are using the values from the progbook
    progset = proj.progsets[progset_name] # Retrieve the progset

    # Add a spending adjustment in the program start year for every program in the progset, using the lower/upper bounds
    # passed in as arguments to this function
    adjustments = []
    for prog_name in progset.programs:
        limits = prog_spending[prog_name]
        adjustments.append(au.SpendingAdjustment(prog_name,t=start_year,limit_type='abs',lower=limits[0],upper=limits[1]))

    # Add a total spending constraint with the given budget scale up
    constraints = au.TotalSpendConstraint(budget_factor=budget_factor)

    # Add all of the terms in the objective
    measurables = []
    for name,weight in objective_weights.items():
        measurables.append(au.Measurable(name,t=[start_year,end_year],weight=weight))

    # Create the Optimization object
    proj.make_optimization(name=optimization_name, adjustments=adjustments, measurables=measurables,constraints=constraints, maxtime=maxtime) # Evaluate from 2020 to end of simulation

    # Run the optimization
    optimized_result = proj.run_optimization(optimization=optimization_name,parset='default',progset='default',progset_instructions=instructions)

    return optimized_result

# Set up an example project
proj = au.demo(which='tb',do_plot=0)
proj.load_progbook(progbook_path="databooks/progbook_tb.xlsx", make_default_progset=True)

# Set up the optimization inputs that would normally be retrieved from the FE
parset_name = 'default'
progset_name = 'default'
optimization_name = 'example'
start_year = 2018
end_year = 2025
budget_factor = 1.0
objective_weights = {'alive':-1,'ddis':1,':acj':1} # These are TB-specific: maximize people alive, minimize people dead due to TB. Note that ASD minimizes the objective, so 'alive' has a negative weight
prog_spending = sc.odict()
for prog_name in proj.progsets[0].programs.keys():
    prog_spending[prog_name] = (1,np.inf)

# Call the optimization RPC and get an optimized result
optimized_result = rpc_optimize(proj,parset_name,progset_name,optimization_name,start_year,end_year,budget_factor,objective_weights,prog_spending)

# For comparison, do an unoptimized budget scenario and plot the differences in simulation output
unoptimized_result = proj.run_sim(parset="default", progset='default', progset_instructions=au.ProgramInstructions(start_year=start_year), result_name="unoptimized")
d = au.PlotData([unoptimized_result, optimized_result], outputs=['alive','ddis'], pops='all', project=proj)
au.plot_series(d, axis="results")

# Retrieve the original and optimized budgets using the contents stored within the Results themselves
print(unoptimized_result.model.progset.get_alloc(start_year,unoptimized_result.model.program_instructions))
print(optimized_result.model.progset.get_alloc(start_year,optimized_result.model.program_instructions))



