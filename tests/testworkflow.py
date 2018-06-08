"""
Version:
"""

import os
import atomica.ui as au
import sciris.core as sc

test = "sir"
# test = "tb"

torun = [
#"makeframeworkfile",
#"makeframework",
#"saveframework",
#"loadframework",
#"makedatabook",
#"makeproject",
#"loaddatabook",
#"makeparset",
#"runsim",
"makeprogramspreadsheet",
"loadprogramspreadsheet",
#"makeplots",
#"export",
#"listspecs",
#"manualcalibrate",
#"autocalibrate",
#"parameterscenario",
#"saveproject",
#"loadproject",
]

# Define plotting variables in case plots are generated
if test == "sir":
    test_vars = ["sus", "inf", "rec", "dead", "ch_all", "foi"]
    test_pop = "adults"
    decomp = ["sus", "inf", "rec", "dead"]
    deaths = ["sus:dead", "inf:dead", "rec:dead"]
    grouped_deaths = {'inf': ['inf:dead'], 'sus': ['sus:dead'], 'rec': ['rec:dead']}  # As rec-dead does not have a unique link tag, plotting rec-dead separately would require actually extracting its link object
    plot_pop = [test_pop]
if test == "tb":
    test_vars = ["sus", "vac", "spdu", "alive", "b_rate"]
    test_pop = "0-4"
    decomp = ["sus", "vac", "lt_inf", "ac_inf", "acr"]
    # Just do untreated TB-related deaths for simplicity.
    deaths = ["pd_term:flow", "pd_sad:flow", "nd_term:flow", "nd_sad:flow", "pm_term:flow", "pm_sad:flow", "nm_term:flow", "nm_sad:flow", "px_term:flow", "px_sad:flow", "nx_term:flow", "nx_sad:flow"]
    grouped_deaths = {"ds_deaths": ["pd_term:flow", "pd_sad:flow", "nd_term:flow", "nd_sad:flow"],
                      "mdr_deaths": ["pm_term:flow", "pm_sad:flow", "nm_term:flow", "nm_sad:flow"],
                      "xdr_deaths": ["px_term:flow", "px_sad:flow", "nx_term:flow", "nx_sad:flow"]}
    plot_pop = ['5-14', '15-64']

tmpdir = "." + os.sep + "temp" + os.sep

if "makeframeworkfile" in torun:
    if test == "sir": args = {"num_comps":4, "num_characs":8, "num_pars":6}
    elif test == "tb": args = {"num_comps":40, "num_characs":70, "num_pars":140, "num_datapages":10}
    au.ProjectFramework.create_template(path=tmpdir + "framework_" + test + "_blank.xlsx", **args)
        
if "makeframework" in torun:
    F = au.ProjectFramework(name=test.upper(), filepath="./frameworks/framework_" + test + ".xlsx")

if "saveframework" in torun:
    F.save(tmpdir+test+".frw")

if "loadframework" in torun:
    F = au.ProjectFramework.load(tmpdir+test+".frw")

if "makedatabook" in torun:
    P = au.Project(framework=F) # Create a project with an empty data structure.
    if test == "sir": args = {"num_pops":1, "num_trans":1, "num_progs":3,
                              "data_start":2000, "data_end":2015, "data_dt":1.0}
    elif test == "tb": args = {"num_pops":12, "num_trans":5, "num_progs":31, "data_end":2018}
    P.create_databook(databook_path=tmpdir + "databook_" + test + "_blank.xlsx", **args)

if "makeproject" in torun:
    # Preventing a run and databook loading so as to make calls explicit for the benefit of the FE.
    P = au.Project(name=test.upper()+" project", framework=F, do_run=False)
    
if "loaddatabook" in torun:
    # Preventing parset creation and a run so as to make calls explicit for the benefit of the FE.
    P.load_databook(databook_path="./databooks/databook_" + test + ".xlsx", make_default_parset=False, do_run=False)
    
if "makeparset" in torun:
    P.make_parset(name="default")
    
if "runsim" in torun:
    P.update_settings(sim_start=2000.0, sim_end=2030, sim_dt=0.25)
    P.run_sim(parset="default", result_name="default")
    
if "makeprogramspreadsheet" in torun:
    print('Making programs spreadsheet ... NOT CURRENTLY WORKING!!!! It will write a sheet, but the format isn''t right')

    P = au.demo(which=test,do_plot=0)
    filename = "temp/programspreadsheet.xlsx"
    comps = [c['label'] for c in P.framework.specs['comp'].values()]
#    makeprogramspreadsheet(filename, pops=2, comps=comps, progs=5)
    au.makeprogramspreadsheet(filename, pops=2, comps=comps, progs=5)

