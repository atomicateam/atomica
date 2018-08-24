"""
Version:
"""

import atomica.ui as au
import atomica_apps as aa
import scirisweb as sw

torun = [
'get_cascade_plot',
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
        'cascade':None, 
        'optim':  True
        }
    output = aa.rpcs.get_cascade_plot(proj, **args)
    print('Output:')
    print(output)
    sw.browser(jsons=output['graphs'])
    
    
print('Done.')