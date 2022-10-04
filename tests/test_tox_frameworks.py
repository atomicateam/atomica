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


if __name__ == "__main__":

    for fname in frameworks:
        test_basic_framework(fname)

    test_framework_par_min_max()
