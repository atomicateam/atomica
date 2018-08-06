"""
Version:
"""

import logging
logger = logging.getLogger()

## Write the log to a file
# h = logging.FileHandler('testworkflow.log',mode='w')
# logger.addHandler(h)

## Setting DEBUG level before importing Atomica will display the structure warnings occurring during import
# logger.setLevel('DEBUG')

import os
import atomica.ui as au
import sciris.core as sc
import numpy as np
import matplotlib.pyplot as plt
from atomica.core.optimization import optimize

# Atomica has INFO level logging by default which is set when Atomica is imported, so need to change it after importing
# logger.setLevel('DEBUG')
test='sir'

torun = [
"standard",
"standard_mindeaths",
"delayed",
"gradual",
'mixed',
'parametric_paired',
"money",
'cascade_final_stage',
'cascade-conversions'
]

# Load the SIR demo and associated programs
P = au.demo(which='sir',do_plot=0)
filename = "databooks/progbook_"+test+".xlsx"
P.load_progbook(progbook_path=filename, make_default_progset=True)

def run_optimization(proj,optimization,instructions):
    unoptimized_result = proj.run_sim(parset=proj.parsets["default"], progset=proj.progsets['default'], progset_instructions=instructions, result_name="unoptimized")
    optimized_instructions = optimize(P, optimization, parset=proj.parsets["default"], progset=proj.progsets['default'], instructions=instructions)
    optimized_result = proj.run_sim(parset=proj.parsets["default"], progset=proj.progsets['default'], progset_instructions=optimized_instructions, result_name="optimized")
    return unoptimized_result,optimized_result

### STANDARD OUTCOME OPTIMIZATION
# In this example, Treatment 2 is more effective than Treatment 1. The initial allocation has the budget
# mostly allocated to Treatment 1, and the result of optimization should be that the budget gets
# reallocated to Treatment 2
if 'standard' in torun:
    alloc = sc.odict([('Risk avoidance',0.),
                     ('Harm reduction 1',0.),
                     ('Harm reduction 2',0.),
                     ('Treatment 1',50.),
                     ('Treatment 2', 1.)])

    instructions = au.ProgramInstructions(alloc=alloc,start_year=2020) # Instructions for default spending
    adjustments = []
    adjustments.append(au.SpendingAdjustment('Treatment 1',2020,'abs',0.,100.))
    adjustments.append(au.SpendingAdjustment('Treatment 2',2020,'abs',0.,100.))
    measurables = au.MaximizeMeasurable('ch_all',[2020,np.inf])
    constraints = au.TotalSpendConstraint() # Cap total spending in all years
    optimization = au.Optimization(name='default', adjustments=adjustments, measurables=measurables,constraints=constraints) # Evaluate from 2020 to end of simulation

    (unoptimized_result,optimized_result) = run_optimization(P, optimization, instructions)

    for adjustable in adjustments:
        print("%s - before=%.2f, after=%.2f" % (adjustable.name,unoptimized_result.model.program_instructions.alloc[adjustable.name].get(2020),optimized_result.model.program_instructions.alloc[adjustable.name].get(2020))) # TODO - add time to alloc

    d = au.PlotData([unoptimized_result, optimized_result], outputs=['ch_all'],project=P)
    au.plot_series(d, axis="results")

