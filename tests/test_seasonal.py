## This script checks that the junction update is correct

import numpy as np
import atomica.ui as au
import matplotlib.pyplot as plt
import os

testdir = au.parent_dir()
tmpdir = os.path.join(testdir,'temp','')

F_path = testdir + 'framework_seasonal_test.xlsx'
D_path = tmpdir + 'databook_seasonal_test.xlsx'

F = au.ProjectFramework(F_path)
D = au.ProjectData.new(F,np.arange(2000,2001),pops={'pop1':'Population 1'},transfers=0)
D.save(D_path)

P = au.Project(name='test', framework=F, do_run=False)
P.settings.update_time_vector(end=2005,dt=0.02)
P.load_databook(databook_path=D_path, make_default_parset=True, do_run=True)
r = P.results[0]

d = au.PlotData(r,outputs=['seasonal_max'],project=P)
au.plot_series(d)
plt.title('Seasonal rainfall')

d = au.PlotData(r,outputs=['seasonal_jan','seasonal_jun'],project=P)
au.plot_series(d)
plt.title('Seasonal rainfall')

d = au.PlotData(r,outputs=['birth'],project=P)
au.plot_series(d)

d = au.PlotData(r,outputs=['mos'],project=P)
au.plot_series(d)
