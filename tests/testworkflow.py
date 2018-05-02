"""
Version:
"""

import atomica.ui as aui
import os

# TODO: Wrap up what the FE is likely to use into either Project or Result level method calls, rather than using functions.
from atomica.plotting import PlotData, plotSeries, plotBars

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
"makeprogramspreadsheet",
"makeplots",
"export",
"listspecs",
"manualcalibrate",
"autocalibrate",
"parameterscenario",
"saveproject",
"loadproject",
]    

tmpdir = "." + os.sep + "temp" + os.sep

if "makeframeworkfile" in torun:
    if test == "sir": args = {"num_comps":4, "num_characs":8, "num_pars":6}
    elif test == "tb": args = {"num_comps":40, "num_characs":70, "num_pars":140, "num_datapages":10}
    aui.ProjectFramework.createTemplate(path=tmpdir+"framework_"+test+"_blank.xlsx", **args)
        
if "makeframework" in torun:
    F = aui.ProjectFramework(name=test.upper(), file_path="./frameworks/framework_"+test+".xlsx")

if "saveframework" in torun:
    F.save(tmpdir+test+".frw")

if "loadframework" in torun:
    F = aui.ProjectFramework.load(tmpdir+test+".frw")

if "makedatabook" in torun:
    P = aui.Project(framework=F) # Create a project with an empty data structure.
    if test == "sir": args = {"num_pops":1, "num_progs":3, "data_start":2005, "data_end":2015, "data_dt":0.5}
    elif test == "tb": args = {"num_pops":12, "num_progs":31, "data_end":2018}
    P.createDatabook(databook_path=tmpdir+"databook_"+test+"_blank.xlsx", **args)
    
if "makeproject" in torun:
    # Preventing a run and databook loading so as to make calls explicit for the benefit of the FE.
    P = aui.Project(name=test.upper()+" project", framework=F, do_run=False)
    
if "loaddatabook" in torun:
    # Preventing parset creation and a run so as to make calls explicit for the benefit of the FE.
    P.loadDatabook(databook_path="./databooks/databook_"+test+".xlsx", make_default_parset=False, do_run=False)
    
if "makeparset" in torun:
    P.makeParset(name="default")
    
if "runsim" in torun:
    P.update_settings(sim_start=2000.0, sim_end=2030, sim_dt=0.25)
    P.runSim(parset="default", result_name="default")
    
if "makeprogramspreadsheet" in torun:
    print('Making programs spreadsheet ...')
    from atomica.defaults import demo
    from atomica.workbook_export import makeprogramspreadsheet

    P = demo(which='sir',do_plot=0)
    filename = 'temp/programspreadsheet.xlsx'
    makeprogramspreadsheet(filename, pops=2, progs=5)

if "makeplots" in torun:
    if test == "sir": 
        test_vars = ["sus","inf","rec","dead","ch_all","foi"]
        test_pop = "adults"
        decomp = ["sus","inf","rec","dead"]
        deaths = ["inf-dead","rec-dead","sus-dead"]
    if test == "tb":
        test_vars = ["sus","vac","spdu","alive","b_rate"]
        test_pop = "0-4"
        decomp = ["sus","vac","lt_inf","ac_inf","acr"]
        # Just do untreated TB-related deaths for simplicity.
#        death_pars = ["pd_term","pm_term","px_term","nd_term","nm_term","nx_term"]
#        death_links = [x.name for death_par in death_pars for x in P.results["default"].getVariable("0-4",death_par)[0].links]
        deaths = {"ds_deaths":["pd_term","pd_sad","nd_term","nd_sad"],
                  "mdr_deaths":["pm_term","pm_sad","nm_term","nm_sad"],
                  "xdr_deaths":["px_term","px_sad","nx_term","nx_sad"]}
        
    # Low level debug plots.
    for var in test_vars: P.results["parset_default"].getVariable(test_pop,var)[0].plot()
    
    # Plot population decomposition.
    d = PlotData(P.results["default"],outputs=decomp)
    plotSeries(d,plot_type="stacked")

    # Plot bars for deaths.
    d = PlotData(P.results["default"],outputs=deaths,t_bins=10)
    plotBars(d,outer="results")#,stack_outputs=[deaths])

    # Plot aggregate flows.
    d = PlotData(P.results["default"],outputs=[{"Death rate":deaths}])
    plotSeries(d)
    

