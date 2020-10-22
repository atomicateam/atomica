import numpy as np
import atomica as at
import os
import pytest

testdir = at.parent_dir()  # Must be relative to current file to work with tox


def test_no_compartments():
    # Test a framework with absolutely no compartments or transitions
    # Only parameters

    # Commands to generate the databook and progbook prior to being filled out

    f_path = testdir / "test_no_compartment_framework.xlsx"
    d_path = testdir / "test_no_compartment_databook.xlsx"
    p_path = testdir / "test_no_compartment_progbook.xlsx"
    # F = at.ProjectFramework(f_path)
    # D = at.ProjectData.new(F,[2000],pops=1,transfers=0)
    # D.save(d_path)
    # P = at.ProgramSet.new(tvec=[2000],framework=F,data=D,progs=1)
    # P.save(p_path)

    P = at.Project(name="test", framework=f_path)
    P.load_databook(d_path, do_run=False)
    P.load_progbook(p_path)
    P.settings.update_time_vector(dt=1)

    # Test a coverage scenario
    res_parset = P.run_sim("default")

    with pytest.raises(Exception):
        instructions = at.ProgramInstructions(2002)
        # Running a progset without compartments and without coverage in the instructions should result in an error
        P.run_sim(parset="default", progset="default", progset_instructions=instructions, result_name="Baseline (no progset)")

    instructions = at.ProgramInstructions(2002, coverage={"treatment": 0.6})
    res_progset = P.run_sim(parset="default", progset="default", progset_instructions=instructions, result_name="Increased treatment via progset")

    d = at.PlotData(results=[res_parset, res_progset], outputs=["deaths", {"Number treated": "p_treat*n_infections"}])
    at.plot_series(d, axis="results")

    # Check the values at the end of the simulation are as expected
    assert res_parset.get_variable("deaths")[0].vals[-1] == 40 * 0.1 + 60 * 0.4
    assert res_progset.get_variable("deaths")[0].vals[-1] == 60 * 0.1 + 40 * 0.4

    print("Test successfully completed")


if __name__ == "__main__":
    test_no_compartments()
