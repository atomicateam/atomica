"""
Version:
"""

import matplotlib.pyplot as plt
import numpy as np
import sciris as sc
import atomica as at
import logging

logger = logging.getLogger()

# Write the log to a file
# h = logging.FileHandler('testworkflow.log',mode='w')
# logger.addHandler(h)

# Setting DEBUG level before importing Atomica will display the structure warnings occurring during import
# logger.setLevel('DEBUG')


# Atomica has INFO level logging by default which is set when Atomica is imported, so need to change it after importing
# logger.setLevel('DEBUG')
test = "sir"  # Only really works for SIR


# np.seterr(all='raise')


def run_optimization(proj, optimization, instructions):
    unoptimized_result = proj.run_sim(parset=proj.parsets["default"], progset=proj.progsets["default"], progset_instructions=instructions, result_name="unoptimized")
    optimized_instructions = at.optimize(proj, optimization, parset=proj.parsets["default"], progset=proj.progsets["default"], instructions=instructions)
    optimized_result = proj.run_sim(parset=proj.parsets["default"], progset=proj.progsets["default"], progset_instructions=optimized_instructions, result_name="optimized")
    return unoptimized_result, optimized_result


# STANDARD OUTCOME OPTIMIZATION
# In this example, Treatment 2 is more effective than Treatment 1. The initial allocation has the budget
# mostly allocated to Treatment 1, and the result of optimization should be that the budget gets
# reallocated to Treatment 2


def test_standard():

    P = at.demo(which=test, do_run=False)
    P.update_settings(sim_end=2030.0)

    alloc = sc.odict([("Risk avoidance", 0.0), ("Harm reduction 1", 0.0), ("Harm reduction 2", 0.0), ("Treatment 1", 50.0), ("Treatment 2", 1.0)])

    instructions = at.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending
    adjustments = list()
    adjustments.append(at.SpendingAdjustment("Treatment 1", 2020, "abs", 0.0, 100.0))
    adjustments.append(at.SpendingAdjustment("Treatment 2", 2020, "abs", 0.0, 100.0))
    measurables = at.MaximizeMeasurable("ch_all", [2020, np.inf])
    constraints = at.TotalSpendConstraint()  # Cap total spending in all years
    optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables, constraints=constraints)  # Evaluate from 2020 to end of simulation

    (unoptimized_result, optimized_result) = run_optimization(P, optimization, instructions)

    for adjustable in adjustments:
        print("%s - before=%.2f, after=%.2f" % (adjustable.name, unoptimized_result.model.program_instructions.alloc[adjustable.name].get(2020), optimized_result.model.program_instructions.alloc[adjustable.name].get(2020)))  # TODO - add time to alloc

    d = at.PlotData([unoptimized_result, optimized_result], outputs=["ch_all"], project=P)
    at.plot_series(d, axis="results")


# UNRESOLVABLE CONSTRAINTS
# If the user specifies bounds on individual spending that are inconsistent with the
# total spending constraint, an informative error should be raised. This test verifies
# that this is detected correctly


def test_unresolvable():

    P = at.demo(which=test, do_run=False)
    P.update_settings(sim_end=2030.0)

    alloc = sc.odict([("Risk avoidance", 0.0), ("Harm reduction 1", 0.0), ("Harm reduction 2", 0.0), ("Treatment 1", 50.0), ("Treatment 2", 50.0)])

    instructions = at.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending

    adjustments = []
    adjustments.append(at.SpendingAdjustment("Treatment 1", 2020, "abs", 10.0, 100.0))
    adjustments.append(at.SpendingAdjustment("Treatment 2", 2020, "abs", 10.0, 100.0))
    measurables = at.MaximizeMeasurable("ch_all", [2020, np.inf])
    constraints = at.TotalSpendConstraint(t=2020, total_spend=201)  # Cap total spending in all years
    optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables, constraints=constraints)  # Evaluate from 2020 to end of simulation

    try:
        (unoptimized_result, optimized_result) = run_optimization(P, optimization, instructions)
    except at.UnresolvableConstraint as e:
        print(e)
        print("Correctly raised UnresolvableConstraint error")

    constraints.total_spend = sc.promotetoarray(5)
    try:
        (unoptimized_result, optimized_result) = run_optimization(P, optimization, instructions)
    except at.UnresolvableConstraint as e:
        print(e)
        print("Correctly raised UnresolvableConstraint error")


