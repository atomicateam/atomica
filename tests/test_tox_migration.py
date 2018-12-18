import atomica as at
import os

def test_migration():
    at.logger.setLevel('DEBUG')

    testdir = at.parent_dir()
    tmpdir = os.path.join(testdir,'temp','')

    P = at.Project.load(testdir+'migration_test_with_result.prj')
    results = P.run_sim()
    at.plot_series(at.PlotData(results))

    P = at.Project.load(testdir+'migration_test_without_result.prj')
    results = P.run_sim()

    at.plot_series(at.PlotData(results))

    P.databook.save(tmpdir + 'migration_test_databook_save')

if __name__ == '__main__':
    test_migration()
