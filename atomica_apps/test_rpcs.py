"""
Version:
"""

import atomica.ui as au
import atomica_apps as aa
import scirisweb as sw

torun = [
#'get_cascade_plot',
#'get_plots',
'run_cascade_optimization',
]

proj = None

def demoproj(which=None):
    if which is None: which = 'tb'
    P = au.demo(which=which)
    return P

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
    output = aa.rpcs.get_cascade_plot(proj, **args)
    print('Output:')
    print(output)
    sw.browser(jsons=output['graphs'])


if 'get_plots' in torun:
    if proj is None: proj = demoproj('tb')
    results = proj.run_sim()
    output = aa.rpcs.get_plots(proj, results=results, calibration=True)
    print('Output:')
    print(output)


if 'run_cascade_optimization' in torun:
    if proj is None: proj = demoproj('hypertension')
    output = aa.apptasks_cascade.run_cascade_optimization(proj, maxtime=10, online=False)
    print('Output:')
    print(output)
    
    
print('Done.')