# STANDARD OUTCOME OPTIMIZATION, MINIMIZE DEATHS
# In this example, Treatment 2 is more effective than Treatment 1. The initial allocation has the budget
# mostly allocated to Treatment 1, and the result of optimization should be that the budget gets
# reallocated to Treatment 2


def test_standard_mindeaths():

    P = at.demo(which=test, do_run=False)
    P.update_settings(sim_end=2030.0)

    alloc = sc.odict([("Risk avoidance", 0.0), ("Harm reduction 1", 0.0), ("Harm reduction 2", 0.0), ("Treatment 1", 50.0), ("Treatment 2", 1.0)])

    instructions = at.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending
    adjustments = []
    adjustments.append(at.SpendingAdjustment("Treatment 1", 2020, "abs", 0.0, 100.0))
    adjustments.append(at.SpendingAdjustment("Treatment 2", 2020, "abs", 0.0, 100.0))
    measurables = at.MinimizeMeasurable(":dead", 2030)
    constraints = at.TotalSpendConstraint()  # Cap total spending in all years
    optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables, constraints=constraints)  # Evaluate from 2020 to end of simulation

    (unoptimized_result, optimized_result) = run_optimization(P, optimization, instructions)

    for adjustable in adjustments:
        print("%s - before=%.2f, after=%.2f" % (adjustable.name, unoptimized_result.model.program_instructions.alloc[adjustable.name].get(2020), optimized_result.model.program_instructions.alloc[adjustable.name].get(2020)))  # TODO - add time to alloc

    d = at.PlotData([unoptimized_result, optimized_result], outputs=[":dead"], project=P)
    at.plot_series(d, axis="results")


# DELAYED OUTCOME OPTIMIZATION
# In this example, Treatment 2 is more effective than Treatment 1. However, we are given the budget in
# 2020 and are only allowed to change it from 2025.


def test_delayed():

    P = at.demo(which=test, do_run=False)
    P.update_settings(sim_end=2030.0)

    alloc = sc.odict([("Risk avoidance", 0.0), ("Harm reduction 1", 0.0), ("Harm reduction 2", 0.0), ("Treatment 1", at.TimeSeries([2020, 2024], [50, 50])), ("Treatment 2", at.TimeSeries([2020, 2024], [1, 1]))])

    instructions = at.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending
    adjustments = []
    adjustments.append(at.SpendingAdjustment("Treatment 1", 2025, "abs", 0.0, 100.0))
    adjustments.append(at.SpendingAdjustment("Treatment 2", 2025, "abs", 0.0, 100.0))
    measurables = at.MaximizeMeasurable("ch_all", [2020, np.inf])
    constraints = at.TotalSpendConstraint()  # Cap total spending in all years
    optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables, constraints=constraints)  # Evaluate from 2020 to end of simulation

    (unoptimized_result, optimized_result) = run_optimization(P, optimization, instructions)

    t = optimized_result.model.t
    unoptimized_spending = unoptimized_result.model.progset.get_alloc(t, unoptimized_result.model.program_instructions)
    optimized_spending = optimized_result.model.progset.get_alloc(t, optimized_result.model.program_instructions)

    plt.figure()
    plt.plot(t, unoptimized_spending["Treatment 1"], label="Unoptimized Treatment 1")
    plt.plot(t, optimized_spending["Treatment 1"], label="Optimized Treatment 1")
    plt.plot(t, unoptimized_spending["Treatment 2"], label="Unoptimized Treatment 2")
    plt.plot(t, optimized_spending["Treatment 2"], label="Optimized Treatment 2")
    plt.legend()
    plt.title("Fixed spending in 2020, optimized from 2025 onwards")


