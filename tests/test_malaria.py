import atomica.ui as au
import numpy as np
import pylab as pl
import matplotlib.pyplot as plt
from atomica.optimization import optimize

# np.seterr('raise')

F = au.ProjectFramework("frameworks/framework_malaria.xlsx")
P = au.Project(framework=F, sim_dt=1./365.)

# P.create_databook(databook_path="databook_malaria.xlsx", num_pops=4, num_transfers=1, data_start=2010.)
P.load_databook('databooks/databook_malaria.xlsx', do_run=False)

# P.make_progbook("progbook_malaria.xlsx", progs=17)
P.load_progbook('databooks/progbook_malaria.xlsx')

instructions = au.ProgramInstructions()

res = P.run_sim('default', 'default', instructions)
# P.save('malaria')
P.plot(res)

d = au.PlotData(res,'dalys',accumulate='integrate')
au.plot_series(d,plot_type='stacked',axis='pops')

plt.show()