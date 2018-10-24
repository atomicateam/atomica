import atomica.ui as au
au.logger.setLevel('DEBUG')
P = au.Project.load('migration_test.prj')
results = P.run_sim()
au.plot_series(au.PlotData(results))