"""
Version:
"""

import atomica.ui as aui
import os

test = "sir"
#test = "tb"

torun = [
"makeframeworkfile",
"makeframework",
"saveframework",
"loadframework",
"makedatabook",
"makeproject",
"loaddatabook",
"makeparset",
"runsim",
"makeplots",
"export",
"manualcalibrate",
"autocalibrate",
"parameterscenario",
"saveproject",
"loadproject",
]    

tmpdir = "." + os.sep + "temp" + os.sep

if "makeframeworkfile" in torun:
    if test == "sir": aui.ProjectFramework.createTemplate(path=tmpdir+"framework_sir_blank.xlsx", num_comps=4, num_pars=6, num_characs=8)
    elif test == "tb": aui.ProjectFramework.createTemplate(path=tmpdir+"framework_tb_blank.xlsx", num_comps=40, num_characs=70, num_pars=140, num_datapages=10)
    
if "makeframework" in torun:
    F = aui.ProjectFramework(name=test.upper(), file_path="./frameworks/framework_"+test+".xlsx")

if "saveframework" in torun:
    F.save(tmpdir+test+".frw")

if "loadframework" in torun:
    F = aui.ProjectFramework.load(tmpdir+test+".frw")

if "makedatabook" in torun:
    P = aui.Project(framework=F) # Create a project with an empty data structure.
    if test == "sir": P.createDatabook(databook_path=tmpdir+"databook_sir_blank.xlsx", num_pops=1, num_progs=3, data_start=2005, data_end=2015, data_dt=0.5)
    elif test == "tb": P.createDatabook(databook_path=tmpdir+"databook_tb_blank.xlsx", num_pops=7, num_progs=14, data_end=2018)

if "makeproject" in torun:
    # Preventing a run and databook loading so as to make calls explicit for the benefit of the FE.
    P = aui.Project(name=test.upper()+" project", framework=F, do_run=False)
    
if "loaddatabook" in torun:
    # Preventing parset creation and a run so as to make calls explicit for the benefit of the FE.
    P.loadDatabook(databook_path="./databooks/databook_"+test+".xlsx", make_default_parset=False, do_run=False)
    
if "makeparset" in torun:
    P.makeParset(name="default")
    
if "runsim" in torun:
    P.updateSettings(sim_start=2005.0, sim_end=2075.5, sim_dt=0.5)
    P.runSim(parset="default")
    
if "makeplots" in torun:
    # TODO: Wrap up what the FE is likely to use into either Project or Result level method calls, rather than using functions.
    from atomica.plotting import PlotData, plotSeries, plotBars
    if test == "sir": 
        test_vars = ["sus","inf","rec","dead","ch_all","foi"]
        pop = "adults"
        # Low level debug plots.
        for var in test_vars: P.results[0].getVariable(pop,var)[0].plot()
        
        # Plot population decomposition.
        d = PlotData(P.results[0],outputs=["sus","inf","rec","dead"])
        plotSeries(d,plot_type="stacked")
    
        # Plot bars for deaths.
        d = PlotData(P.results[0],outputs=["inf-dead","rec-dead","sus-dead"],t_bins=10)
        plotBars(d,outer="results",stack_outputs=[["inf-dead","rec-dead","sus-dead"]])
    
        # Plot aggregate flows.
        d = PlotData(P.results[0],outputs=[{"Death rate":["inf-dead","rec-dead","sus-dead"]}])
        plotSeries(d)
        
    if test == "tb":
        test_vars = ["sus","vac","spdu","alive","b_rate"]
        pop = "pop_0"
        for var in test_vars:
            P.results[0].getVariable(pop,var)[0].plot()

if "export" in torun:
    P.results[0].export(tmpdir+test+"_results")
    
if "manualcalibrate" in torun:
    P.copyParset(old_name="default", new_name="manual")
    
if "autocalibrate" in torun:
    P.copyParset(old_name="default", new_name="auto")
    
if "parameterscenario" in torun:
    pass
    
if "saveproject" in torun:
    P.save(tmpdir+test+".prj")

if "loadproject" in torun:
    P = aui.Project.load(tmpdir+test+".prj")