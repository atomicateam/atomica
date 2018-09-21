## This script tests the oscillations case (and implements some tests for the `fix-oscillations` branch)
# It can be safely deleted once `fix-oscillations` is merged

import atomica.ui as au
from atomica.excel import transfer_comments
import numpy as np
from atomica.ui import ProjectFramework, Project, ProjectData
import sciris as sc

# P = Project(name="test", framework="./frameworks/framework_tb.xlsx", databook_path="./databooks/databook_tb.xlsx",do_run=True)
# np.seterr(all='raise')
P = au.demo('tb')
res = P.run_sim(P.parsets[0])
d = au.PlotData(res,outputs=['alive','alive_databook'],project=P,pops='0-4')
au.plot_series(d,axis='outputs',data=P.data)
# res.model.pops
# P.parsets[0].get_par('l_dep').meta_y_factor = 0.01
# P.parsets[0].get_par('spd_infxness').meta_y_factor = 0.1
# # P.parsets[0].get_par('ltei_idiv').meta_y_factor = 0.1

# P = sc.loadobj('Stop TB.prj')
# # P.framework.pars.loc['pd_diag']['function'] = '1-(1-pd_ndiag*dt/(spdu+10))**(1/dt)'
# res = P.run_sim(parset=P.parsets[0])
# d = au.PlotData(res,outputs='pd_treat',project=P)
# au.plot_series(d,axis='pops',data=P.data)