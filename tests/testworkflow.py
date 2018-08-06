"""
Version:
"""

import logging
logger = logging.getLogger()

import os
import atomica.ui as au
import sciris.core as sc
import pylab as pl
import matplotlib.pyplot as plt
from atomica.core.optimization import optimize

test = "sir"
# test = "tb"
# test = "diabetes"
#test = "service"


torun = [
# "makeframework",
# "saveframework",
# "loadframework",
# "makedatabook",
# "makeproject",
# "loaddatabook",
# "makeparset",
# "runsim",
# 'plotcascade',
# "makeprogramspreadsheet",
#"loadprogramspreadsheet",
#"runsim_programs",
# "makeplots",
# "export",
# "listspecs",
# "manualcalibrate",
#"autocalibrate",
# "parameterscenario",
# 'budgetscenarios',
'optimization',
# "saveproject",
# "loadproject",
]

forceshow = True # Whether or not to force plots to show (warning, only partly implemented)

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

if "makeframework" in torun:
    F = au.ProjectFramework("./frameworks/framework_" + test + ".xlsx")

if "saveframework" in torun:
    F.save(tmpdir+test+".frw")

if "loadframework" in torun:
    F = au.ProjectFramework.load(tmpdir+test+".frw")

if "makedatabook" in torun:
    P = au.Project(framework=F) # Create a project with an empty data structure.
    if test == "sir": args = {"num_pops":1, "num_transfers":1,"data_start":2000, "data_end":2015, "data_dt":1.0}
    elif test == "tb": args = {"num_pops":12, "num_transfers":3, "data_end":2018}
    elif test == "diabetes": args = {"num_pops":1, "num_transfers":0, "data_start":2014, "data_end":2017, "data_dt":1.0}
    elif test == "service": args = {"num_pops":1, "num_transfers":0,"data_start":2014, "data_end":2017, "data_dt":1.0}
    P.create_databook(databook_path=tmpdir + "databook_" + test + "_blank.xlsx", **args)

if "makeproject" in torun:
    # Preventing a run and databook loading so as to make calls explicit for the benefit of the FE.
    P = au.Project(name=test.upper()+" project", framework=F, do_run=False)
    
if "loaddatabook" in torun:
    # Preventing parset creation and a run so as to make calls explicit for the benefit of the FE.
    P.load_databook(databook_path="./databooks/databook_" + test + ".xlsx", make_default_parset=False, do_run=False)
    
if "makeparset" in torun:
    if test in ['di2abetes']:
        print('\n\n\nDatabook not yet filled in for diabetes example.')
    else:
        P.make_parset(name="default")
    
if "runsim" in torun:
    if test in ["tb"]:
        P.update_settings(sim_start=2000.0, sim_end=2030, sim_dt=0.25)
    elif test=='diabetes':
        print('\n\n\nWARNING, diabetes example does not run yet... need to debug')
        P.update_settings(sim_start=2014.0, sim_end=2020, sim_dt=1.)
    else:
        P.update_settings(sim_start=2014.0, sim_end=2020, sim_dt=1.)

    P.run_sim(parset="default", result_name="default")    
    cascade = P.results[-1].get_cascade_vals(cascade='main', pops='all', t_bins=2020)

if 'plotcascade' in torun:
    au.plot_cascade(P.results[-1], cascade='main', pops='all', year=2020)
    if forceshow: pl.show()
    
    # Browser test
    as_mpld3 = True
    if as_mpld3:
        import sciris.weblib.quickserver as sqs
        fig = pl.gcf()
        sqs.browser(fig)
    
if "makeprogramspreadsheet" in torun:
    print('\n\n\nMaking programs spreadsheet ... ')
    P = au.demo(which=test, do_plot=0, do_run=False)
    filename = "temp/progbook_"+test+"_blank.xlsx"
    if test == "tb":
        P.make_progbook(filename, progs=29)
    elif test == "diabetes":
        P.make_progbook(filename, progs=14)
    else:
        P.make_progbook(filename, progs=5)


