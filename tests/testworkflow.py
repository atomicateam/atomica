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
"loadprogramspreadsheet",
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
    aui.ProjectFramework.create_template(path=tmpdir + "framework_" + test + "_blank.xlsx", **args)
        
if "makeframework" in torun:
    F = aui.ProjectFramework(name=test.upper(), filepath="./frameworks/framework_" + test + ".xlsx")

if "saveframework" in torun:
    F.save(tmpdir+test+".frw")

if "loadframework" in torun:
    F = aui.ProjectFramework.load(tmpdir+test+".frw")

if "makedatabook" in torun:
    P = aui.Project(framework=F) # Create a project with an empty data structure.
    if test == "sir": args = {"num_pops":1, "num_progs":3, "data_start":2005, "data_end":2015, "data_dt":0.5}
    elif test == "tb": args = {"num_pops":12, "num_progs":31, "data_end":2018}
    P.create_databook(databook_path=tmpdir + "databook_" + test + "_blank.xlsx", **args)
    
if "makeproject" in torun:
    # Preventing a run and databook loading so as to make calls explicit for the benefit of the FE.
    P = aui.Project(name=test.upper()+" project", framework=F, do_run=False)
    
if "loaddatabook" in torun:
    # Preventing parset creation and a run so as to make calls explicit for the benefit of the FE.
    P.load_databook(databook_path="./databooks/databook_" + test + ".xlsx", make_default_parset=False, do_run=False)
    
if "makeparset" in torun:
    P.make_parset(name="default")
    
if "runsim" in torun:
    P.update_settings(sim_start=2000.0, sim_end=2030, sim_dt=0.25)
    P.run_sim(parset="default", result_name="default")
    
if "makeprogramspreadsheet" in torun:
    print('Making programs spreadsheet ...')
    from atomica.defaults import demo
    from atomica.workbook_export import makeprogramspreadsheet

    P = demo(which='sir',do_plot=0)
    filename = 'temp/programspreadsheet.xlsx'
    makeprogramspreadsheet(filename, pops=2, progs=5)

if "loadprogramspreadsheet" in torun:
    print('\n\n\nLoading programs spreadsheet ...')
    from atomica.defaults import demo

    P = demo(which='sir',do_plot=0)
    filename = 'databooks/programdata_sir.xlsx'
    P.load_progbook(databook_path=filename)

if "makeplots" in torun:
    if test == "sir": 
        test_vars = ["sus","inf","rec","dead","ch_all","foi"]
        test_pop = "adults"
        decomp = ["sus","inf","rec","dead"]
        deaths = ["inf-dead","rec-dead","sus-dead"]
        grouped_deaths = {'inf':['inf-dead:flow'],'rec':['rec-dead:flow'],'sus':['sus-dead:flow']}
        plot_pop = [test_pop]
    if test == "tb":
        test_vars = ["sus","vac","spdu","alive","b_rate"]
        test_pop = "0-4"
        decomp = ["sus","vac","lt_inf","ac_inf","acr"]
        # Just do untreated TB-related deaths for simplicity.
        deaths = ["pd_term:flow","pd_sad:flow","nd_term:flow","nd_sad:flow","pm_term:flow","pm_sad:flow","nm_term:flow","nm_sad:flow","px_term:flow","px_sad:flow","nx_term:flow","nx_sad:flow"]
        grouped_deaths = {"ds_deaths":["pd_term:flow","pd_sad:flow","nd_term:flow","nd_sad:flow"],
                  "mdr_deaths":["pm_term:flow","pm_sad:flow","nm_term:flow","nm_sad:flow"],
                  "xdr_deaths":["px_term:flow","px_sad:flow","nx_term:flow","nx_sad:flow"]}
        plot_pop = ['5-14','15-64']

    # Low level debug plots.
    for var in test_vars: P.results["parset_default"].getVariable(test_pop,var)[0].plot()
    
    # Plot population decomposition.
    d = PlotData(P.results["parset_default"],outputs=decomp,pops=plot_pop)
    plotSeries(d,plot_type="stacked")

    if test == "tb":
        # TODO: Decide how to deal with aggregating parameters that are not transition-related, i.e. flows.
        # Plot bars for deaths, aggregated by strain, stacked by pop
        d = PlotData(P.results["parset_default"],outputs=grouped_deaths,t_bins=10,pops=plot_pop)
        plotBars(d,outer="results",stack_pops=[plot_pop])

        # Plot bars for deaths, aggregated by pop, stacked by strain
        d = PlotData(P.results["parset_default"],outputs=grouped_deaths,t_bins="all",pops=plot_pop)
        plotBars(d,stack_outputs=[list(grouped_deaths.keys())])

        # Plot total death flow over time
        # Plot death flow rate decomposition over all time
        d = PlotData(P.results["parset_default"],outputs=grouped_deaths,pops=plot_pop)
        plotSeries(d,plot_type='stacked',axis='outputs')

    # Plot aggregate flows.
