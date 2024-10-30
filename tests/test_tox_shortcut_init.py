# Test frameworks with no compartments/characteristics to ensure that
# they are initialized as 0 correctly

import atomica as at
import numpy as np
from numpy.testing import assert_allclose
import pytest

testdir = at.rootdir / "tests"
tmpdir = testdir / "temp"


def _run_framework(fname):
    F = at.ProjectFramework(testdir / fname)
    D = at.ProjectData.new(F, [2020], 1, 0)
    P = at.Project(framework=F, databook=D, do_run=False)
    P.settings.update_time_vector(dt=1)
    res = P.run_sim()
    return res


def test_shortcut_init_1():
    res = _run_framework("test_shortcut_init_framework_1.xlsx")
    print(res)

    # With no shortcut initialization for infected, 40 people get assigned to it, which flow downstream to R and D
    assert_allclose(res.get_variable("s")[0].vals[0], 40)
    assert_allclose(res.get_variable("i")[0].vals[0], 0)
    assert_allclose(res.get_variable("r")[0].vals[0], 60)
    assert_allclose(res.get_variable("d")[0].vals[0], 20)


def test_shortcut_init_2():
    res = _run_framework("test_shortcut_init_framework_2.xlsx")

    # With 0 shortcut initialization for infected, 0 people get assigned to it, so we have an even split
    assert_allclose(res.get_variable("s")[0].vals[0], 60)
    assert_allclose(res.get_variable("i")[0].vals[0], 0)
    assert_allclose(res.get_variable("r")[0].vals[0], 60)
    assert_allclose(res.get_variable("d")[0].vals[0], 0)


def test_shortcut_init_3():
    # With a nonzero shortcut initialization, an error should occur
    with pytest.raises(at.InvalidFramework):
        _run_framework("test_shortcut_init_framework_3.xlsx")


def test_shortcut_init_4():
    res = _run_framework("test_shortcut_init_framework_4.xlsx")

    # With 0 shortcut initialization for infected, 0 people get assigned to it, so we have an even split
    assert_allclose(res.get_variable("s")[0].vals[0], 60)
    assert_allclose(res.get_variable("i")[0].vals[0], 0)
    assert_allclose(res.get_variable("r")[0].vals[0], 60)
    assert_allclose(res.get_variable("d")[0].vals[0], 0)


def test_shortcut_init_5():
    # With a nonzero shortcut initialization, an error should occur
    with pytest.raises(at.InvalidFramework):
        _run_framework("test_shortcut_init_framework_5.xlsx")


if __name__ == "__main__":
    test_shortcut_init_1()
    test_shortcut_init_2()
    test_shortcut_init_3()
    test_shortcut_init_4()
    test_shortcut_init_5()