# MULTI YEAR FIXED
# In this example (requested by applications) the total spend constraint
# is explicitly specified in several years, yielding a time-dependent scale-up
# Note that the total spend constraint necessarily only affects programs which are
# optimizable (i.e. if a program is excluded from the optimization, then it won't be
# touched by the total spending constraint). This also applies in the case where the
# different programs are optimizable in different years. The flip side of this is that
# typically the Optimization should therefore contain an adjustment in every year that
# the total spend is specified - which can be done simply by passing the array of times
# to the SpendingAdjustment constructor, as demonstrated here
#
# In this example, the optimal solution is to spend as much as possible on Program 2, subject
# to constraints. Thus, in 2020 the optimal budget is $5 on program 1 and $95 on program 2,
# and in 2040 the optimal budget is $25 on program 1 and $125 on program 2


def test_multiyear_fixed():

    P = at.demo(which=test, do_run=False)
    P.update_settings(sim_end=2030.0)

    alloc = sc.odict([("Risk avoidance", 0.0), ("Harm reduction 1", 0.0), ("Harm reduction 2", 0.0), ("Treatment 1", at.TimeSeries([2020, 2024], [50, 50])), ("Treatment 2", at.TimeSeries([2020, 2024], [1, 1]))])

    instructions = at.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending
    adjustments = []
    adjustments.append(at.SpendingAdjustment("Treatment 1", [2020, 2024], "abs", 5.0, 100.0, 5.0))
    adjustments.append(at.SpendingAdjustment("Treatment 2", [2020, 2024], "abs", 5.0, 125.0, 5.0))
    measurables = at.MaximizeMeasurable("ch_all", [2020, np.inf])
    constraints = at.TotalSpendConstraint(t=[2020, 2024], total_spend=[100, 150])  # Cap total spending in all years
    # Use PSO because this example seems a bit susceptible to local minima with ASD
    optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables, constraints=constraints, method="pso")  # Evaluate from 2020 to end of simulation

    (unoptimized_result, optimized_result) = run_optimization(P, optimization, instructions)

    t = optimized_result.model.t
    unoptimized_spending = unoptimized_result.model.progset.get_alloc(t, unoptimized_result.model.program_instructions)
    optimized_spending = optimized_result.model.progset.get_alloc(t, optimized_result.model.program_instructions)
    print(unoptimized_spending)
    print(optimized_spending)

    d = at.PlotData.programs(optimized_result)
    at.plot_series(d, plot_type="stacked")
    plt.title("Scale up spending to 100 in 2020 and 150 in 2040")


# MULTI YEAR RELATIVE
# This is an interesting example. The total budget in 2020 is fixed at $50
# Then, we have adjustments in 2022 and 2024 with total spending constraints of
# $75 and $150 respectively. The spending is fixed until 2022, so treatment 1
# remains at $49 until then. In 2022, treatment 1 should be defunded to its minimum, so
# we have $5 on treatment 1, and $70 on treatment 2. Then, in 2024, we should max out
# treatment 2 at $100, and allocate $50 to treatment 1 again.
# Note how the spending is linearly ramped in between the times when spending is specified,
# whether explicitly in the allocation or through the spending adjustment


def test_multiyear_relative():

    P = at.demo(which=test, do_run=False)
    P.update_settings(sim_end=2030.0)

    alloc = sc.odict([("Risk avoidance", 0.0), ("Harm reduction 1", 0.0), ("Harm reduction 2", 0.0), ("Treatment 1", at.TimeSeries([2020], [49])), ("Treatment 2", at.TimeSeries([2020], [1]))])

    instructions = at.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending
    adjustments = []
    adjustments.append(at.SpendingAdjustment("Treatment 1", [2022, 2024], "abs", 1.0, 100))
    adjustments.append(at.SpendingAdjustment("Treatment 2", [2022, 2024], "abs", 1.0, 100))
    measurables = at.MaximizeMeasurable("ch_all", [2020, np.inf])
    constraints = at.TotalSpendConstraint(t=[2022, 2024], budget_factor=[1.5, 3.0])  # Cap total spending in all years
    # Use PSO because this example seems a bit susceptible to local minima with ASD
    optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables, constraints=constraints, method="pso")  # Evaluate from 2020 to end of simulation

    (unoptimized_result, optimized_result) = run_optimization(P, optimization, instructions)

    t = optimized_result.model.t
    unoptimized_spending = unoptimized_result.model.progset.get_alloc(t, unoptimized_result.model.program_instructions)
    optimized_spending = optimized_result.model.progset.get_alloc(t, optimized_result.model.program_instructions)
    print(unoptimized_spending)
    print(optimized_spending)

    d = at.PlotData.programs(optimized_result)
    at.plot_series(d, plot_type="stacked")
    plt.title("Scale up spending to 1x in 2020 and 1.5x in 2040")