#    d = PlotData(P.results["parset_default"],outputs=[{"Death rate":deaths}])
#    plotSeries(d,axis="pops")


if "export" in torun:
    P.results["parset_default"].export(tmpdir+test+"_results")
    
if "listspecs" in torun:
    # For the benefit of FE devs, to work out how to list framework-related items in calibration and scenarios.
    FS = aui.FrameworkSettings
    DS = aui.DataSettings
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
        outputs = ["ch_prev"]
    if test == "tb":
        P.parsets["manual"].set_scaling_factor(par_name="foi", pop_name="15-64", scale=2.0)
        outputs = ["ac_inf"]
    P.runSim(parset="manual", result_name="manual")
    d = PlotData([P.results["parset_default"],P.results["manual"]], outputs=outputs, pops=plot_pop)
    plotSeries(d, axis="results", data=P.data)
    
if "autocalibrate" in torun:
    # Manual fit was not good enough according to plots, so run autofit.
    P.copy_parset(old_name="default", new_name="auto")
    if test == "sir":
        # Explicitly specify full tuples for inputs and outputs, with 'None' for pop denoting all populations
        adjustables = [("transpercontact", None, 0.1, 1.9)]         # Absolute scaling factor limits.
        measurables = [("ch_prev", "adults", 1.0, "fractional")]        # Weight and type of metric.
        # New name argument set to old name to do in-place calibration.
        P.calibrate(parset="auto", new_name="auto", adjustables=adjustables, measurables=measurables, max_time=30)
    if test == "tb":
        # Shortcut for calibration inputs.
        P.calibrate(parset="auto", new_name="auto", adjustables=["foi"], measurables=["ac_inf"], max_time=10)
    P.run_sim(parset="auto", result_name="auto")
    d = PlotData(P.results, outputs=outputs)   # Values method used to plot all existent results.
    plotSeries(d, axis='results', data=P.data)
    
if "parameterscenario" in torun:
    scvalues = dict()
    scen_par = "infdeath"
    scen_pop = "adults"
    scen_outputs = ["inf","dead"]
    if test == "tb":
        scen_par = "spd_infxness"
        scen_pop = "15-64"
        scen_outputs = ["lt_inf", "ac_inf"]

    scvalues[scen_par] = dict()
    scvalues[scen_par][scen_pop] = dict()

    # Insert (or possibly overwrite) one value.
    scvalues[scen_par][scen_pop]["y"] = [0.125]
    scvalues[scen_par][scen_pop]["t"] = [2015.]
    scvalues[scen_par][scen_pop]["smooth_onset"] = [2]

    P.make_scenario(name="varying_infections", instructions=scvalues)
    P.run_scenario(scenario="varying_infections", parset="auto", result_name="scen1")

    # Insert two values and eliminate everything between them.
    scvalues[scen_par][scen_pop]["y"] = [0.125, 0.5]
    scvalues[scen_par][scen_pop]["t"] = [2015., 2020.]
    scvalues[scen_par][scen_pop]["smooth_onset"] = [2, 3]

    P.make_scenario(name="varying_infections", instructions=scvalues, overwrite=True)
    P.run_scenario(scenario="varying_infections", parset="auto", result_name="scen2")

    d = PlotData([P.results["scen1"],P.results["scen2"]], outputs=scen_outputs[0], pops=[scen_pop])
    plotSeries(d, axis="results")

    d = PlotData([P.results["scen1"],P.results["scen2"]], outputs=scen_outputs[-1], pops=[scen_pop])
    plotSeries(d, axis="results")
    
if "saveproject" in torun:
    P.save(tmpdir+test+".prj")

if "loadproject" in torun:
    P = aui.Project.load(tmpdir+test+".prj")