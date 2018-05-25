"""
Version:
"""

# Romesh PyCharm commands
from IPython import get_ipython
ipython = get_ipython()
if ipython is not None:
    ipython.magic('load_ext autoreload')
    ipython.magic('autoreload 2')
from atomica.plotting import PlotData,plot_series,plot_bars
from copy import deepcopy as dcp

import atomica.ui as aui
import os
from atomica.scenarios import ParameterScenario
from atomica.calibration import perform_autofit

plot_initial = True

test = "sir"
tmpdir = "." + os.sep + "temp" + os.sep

F = aui.ProjectFramework.load(tmpdir+test+".frw")
P = aui.Project(name=test.upper()+" project", framework=F,do_run=False)
P.load_databook(databook_path="./databooks/databook_" + test + ".xlsx", make_default_parset=True, do_run=False)

P.copy_parset('default','increased_foi_yfactor')
P.get_parset('increased_foi_yfactor').get_par('foi').y_factor['adults']=2.0

baseline_results = P.run_sim(P.parsets['default'])
increased_foi_yfactor = P.run_sim(P.parsets['increased_foi_yfactor'])

d = PlotData([baseline_results,increased_foi_yfactor], outputs=['ch_prev'])
figs = plot_series(d, axis='results', data=P.data)
figs[0].axes[-1].set_title('Increased FOI via Y-factor')

from numpy import floor
def foi_func(ch_prev,transpercontact,contacts,susdeath):
    x = (1-(1-ch_prev*transpercontact)**floor(contacts)*(1-ch_prev*transpercontact*(contacts-floor(contacts))))*(1-susdeath)
    return 2*x

P.framework.get_spec('foi')['func'] = foi_func
P.framework.get_spec('foi')['dependencies'] = ['ch_prev','transpercontact','contacts','susdeath']
increased_foi_functor = P.run_sim(P.parsets['default'])
d = PlotData([baseline_results,increased_foi_functor], outputs=['ch_prev'])
figs = plot_series(d, axis='results', data=P.data)
figs[0].axes[-1].set_title('Increased FOI via custom functor')

import matplotlib.pyplot as plt
plt.show()