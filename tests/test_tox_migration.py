import atomica.ui as au
import os

def test_migration():
    au.logger.setLevel('DEBUG')

    testdir = au.parent_dir()
    tmpdir = os.path.join(testdir,'temp','')

    P = au.Project.load(testdir+'migration_test_with_result.prj')
    results = P.run_sim()
    au.plot_series(au.PlotData(results))

    P = au.Project.load(testdir+'migration_test_without_result.prj')
    results = P.run_sim()

    au.plot_series(au.PlotData(results))

if __name__ == '__main__':
    test_migration()
