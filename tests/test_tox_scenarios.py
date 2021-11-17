"""
Check whether automated model documentation template generation works
"""

import atomica as at
import numpy as np


def test_program_scenarios():

    P = at.demo("tb", do_run=False)

    # Get the default values for coverage etc.
    instructions = at.ProgramInstructions(2018)
    res_baseline = P.run_sim(result_name="Baseline", parset="default", progset="default", progset_instructions=instructions)

    alloc = res_baseline.get_alloc(2018)
    capacity = res_baseline.get_coverage("capacity", 2018)
    coverage = res_baseline.get_coverage("fraction", 2018)

    # Run a budget scenario manually
    doubled_budget = {x: v * 2 for x, v in alloc.items()}
    instructions = at.ProgramInstructions(2018, alloc=doubled_budget)
    res_doubled = P.run_sim(result_name="Doubled budget", parset="default", progset="default", progset_instructions=instructions)

    # Compare spending in 2018
    d = at.PlotData.programs([res_baseline, res_doubled], quantity="spending")
    d.interpolate(2018)
    at.plot_bars(d, stack_outputs="all")

    # Run a capacity scenario manually
    doubled_capacity = {x: v * 2 for x, v in capacity.items()}
    instructions = at.ProgramInstructions(2018, capacity=doubled_capacity)
    res_capacity = P.run_sim(result_name="Doubled capacity", parset="default", progset="default", progset_instructions=instructions)

    # # Compare capacity in 2018
    d = at.PlotData.programs([res_baseline, res_capacity], quantity="coverage_capacity")
    d.interpolate(2018)
    at.plot_bars(d, stack_outputs="all")

    # Run a coverage scenario manually
    doubled_coverage = {x: v * 2 for x, v in coverage.items()}
    instructions = at.ProgramInstructions(2018, coverage=doubled_coverage)
    res_coverage = P.run_sim(result_name="Doubled coverage", parset="default", progset="default", progset_instructions=instructions)

    # Compare coverage in 2018 - notice how the output coverage is capped to 1.0
    # even though the instructions contain fractional coverage values >1.0
    d = at.PlotData.programs([res_baseline, res_coverage], quantity="coverage_fraction")
    d.interpolate(2018)
    at.plot_bars(d, stack_outputs="all")

    # Compare program outcomes (incidence from 2018-2023)
    # Note that the doubled capacity scenario here is basically the same as
    # the doubled budget scenario because there were no capacity constraints
    # (the main use case for running a capacity scenario would be to
    # investigate circumventing capacity constraints).
    # On the other hand, the coverage scenario has fixed coverage from 2018-2023 whereas
    # the other scenarios have variable coverage, which is why the coverage scenario has
    # a different outcome
    d = at.PlotData([res_baseline, res_doubled, res_capacity, res_coverage], outputs=":acj", pops="total", t_bins=[2018, 2023])
    # Show change in incidence relative to baseline to improve clarity in this plot
    baseline = d.series[0].vals[0]
    for s in d.series:
        s.vals -= baseline
    at.plot_bars(d)

    # Run a budget scenario via the actual scenario infrastructure
    scen = at.BudgetScenario(name="Doubled budget scenario", alloc=doubled_budget, start_year=2018)
    res_doubled_scen = scen.run(P, parset="default", progset="default")

    # Run a coverage scenario via the scenario infrastructure
    scen = at.CoverageScenario(name="Double coverage scenario", coverage=doubled_coverage, start_year=2018)
    res_coverage_scen = scen.run(P, parset="default", progset="default")

    # Check that the infrastructure gives the same result as direct instructions and
    # also that the budget and coverage scenarios give different results
    d = at.PlotData([res_doubled, res_doubled_scen, res_coverage, res_coverage_scen], outputs=":acj", pops="total", t_bins=[2018, 2023])
    at.plot_bars(d)


def test_timevarying_progscen():
    # This test demonstrates doing time-varying overwrites
    # The example below shows how you can pass in a TimeSeries
    # instead of a scalar in the dict of overwrites. Although shown
    # for coverage below, this same approach works for alloc/budget
    # and capacity scenarios as well

    P = at.demo("sir", do_run=False)
    instructions = at.ProgramInstructions(2018)
    res_baseline = P.run_sim(result_name="Baseline", parset="default", progset="default", progset_instructions=instructions)

    coverage = {
        "Risk avoidance": 0.5,
        "Harm reduction 1": 0.25,
        "Harm reduction 2": at.TimeSeries([2018, 2020], [0.7, 0.2]),
    }
    scen = at.CombinedScenario("Reduced coverage", parsetname="default", progsetname="default", instructions=at.ProgramInstructions(coverage=coverage, start_year=2018))
    scen_result = scen.run(project=P)
    d = at.PlotData.programs([res_baseline, scen_result], quantity="coverage_fraction")
    at.plot_series(d)