# GRADUAL OUTCOME OPTIMIZATION
# This is similar to ramped constraints, except the constraint is time-based rather than
# rate-of-change based. That is, rather than limiting the amount by which the spending can
# change, it is specified that the total change takes place over a certain number of years.
# In this case, we have specified spending in 2020 and want to meet spending targets in 2025
# with the caveat that the rollout of the change will take 3 years. Therefore, we fix the spending
# in 2022 and apply the adjustment in 2025, resulting in a smooth change in spending from 2022-2025


def test_gradual():

    P = at.demo(which=test, do_run=False)
    P.update_settings(sim_end=2030.0)

    alloc = sc.odict([("Risk avoidance", 0.0), ("Harm reduction 1", 0.0), ("Harm reduction 2", 0.0), ("Treatment 1", at.TimeSeries([2020, 2022], [50, 50])), ("Treatment 2", at.TimeSeries([2020, 2022], [1, 1]))])

    instructions = at.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending
    adjustments = []
    adjustments.append(at.SpendingAdjustment("Treatment 1", 2025, "abs", 0.0, 100.0))
    adjustments.append(at.SpendingAdjustment("Treatment 2", 2025, "abs", 0.0, 100.0))
    measurables = at.MaximizeMeasurable("ch_all", [2020, np.inf])
    constraints = at.TotalSpendConstraint()  # Cap total spending in all years
    optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables, constraints=constraints)  # Evaluate from 2020 to end of simulation

    (unoptimized_result, optimized_result) = run_optimization(P, optimization, instructions)

    t = optimized_result.model.t
    unoptimized_spending = unoptimized_result.model.progset.get_alloc(t, unoptimized_result.model.program_instructions)
    optimized_spending = optimized_result.model.progset.get_alloc(t, optimized_result.model.program_instructions)

    plt.figure()
    plt.plot(t, unoptimized_spending["Treatment 1"], label="Unoptimized Treatment 1")
    plt.plot(t, optimized_spending["Treatment 1"], label="Optimized Treatment 1")
    plt.plot(t, unoptimized_spending["Treatment 2"], label="Unoptimized Treatment 2")
    plt.plot(t, optimized_spending["Treatment 2"], label="Optimized Treatment 2")
    plt.legend()
    plt.title("Fixed spending in 2020, optimized in 2025 with 3y onset")


# MIXED TIMING OUTCOME OPTIMIZATION
# Treatment 2 can have its funding adjusted in both 2023 and 2027. Treatment 1 can have its funding
# only adjusted in 2023. The default allocation sees the funding smoothly change to equal funding on both
# programs in 2022. The total spend constraint is only applied in 2023, at which time both Treatment 1 and
# Treatment 2 are adjustable and spending is capped at 25+25=50 units. In 2027, Treatment 2 is the only
# adjustable program and there is no total spending constraint. Thus spending on this program should hit
# the upper bound. Thus the optimal spending pattern will be spending $50 on Treatment 2 in 2023, and $100
# on Treatment 2 in 2025, with $0 spend on Treatment 1 from 2023 onwards


