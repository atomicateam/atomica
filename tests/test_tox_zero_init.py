# Test frameworks where characteristics with zero values get extra initialization conditions for constituent compartments

import atomica as at
import numpy as np
from numpy.testing import assert_allclose
import pytest

testdir = at.parent_dir()
tmpdir = testdir / "temp"


def test_zero_initialization():
    F = at.ProjectFramework(testdir / "framework_init_zero.xlsx")
    D = at.ProjectData.new(F, [2020], 1, 0)
    P = at.Project(framework=F, databook=D, do_run=False)
    P.settings.update_time_vector(start=2020 ,end=2021, dt=1)
    res = P.run_sim()
    return res



if __name__ == "__main__":
    test_zero_initialization()