### STANDARD OUTCOME OPTIMIZATION, MINIMIZE DEATHS
# In this example, Treatment 2 is more effective than Treatment 1. The initial allocation has the budget
# mostly allocated to Treatment 1, and the result of optimization should be that the budget gets
# reallocated to Treatment 2
if 'standard_mindeaths' in torun:
    alloc = sc.odict([('Risk avoidance',0.),
                     ('Harm reduction 1',0.),
                     ('Harm reduction 2',0.),
                     ('Treatment 1',50.),
                     ('Treatment 2', 1.)])

    instructions = au.ProgramInstructions(alloc=alloc,start_year=2020) # Instructions for default spending
    adjustments = []
    adjustments.append(au.SpendingAdjustment('Treatment 1',2020,'abs',0.,100.))
    adjustments.append(au.SpendingAdjustment('Treatment 2',2020,'abs',0.,100.))
    measurables = au.MinimizeMeasurable(':dead',2030)
    constraints = au.TotalSpendConstraint() # Cap total spending in all years
    optimization = au.Optimization(name='default', adjustments=adjustments, measurables=measurables,constraints=constraints) # Evaluate from 2020 to end of simulation

    (unoptimized_result,optimized_result) = run_optimization(P, optimization, instructions)

    for adjustable in adjustments:
        print("%s - before=%.2f, after=%.2f" % (adjustable.name,unoptimized_result.model.program_instructions.alloc[adjustable.name].get(2020),optimized_result.model.program_instructions.alloc[adjustable.name].get(2020))) # TODO - add time to alloc

    d = au.PlotData([unoptimized_result, optimized_result], outputs=[':dead'],project=P)
    au.plot_series(d, axis="results")

### DELAYED OUTCOME OPTIMIZATION
# In this example, Treatment 2 is more effective than Treatment 1. However, we are given the budget in
# 2020 and are only allowed to change it from 2025.
if 'delayed' in torun:
    alloc = sc.odict([('Risk avoidance',0.),
                     ('Harm reduction 1',0.),
                     ('Harm reduction 2',0.),
                     ('Treatment 1',au.TimeSeries([2020,2024],[50,50])),
                     ('Treatment 2', au.TimeSeries([2020,2024],[1,1]))])

    instructions = au.ProgramInstructions(alloc=alloc,start_year=2020) # Instructions for default spending
    adjustments = []
    adjustments.append(au.SpendingAdjustment('Treatment 1',2025,'abs',0.,100.))
    adjustments.append(au.SpendingAdjustment('Treatment 2',2025,'abs',0.,100.))
    measurables = au.MaximizeMeasurable('ch_all',[2020,np.inf])
    constraints = au.TotalSpendConstraint() # Cap total spending in all years
    optimization = au.Optimization(name='default', adjustments=adjustments, measurables=measurables,constraints=constraints) # Evaluate from 2020 to end of simulation

    (unoptimized_result,optimized_result) = run_optimization(P, optimization, instructions)

    t = optimized_result.model.t
    unoptimized_spending = unoptimized_result.model.progset.get_alloc(unoptimized_result.model.program_instructions,t)
    optimized_spending = optimized_result.model.progset.get_alloc(optimized_result.model.program_instructions,t)

    plt.figure()
    plt.plot(t,unoptimized_spending['Treatment 1'],label='Unoptimized Treatment 1')
    plt.plot(t,optimized_spending['Treatment 1'],label='Optimized Treatment 1')
    plt.plot(t,unoptimized_spending['Treatment 2'],label='Unoptimized Treatment 2')
    plt.plot(t,optimized_spending['Treatment 2'],label='Optimized Treatment 2')
    plt.legend()
    plt.title('Fixed spending in 2020, optimized from 2025 onwards')