def test_mixed_timing():

    P = at.demo(which=test, do_run=False)
    P.update_settings(sim_end=2030.0)

    alloc = sc.odict([("Risk avoidance", 0.0), ("Harm reduction 1", 0.0), ("Harm reduction 2", 0.0), ("Treatment 1", at.TimeSeries([2020, 2022], [50, 25])), ("Treatment 2", at.TimeSeries([2020, 2022], [1, 25]))])

    instructions = at.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending
    adjustments = []
    adjustments.append(at.SpendingAdjustment("Treatment 1", 2023, "abs", 0.0, 100.0))
    adjustments.append(at.SpendingAdjustment("Treatment 2", [2023, 2027], "abs", 0.0, 100.0))
    measurables = at.MaximizeMeasurable("ch_all", [2020, np.inf])
    constraints = at.TotalSpendConstraint(t=2023)  # Cap total spending in 2023 only
    optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables, constraints=constraints)  # Evaluate from 2020 to end of simulation

    (unoptimized_result, optimized_result) = run_optimization(P, optimization, instructions)

    t = optimized_result.model.t
    unoptimized_spending = unoptimized_result.model.progset.get_alloc(t, unoptimized_result.model.program_instructions)
    optimized_spending = optimized_result.model.progset.get_alloc(t, optimized_result.model.program_instructions)

    plt.figure()
    plt.plot(t, unoptimized_spending["Treatment 1"], label="Unoptimized Treatment 1")
    plt.plot(t, optimized_spending["Treatment 1"], label="Optimized Treatment 1")
    plt.plot(t, unoptimized_spending["Treatment 2"], label="Unoptimized Treatment 2")
    plt.plot(t, optimized_spending["Treatment 2"], label="Optimized Treatment 2")
    plt.legend()
    plt.title("Multi-time optimization in 2023 and 2025 (constrained in 2023)")


def test_parametric_paired():

    P = at.demo(which=test, do_run=False)
    P.update_settings(sim_end=2030.0)

    alloc = sc.odict([("Risk avoidance", 0.0), ("Harm reduction 1", 0.0), ("Harm reduction 2", 0.0), ("Treatment 1", 50.0), ("Treatment 2", 1.0)])

    instructions = at.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending
    adjustments = []
    adjustments.append(at.PairedLinearSpendingAdjustment(["Treatment 1", "Treatment 2"], [2020, 2025]))
    measurables = at.MaximizeMeasurable("ch_all", [2020, np.inf])
    constraints = None  # Total spending constraint is automatically satisfied by the paired parametric adjustment
    optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables, constraints=constraints)  # Evaluate from 2020 to end of simulation

    (unoptimized_result, optimized_result) = run_optimization(P, optimization, instructions)

    t = optimized_result.model.t
    unoptimized_spending = unoptimized_result.model.progset.get_alloc(t, unoptimized_result.model.program_instructions)
    optimized_spending = optimized_result.model.progset.get_alloc(t, optimized_result.model.program_instructions)

    plt.figure()
    plt.plot(t, unoptimized_spending["Treatment 1"], label="Unoptimized Treatment 1")
    plt.plot(t, optimized_spending["Treatment 1"], label="Optimized Treatment 1")
    plt.plot(t, unoptimized_spending["Treatment 2"], label="Unoptimized Treatment 2")
    plt.plot(t, optimized_spending["Treatment 2"], label="Optimized Treatment 2")
    plt.legend()
    plt.title("Paired linear funding transfer from 2020-2025")


# MONEY MINIMIZATION
# In this example, Treatment 2 is more effective than Treatment 1. If we spend
# $40 on Treatment 2, then there are 729.90 people alive in 2030. Since Treatment 2 is more
# effective, the cheapest way to achieve at least 729.90 people alive in 2030 is to
# spend only ~$40 on Treatment 2. So to do this optimization, we start by spending $100 on both
# Treatment 1 and Treatment 2 and demonstrate that money optimization where we minimize total
# spend subject to the constraint of the total people alive being at least 729.90 in 2030


