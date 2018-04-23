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

test = "sir"
tmpdir = "." + os.sep + "temp" + os.sep

aui.ProjectFramework.createTemplate(path=tmpdir+"framework_sir_blank.xlsx", num_comps=4, num_pars=6, num_characs=8)
F = aui.ProjectFramework(name=test.upper(), file_path="./frameworks/framework_"+test+".xlsx")
F.save(tmpdir+test+".frw")
F = aui.ProjectFramework.load(tmpdir+test+".frw")
P = aui.Project(framework=F) # Create a project with no data
P.createDatabook(databook_path="./databooks/databook_sir_blank.xlsx", num_pops=1, num_progs=3)
P = aui.Project(name=test.upper()+" project", framework=F, databook="./databooks/databook_"+test+".xlsx")
    
for var in ["sus","inf","rec","dead","ch_all","foi"]:
        P.results[0].getVariable("adults",var)[0].plot()

P.results[0].export(test.upper()+" results")
    
P.save(tmpdir+test+".prj")

P = aui.Project.load(tmpdir+test+".prj")



# Plot decomposition of population
d = PlotData(P.results[0],outputs=['sus','inf','rec','dead'])
plotSeries(d,plot_type='stacked')

# Bar plot showing deaths
d = PlotData(P.results[0],outputs=['inf-dead','rec-dead', 'sus-dead'],t_bins=10)
plotBars(d,outer='results',stack_outputs=[['inf-dead','rec-dead', 'sus-dead']])

# Aggregate flows
d = PlotData(P.results[0],outputs=[{'Death rate':['inf-dead','rec-dead', 'sus-dead']}])
plotSeries(d)
