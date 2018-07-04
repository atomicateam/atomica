"""
Version:
"""

import logging
logger = logging.getLogger()

## Write the log to a file
# h = logging.FileHandler('testworkflow.log',mode='w')
# logger.addHandler(h)

## Setting DEBUG level before importing Atomica will display the structure warnings occurring during import
# logger.setLevel('DEBUG')

import os
import atomica.ui as au
import sciris.core as sc

# Atomica has INFO level logging by default which is set when Atomica is imported, so need to change it after importing
# logger.setLevel('DEBUG')

#test = "sir"
#test = "tb"
#test = "diabetes"
test = "service"

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
'plotcascade',
"makeprogramspreadsheet",
"loadprogramspreadsheet",
"runsim_programs",
# "makeplots",
# "export",
# "listspecs",
# "manualcalibrate",
# "autocalibrate",
# "parameterscenario",
# "saveproject",
# "loadproject",
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
    elif test == "diabetes": args = {"num_comps":13, "num_characs":9, "num_pars":16}
    elif test == "service": args = {"num_comps":7, "num_characs":4, "num_pars":10}
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
    elif test == "tb": args = {"num_pops":12, "num_trans":3, "num_progs":31, "data_end":2018}
    elif test == "diabetes": args = {"num_pops":1, "num_trans":0, "num_progs":0,
                              "data_start":2014, "data_end":2017, "data_dt":1.0}
    elif test == "service": args = {"num_pops":1, "num_trans":0, "num_progs":0,
                              "data_start":2014, "data_end":2017, "data_dt":1.0}
    P.create_databook(databook_path=tmpdir + "databook_" + test + "_blank.xlsx", **args)

if "makeproject" in torun:
    # Preventing a run and databook loading so as to make calls explicit for the benefit of the FE.
    P = au.Project(name=test.upper()+" project", framework=F, do_run=False)
    
if "loaddatabook" in torun:
    if test in ['diabetes']:
        print('\n\n\nDatabook not yet filled in for diabetes example.')
    else:
        # Preventing parset creation and a run so as to make calls explicit for the benefit of the FE.
        P.load_databook(databook_path="./databooks/databook_" + test + ".xlsx", make_default_parset=False, do_run=False)
    
if "makeparset" in torun:
    if test in ['diabetes']:
        print('\n\n\nDatabook not yet filled in for diabetes example.')
    else:
        P.make_parset(name="default")
    
if "runsim" in torun:
    if test in ['diabetes']:
        print('\n\n\nDatabook not yet filled in for diabetes example.')
    else:
        if test in ["tb"]:
            P.update_settings(sim_start=2000.0, sim_end=2030, sim_dt=0.25)
        else:
            P.update_settings(sim_start=2014.0, sim_end=2020, sim_dt=1.)
        P.run_sim(parset="default", result_name="default")
        
        cascade = P.results[-1].get_cascade_vals(project=P)

if 'plotcascade' in torun:
    au.plot_cascade(project=P)
    
    
    
if "makeprogramspreadsheet" in torun:
    print('\n\n\nMaking programs spreadsheet ... ')
    if test not in ['diabetes']:
        P = au.demo(which=test, do_plot=0)
        filename = "temp/progbook_"+test+"_blank.xlsx"
        if test == "tb":
            P.make_progbook(filename, progs=31)
        else:
            P.make_progbook(filename, progs=5)

if "loadprogramspreadsheet" in torun:
    if test in ['diabetes','service']:
        print('\n\n\nLoading program spreadsheet not yet implemented for TB, diabetes or service examples.')
    else:
        print('\n\n\nLoading programs spreadsheet ...')
    
        P = au.demo(which=test,do_plot=0)
        filename = "databooks/progbook_"+test+".xlsx"
        P.load_progbook(progbook_path=filename, make_default_progset=True)
        if test not in ["tb"]:      # TODO: Test TB progset after successful progset construction.
            P.progsets[0].programs[0].get_spend(year=2015)

            # Create a sample dictionary of dummry coverage (%) values to demonstrate how get_outcomes works
            coverage = sc.odict([('Risk avoidance',     .99),
                                 ('Harm reduction 1',   .8),
                                 ('Harm reduction 2',   .9),
                                 ('Treatment 1',        .99),
                                 ('Treatment 2',        .8)])
            print(P.progsets[0].get_outcomes(coverage)) # NB, calculations don't quite make sense atm, need to work in the impact interactions

            # For a single program, demonstrate how to get a vector of number/proportion covered given a time vector, a budget (note, budget is optional!!), and denominators
            print(P.progsets[0].programs[4].get_num_covered(year=[2014,2015,2016,2017], budget=[1e5,2e5,3e5,4e5]))
            print(P.progsets[0].programs[4].get_prop_covered(year=[2014,2015,2016,2017], budget=[1e5,2e5,3e5,4e5],denominator = [1e4,1.1e4,1.2e4,1.3e4]))

            # For a whole parset, demonstrate how to get a dictionary of proportion covered for each program given a time vector and denominators
            denominator = sc.odict([('Risk avoidance',  [1e6,1.1e6,1.2e6,1.3e6]),
                                 ('Harm reduction 1',   [2e4,2.1e4,2.2e4,2.3e4]),
                                 ('Harm reduction 2',   [2e4,2.1e4,2.2e4,2.3e4]),
                                 ('Treatment 1',        [3e4,3.1e4,3.2e4,3.3e4]),
                                 ('Treatment 2',        [4e4,4.1e4,4.2e4,4.3e4])])

            print(P.progsets[0].get_num_covered(year=[2014,2015,2016,2017]))
            print(P.progsets[0].get_prop_covered(year=[2014,2015,2016,2017],denominator = denominator))


if "runsim_programs" in torun:
    if test in ['tb','diabetes','service']:
        print('\n\n\nRunning with programs not yet implemented for TB, diabetes or service examples.')
    else:
        P.update_settings(sim_start=2000.0, sim_end=2030, sim_dt=0.25)
        alloc  = {'Risk avoidance': 400000} # Other programs will use default spend
        instructions = au.ProgramInstructions() 
        instructions = au.ProgramInstructions(alloc) # TODO - get default instructions
        P.run_sim(parset="default", result_name="default-noprogs")
        P.run_sim(parset="default", progset='default',progset_instructions=instructions,result_name="default-progs")
        d = au.PlotData([P.results["default-noprogs"],P.results["default-progs"]], outputs=['transpercontact','contacts','recrate','infdeath','susdeath'])
        au.plot_series(d, axis="results")


if "makeplots" in torun:

    # Low level debug plots.
    for var in test_vars:
        P.results["default"].get_variable(test_pop,var)[0].plot()
    
    # Plot population decomposition.
    d = au.PlotData(P.results["default"],outputs=decomp,pops=plot_pop)
    au.plot_series(d, plot_type="stacked")

    if test == "tb":
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

        d = au.PlotData(P.results["default"], pops='0-4')
        au.plot_series(d, plot_type='stacked')

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

if "runsimprogs" in torun:
    from atomica.core.programs import ProgramInstructions

    # instructions = ProgramInstructions(progset=P.progsets["default"])
    P.run_sim(parset="default", progset="default", progset_instructions=ProgramInstructions(), result_name="progtest")
    
if "saveproject" in torun:
    P.save(tmpdir+test+".prj")

if "loadproject" in torun:
    P = au.Project.load(tmpdir+test+".prj")