def test_minmoney():

    P = at.demo(which=test, do_run=False)
    P.update_settings(sim_end=2030.0)

    alloc = sc.odict([("Risk avoidance", 0.0), ("Harm reduction 1", 0.0), ("Harm reduction 2", 0.0), ("Treatment 1", 100.0), ("Treatment 2", 100.0)])

    instructions = at.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending

    adjustments = []
    adjustments.append(at.SpendingAdjustment("Treatment 1", 2020, "abs", 0.0, 100.0))  # We can adjust Treatment 1
    adjustments.append(at.SpendingAdjustment("Treatment 2", 2020, "abs", 0.0, 100.0))  # We can adjust Treatment 2

    measurables = []
    measurables.append(at.AtLeastMeasurable("ch_all", 2030, 729.90))  # Need at least 729.90 people in 2030
    measurables.append(at.MinimizeMeasurable("Treatment 1", 2020))  # Minimize 2020 spending on Treatment 1
    measurables.append(at.MinimizeMeasurable("Treatment 2", 2020))  # Minimize 2020 spending on Treatment 2

    constraints = None  # No extra constraints aside from individual bounds

    optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables, constraints=constraints, method="pso")  # Evaluate from 2020 to end of simulation

    (unoptimized_result, optimized_result) = run_optimization(P, optimization, instructions)

    for adjustable in adjustments:
        print("%s - before=%.2f, after=%.2f" % (adjustable.name, unoptimized_result.model.program_instructions.alloc[adjustable.name].get(2020), optimized_result.model.program_instructions.alloc[adjustable.name].get(2020)))  # TODO - add time to alloc

    d = at.PlotData([unoptimized_result, optimized_result], outputs=["ch_all"], project=P)
    at.plot_series(d, axis="results")


# MONEY MINIMIZATION 2
# Essentially the same example as ``test_minmoney``. However, in this example, we want to both minimize spending
# and increase the number of people alive by some percentage. If we spend about $1000 on Treatment 2, then we can
# achieve 731.5 people alive in 2030, compared to 729.95 if we spend $50 on each program. Thus, we set our initial
# budget as $50 on each program, and explicitly set the initial spend to $2000 on each program, and request a
# 0.2% increase in ``ch_all``. The optimization should spend close to $0 on Treatment 1 and about $1000 on Treatment 2


def test_minmoney_relative():

    P = at.demo(which=test, do_run=False)
    P.update_settings(sim_end=2030.0)

    alloc = sc.odict([("Risk avoidance", 0.0), ("Harm reduction 1", 0.0), ("Harm reduction 2", 0.0), ("Treatment 1", 50.0), ("Treatment 2", 50.0)])

    instructions = at.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending. Note that this does NOT have the scaled up initial spends for money minimization

    adjustments = []
    adjustments.append(at.SpendingAdjustment("Treatment 1", 2020, "abs", 0.0, 2000.0, initial=2000.0))  # We can adjust Treatment 1
    adjustments.append(at.SpendingAdjustment("Treatment 2", 2020, "abs", 0.0, 2000.0, initial=2000.0))  # We can adjust Treatment 2

    measurables = []
    measurables.append(at.IncreaseByMeasurable("ch_all", 2030, 0.002))  # Get a 0.02% increase in ch_all in 2030
    measurables.append(at.MinimizeMeasurable("Treatment 1", 2020))  # Minimize 2020 spending on Treatment 1
    measurables.append(at.MinimizeMeasurable("Treatment 2", 2020))  # Minimize 2020 spending on Treatment 2

    constraints = None  # No extra constraints aside from individual bounds

    optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables, constraints=constraints, method="pso")  # Evaluate from 2020 to end of simulation

    (unoptimized_result, optimized_result) = run_optimization(P, optimization, instructions)

    for adjustable in adjustments:
        print("%s - before=%.2f, after=%.2f" % (adjustable.name, unoptimized_result.model.program_instructions.alloc[adjustable.name].get(2020), optimized_result.model.program_instructions.alloc[adjustable.name].get(2020)))  # TODO - add time to alloc

    d = at.PlotData([unoptimized_result, optimized_result], outputs=["ch_all"], project=P)
    at.plot_series(d, axis="results")
    print("Change: %.4f" % (d.series[1].vals[-1] / d.series[0].vals[-1]))


# MONEY MINIMIZATION 3
# Essentially the same example as ``test_minmoney_relative`` but now we want an absolute increase
# of 1 person alive