### GRADUAL OUTCOME OPTIMIZATION
# This is similar to ramped constraints, except the constraint is time-based rather than
# rate-of-change based. That is, rather than limiting the amount by which the spending can
# change, it is specified that the total change takes place over a certain number of years.
# In this case, we have specified spending in 2020 and want to meet spending targets in 2025
# with the caveat that the rollout of the change will take 3 years. Therefore, we fix the spending
# in 2022 and apply the adjustment in 2025, resulting in a smooth change in spending from 2022-2025
if 'gradual' in torun:
    alloc = sc.odict([('Risk avoidance',0.),
                     ('Harm reduction 1',0.),
                     ('Harm reduction 2',0.),
                     ('Treatment 1',au.TimeSeries([2020,2022],[50,50])),
                     ('Treatment 2', au.TimeSeries([2020,2022],[1,1]))])

    instructions = au.ProgramInstructions(alloc=alloc,start_year=2020) # Instructions for default spending
    adjustments = []
    adjustments.append(au.SpendingAdjustment('Treatment 1',2025,'abs',0.,100.))
    adjustments.append(au.SpendingAdjustment('Treatment 2',2025,'abs',0.,100.))
    measurables = au.MaximizeMeasurable('ch_all',[2020,np.inf])
    constraints = au.TotalSpendConstraint() # Cap total spending in all years
    optimization = au.Optimization(name='default', adjustments=adjustments, measurables=measurables,constraints=constraints) # Evaluate from 2020 to end of simulation

    (unoptimized_result,optimized_result) = run_optimization(P, optimization, instructions)

    t = optimized_result.model.t
    unoptimized_spending = unoptimized_result.model.progset.get_alloc(unoptimized_result.model.program_instructions,t)
    optimized_spending = optimized_result.model.progset.get_alloc(optimized_result.model.program_instructions,t)

    plt.figure()
    plt.plot(t,unoptimized_spending['Treatment 1'],label='Unoptimized Treatment 1')
    plt.plot(t,optimized_spending['Treatment 1'],label='Optimized Treatment 1')
    plt.plot(t,unoptimized_spending['Treatment 2'],label='Unoptimized Treatment 2')
    plt.plot(t,optimized_spending['Treatment 2'],label='Optimized Treatment 2')
    plt.legend()
    plt.title('Fixed spending in 2020, optimized in 2025 with 3y onset')

### MIXED TIMING OUTCOME OPTIMIZATION
# Treatment 2 can have its funding adjusted in both 2023 and 2027. Treatment 1 can have its funding
# only adjusted in 2023. The default allocation sees the funding smoothly change to equal funding on both
# programs in 2022. The total spend constraint is only applied in 2023, at which time both Treatment 1 and
# Treatment 2 are adjustable and spending is capped at 25+25=50 units. In 2027, Treatment 2 is the only
# adjustable program and there is no total spending constraint. Thus spending on this program should hit
# the upper bound. Thus the optimal spending pattern will be spending $50 on Treatment 2 in 2023, and $100
# on Treatment 2 in 2025, with $0 spend on Treatment 1 from 2023 onwards
if 'mixed' in torun:
    alloc = sc.odict([('Risk avoidance',0.),
                     ('Harm reduction 1',0.),
                     ('Harm reduction 2',0.),
                     ('Treatment 1',au.TimeSeries([2020,2022],[50,25])),
                     ('Treatment 2', au.TimeSeries([2020,2022],[1,25]))])

    instructions = au.ProgramInstructions(alloc=alloc,start_year=2020) # Instructions for default spending
    adjustments = []
    adjustments.append(au.SpendingAdjustment('Treatment 1',2023,'abs',0.,100.))
    adjustments.append(au.SpendingAdjustment('Treatment 2',[2023,2027],'abs',0.,100.))
    measurables = au.MaximizeMeasurable('ch_all',[2020,np.inf])
    constraints = au.TotalSpendConstraint(t=2023) # Cap total spending in 2023 only
    optimization = au.Optimization(name='default', adjustments=adjustments, measurables=measurables,constraints=constraints) # Evaluate from 2020 to end of simulation

    (unoptimized_result,optimized_result) = run_optimization(P, optimization, instructions)

    t = optimized_result.model.t
    unoptimized_spending = unoptimized_result.model.progset.get_alloc(unoptimized_result.model.program_instructions,t)
    optimized_spending = optimized_result.model.progset.get_alloc(optimized_result.model.program_instructions,t)

    plt.figure()
    plt.plot(t,unoptimized_spending['Treatment 1'],label='Unoptimized Treatment 1')
    plt.plot(t,optimized_spending['Treatment 1'],label='Optimized Treatment 1')
    plt.plot(t,unoptimized_spending['Treatment 2'],label='Unoptimized Treatment 2')
    plt.plot(t,optimized_spending['Treatment 2'],label='Optimized Treatment 2')
    plt.legend()
    plt.title('Multi-time optimization in 2023 and 2025 (constrained in 2023)')