if "loadprogramspreadsheet" in torun:
    if test in ['diabetes','service']:
        print('\n\n\nLoading program spreadsheet not yet implemented for TB, diabetes or service examples.')
    else:
        print('\n\n\nLoading programs spreadsheet ...')
    
        P = au.demo(which=test,do_plot=0)
        filename = "databooks/progbook_"+test+".xlsx"
        blh_effects = False if test=='tb' else True
        P.load_progbook(progbook_path=filename, make_default_progset=True, blh_effects=blh_effects)

        P.progsets[0].programs[0].get_spend(year=2015)

        if test =="sir":      

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

        elif test =="tb":      

            # For a whole parset, demonstrate how to get a dictionary of proportion covered for each program given a time vector and denominators
            denominator = sc.odict([('BCG',             [9e6]),
                                    ('MS-PHC',          [9e6]),
                                    ('ENH-MS-PHC',      [9e6]),
                                    ('MS-HR',           [9e6]),
                                    ('CT-DS',           [9e6]),
                                    ('CT-DR',           [9e6]),
                                    ('ACF-PLHIV',       [9e6]),
                                    ('DS-TB',           [9e6]),
                                    ('Old MDR',         [9e6]),
                                    ('Old MDR/BDQ',     [9e6]),
                                    ('MDR/BDQ',         [9e6]),
                                    ('KM-SC',           [9e6]),
                                    ('BDQ-SC',          [9e6]),
                                    ('XDR-Current',     [9e6]),
                                    ('XDR-new',         [9e6]),
                                    ('PLHIV/DS-TB',     [9e6]),
                                    ('PLHIV/Old MDR',   [9e6]),
                                    ('PLHIV/Old MDR-BDQ',[9e6]),
                                    ('PLHIV/New MDR',   [9e6]),
                                    ('PLHIV/Old XDR',   [9e6]),
                                    ('PLHIV/New XDR',   [9e6]),
                                    ('Pris DS-TB',      [9e6]),
                                    ('Pris MDR',        [9e6]),
                                    ('Pris XDR',        [9e6]),
                                    ('Min DS-TB',       [9e6]),
                                    ('Min MDR',         [9e6]),
                                    ('Min XDR',         [9e6]),
                                    ('PCF-HIV-',        [9e6]),
                                    ('PCF-HIV+',        [9e6])])

            print(P.progsets[0].get_num_covered(year=[2017]))
            print(P.progsets[0].get_prop_covered(year=[2017],denominator = denominator))


if "runsim_programs" in torun:

    P = au.demo(which=test,do_plot=0)

    if test == 'sir':
        P.update_settings(sim_start=2000.0, sim_end=2030, sim_dt=0.25)
        alloc  = {'Risk avoidance': 400000} # Other programs will use default spend
        instructions = au.ProgramInstructions() 
        instructions = au.ProgramInstructions(alloc) # TODO - get default instructions
        P.run_sim(parset="default", result_name="default-noprogs")
        P.run_sim(parset="default", progset='default',progset_instructions=instructions,result_name="default-progs")
        d = au.PlotData([P.results["default-noprogs"],P.results["default-progs"]], outputs=['transpercontact','contacts','recrate','infdeath','susdeath'])
        au.plot_series(d, axis="results")

    elif test == 'tb':
        instructions = au.ProgramInstructions(start_year=2015,stop_year=2030) 
#        P.run_sim(parset="default", result_name="default-noprogs")
        P.run_sim(parset="default", progset='default',progset_instructions=instructions,result_name="default-progs")

    elif test in ['diabetes','service']:
        print('\n\n\nRunning with programs not yet implemented for diabetes or service examples.')

    else:
        print('\n\n\nUnknown test.')

if "makeplots" in torun:

    # Low level debug plots.
    for var in test_vars:
        P.results["parset_default"].get_variable(test_pop,var)[0].plot()
    
    # Plot population decomposition.
    d = au.PlotData(P.results["parset_default"],outputs=decomp,pops=plot_pop)
    au.plot_series(d, plot_type="stacked")

    if test == "tb":
        # Plot bars for deaths, aggregated by strain, stacked by pop
        d = au.PlotData(P.results["parset_default"],outputs=grouped_deaths,t_bins=10,pops=plot_pop)
        au.plot_bars(d, outer="results", stack_pops=[plot_pop])

        # Plot bars for deaths, aggregated by pop, stacked by strain
        d = au.PlotData(P.results["parset_default"],outputs=grouped_deaths,t_bins="all",pops=plot_pop)
        au.plot_bars(d, stack_outputs=[list(grouped_deaths.keys())])

        # Plot total death flow over time
        # Plot death flow rate decomposition over all time
        d = au.PlotData(P.results["parset_default"],outputs=grouped_deaths,pops=plot_pop)
        au.plot_series(d, plot_type='stacked', axis='outputs')

        d = au.PlotData(P.results["parset_default"], pops='0-4')
        au.plot_series(d, plot_type='stacked')

    elif test == 'sir':
        # Plot disaggregated flow into deaths over time
        d = au.PlotData(P.results["parset_default"],outputs=grouped_deaths,pops=plot_pop)
        au.plot_series(d, plot_type='stacked', axis='outputs')

    # Plot aggregate flows
    d = au.PlotData(P.results["parset_default"],outputs=[{"Death rate":deaths}])
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
#    if test == "sir":
#        # Explicitly specify full tuples for inputs and outputs, with 'None' for pop denoting all populations
#        adjustables = [("transpercontact", None, 0.1, 1.9)]         # Absolute scaling factor limits.
#        measurables = [("ch_prev", "adults", 1.0, "fractional")]        # Weight and type of metric.
#        # New name argument set to old name to do in-place calibration.
#        P.calibrate(parset="default", new_name="auto", adjustables=adjustables, measurables=measurables, max_time=30)
#    if test == "tb":
#        # Shortcut for calibration measurables.
#        adjustables = [("foi", "15-64", 0.0, 3.0)]
#        P.calibrate(parset="default", new_name="auto", adjustables=adjustables, measurables=["ac_inf"], max_time=30)
    P.calibrate(max_time=10, new_name="auto")
    P.run_sim(parset="auto", result_name="auto")
    if test == "sir":
        outputs = ["ch_prev"]
    if test == "tb":
        outputs = ["ac_inf"]
    d = au.PlotData(P.results, outputs=outputs)   # Values method used to plot all existent results.
    au.plot_series(d, axis='results', data=P.data)
    
