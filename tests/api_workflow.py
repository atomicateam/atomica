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

import atomica.ui as aui
import os
from atomica.scenarios import ParameterScenario

plot_initial = False

test = "sir"
tmpdir = "." + os.sep + "temp" + os.sep

F = aui.ProjectFramework.load(tmpdir+test+".frw")
P = aui.Project(name=test.upper()+" project", framework=F, databook="./databooks/databook_"+test+".xlsx")

P.results[0].export(test.upper()+" results")
    
P.save(tmpdir+test+".prj")

P = aui.Project.load(tmpdir+test+".prj")

if plot_initial:

    for var in ["sus", "inf", "rec", "dead", "ch_all", "foi"]:
        P.results[0].getVariable("adults", var)[0].plot()

    # Plot decomposition of population
    d = PlotData(P.results[0],outputs=['sus','inf','rec','dead'])
    plotSeries(d,plot_type='stacked')

    # Bar plot showing deaths
    d = PlotData(P.results[0],outputs=['inf-dead','rec-dead', 'sus-dead'],t_bins=10)
    plotBars(d,outer='results',stack_outputs=[['inf-dead','rec-dead', 'sus-dead']])

    # Aggregate flows
    d = PlotData(P.results[0],outputs=[{'Death rate':['inf-dead','rec-dead', 'sus-dead']}])
    plotSeries(d)


# Make a scenario e.g. decreased infection rate
scvalues = dict()
scvalues['infdeath'] = dict()
scvalues['infdeath']['adults'] = dict()
scvalues['infdeath']['adults']['y'] = [0.125]
scvalues['infdeath']['adults']['t'] = [2015.]


scvalues['infdeath']['adults']['smooth_onset'] = [2]

scvalues['infdeath']['adults']['y'] = [0.125, 0.5]
scvalues['infdeath']['adults']['t'] = [2015., 2020.]
scvalues['infdeath']['adults']['smooth_onset'] = [2, 3]

s = ParameterScenario('increased_infections',scvalues)
P.results['scen1']=P.run_scenario(s)

d = PlotData(P.results, outputs=['inf'])
plotSeries(d, axis='results')

d = PlotData(P.results, outputs=['dead'])
plotSeries(d, axis='results')



import matplotlib.pyplot as plt
plt.show()