if 'parametric_paired' in torun:
    alloc = sc.odict([('Risk avoidance',0.),
                     ('Harm reduction 1',0.),
                     ('Harm reduction 2',0.),
                     ('Treatment 1',50.),
                     ('Treatment 2',1.)])

    instructions = au.ProgramInstructions(alloc=alloc,start_year=2020) # Instructions for default spending
    adjustments = []
    adjustments.append(au.PairedLinearSpendingAdjustment(['Treatment 1','Treatment 2'],[2020,2025]))
    measurables = au.MaximizeMeasurable('ch_all',[2020,np.inf])
    constraints = None # Total spending constraint is automatically satisfied by the paired parametric adjustment
    optimization = au.Optimization(name='default', adjustments=adjustments, measurables=measurables,constraints=constraints) # Evaluate from 2020 to end of simulation

    (unoptimized_result,optimized_result) = run_optimization(P, optimization, instructions)

    t = optimized_result.model.t
    unoptimized_spending = unoptimized_result.model.progset.get_alloc(unoptimized_result.model.program_instructions,t)
    optimized_spending = optimized_result.model.progset.get_alloc(optimized_result.model.program_instructions,t)

    plt.figure()
    plt.plot(t,unoptimized_spending['Treatment 1'],label='Unoptimized Treatment 1')
    plt.plot(t,optimized_spending['Treatment 1'],label='Optimized Treatment 1')
    plt.plot(t,unoptimized_spending['Treatment 2'],label='Unoptimized Treatment 2')
    plt.plot(t,optimized_spending['Treatment 2'],label='Optimized Treatment 2')
    plt.legend()
    plt.title('Paired linear funding transfer from 2020-2025')

### MONEY MINIMIZATION
# In this example, Treatment 2 is more effective than Treatment 1. If we spend
# $50 on Treatment 2, then there are 728.01 people alive in 2030. Since Treatment 2 is more
# effective, the cheapest way to achieve at least 728.01 people alive in 2030 is to
# spend only ~$50 on Treatment 2. So to do this optimization, we start by spending $100 on both
# Treatment 1 and Treatment 2 and demonstrate that money optimization where we minimize total
# spend subject to the constraint of the total people alive being at least 728.01
if 'money' in torun:
    alloc = sc.odict([('Risk avoidance',0.),
                     ('Harm reduction 1',0.),
                     ('Harm reduction 2',0.),
                     ('Treatment 1',50.),
                     ('Treatment 2', 60.)])

    instructions = au.ProgramInstructions(alloc=alloc,start_year=2020) # Instructions for default spending

    adjustments = []
    adjustments.append(au.SpendingAdjustment('Treatment 1', 2020, 'abs', 0., 100.)) # We can adjust Treatment 1
    adjustments.append(au.SpendingAdjustment('Treatment 2', 2020, 'abs', 0., 100.)) # We can adjust Treatment 2

    measurables = []
    measurables.append(au.AtLeastMeasurable('ch_all',2030,728.01)) # Need at least 728.01 people in 2030
    measurables.append(au.MinimizeMeasurable('Treatment 1',2020)) # Minimize 2020 spending on Treatment 1
    measurables.append(au.MinimizeMeasurable('Treatment 2',2020)) # Minimize 2020 spending on Treatment 2

    constraints = None  # No extra constraints aside from individual bounds

    optimization = au.Optimization(name='default', adjustments=adjustments, measurables=measurables,constraints=constraints) # Evaluate from 2020 to end of simulation

    (unoptimized_result,optimized_result) = run_optimization(P, optimization, instructions)

    for adjustable in adjustments:
        print("%s - before=%.2f, after=%.2f" % (adjustable.name,unoptimized_result.model.program_instructions.alloc[adjustable.name].get(2020),optimized_result.model.program_instructions.alloc[adjustable.name].get(2020))) # TODO - add time to alloc

    d = au.PlotData([unoptimized_result, optimized_result], outputs=['ch_all'],project=P)
    au.plot_series(d, axis="results")