if "export" in torun:
    P.results["default"].export(tmpdir+test+"_results")
    
if "listspecs" in torun:
    # For the benefit of FE devs, to work out how to list framework-related items in calibration and scenarios.
    FS = aui.FrameworkSettings
    DS = aui.DatabookSettings
    # Print list of characteristic names, i.e. state variables.
    print("\nCharacteristics...")
    print(P.framework.specs[FS.KEY_CHARACTERISTIC].keys())
    # Print list of compartment names. Should be added to the characteristics list for typical processes.
    print("Compartments...")
    print(P.framework.specs[FS.KEY_COMPARTMENT].keys())
    # Print list of parameters. Some of these relate to actual transitions, some are just dependencies.
    print("Parameters...")
    print(P.framework.specs[FS.KEY_PARAMETER].keys())
    # Print list of populations.
    print("Populations...")
    print(P.data.specs[DS.KEY_POPULATION].keys())
    # Print list of programs.
    print("Programs...")
    print(P.data.specs[DS.KEY_PROGRAM].keys())
    print()
    
if "manualcalibrate" in torun:
    # Attempt a manual calibration, i.e. edit the scaling factors directly.
    P.copy_parset(old_name="default", new_name="manual")
    if test == "sir":
        P.parsets["manual"].set_scaling_factor(par_name="transpercontact", pop_name="adults", scale=0.5)
        P.runSim(parset="manual", result_name="manual")
        d = PlotData([P.results["default"],P.results["manual"]], outputs=["ch_prev"])
        plotSeries(d, axis='results', data=P.data)
    
if "autocalibrate" in torun:
    # Manual fit was not good enough according to plots, so run autofit.
    P.copy_parset(old_name="default", new_name="auto")
    if test == "sir":
        # Explicitly specify full tuples for inputs and outputs, with 'None' for pop denoting all populations
        adjustables = [("transpercontact", None, 0.1, 1.9)]         # Absolute scaling factor limits.
        measurables = [("ch_prev", "adults", 1.0, "fractional")]        # Weight and type of metric.
        # New name argument set to old name to do in-place calibration.
        P.calibrate(parset="auto", new_name="auto", adjustables=adjustables, measurables=measurables, max_time=30)
        P.runSim(parset="auto", result_name="auto")
        d = PlotData(P.results, outputs=["ch_prev"])   # Values method used to plot all existent results.
        plotSeries(d, axis='results', data=P.data)
    
if "parameterscenario" in torun:
    scvalues = dict()
    if test == "sir":
        scvalues["infdeath"] = dict()
        scvalues["infdeath"]["adults"] = dict()
        
        # Insert (and possibly overwrite) one value.
        scvalues["infdeath"]["adults"]["y"] = [0.125]
        scvalues["infdeath"]["adults"]["t"] = [2015.]
        scvalues["infdeath"]["adults"]["smooth_onset"] = [2]
        
        P.make_scenario(name="increased_infections", instructions=scvalues)
        P.run_scenario(scenario="increased_infections", parset="auto", result_name="scen1")
        
        # Insert two values and eliminate everything between them.
        scvalues["infdeath"]["adults"]["y"] = [0.125, 0.5]
        scvalues["infdeath"]["adults"]["t"] = [2015., 2020.]
        scvalues["infdeath"]["adults"]["smooth_onset"] = [2, 3]
        
        P.make_scenario(name="increased_infections", instructions=scvalues, overwrite=True)
        P.run_scenario(scenario="increased_infections", parset="auto", result_name="scen2")
        
        d = PlotData([P.results["scen1"],P.results["scen2"]], outputs=["inf"])
        plotSeries(d, axis="results")
        
        d = PlotData([P.results["scen1"],P.results["scen2"]], outputs=["dead"])
        plotSeries(d, axis="results")
    
if "saveproject" in torun:
    P.save(tmpdir+test+".prj")

if "loadproject" in torun:
    P = aui.Project.load(tmpdir+test+".prj")