## This script checks that the junction update is correct

import numpy as np
from atomica.ui import ProjectFramework, Project, ProjectData, PlotData, plot_series
import matplotlib.pyplot as plt

F_path = "./frameworks/framework_seasonal_test.xlsx"
D_path = './temp/databook_seasonal_test.xlsx'

F = ProjectFramework(F_path)
D = ProjectData.new(F,np.arange(2000,2001),pops={'pop1':'Population 1'},transfers=0)
D.save(D_path)

P = Project(name="test", framework=F, do_run=False)
P.settings.update_time_vector(end=2005,dt=0.02)
P.load_databook(databook_path=D_path, make_default_parset=True, do_run=True)
r = P.results[0]

d = PlotData(r,outputs=['seasonal_jan','seasonal_jun'],project=P)
plot_series(d)
plt.title('Seasonal rainfall')

d = PlotData(r,outputs=['birth'],project=P)
plot_series(d)

d = PlotData(r,outputs=['mos'],project=P)
plot_series(d)
