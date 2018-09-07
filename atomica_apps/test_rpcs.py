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
import json

torun = [
'project_io',
#'get_cascade_plot',
#'get_cascade_json',
#'get_plots',
#'run_cascade_optimization',
#'run_tb_optimization',
]

# Set parameters
tool = ['tb','cascade'][1] # Change this to change between TB and Cascade
default_which = {'tb':'tb', 'cascade':'hypertension'}
user_id = '12345678123456781234567812345678' # This is the hard-coded UID of the "demo" user


###########################################################################
### Initialization and definitions
###########################################################################

T = sc.tic()

app = main.make_app(which=tool)

def demoproj(which=None):
    if which is None: which = default_which[tool]
    P = au.demo(which=which)
    return P

def heading(string, style=None):
    divider = '#'*60
    sc.blank()
    if style == 'big': string = '\n'.join([divider, string, divider])
    sc.colorize('blue', string)
    return None

###########################################################################
### Run the tests
###########################################################################

if 'project_io' in torun:
    if proj is None: proj = demoproj('hypertension')
    uid = rpcs.save_project_as_new(proj, user_id=user_id)
    P = rpcs.load_project_record(uid)
    print(P)



if 'get_cascade_plot' in torun:
    if proj is None: proj = demoproj('hypertension')
    results = proj.run_optimization(maxtime=3)
    args = {
        'results':results, 
        'pops':   'All', 
        'year':   2030, 
        'cascade': None, 
        'plot_budget': True
        }
    output = rpcs.get_cascade_plot(proj, **args)
    print('Output:')
    print(output)
    sw.browser(jsons=output[0]['graphs'])


if 'get_cascade_json' in torun:
    dosave = True
    filename = 'cascade.json'
    if proj is None: proj = demoproj('hypertension')
    results = proj.run_optimization(maxtime=3)
    output = rpcs.get_json_cascade(results, proj.data)
    print('Output:')
    print(output)
    if dosave:
        with open(filename,'w') as f:
            json.dump(sw.sanitize_json(output), f)
            print('JSON saved to %s' % filename)


if 'get_plots' in torun:
    if proj is None: proj = demoproj('tb')
    results = proj.run_sim()
    output = rpcs.get_plots(proj, results=results, calibration=True)
    print('Output:')
    print(output)


if 'run_cascade_optimization' in torun:
    maxtime = 10
    if proj is None: proj = demoproj('hypertension')
    output = atca.run_cascade_optimization(proj, 'dummy_cache_ID', maxtime=maxtime, online=True)
    print('Output:')
    print(output)
    
    
if 'run_tb_optimization' in torun:
    maxtime = 10
    if proj is None: proj = demoproj('tb')
    output = attb.run_tb_optimization(proj, maxtime=maxtime, online=False)
    print('Output:')
    print(output)
    

sc.toc(T)
print('Done.')