import atomica as at
import numpy as np
import os

testdir = at.parent_dir()  # Must be relative to current file to work with tox


def test_indirect_programs():

    F = at.ProjectFramework(testdir/'test_indirect_programs_framework.xlsx')
    D = at.ProjectData.new(F, tvec=[2019],pops=1, transfers=0)

    P = at.Project(framework=F, databook=D, do_run=False)
    P.settings.update_time_vector(start=2019, end=2025, dt=1)
    res = P.run_sim()

    np.testing.assert_array_equal(res.get_variable('par_1')[0].vals, res.get_variable('v_rate')[0].vals)
    np.testing.assert_array_equal(res.get_variable('par_1')[0].vals, res.get_variable('par_2')[0].vals)

    P.load_progbook(testdir/"test_indirect_programs_progbook.xlsx")
    ins = at.ProgramInstructions(start_year=2019)
    res = P.run_sim(parset=0, progset=0, progset_instructions=ins)

    np.testing.assert_array_equal(res.get_variable('par_1')[0].vals, res.get_variable('v_rate')[0].vals)
    np.testing.assert_array_equal(res.get_variable('par_1')[0].vals, res.get_variable('par_2')[0].vals)


if __name__ == "__main__":
    test_indirect_programs()
