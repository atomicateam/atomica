# Basic minimum working product test to verify all library models run
# Note that plotting is not tested here, because plotting (and other functions) already have
# separate automatic tests

import atomica as at
import os
import pytest
import numpy as np
import sciris as sc

testdir = at.parent_dir()
tmpdir = testdir / "temp"

# List available models based on which framework files exist
models = list()
for f in os.listdir(at.LIBRARY_PATH):
    if f.endswith("_framework.xlsx") and not f.startswith("~$"):
        models.append(f.replace("_framework.xlsx", ""))


def run_auto_calibration(proj):
    """Run an automatic calibration

    :param proj: A Project object
    :return:
    """

    proj.calibrate(max_time=10, new_name="auto")

    return


def run_parameter_scenario(proj):
    """Run an example parameter scenario for a project

    :param proj: A Project object
    :return: None

    """

    print("Testing parameter scenario")

    # Find a parameter from the databook
    for _, spec in proj.framework.pars.iterrows():
        if spec["databook page"]:
            break
    else:
        raise Exception("No Framework parameters appeared in the databook")

    par = proj.parsets[0].pars[spec.name]  # Get the parameter
    pop_name = par.pops[0]

    # Add overwrite with a slight increase in the 2020 value
    scvalues = dict()
    scvalues[spec.name] = dict()
    scvalues[spec.name][pop_name] = dict()
    scvalues[spec.name][pop_name]["t"] = [2015.0, 2020.0]
    scvalues[spec.name][pop_name]["y"] = par.interpolate(scvalues[spec.name][pop_name]["t"], pop_name) * np.array([1, 1.5]).ravel()
    scen = proj.make_scenario(which="parameter", name="Test", scenario_values=scvalues)
    res = scen.run(proj, proj.parsets["default"])
    if res.check_for_nans():
        raise Exception("NaNs detected")
    return


def run_reconciliation(proj):
    """Run an example reconciliation

    :param proj: A Project object
    :return: None

    """

    at.reconcile(project=proj, parset=proj.parsets[0], progset=proj.progsets[0], reconciliation_year=2018, unit_cost_bounds=0.05, baseline_bounds=0.05, capacity_bounds=0.05, outcome_bounds=0.05)

    return


def run_budget_scenario(proj):
    """Run a budget scenario

    :param proj: A Project object
    :return: None

    """

    print("Testing budget scenario")

    alloc = proj.progsets[0].get_alloc(2018)
    doubled_budget = {x: v * 2 for x, v in alloc.items()}
    instructions = at.ProgramInstructions(start_year=2018, alloc=doubled_budget)
    scen = at.CombinedScenario(name="Doubled budget", instructions=instructions)
    res = scen.run(proj, parset="default", progset="default")
    if res.check_for_nans():
        raise Exception("NaNs detected")

    return


def run_coverage_scenario(proj):
    """Run a coverage scenario

    :param proj: A Project object
    :return: None

    """

    print("Testing coverage scenario")

    half_coverage = {x: 0.5 for x in proj.progsets[0].programs.keys()}
    instructions = at.ProgramInstructions(start_year=2018, coverage=half_coverage)
    scen = at.CombinedScenario(name="Doubled budget", instructions=instructions)
    res = scen.run(proj, parset="default", progset="default")
    if res.check_for_nans():
        raise Exception("NaNs detected")

    return


def run_optimization(proj):
    """
    Run an optimization

    This demo optimization will adjust spending on all programs optimize all programs with the last default cascade stage)

    :param proj: A Project object
    :return: None

    """

    instructions = at.ProgramInstructions(alloc=proj.progsets[0], start_year=2020)  # Instructions for default spending
    adjustments = [at.SpendingAdjustment(x, 2020, "rel", 0.0, 2.0) for x in instructions.alloc.keys()]
    measurables = at.MaximizeCascadeStage(None, 2020)
    constraints = at.TotalSpendConstraint()  # Cap total spending in all years
    optimization = at.Optimization(name="default", adjustments=adjustments, measurables=measurables, constraints=constraints, maxtime=10)  # Evaluate from 2020 to end of simulation
    at.optimize(proj, optimization, parset=proj.parsets["default"], progset=proj.progsets["default"], instructions=instructions)

    return


def run_export(result, model):
    """
    Test exporting results

    :param result:
    :param model:
    :return:
    """

    at.export_results(result, tmpdir / f"{model}_single_export_test")  # Export single
    result.export_raw(tmpdir / f"{model}_raw_export_test")
    r2 = sc.dcp(result)
    r2.name = "Copied"
    at.export_results([result, r2], tmpdir / f"{model}_multiple_export_test")  # Export single


def run_regenerated_framework(proj):

    r1 = at.run_model(proj.settings, proj.framework, proj.parsets[0], proj.progsets[0], at.ProgramInstructions(start_year=2020))

    ss = proj.framework.to_spreadsheet()
    f2 = at.ProjectFramework(ss)

    r2 = at.run_model(proj.settings, f2, proj.parsets[0], proj.progsets[0], at.ProgramInstructions(start_year=2020))

    for p1, p2 in zip(r1.model.pops, r2.model.pops):
        for v1, v2 in zip(p1.pars + p1.comps + p1.characs + p1.links, p2.pars + p2.comps + p2.characs + p2.links):
            assert np.all(v1.vals == v2.vals)


# Testing optimizations and calibrations could be expensive
# Using the parametrize decorator means Pytest will treat
# each function call as a separate test, which can be run in parallel
# simply by adding `pytest -n 4` for instance. Or via tox
# `tox -- -o -n 4` (because the default config is to use n=2 for TravisCI)
@pytest.mark.parametrize("model", models)
def test_model(model):

    framework_file = at.LIBRARY_PATH / f"{model}_framework.xlsx"
    databook_file = at.LIBRARY_PATH / f"{model}_databook.xlsx"
    progbook_file = at.LIBRARY_PATH / f"{model}_progbook.xlsx"

    print("\n\nTESTING %s project" % (model))

    P = at.Project(framework=framework_file)

    if not os.path.isfile(databook_file):
        print("No databook found, test complete")
        return

    P.update_settings(sim_end=2025)  # Make sure we run until 2025

    # Test loading the databook and doing a basic run
    P.load_databook(databook_file, make_default_parset=True, do_run=True)

    # Test doing auto-calibration
    # run_auto_calibration(P)

    # Test a parameter scenario
    run_parameter_scenario(P)

    if not os.path.isfile(progbook_file):
        print("No progbook found, test complete")
        return

    # Test loading the progbook and doing a basic run
    P.load_progbook(progbook_file)
    res = P.run_sim(P.parsets[0], P.progsets[0], at.ProgramInstructions(start_year=2018))
    if res.check_for_nans():
        raise Exception("NaNs detected")

    # Test re-saving the framework
    run_regenerated_framework(P)

    # Test exporting the model with progset results
    run_export(res, model)

    # Test a reconciliation
    run_reconciliation(P)

    # Test a BudgetScenario
    run_budget_scenario(P)

    # Test a CoverageScenario
    run_coverage_scenario(P)

    # Test an optimization
    run_optimization(P)

    print("Test complete")


if __name__ == "__main__":

    np.seterr(all="raise")
    # models = ['tb']
    for m in models:
        test_model(m)
