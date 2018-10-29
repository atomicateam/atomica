import atomica.ui as au
import os

au.logger.setLevel('DEBUG')

testdir = au.parent_dir()
tmpdir = os.path.join('temp','')

P = au.Project.load(testdir+'migration_test_with_result.prj')
results = P.run_sim()
au.plot_series(au.PlotData(results))

P = au.Project.load(testdir+'migration_test_without_result.prj')
results = P.run_sim()

au.plot_series(au.PlotData(results))