if "loadprogramspreadsheet" in torun:
    if test=='tb':
        print('\n\n\nLoading program spreadsheet not yet implemented for TB.')
    else:
        print('\n\n\nLoading programs spreadsheet ...')
    
        P = au.demo(which=test,do_plot=0)
        filename = "databooks/programdata_"+test+".xlsx"
        P.load_progbook(databook_path=filename, make_default_progset=True)
        
        coverage = sc.odict([('Risk avoidance',     .99),
                             ('Harm reduction 1',   .8),
                             ('Harm reduction 2',   .9),
                             ('Treatment 1',        .99),
                             ('Treatment 2',        .8)])
        print(P.progsets[0].get_outcomes(coverage)) # NB, calculations don't quite make sense atm, need to work in the impact interactions

if "makeplots" in torun:

    # Low level debug plots.
    for var in test_vars:
        P.results["default"].get_variable(test_pop,var)[0].plot()
    
    # Plot population decomposition.
    d = au.PlotData(P.results["default"],outputs=decomp,pops=plot_pop)
    au.plot_series(d, plot_type="stacked")

    if test == "tb":
        # TODO: Decide how to deal with aggregating parameters that are not transition-related, i.e. flows.
        # Plot bars for deaths, aggregated by strain, stacked by pop
        d = au.PlotData(P.results["default"],outputs=grouped_deaths,t_bins=10,pops=plot_pop)
        au.plot_bars(d, outer="results", stack_pops=[plot_pop])

        # Plot bars for deaths, aggregated by pop, stacked by strain
        d = au.PlotData(P.results["default"],outputs=grouped_deaths,t_bins="all",pops=plot_pop)
        au.plot_bars(d, stack_outputs=[list(grouped_deaths.keys())])

        # Plot total death flow over time
        # Plot death flow rate decomposition over all time
        d = au.PlotData(P.results["default"],outputs=grouped_deaths,pops=plot_pop)
        au.plot_series(d, plot_type='stacked', axis='outputs')
    elif test == 'sir':
        # Plot disaggregated flow into deaths over time
        d = au.PlotData(P.results["default"],outputs=grouped_deaths,pops=plot_pop)
        au.plot_series(d, plot_type='stacked', axis='outputs')


    # Plot aggregate flows
    d = au.PlotData(P.results["default"],outputs=[{"Death rate":deaths}])
    au.plot_series(d, axis="pops")


if "export" in torun:
    P.results["default"].export(tmpdir+test+"_results")
    
if "listspecs" in torun:
    # For the benefit of FE devs, to work out how to list framework-related items in calibration and scenarios.
    FS = au.FrameworkSettings
    DS = au.DataSettings
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
    P.parsets.copy("default", "manual")
    if test == "sir":
        P.parsets["manual"].set_scaling_factor(par_name="transpercontact", pop_name="adults", scale=0.5)
        outputs = ["ch_prev"]
    if test == "tb":
        P.parsets["manual"].set_scaling_factor(par_name="foi", pop_name="15-64", scale=2.0)
        outputs = ["ac_inf"]
    P.run_sim(parset="manual", result_name="manual")
    d = au.PlotData([P.results["default"],P.results["manual"]], outputs=outputs, pops=plot_pop)
    au.plot_series(d, axis="results", data=P.data)
    
if "autocalibrate" in torun:
    # Manual fit was not good enough according to plots, so run autofit.
    if test == "sir":
        # Explicitly specify full tuples for inputs and outputs, with 'None' for pop denoting all populations
        adjustables = [("transpercontact", None, 0.1, 1.9)]         # Absolute scaling factor limits.
        measurables = [("ch_prev", "adults", 1.0, "fractional")]        # Weight and type of metric.
        # New name argument set to old name to do in-place calibration.
        P.calibrate(parset="default", new_name="auto", adjustables=adjustables, measurables=measurables, max_time=30)
    if test == "tb":
        # Shortcut for calibration measurables.
        adjustables = [("foi", "15-64", 0.0, 3.0)]
        P.calibrate(parset="default", new_name="auto", adjustables=adjustables, measurables=["ac_inf"], max_time=30)
    P.run_sim(parset="auto", result_name="auto")
    d = au.PlotData(P.results, outputs=outputs)   # Values method used to plot all existent results.
    au.plot_series(d, axis='results', data=P.data)
    
if "parameterscenario" in torun:
    scvalues = dict()
    if test == "sir":
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
    P.run_scenario(scenario="varying_infections", parset="default", result_name="scen1")

    # Insert two values and eliminate everything between them.
    scvalues[scen_par][scen_pop]["y"] = [0.125, 0.5]
    scvalues[scen_par][scen_pop]["t"] = [2015., 2020.]
    scvalues[scen_par][scen_pop]["smooth_onset"] = [2, 3]

    P.make_scenario(name="varying_infections2", instructions=scvalues)
    P.run_scenario(scenario="varying_infections2", parset="default", result_name="scen2")

    d = au.PlotData([P.results["scen1"],P.results["scen2"]], outputs=scen_outputs, pops=[scen_pop])
    au.plot_series(d, axis="results")
    
if "saveproject" in torun:
    P.save(tmpdir+test+".prj")

if "loadproject" in torun:
    P = au.Project.load(tmpdir+test+".prj")