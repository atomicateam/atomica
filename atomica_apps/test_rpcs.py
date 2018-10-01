"""
Version:
"""

###########################################################################
### Housekeeping
###########################################################################

torun = [
#'slack',
#'project_io',
#'get_cascade_plot',
#'get_cascade_json',
#'make_plots',
#'get_y_factors',
#'autocalibration',
#'run_scenarios',
#'run_cascade_optimization',
#'run_tb_optimization',
# 'minimize_money',
#'default_programs',
'parameter_scenario',
]

# Set defaults
tool = ['tb','cascade'][0] # Change this to change between TB and Cascade
default_which = {'tb':'tb', 'cascade':'hypertension'}[tool]

# Imports
import sciris as sc
import scirisweb as sw
import atomica.ui as au
from atomica_apps import rpcs, main
if tool == 'cascade': from atomica_apps import config_cascade as config, apptasks_cascade as appt
elif tool == 'tb':    from atomica_apps import config_tb      as config, apptasks_tb      as appt


###########################################################################
### Definitions
###########################################################################

def demoproj(proj_id, username, which=None):
    if which is None: which = default_which
    P = au.demo(which=which)
    P.name = 'RPCs test %s' % proj_id[:6]
    P.uid = sc.uuid(proj_id)
    P = rpcs.cache_results(P)
    rpcs.save_new_project(P, username, uid=P.uid) # Force a matching uid
    proj = rpcs.load_project(P.uid) # Since some operations get performed on it while it's being saved
    return proj

def heading(string, style=None):
    divider = '='*60
    sc.blank()
    if style == 'big': string = '\n'.join([divider, string, divider])
    sc.colorize('blue', string)
    return None

# Launch app
T = sc.tic()
app = main.make_app(which=tool)
user = sw.make_default_users(app)[0]
proj_id  = sc.uuid(tostring=True)
cache_id = sc.uuid(tostring=True)
proj = demoproj(proj_id, user.username, which=default_which)
datastore = rpcs.find_datastore(config=config)


###########################################################################
### Run the tests
###########################################################################

string = 'Starting tests for:\n  tool = %s\n  which = %s\n  user = %s\n  proj = %s' % (tool, default_which, user.username, proj_id)
heading(string, 'big')


if 'slack' in torun:
    app.slacknotification('Test Slack notification from test_rpcs.py')


if 'project_io' in torun:
    heading('Running project_io', 'big')
    uid = rpcs.save_new_project(proj, username=user.username)
    P = rpcs.load_project_record(uid)
    print(P)


if 'get_cascade_plot' in torun and tool=='cascade':
    heading('Running get_cascade_plot', 'big')
    browser = False
    results = proj.run_optimization(maxtime=3)
    args = {
        'results':results,
        'pops':   'All',
        'year':   2030,
        'cascade': None,
        'plot_budget': True
        }
    output, figs, legends = rpcs.get_cascade_plot(proj, **args)
    print('Output:')
    print(output)
    if browser:
        sw.browser(output['graphs'])


if 'get_cascade_json' in torun and tool=='cascade':
    heading('Running get_cascade_json', 'big')
    dosave = True
    filename = 'cascade.json'
    results = proj.run_optimization(maxtime=3)
    output = rpcs.get_json_cascade(results, proj.data)
    print('Output:')
    print(output)
    if dosave:
        sc.savejson(filename, output)
        print('JSON saved to %s' % filename)


if 'make_plots' in torun:
    heading('Running make_plots', 'big')

    # Settings
    browser     = False
    calibration = True
    verbose     = False

    # Run
    results = proj.run_sim()
    output, figs, legends = rpcs.make_plots(proj, results=results, calibration=calibration, outputfigs=True)

    # Output
    print('Output:')
    if verbose:
        sc.pp(output)
    if browser:
        sw.browser(output['graphs']+output['legends'])


if 'get_y_factors' in torun:
    output = rpcs.get_y_factors(proj_id)


if 'autocalibration' in torun:
    max_time = '30'
    output = rpcs.automatic_calibration(proj_id, cache_id, parsetname=-1, max_time=max_time, saveresults=True, plot_options=None, tool=tool, plotyear=None, pops=None,cascade=None, dosave=True)


if 'export_results' in torun:
    # This test validates exporting Excel files from Result objects
    proj = demoproj('tb')
    results = proj.demo_scenarios(dorun=True)
    au.export_results(results,'test_rpcs_export_results.zip')


if 'run_scenarios' in torun:
    browser = True
    output = rpcs.run_scenarios(proj_id, cache_id, tool='cascade')
    sc.pp(output)
    if browser:
        sw.browser(output['graphs']+output['legends'])


if 'run_cascade_optimization' in torun and tool=='cascade':
    heading('Running run_cascade_optimization', 'big')
    browser = True
    maxtime = 5
    optim_summaries = rpcs.get_optim_info(proj_id)
    rpcs.set_optim_info(proj_id, optim_summaries)
    output = appt.run_cascade_optimization(proj_id, cache_id, maxtime=maxtime, online=True)
    print('Output:')
    sc.pp(output)
    if browser:
        sw.browser(output['graphs']+output['legends'])


if 'run_tb_optimization' in torun and tool=='tb':
    heading('Running run_tb_optimization', 'big')
    browser = True
    maxtime = 10
    optim_summaries = rpcs.get_optim_info(proj_id)
    rpcs.set_optim_info(proj_id, optim_summaries)
    output = appt.run_tb_optimization(proj_id, cache_id, pops='All', tool='tb', maxtime=maxtime, online=True)
    print('Output:')
    sc.pp(output)
    if browser:
        sw.browser(output['graphs']+output['legends'])


if 'minimize_money' in torun and tool=='tb':
    browser = False
    results = proj.demo_optimization(dorun=True,tool=tool,optim_type='money')


if 'default_programs' in torun:
    progyears = [2015,2017]
    active_progs = rpcs.get_default_programs()
    rpcs.create_default_progbook(proj_id, progyears, active_progs=active_progs)
    print(active_progs)


if 'parameter_scenario' in torun:
    # These populate the FE
    parsetname='default'
    start_year = 2018 # Populate this from the dropdown
    scen_pars = rpcs.get_parscen_params(proj,parsetname,start_year)

    # These are supplied by the user in the FE
    end_year = 2025
    fe_scen_pars = sc.odict()
    for k,v in scen_pars.items():
        fe_scen_pars[k] = [v,None]
    baseline_scen = sc.dcp(fe_scen_pars)
    fe_scen_pars[('Early latency departure rate','Children 0-4')][1] = fe_scen_pars[('Early latency departure rate','Children 0-4')][0]*0.5

    # Make and add the scenarios
    rpcs.make_par_scen(proj, 'Baseline', parsetname, start_year, end_year, baseline_scen)
    rpcs.make_par_scen(proj, 'Scenario', parsetname, start_year, end_year, fe_scen_pars)

    # Run and plot results
    for scen in proj.scens.values():
        if isinstance(scen,au.ParameterScenario):
            scen.active = True
        else:
            scen.active = False
    results = proj.run_scenarios() # Run all the scenarios marked 'active' - for running parameter scenarios, can set 'active' based on the type
    # rpcs.make_plots(proj,results,tool='tb') # Differences depends on what the changes made above are, maybe make some more drastic changes

    d = au.PlotData(results,outputs='e_dep',pops='0-4')
    figs = au.plot_series(d,axis='results')
    au.save_figs(figs)

sc.toc(T)
print('Done.')