def test_combined_scenario():

    P = at.demo("tb", do_run=False)

    res_baseline = P.run_sim(P.parsets[0], P.progsets[0], at.ProgramInstructions(2018))

    # Make a parameter overwrite]
    scenario_values = dict()
    scenario_values["b_rate"] = dict()
    scenario_values["b_rate"]["0-4"] = dict()
    scenario_values["b_rate"]["0-4"]["t"] = [2016.0, 2020.0, 2050]
    scenario_values["b_rate"]["0-4"]["y"] = [270000, 300000, 300000]

    # Make instructions for the program scenario
    alloc = {"BCG": at.TimeSeries([2018, 2020], [345000, 500000])}
    coverage = {"PCF": at.TimeSeries([2018, 2020], [0.00274411, 0.004])}
    instructions = at.ProgramInstructions(2018, alloc=alloc, coverage=coverage)

    # Instantiate the combined scenario
    scen = at.CombinedScenario(name="Combined test", parsetname="default", progsetname="default", scenario_values=scenario_values, instructions=instructions)

    # Run the scenario via `Project.run_scenarios()` and check the output
    for s in P.scens.values():
        s.active = False
    P.scens.append(scen)
    scen_result = P.run_scenarios(store_results=False)[0]

    # Check parameter overwrite
    d = at.PlotData([res_baseline, scen_result], outputs="b_rate", pops="0-4")
    at.plot_series(d, axis="results")

    # Check budget overwrite
    d = at.PlotData.programs([res_baseline, scen_result], quantity="spending", outputs="BCG")
    at.plot_series(d, axis="results")

    # Check coverage overwrite
    d = at.PlotData.programs([res_baseline, scen_result], quantity="coverage_fraction", outputs="PCF")
    at.plot_series(d, axis="results")

    # Check the combined scenario would work for just parameters or just programs
    pars_only = at.CombinedScenario(name="Parameters only", scenario_values=scenario_values)
    pars_only.run(project=P, parset=P.parsets["default"])

    progs_only = at.CombinedScenario(name="Programs only", instructions=instructions)
    progs_only.run(project=P, parset=P.parsets["default"], progset=P.progsets["default"])


def test_parameter_scenarios():

    proj = at.demo("sir", do_run=False)
    proj.settings.update_time_vector(start=2000, end=2023)

    # Check that it runs with an empty scvalues
    scvalues = dict()
    scen = proj.make_scenario(which="parameter", scenario_values=scvalues)
    scen.run(proj, proj.parsets["default"])

    # Check that it runs with a single overwrite
    scen_par1 = "contacts"
    scen_pop = "adults"
    scvalues[scen_par1] = dict()
    scvalues[scen_par1][scen_pop] = dict()
    scvalues[scen_par1][scen_pop]["y"] = [80.0, 40]
    scvalues[scen_par1][scen_pop]["t"] = [2010.0, 2020.0]
    scen = proj.make_scenario(which="parameter", scenario_values=scvalues)
    scen_results = scen.run(proj, proj.parsets["default"])

    # Check that default is linear interpolation
    var = scen_results.get_variable(scen_par1, scen_pop)[0]
    assert np.allclose(var.vals[var.t == 2010][0], 80, equal_nan=True)  # Default tolerances are rtol=1e-05, atol=1e-08
    assert np.allclose(var.vals[var.t == 2015][0], 60, equal_nan=True)
    assert np.allclose(var.vals[var.t == 2020][0], 40, equal_nan=True)

    # Check stepped/previous method also works
    scen.interpolation = "previous"
    scen_results = scen.run(proj, proj.parsets["default"])
    var = scen_results.get_variable(scen_par1, scen_pop)[0]
    assert np.allclose(var.vals[var.t == 2018][0], 80, equal_nan=True)
    assert np.allclose(var.vals[var.t == 2019][0], 80, equal_nan=True)
    assert np.allclose(var.vals[var.t == 2020][0], 40, equal_nan=True)

    # Check that multiple overwrites work
    scen_par2 = "transpercontact"
    scen_pop = "adults"
    scvalues[scen_par2] = dict()
    scvalues[scen_par2][scen_pop] = dict()
    scvalues[scen_par2][scen_pop]["y"] = [0.008, 0.006]
    scvalues[scen_par2][scen_pop]["t"] = [2010.0, 2020.0]
    scen = proj.make_scenario(which="parameter", scenario_values=scvalues)
    scen_results = scen.run(proj, proj.parsets["default"])
    var1 = scen_results.get_variable(scen_par1, scen_pop)[0]
    var2 = scen_results.get_variable(scen_par2, scen_pop)[0]

    assert np.allclose(var1.vals[var1.t == 2010][0], 80, equal_nan=True)
    assert np.allclose(var1.vals[var1.t == 2015][0], 60, equal_nan=True)
    assert np.allclose(var1.vals[var1.t == 2020][0], 40, equal_nan=True)
    assert np.allclose(var2.vals[var2.t == 2010][0], 0.008, equal_nan=True)
    assert np.allclose(var2.vals[var2.t == 2015][0], 0.007, equal_nan=True)
    assert np.allclose(var2.vals[var2.t == 2020][0], 0.006, equal_nan=True)

    # Check that scenarios don't end
    scen_par1 = "contacts"
    scen_pop = "adults"
    scvalues[scen_par1] = dict()
    scvalues[scen_par1][scen_pop] = dict()
    scvalues[scen_par1][scen_pop]["y"] = [80.0, 40]
    scvalues[scen_par1][scen_pop]["t"] = [2010.0, 2020.0]
    scen = proj.make_scenario(which="parameter", scenario_values=scvalues)
    scen_results = scen.run(proj, proj.parsets["default"])
    var = scen_results.get_variable(scen_par1, scen_pop)[0]
    assert np.allclose(var.vals[var.t == 2020][0], 40, equal_nan=True)
    assert np.allclose(var.vals[var.t == 2021][0], 40, equal_nan=True)


