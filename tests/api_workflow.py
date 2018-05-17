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
P.load_databook(databook_path="./databooks/databook_" + test + ".xlsx", make_default_parset=True, do_run=True)

P.results[0].export(test.upper()+" results")


P.save(tmpdir+test+".prj")

P = aui.Project.load(tmpdir+test+".prj")

if plot_initial:

    for var in ["sus", "inf", "rec", "dead", "ch_all", "foi"]:
        P.results[0].get_variable("adults", var)[0].plot()

    # Plot decomposition of population
    d = PlotData(P.results[0],outputs=['sus','inf','rec','dead'],project=P)
    plot_series(d, plot_type='stacked')

    # Bar plot showing deaths, disaggregated by source compartment
    d = PlotData(P.results[0],outputs=['sus:dead','inf:dead','rec:dead'],t_bins=10,project=P)
    plot_bars(d, outer='results', stack_outputs='all')

    # Aggregate flows
    d = PlotData(P.results[0],outputs=[{'Death rate':['infdeath:flow', 'susdeath:flow']}],project=P)
    plot_series(d)

    # Demonstrate how susdeath:flow sums over all of the tags sharing that label
    d = PlotData(P.results[0],outputs=['susdeath:flow'],project=P)
    plot_series(d)

    # Summing over the transitions between compartments in susdeath gives the same result
    d = PlotData(P.results[0],outputs=['sus:dead','rec:dead'],project=P)
    plot_series(d, plot_type='stacked')

# Make a scenario e.g. decreased infection rate
scvalues = dict()
scvalues['infdeath'] = dict()
scvalues['infdeath']['adults'] = dict()
scvalues['infdeath']['adults']['y'] = [0.125]
scvalues['infdeath']['adults']['t'] = [2015.]

scvalues['infdeath']['adults']['y'] = [0.125, 0.5]
scvalues['infdeath']['adults']['t'] = [2015., 2020.]
scvalues['infdeath']['adults']['smooth_onset'] = [2, 3]

scvalues['infdeath']['adults']['y'] = [0.125, 0.25, 0.50, 0.50]
scvalues['infdeath']['adults']['t'] = [2015., 2020., 2025., 2030.]
scvalues['infdeath']['adults']['smooth_onset'] = [4.,3.,2.,1.]


s = ParameterScenario('increased_infections',scvalues)
P.run_scenario(s)

d = PlotData(P.results, outputs=['infdeath'])
plot_series(d, axis='results')
import matplotlib.pyplot as plt
plt.show()

d = PlotData(P.results, outputs=['inf'])
plot_series(d, axis='results')

d = PlotData(P.results, outputs=['dead'])
plot_series(d, axis='results')

plt.show()

# Synthesize the calibration target
# P.parsets['calibration_target'] = dcp(P.parsets[0])
# P.parsets['calibration_target'].name = 'calibration_target'
# par = P.parsets['calibration_target'].get_par('transpercontact')
# par.y_factor['adults']=0.2
# r2 = P.run_sim(parset='calibration_target')
# d = PlotData([P.results[0],r2], outputs=['ch_prev'])
# plot_series(d, axis='results',data=P.data)


# Perform calibration to get a calibrated parset
pars_to_adjust = [('transpercontact','adults',0.1,1.9)]
output_quantities = []
for pop in P.parsets[0].pop_names:
    output_quantities.append(('ch_prev',pop,1.0,"fractional"))
calibrated_parset = perform_autofit(P, P.parsets[0], pars_to_adjust, output_quantities, max_time=30)

# Plot the results before and after calibration
calibrated_results = P.run_sim(calibrated_parset)
d = PlotData([P.results[0],calibrated_results], outputs=['ch_prev'])
plot_series(d, axis='results', data=P.data)


import matplotlib.pyplot as plt
plt.show()