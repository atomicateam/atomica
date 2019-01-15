import atomica as at
import numpy as np
import pylab as pl
import matplotlib.pyplot as plt
from atomica.optimization import optimize

# np.seterr('raise')

F = at.ProjectFramework(at.LIBRARY_PATH+'malaria_framework.xlsx')
P = at.Project(framework=F, sim_dt=1./365.)

# P.create_databook(databook_path=at.LIBRARY_PATH'malaria_databook.xlsx', num_pops=4, num_transfers=1, data_start=2010.)
P.load_databook(at.LIBRARY_PATH+'malaria_databook.xlsx', do_run=False)

# P.make_progbook(at.LIBRARY_PATH'malaria_progbook.xlsx', progs=17)
P.load_progbook(at.LIBRARY_PATH+'malaria_progbook.xlsx''')

instructions = at.ProgramInstructions(2018)

res = P.run_sim('default', 'default', instructions)
# P.save('malaria')
P.plot(res)

# Model is still in flux
# d = at.PlotData(res,'dalys',accumulate='integrate')
# at.plot_series(d,plot_type='stacked',axis='pops')
#
# # Number of treatments
# d = at.PlotData(res,'treated','gp')
# at.plot_series(d)
#
# # Eligibility for treatments
# d = at.PlotData(res,['hinf','himmmls','hwanmls'],'gp')
# at.plot_series(d,plot_type='stacked')
#
# # Flow into treatment eligibility
# d = at.PlotData(res,[':hinf',':himmmls',':hwanmls'],'gp')
# at.plot_series(d,plot_type='stacked')
#
# # Treated actual flow
# d = at.PlotData(res,'treated:flow','gp')
# at.plot_series(d)