if 'cascade_final_stage' in torun:
    # This is the same as the 'standard' example, just setting up the fact that we can adjust spending on Treatment 1 and Treatment 2
    # and want a total spending constraint
    alloc = sc.odict([('Risk avoidance',0.),
                     ('Harm reduction 1',0.),
                     ('Harm reduction 2',0.),
                     ('Treatment 1',50.),
                     ('Treatment 2', 1.)])

    instructions = au.ProgramInstructions(alloc=alloc,start_year=2020) # Instructions for default spending
    adjustments = []
    adjustments.append(au.SpendingAdjustment('Treatment 1',2020,'abs',0.,100.))
    adjustments.append(au.SpendingAdjustment('Treatment 2',2020,'abs',0.,100.))
    constraints = au.TotalSpendConstraint() # Cap total spending in all years

    ## CASCADE MEASURABLE
    # This measurable will maximize the number of people in the final cascade stage, whatever it is
    measurables = au.MaximizeCascadeFinalStage('main',[2030],pop_names='all') # NB. make sure the objective year is later than the program start year, otherwise no time for any changes

    # This is the same as the 'standard' example, just running the optimization and comparing the results
    optimization = au.Optimization(name='default', adjustments=adjustments, measurables=measurables, constraints=constraints)
    unoptimized_result = P.run_sim(parset=P.parsets["default"], progset=P.progsets['default'], progset_instructions=instructions, result_name="unoptimized")
    optimized_instructions = optimize(P, optimization, parset=P.parsets["default"], progset=P.progsets['default'], instructions=instructions)
    optimized_result = P.run_sim(parset=P.parsets["default"], progset=P.progsets['default'], progset_instructions=optimized_instructions, result_name="optimized")

    for adjustable in adjustments:
        print("%s - before=%.2f, after=%.2f" % (adjustable.name,unoptimized_result.model.program_instructions.alloc[adjustable.name].get(2020),optimized_result.model.program_instructions.alloc[adjustable.name].get(2020))) # TODO - add time to alloc

    au.plot_multi_cascade([unoptimized_result, optimized_result],'main',pops='all',year=2020)

if 'cascade-conversions' in torun:
    # This is the same as the 'standard' example, just setting up the fact that we can adjust spending on Treatment 1 and Treatment 2
    # and want a total spending constraint
    alloc = sc.odict([('Risk avoidance', 0.),
                      ('Harm reduction 1', 0.),
                      ('Harm reduction 2', 0.),
                      ('Treatment 1', 50.),
                      ('Treatment 2', 1.)])

    instructions = au.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending
    adjustments = []
    adjustments.append(au.SpendingAdjustment('Treatment 1', 2020, 'abs', 0., 100.))
    adjustments.append(au.SpendingAdjustment('Treatment 2', 2020, 'abs', 0., 100.))
    constraints = au.TotalSpendConstraint()  # Cap total spending in all years

    ## CASCADE MEASURABLE
    # This measurable will be
    measurables = au.MaximizeCascadeConversionRate('main',[2030],pop_names='all') # NB. make sure the objective year is later than the program start year, otherwise no time for any changes

    # This is the same as the 'standard' example, just running the optimization and comparing the results
    optimization = au.Optimization(name='default', adjustments=adjustments, measurables=measurables, constraints=constraints)
    unoptimized_result = P.run_sim(parset=P.parsets["default"], progset=P.progsets['default'], progset_instructions=instructions, result_name="unoptimized")
    optimized_instructions = optimize(P, optimization, parset=P.parsets["default"], progset=P.progsets['default'], instructions=instructions)
    optimized_result = P.run_sim(parset=P.parsets["default"], progset=P.progsets['default'], progset_instructions=optimized_instructions, result_name="optimized")

    for adjustable in adjustments:
        print("%s - before=%.2f, after=%.2f" % (adjustable.name, unoptimized_result.model.program_instructions.alloc[adjustable.name].get(2020), optimized_result.model.program_instructions.alloc[adjustable.name].get(2020)))  # TODO - add time to alloc

    au.plot_cascade(unoptimized_result,'main',pops='all',year=2030)
    plt.title('Unoptimized')
    au.plot_cascade(optimized_result,'main',pops='all',year=2030)
    plt.title('Optimized')
