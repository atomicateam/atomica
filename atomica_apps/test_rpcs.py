"""
Version:
"""

###########################################################################
### Housekeeping
###########################################################################

import pylab as pl
import sciris as sc
import scirisweb as sw
import atomica.ui as au
from atomica_apps import rpcs, apptasks_cascade as atca, apptasks_tb as attb, main
pl.switch_backend('Qt4Agg')

torun = [
#'project_io',
#'get_cascade_plot',
#'get_cascade_json',
'make_plots',
#'run_cascade_optimization',
#'run_tb_optimization',
]

# Set parameters
tool = ['tb','cascade'][0] # Change this to change between TB and Cascade
default_which = {'tb':'tb', 'cascade':'hypertension'}[tool]
user_id  = '12345678123456781234567812345678' # This is the hard-coded UID of the "demo" user
proj_id  = sc.uuid(as_string=True) # These can all be the same
cache_id = sc.uuid(as_string=True) # These can all be the same


###########################################################################
### Definitions
###########################################################################

def demoproj(which=None, online=True):
    if which is None: which = default_which
    P = au.demo(which=which)
    if online:
        rpcs.save_project_as_new(P, user_id=user_id, uid=proj_id)
        rpcs.make_results_cache_entry(cache_id)
    return P

def heading(string, style=None):
    divider = '='*60
    sc.blank()
    if style == 'big': string = '\n'.join([divider, string, divider])
    sc.colorize('blue', string)
    return None



###########################################################################
### Run the tests
###########################################################################

string = 'Starting tests for:\n  tool = %s\n  which = %s\n  user = %s\n  proj = %s' % (tool, default_which, user_id, proj_id)
heading(string, 'big')
T = sc.tic()
app = main.make_app(which=tool)
proj = demoproj(which=default_which, online=True)


if 'project_io' in torun:
    heading('Running project_io', 'big')
    uid = rpcs.save_project_as_new(proj, user_id=user_id)
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
    browser = True
    calibration = True
#    results = proj.run_sim()
#    output = proj.plot(results) # WARNING, doesn't work
    output, figs, legends = rpcs.make_plots(proj, results=results, calibration=calibration, outputfigs=True)
    print('Output:')
    print(output)
    if browser:
        sw.browser(output['graphs'])


if 'run_cascade_optimization' in torun and tool=='cascade':
    heading('Running run_cascade_optimization', 'big')
    maxtime = 10
    output = atca.run_cascade_optimization(proj_id, cache_id, maxtime=maxtime, online=True)
    print('Output:')
    print(output)
    
    
if 'run_tb_optimization' in torun and tool=='tb':
    heading('Running run_tb_optimization', 'big')
    maxtime = 10
    output = attb.run_tb_optimization(proj_id, cache_id, maxtime=maxtime, online=True)
    print('Output:')
    print(output)
    

sc.toc(T)
print('Done.')