if "parameterscenario" in torun:
    
    P = au.demo(which=test)
    
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
    scvalues[scen_par][scen_pop]["y"] = [0.125,0.15]
    scvalues[scen_par][scen_pop]["t"] = [2015., 2020.]
    scvalues[scen_par][scen_pop]["smooth_onset"] = 2

    P.make_scenario(which='parameter',name="Varying Infections", instructions=scvalues)
    P.run_scenario(scenario="Varying Infections", parset="default")

    # Insert two values and eliminate everything between them.
    scvalues[scen_par][scen_pop]["y"] = [0.125, 0.5]
    scvalues[scen_par][scen_pop]["t"] = [2015., 2020.]
    scvalues[scen_par][scen_pop]["smooth_onset"] = [2, 3]

    P.make_scenario(which='parameter',name="Varying Infections 2", instructions=scvalues)
    P.run_scenario(scenario="Varying Infections 2", parset="default")

    d = au.PlotData([P.results["Varying Infections"],P.results["Varying Infections 2"]], outputs=scen_outputs, pops=[scen_pop],project=P)
    au.plot_series(d, axis="results")
    plt.title('Scenario comparison')
    plt.ylabel('Number of people')


def supported_plots_func():
    ''' TEMP '''
    supported_plots = {
            'Population size':'alive',
            'Latent infections':'lt_inf',
            'Active TB':'ac_inf',
            'Active DS-TB':'ds_inf',
            'Active MDR-TB':'mdr_inf',
            'Active XDR-TB':'xdr_inf',
            'New active DS-TB':{'New active DS-TB':['pd_div:flow','nd_div:flow']},
            'New active MDR-TB':{'New active MDR-TB':['pm_div:flow','nm_div:flow']},
            'New active XDR-TB':{'New active XDR-TB':['px_div:flow','nx_div:flow']},
            'Smear negative active TB':'sn_inf',
            'Smear positive active TB':'sp_inf',
            'Latent diagnoses':{'Latent diagnoses':['le_treat:flow','ll_treat:flow']},
            'New active TB diagnoses':{'Active TB diagnoses':['pd_diag:flow','pm_diag:flow','px_diag:flow','nd_diag:flow','nm_diag:flow','nx_diag:flow']},
            'New active DS-TB diagnoses':{'Active DS-TB diagnoses':['pd_diag:flow','nd_diag:flow']},
            'New active MDR-TB diagnoses':{'Active MDR-TB diagnoses':['pm_diag:flow','nm_diag:flow']},
            'New active XDR-TB diagnoses':{'Active XDR-TB diagnoses':['px_diag:flow','nx_diag:flow']},
            'Latent treatment':'ltt_inf',
            'Active treatment':'num_treat',
            'TB-related deaths':':ddis',
            }
    return supported_plots

#def get_plots(proj, results=None, plot_names=None, pops='all', axis=None, outputs=None, plotdata=None):
#    results = sc.promotetolist(results)
#    supported_plots = supported_plots_func() 
#    if plot_names is None: plot_names = supported_plots.keys()
#    plot_names = sc.promotetolist(plot_names)
#    if outputs is None:
#        outputs = [supported_plots[plot_name] for plot_name in plot_names]
#    data = proj.data if plotdata is not False else None # Plot data unless asked not to
#    all_figs = []
#    for output in outputs:
#        try:
#            import numpy as np # TEMP
#            plotdata = au.PlotData(results, outputs=output, project=proj, pops=pops)
#            for series in plotdata.series:
#                if any(np.isnan(series.vals)):
#                    print('NANS?????????!!')
#                    print series.vals
#            figs = au.plot_series(plotdata, data=data, axis=axis) # Todo - customize plot formatting here
#            all_figs += sc.promotetolist(figs)
#            print('Plot %s succeeded' % (output))
#        except Exception as E:
#            print('WARNING: plot %s failed (%s)' % (output, repr(E)))
#
#    return all_figs

