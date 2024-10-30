import pytest
import atomica as at

testdir = at.rootdir / "tests"
tmpdir = testdir / "temp"

models = ["tb", "tb_simple", "hypertension_dyn"]


@pytest.mark.parametrize("model", [m for m in models])
def test_reconciliation(model):
    if model == "tb":
        par_name = "v_rate"
        pop_name = "0-4"
    elif model == "tb_simple":
        par_name = "vac_rate"
        pop_name = "adults"

    doplot = False

    P = at.demo(which=model, do_run=False)

    # Test single year reconciliation
    program_start_year = 2018.0
    original_progset = P.progsets[0]
    parset = P.parsets[0]
    reconciled_progset, progset_comparison, parameter_comparison = at.reconcile(project=P, parset=P.parsets[0], progset=original_progset, reconciliation_year=program_start_year, unit_cost_bounds=0.2)

    instructions = at.ProgramInstructions(start_year=program_start_year)
    parset_result = P.run_sim(parset=P.parsets[0], result_name="Parset")
    original_result = P.run_sim(parset=P.parsets[0], progset=original_progset, progset_instructions=instructions, result_name="Original")
    reconciled_result = P.run_sim(parset=P.parsets[0], progset=reconciled_progset, progset_instructions=instructions, result_name="Reconciled")

    print(progset_comparison)
    print(parameter_comparison)

    if doplot:
        for par, pop in [(par_name, pop_name)]:
            d = at.PlotData([parset_result, original_result, reconciled_result], outputs=par, pops=pop, project=P)
            at.plot_series(d, axis="results")

    reconciled_progset.save(tmpdir / "reconciled_progset.xlsx")

    # Test multi year reconciliation

    program_start_year = 2018.0
    eval_range = [2018.0, 2020.0]
    original_progset = P.progsets[0]
    parset = P.parsets[0]
    reconciled_progset, progset_comparison, parameter_comparison = at.reconcile(project=P, parset=parset, progset=original_progset, reconciliation_year=program_start_year, unit_cost_bounds=0.2, eval_range=eval_range)

    instructions = at.ProgramInstructions(start_year=program_start_year)
    parset_result = P.run_sim(parset=parset, result_name="Parset")
    original_result = P.run_sim(parset=parset, progset=original_progset, progset_instructions=instructions, result_name="Original")
    reconciled_result = P.run_sim(parset=parset, progset=reconciled_progset, progset_instructions=instructions, result_name="Reconciled")

    print(progset_comparison)
    print(parameter_comparison)

    if doplot:
        for par, pop in [(par_name, pop_name)]:
            d = at.PlotData([parset_result, original_result, reconciled_result], outputs=par, pops=pop, project=P)
            at.plot_series(d, axis="results")


if __name__ == "__main__":
    for model in models:
        test_reconciliation(model)
