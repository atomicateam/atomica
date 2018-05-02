"""
Version:
"""

# Romesh PyCharm commands
from IPython import get_ipython
ipython = get_ipython()
if ipython is not None:
    ipython.magic('load_ext autoreload')
    ipython.magic('autoreload 2')
from atomica.plotting import PlotData,plotSeries,plotBars
from copy import deepcopy as dcp

import atomica.ui as aui
import os
from atomica.scenarios import ParameterScenario
from atomica.calibration import performAutofit

plot_initial = True

test = "sir"
tmpdir = "." + os.sep + "temp" + os.sep

F = aui.ProjectFramework.load(tmpdir+test+".frw")
P = aui.Project(name=test.upper()+" project", framework=F)
P.loadDatabook(databook_path="./databooks/databook_sir_twopop.xlsx", make_default_parset=True, do_run=True)

P.results[0].export(test.upper()+" results")
    
P.save(tmpdir+test+".prj")

P = aui.Project.load(tmpdir+test+".prj")

def plot_calibration(adjustables,measurables,titlestr):
    # Run calibration and plot results showing y-factors in title
    new_parset = performAutofit(P, P.parsets['default'], adjustables, measurables, max_time=30)
    new_result = P.runSim(new_parset)
    d = PlotData(new_result, outputs=['ch_prev'])
    figs = plotSeries(d, axis='pops', data=P.data)
    figs[0].axes[0].set_title("Calibrating {}: adults={:.2f}, children={:.2f}".format(titlestr,new_parset.getPar('transpercontact').y_factor['adults'],new_parset.getPar('transpercontact').y_factor['children']))

# Calibrate explicitly listing out the pops
# Expected result is y-factors around adults=0.2 and children=0.3
adjustables = [("transpercontact", 'adults', 0.1, 1.9),("transpercontact", 'children', 0.1, 1.9)]  # Absolute scaling factor limits.
measurables = [("ch_prev", 'adults', 1.0, "fractional"),("ch_prev", 'children', 1.0, "fractional")]  # Weight and type of metric.
plot_calibration(adjustables,measurables,'explicit')

# Calibrate with pops=None to calibrate each pop independently
# Expected result is that this should be the same as above
adjustables = [("transpercontact", None, 0.1, 1.9)]  # Absolute scaling factor limits.
measurables = [("ch_prev", None, 1.0, "fractional")]  # Weight and type of metric.
plot_calibration(adjustables,measurables,"'None'")

# Calibrate with pops='all' to use the same y-factor in all pops
# Expected result is that the fit looks acceptable with the same y-factor for both pops
adjustables = [("transpercontact", 'all', 0.1, 1.9)]  # Absolute scaling factor limits.
measurables = [("ch_prev", None, 1.0, "fractional")]  # Weight and type of metric.
plot_calibration(adjustables,measurables,"'all'")

# Calibrate using only one pop as the objective
# Expected result is that both adults and children get the child-fitted value of 0.3
adjustables = [("transpercontact", 'all', 0.1, 1.9)]  # Absolute scaling factor limits.
measurables = [("ch_prev", 'children', 1.0, "fractional")]  # Weight and type of metric.
plot_calibration(adjustables,measurables,"children objective")

# Calibrate using only one pop in both adjustables and measurables
# Expected result is that adults will have y-factor=1.0 (no change) while children get 0.3
adjustables = [("transpercontact", 'children', 0.1, 1.9)]  # Absolute scaling factor limits.
measurables = [("ch_prev", 'children', 1.0, "fractional")]  # Weight and type of metric.
plot_calibration(adjustables,measurables,"children only")

import matplotlib.pyplot as plt
plt.show()