def test_overwrite_function_scenario():
    proj = at.demo("sir", do_run=False)
    proj.settings.update_time_vector(start=2000, end=2023)
    baseline = proj.run_sim()

    baseline.get_variable("foi")[0].plot()

    # Check that it runs with a single overwrite
    scen_par1 = "foi"
    scen_pop = "adults"
    scvalues = dict()
    scvalues[scen_par1] = dict()
    scvalues[scen_par1][scen_pop] = dict()
    scvalues[scen_par1][scen_pop]["y"] = [0.1, 0.15]
    scvalues[scen_par1][scen_pop]["t"] = [2015.0, 2018.0]
    scen = proj.make_scenario(which="parameter", scenario_values=scvalues)
    scen_results = scen.run(proj, proj.parsets["default"])
    scen_results.get_variable("foi")[0].plot()

    var1 = baseline.get_variable(scen_par1, scen_pop)[0]
    var2 = scen_results.get_variable(scen_par1, scen_pop)[0]

    assert np.allclose(var1.vals[var1.t == 2010][0], var2.vals[var2.t == 2010][0], equal_nan=True)
    assert np.allclose(var2.vals[var2.t == 2015][0], 0.1, equal_nan=True)
    assert np.allclose(var2.vals[var2.t == 2018][0], 0.15, equal_nan=True)
    assert np.allclose(var2.vals[var2.t == 2019][0], 0.15, equal_nan=True)  # Check that the function didn't turn back on


def test_interaction_scenario():

    proj = at.demo("tb", do_run=False)
    parset = proj.parsets[0]
    res_baseline = proj.run_sim(result_name="Baseline", parset="default")

    # Run an interaction and transfer scenario - take out aging 0-4 to 5-14, and also
    # no FOI input for 15-64
    ps = at.ParameterScenario(name="examplePS")
    ps.add("age", ("0-4", "5-14"), [2020.0, np.inf], [0, 0])

    for from_pop in proj.data.pops:
        if from_pop in parset.interactions["w_ctc"] and "15-64" in parset.interactions["w_ctc"][from_pop].ts:
            ps.add("w_ctc", (from_pop, "15-64"), [2020.0, np.inf], [0, 0])

    res_scen = proj.run_sim(result_name="Scen", parset=ps.get_parset(parset, proj))

    d = at.PlotData([res_baseline, res_scen], "age_0-4_to_5-14", pops="0-4")
    at.plot_series(d, axis="results")

    d = at.PlotData([res_baseline, res_scen], "foi_in", pops="15-64")
    at.plot_series(d, axis="results")

    assert res_baseline.get_variable("foi_in", "15-64")[0].vals[-1] > 0
    assert res_scen.get_variable("foi_in", "15-64")[0].vals[-1] == 0  # Check scenario has 0 FOI in 15-64
    assert res_scen.get_variable("foi_in", "0-4")[0].vals[-1] > 0  # Check that a different population was not affected
    assert res_scen.get_variable("foi_in", "5-14")[0].vals[-1] > 0  # Check that a different population was not affected
    assert res_baseline.get_variable("age_0-4_to_5-14", "0-4")[0].vals[-1] > 0
    assert res_scen.get_variable("age_0-4_to_5-14", "0-4")[0].vals[-1] == 0  # Check scenario has 0 FOI in 15-64


if __name__ == "__main__":
    test_program_scenarios()
    test_timevarying_progscen()
    test_parameter_scenarios()
    test_combined_scenario()
    test_overwrite_function_scenario()
    test_interaction_scenario()
