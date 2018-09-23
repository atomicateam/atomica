"""
Version:
"""

###########################################################################
### Housekeeping
###########################################################################

import sciris as sc
import scirisweb as sw
import atomica.ui as au
from atomica_apps import rpcs, apptasks_cascade as atca, apptasks_tb as attb, main

torun = [
'datastore',
#'project_io',
#'get_cascade_plot',
#'get_cascade_json',
#'make_plots',
#'run_scenarios',
#'run_cascade_optimization',
#'run_tb_optimization',
# 'minimize_money',
]

# Set defaults
tool = ['tb','cascade'][1] # Change this to change between TB and Cascade
default_which = {'tb':'tb', 'cascade':'hypertension'}[tool]


###########################################################################
### Definitions
###########################################################################

def demoproj(proj_id, username, which=None):
    if which is None: which = default_which
    P = au.demo(which=which)
    P.name = 'RPCs test %s' % proj_id[:6]
    P.uid = proj_id
    P = rpcs.cache_results(P)
    rpcs.save_new_project(P, username)
    return P

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
proj_id  = sc.uuid(as_string=True)
cache_id = sc.uuid(as_string=True)
proj = demoproj(proj_id, user.username, which=default_which)


###########################################################################
### Run the tests
###########################################################################

string = 'Starting tests for:\n  tool = %s\n  which = %s\n  user = %s\n  proj = %s' % (tool, default_which, user.username, proj_id)
heading(string, 'big')


if 'datastore' in torun:
    heading('Running datastore', 'big')
    ds = rpcs.find_datastore()


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
    browser     = True
    calibration = True
    show_BE     = False

    # Run
    results = proj.run_sim()
    if show_BE: output = proj.plot(results) # WARNING, doesn't work
    output, figs, legends = rpcs.make_plots(proj, results=results, calibration=calibration, outputfigs=True)

    # Output
    print('Output:')
    sc.pp(output)
    if browser:
        sw.browser(output['graphs']+output['legends'])

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
    output = atca.run_cascade_optimization(proj_id, cache_id, maxtime=maxtime, online=True)
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
    output = attb.run_tb_optimization(proj_id, cache_id, pops='All', tool='tb', maxtime=maxtime, online=True)
    print('Output:')
    sc.pp(output)
    if browser:
        sw.browser(output['graphs']+output['legends'])

if 'minimize_money' in torun and tool=='tb':
    browser = False
    results = proj.demo_optimization(dorun=True,tool=tool,optim_type='money')

sc.toc(T)
print('Done.')