def test_minmoney_absolute():

    P = at.demo(which=test, do_run=False)
    P.update_settings(sim_end=2030.0)

    alloc = sc.odict([("Risk avoidance", 0.0), ("Harm reduction 1", 0.0), ("Harm reduction 2", 0.0), ("Treatment 1", 50.0), ("Treatment 2", 50.0)])

    instructions = at.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending. Note that this does NOT have the scaled up initial spends for money minimization

    adjustments = []
    adjustments.append(at.SpendingAdjustment("Treatment 1", 2020, "abs", 0.0, 2000.0, initial=2000.0))  # We can adjust Treatment 1
    adjustments.append(at.SpendingAdjustment("Treatment 2", 2020, "abs", 0.0, 2000.0, initial=2000.0))  # We can adjust Treatment 2

    measurables = []
    measurables.append(at.IncreaseByMeasurable("ch_all", 2030, 1, target_type="abs"))  # Get a 0.02% increase in ch_all in 2030
    measurables.append(at.MinimizeMeasurable("Treatment 1", 2020))  # Minimize 2020 spending on Treatment 1
    measurables.append(at.MinimizeMeasurable("Treatment 2", 2020))  # Minimize 2020 spending on Treatment 2

    constraints = None  # No extra constraints aside from individual bounds

    optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables, constraints=constraints, method="pso")  # Evaluate from 2020 to end of simulation

    (unoptimized_result, optimized_result) = run_optimization(P, optimization, instructions)

    for adjustable in adjustments:
        print("%s - before=%.2f, after=%.2f" % (adjustable.name, unoptimized_result.model.program_instructions.alloc[adjustable.name].get(2020), optimized_result.model.program_instructions.alloc[adjustable.name].get(2020)))  # TODO - add time to alloc

    d = at.PlotData([unoptimized_result, optimized_result], outputs=["ch_all"], project=P)
    at.plot_series(d, axis="results")
    print("Before: %.2f, After: %.2f" % (d.series[0].vals[-1], d.series[1].vals[-1]))


def test_cascade_final_stage():

    P = at.demo(which=test, do_run=False)
    P.update_settings(sim_end=2030.0)

    # This is the same as the 'standard' example, just setting up the fact that we can adjust spending on Treatment 1 and Treatment 2
    # and want a total spending constraint
    alloc = sc.odict([("Risk avoidance", 0.0), ("Harm reduction 1", 0.0), ("Harm reduction 2", 0.0), ("Treatment 1", 50.0), ("Treatment 2", 1.0)])

    instructions = at.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending
    adjustments = []
    adjustments.append(at.SpendingAdjustment("Treatment 1", 2020, "abs", 0.0, 100.0))
    adjustments.append(at.SpendingAdjustment("Treatment 2", 2020, "abs", 0.0, 100.0))
    constraints = at.TotalSpendConstraint()  # Cap total spending in all years

    # CASCADE MEASURABLE
    # This measurable will maximize the number of people in the final cascade stage, whatever it is
    measurables = at.MaximizeCascadeStage("main", [2030], pop_names="all")  # NB. make sure the objective year is later than the program start year, otherwise no time for any changes

    # This is the same as the 'standard' example, just running the optimization and comparing the results
    optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables, constraints=constraints)
    unoptimized_result = P.run_sim(parset=P.parsets["default"], progset=P.progsets["default"], progset_instructions=instructions, result_name="unoptimized")
    optimized_instructions = at.optimize(P, optimization, parset=P.parsets["default"], progset=P.progsets["default"], instructions=instructions)
    optimized_result = P.run_sim(parset=P.parsets["default"], progset=P.progsets["default"], progset_instructions=optimized_instructions, result_name="optimized")

    for adjustable in adjustments:
        print("%s - before=%.2f, after=%.2f" % (adjustable.name, unoptimized_result.model.program_instructions.alloc[adjustable.name].get(2020), optimized_result.model.program_instructions.alloc[adjustable.name].get(2020)))  # TODO - add time to alloc

    at.plot_multi_cascade([unoptimized_result, optimized_result], "main", pops="all", year=2020)


