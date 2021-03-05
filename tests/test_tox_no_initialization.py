# Test frameworks with no compartments/characteristics to ensure that
# they are initialized as 0 correctly

import atomica as at
import numpy as np

testdir = at.parent_dir()
tmpdir = testdir / "temp"


def test_no_initialization():

    at.logger.setLevel("DEBUG")

    F = at.ProjectFramework(testdir / "test_no_initialization.xlsx")
    D = at.ProjectData.new(F, [2020], 1, 0)
    P = at.Project(framework=F, databook=D, do_run=False)
    P.settings.update_time_vector(dt=1)
    res = P.run_sim()

    ca = res.get_variable("ca")[0]
    ja = res.get_variable("ja")[0]
    sink = res.get_variable("sink")[0]

    assert ca.vals[0] == 0
    assert ca.vals[1] == 10
    assert ja.vals[0] == 0
    assert ja.outflow[0] == 0
    assert ja.outflow[1] == 5


if __name__ == "__main__":
    test_no_initialization()
