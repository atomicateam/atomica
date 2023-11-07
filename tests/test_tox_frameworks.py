# Run various framework-related tests

import atomica as at
import numpy as np
import pytest

testdir = at.parent_dir()
tmpdir = testdir / "temp"

frameworks = [
    "framework_blank_sheet.xlsx",
    "framework_mixed_pages.xlsx",
    "framework_no_pages.xlsx",
    "framework_extra_pages.xlsx",
    "framework_missing_page_column.xlsx",
]


@pytest.mark.parametrize("fname", frameworks)
def test_basic_framework(fname):
    F = at.ProjectFramework(testdir / fname)
    D = at.ProjectData.new(F, np.arange(2020, 2022), 1, 1)
    D.save(tmpdir / fname.replace("framework", "databook"))


def test_framework_par_min_max():
    # Check that the vector min/max functions work properly

    F_path = testdir / "framework_par_min_max_test.xlsx"
    F = at.ProjectFramework(F_path)

    # D = at.ProjectData.new(F,[2020,2021,2022],1,0)
    # D.save(testdir / 'par_min_max_databook.xlsx')
    D = at.ProjectData.from_spreadsheet(testdir / "par_min_max_databook.xlsx", F)

    # Example of running a bare model without a project
    res = at.run_model(at.ProjectSettings(2020, 2022, 1), F, at.ParameterSet(F, D))

    minpar = res.get_variable("minpar")[0].vals
    maxpar = res.get_variable("maxpar")[0].vals

    assert np.array_equal(minpar, [2, 5, 4])
    assert np.array_equal(maxpar, [5, 10, 6])


def test_framework_single_char():
    # Check that single chracter variable names work

    P1 = at.demo("sir")
    r1 = P1.results[0]

    F = at.ProjectFramework(testdir / "test_single_char_framework.xlsx")
    D = at.ProjectData.new(tvec=P1.data.tvec, framework=F, pops=P1.data.pops, transfers=0)
    P = at.Project(framework=F, databook=D, do_run=False)
    P.settings = P1.settings
    r2 = P.run_sim()

    test_equal = lambda var1, var2: np.testing.assert_array_equal(r1.get_variable(var1)[0].vals, r2.get_variable(var2)[0].vals)

    test_equal("sus", "s")
    test_equal("inf", "i")
    test_equal("rec", "r")


def test_framework_spaces():
    F = at.ProjectFramework(testdir / "test_framework_spaces.xlsx")
    F.get_variable("Transmission probability per contact")  # Has no leading or trailing spaces in the framework
    F.get_variable("Number of contacts annually")  # Has a leading space in the framework
    F.get_variable("Death rate for infected people")  # Has a trailing space in the framework

def test_framework_comments():
    F1 = at.ProjectFramework(testdir / "sir_framework_ignore.xlsx")
    F2 = at.ProjectFramework(at.LIBRARY_PATH / "sir_framework.xlsx")

    assert F1.transitions == F2.transitions
    assert F1.pars.equals(F2.pars)

if __name__ == "__main__":

    for fname in frameworks:
        test_basic_framework(fname)

    test_framework_par_min_max()
    test_framework_single_char()
    test_framework_spaces()
