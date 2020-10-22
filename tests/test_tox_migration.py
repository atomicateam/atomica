import atomica as at
import os
import sys


def test_migration():

    # The migration test tries to load a pickle saved in Python 3.7
    # This is known not to work in Python 3.6 because SafeUUID in the
    # UUID module was only introduced in Python 3.7. Therefore, we skip
    # this test in versions older than Python 3.7
    if sys.version_info[1] < 7:
        return

    at.logger.setLevel("DEBUG")

    testdir = at.parent_dir()
    tmpdir = testdir / "temp"

    P = at.Project.load(testdir / "migration_test_with_scenarios.prj")
    results = P.run_scenarios()
    P.progsets[0].save(tmpdir / "migration_test_progbook_save")  # Save original databook

    P = at.Project.load(testdir / "migration_test_with_result.prj")
    results = P.run_sim()
    at.plot_series(at.PlotData(results))

    P = at.Project.load(testdir / "migration_test_without_result.prj")
    results = P.run_sim()

    at.plot_series(at.PlotData(results))

    P.databook.save(tmpdir / "migration_test_databook_save")  # Save original databook
    P.data.save(tmpdir / "migration_test_data_save")  # Re-convert data to spreadsheet and save


if __name__ == "__main__":
    test_migration()