def test_cascade_multi_stage():

    P = at.demo(which=test, do_run=False)
    P.update_settings(sim_end=2030.0)

    alloc = sc.odict([("Risk avoidance", 0.0), ("Harm reduction 1", 0.0), ("Harm reduction 2", 0.0), ("Treatment 1", 50.0), ("Treatment 2", 1.0)])

    instructions = at.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending
    adjustments = []
    adjustments.append(at.SpendingAdjustment("Treatment 1", 2020, "abs", 0.0, 100.0))
    adjustments.append(at.SpendingAdjustment("Treatment 2", 2020, "abs", 0.0, 100.0))

    # CASCADE MEASURABLE
    measurables = at.MaximizeCascadeStage(None, [2017, 2018], pop_names="all", cascade_stage=["Number ever infected", "Recovered"])  # NB. make sure the objective year is later than the program start year, otherwise no time for any changes
    # This is the same as the 'standard' example, just running the optimization and comparing the results
    optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables)
    P.run_sim(parset=P.parsets["default"], progset=P.progsets["default"], progset_instructions=instructions, result_name="baseline")
    optimized_instructions = at.optimize(P, optimization, parset=P.parsets["default"], progset=P.progsets["default"], instructions=instructions)
    P.run_sim(parset=P.parsets["default"], progset=P.progsets["default"], progset_instructions=optimized_instructions, result_name="optimized")


def test_cascade_conversions():

    P = at.demo(which=test, do_run=False)
    P.update_settings(sim_end=2030.0)

    # This is the same as the 'standard' example, just setting up the fact that we can adjust spending on Treatment 1 and Treatment 2
    # and want a total spending constraint

    alloc = sc.odict([("Risk avoidance", 0.0), ("Harm reduction 1", 0.0), ("Harm reduction 2", 0.0), ("Treatment 1", 50.0), ("Treatment 2", 1.0)])

    instructions = at.ProgramInstructions(alloc=alloc, start_year=2020)  # Instructions for default spending
    adjustments = []
    adjustments.append(at.SpendingAdjustment("Treatment 1", 2020, "abs", 0.0, 100.0))
    adjustments.append(at.SpendingAdjustment("Treatment 2", 2020, "abs", 0.0, 100.0))
    constraints = at.TotalSpendConstraint()  # Cap total spending in all years

    # CASCADE MEASURABLE
    # This measurable will be
    measurables = at.MaximizeCascadeConversionRate("main", [2030], pop_names="all")  # NB. make sure the objective year is later than the program start year, otherwise no time for any changes

    # This is the same as the 'standard' example, just running the optimization and comparing the results
    optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables, constraints=constraints)
    unoptimized_result = P.run_sim(parset=P.parsets["default"], progset=P.progsets["default"], progset_instructions=instructions, result_name="unoptimized")
    optimized_instructions = at.optimize(P, optimization, parset=P.parsets["default"], progset=P.progsets["default"], instructions=instructions)
    optimized_result = P.run_sim(parset=P.parsets["default"], progset=P.progsets["default"], progset_instructions=optimized_instructions, result_name="optimized")

    for adjustable in adjustments:
        print("%s - before=%.2f, after=%.2f" % (adjustable.name, unoptimized_result.model.program_instructions.alloc[adjustable.name].get(2020), optimized_result.model.program_instructions.alloc[adjustable.name].get(2020)))  # TODO - add time to alloc

    at.plot_cascade(unoptimized_result, "main", pops="all", year=2030)
    plt.title("Unoptimized")
    at.plot_cascade(optimized_result, "main", pops="all", year=2030)
    plt.title("Optimized")


if __name__ == "__main__":
    test_standard()
    test_unresolvable()
    test_standard_mindeaths()
    test_delayed()
    test_multiyear_fixed()
    test_multiyear_relative()
    test_gradual()
    test_mixed_timing()
    test_parametric_paired()
    test_minmoney()
    test_minmoney_relative()
    test_minmoney_absolute()
    test_cascade_final_stage()
    test_cascade_multi_stage()
    test_cascade_conversions()
