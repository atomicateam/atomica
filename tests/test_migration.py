import atomica.ui as au
au.logger.setLevel('DEBUG')

P = au.Project.load('migration_test_with_result.prj')
results = P.run_sim()
au.plot_series(au.PlotData(results))

P = au.Project.load('migration_test_without_result.prj')
results = P.run_sim()

au.plot_series(au.PlotData(results))