def get_plots(proj, results=None, plot_names=None, pops='all', axis=None, outputs=None, plotdata=None, replace_nans=True):
    import numpy as np
    results = sc.promotetolist(results)
    supported_plots = supported_plots_func() 
    if plot_names is None: plot_names = supported_plots.keys()
    plot_names = sc.promotetolist(plot_names)
    if outputs is None:
        outputs = [supported_plots[plot_name] for plot_name in plot_names]
    graphs = []
    data = proj.data if plotdata is not False else None # Plot data unless asked not to
    for output in outputs:
        try:
            plotdata = au.PlotData(results, outputs=output, project=proj, pops=pops)
            nans_replaced = 0
            series_list = sc.promotetolist(plotdata.series)
            for series in series_list:
                if replace_nans and any(np.isnan(series.vals)):
                    nan_inds = sc.findinds(np.isnan(series.vals))
                    for nan_ind in nan_inds:
                        if nan_ind>0: # Skip the first point
                            series.vals[nan_ind] = series.vals[nan_ind-1]
                            nans_replaced += 1
            if nans_replaced:
                print('Warning: %s nans were replaced' % nans_replaced)
            figs = au.plot_series(plotdata, data=data, axis=axis) # Todo - customize plot formatting here
            graphs += figs
            print('Plot %s succeeded' % (output))
        except Exception as E:
            print('WARNING: plot %s failed (%s)' % (output, repr(E)))
            import traceback; traceback.print_exc(); import pdb; pdb.set_trace()

    return graphs


if 'budgetscenarios' in torun: # WARNING, assumes that default scenarios are budget scenarios
    browser = False # Display as mpld3 plots in the browser
    plot_option = 2
    scen_outputs = ["lt_inf", "ac_inf"]
    scen_pop = "15-64"
    P = au.demo(which='tb')
    results = P.run_scenarios()
    if plot_option == 1:
        d = au.PlotData(results, outputs=scen_outputs, pops=[scen_pop])
        figs = au.plot_series(d, axis="results")
    elif plot_option == 2:
        figs = get_plots(P, results, axis="results")
    if browser:
        from sciris.weblib import quickserver as qs
        qs.browser(figs)
    

if "optimization" in torun:
    if test == 'tb':
        P = au.demo(which='tb')
        P.run_optimization(maxtime=30)
    elif test == 'sir':
        P = au.demo(which='sir')
        P.load_progbook(progbook_path="databooks/progbook_" + test + ".xlsx", make_default_progset=True)

        alloc = sc.odict([('Risk avoidance',0.),
                         ('Harm reduction 1',0.),
                         ('Harm reduction 2',0.),
                         ('Treatment 1',50.),
                         ('Treatment 2', 1.)])

        instructions = au.ProgramInstructions(alloc=alloc,start_year=2020) # Instructions for default spending
        adjustments = []
        adjustments.append(au.SpendingAdjustment('Treatment 1',2020,'abs',0.,100.))
        adjustments.append(au.SpendingAdjustment('Treatment 2',2020,'abs',0.,100.))
        constraints = au.TotalSpendConstraint() # Cap total spending in all years

        ## CASCADE MEASURABLE
        # This measurable will maximize the number of people in the final cascade stage, whatever it is
        measurables = au.MaximizeCascadeFinalStage('main',[2030],pop_names='all') # NB. make sure the objective year is later than the program start year, otherwise no time for any changes

        # This is the same as the 'standard' example, just running the optimization and comparing the results
        optimization = au.Optimization(name='default', adjustments=adjustments, measurables=measurables, constraints=constraints)
        unoptimized_result = P.run_sim(parset=P.parsets["default"], progset=P.progsets['default'], progset_instructions=instructions, result_name="unoptimized")
        optimized_instructions = optimize(P, optimization, parset=P.parsets["default"], progset=P.progsets['default'], instructions=instructions)
        optimized_result = P.run_sim(parset=P.parsets["default"], progset=P.progsets['default'], progset_instructions=optimized_instructions, result_name="optimized")

        for adjustable in adjustments:
            print("%s - before=%.2f, after=%.2f" % (adjustable.name,unoptimized_result.model.program_instructions.alloc[adjustable.name].get(2020),optimized_result.model.program_instructions.alloc[adjustable.name].get(2020))) # TODO - add time to alloc

        au.plot_multi_cascade([unoptimized_result, optimized_result],'main',pops='all',year=2020)

if "runsimprogs" in torun:
    from atomica.core.programs import ProgramInstructions

    # instructions = ProgramInstructions(progset=P.progsets["default"])
    P.run_sim(parset="default", progset="default", progset_instructions=ProgramInstructions(), result_name="progtest")
    
if "saveproject" in torun:
    P.save(tmpdir+test+".prj")

if "loadproject" in torun:
    P = au.Project.load(tmpdir+test+".prj")

