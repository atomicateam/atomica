import atomica.ui as au
import numpy as np
import pylab as pl
import matplotlib.pyplot as plt
from atomica.optimization import optimize

# np.seterr('raise')

F = au.ProjectFramework(au.LIBRARY_PATH + 'malaria_framework.xlsx')
P = au.Project(framework=F, sim_dt=5./365.)

# P.create_databook(databook_path='malaria_databook.xlsx', num_pops=3, num_transfers=1, data_start=2010.)
P.load_databook(au.LIBRARY_PATH + 'malaria_databook.xlsx', do_run=False)

# P.make_progbook('malaria_progbook.xlsx', progs=17)
P.load_progbook(au.LIBRARY_PATH + 'malaria_progbook.xlsx''')

instructions = au.ProgramInstructions()

res = P.run_sim('default', 'default', instructions)
# P.save('malaria')
P.plot(res)
plt.show()

# Model is still in flux
# d = au.PlotData(res,'dalys',accumulate='integrate')
# au.plot_series(d,plot_type='stacked',axis='pops')
#
# # Number of treatments
# d = au.PlotData(res,'treated','gp')
# au.plot_series(d)
#
# # Eligibility for treatments
# d = au.PlotData(res,['hinf','himmmls','hwanmls'],'gp')
# au.plot_series(d,plot_type='stacked')
#
# # Flow into treatment eligibility
# d = au.PlotData(res,[':hinf',':himmmls',':hwanmls'],'gp')
# au.plot_series(d,plot_type='stacked')
#
# # Treated actual flow
# d = au.PlotData(res,'treated:flow','gp')
# au.plot_series(d)