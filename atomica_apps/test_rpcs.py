"""
Version:
"""

import sciris as sc
import scirisweb as sw
import atomica.ui as au
from atomica_apps import rpcs, apptasks_cascade as atca, apptasks_tb as attb
import json
import sciris as sc

torun = [
# 'get_cascade_plot',
# 'get_cascade_json',
# 'get_plots',
'process_plots',
# 'run_cascade_optimization',
# 'run_tb_optimization',
]

proj = None

def demoproj(which=None):
    if which is None: which = 'tb'
    P = au.demo(which=which)
    return P

T = sc.tic()

def heading(string, style=None):
    divider = '#'*60
    sc.blank()
    if style == 'big': string = '\n'.join([divider, string, divider])
    sc.colorize('blue', string)
    return None


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
            json.dump(sc.sanitizejson(output), f)
            print('JSON saved to %s' % filename)


if 'get_plots' in torun:
    if proj is None: proj = demoproj('tb')
    results = proj.run_sim()
    output = rpcs.get_plots(proj, results=results, calibration=True)
    print('Output:')
    print(output)

if 'process_plots' in torun:
    proj = demoproj('tb')
    results = proj.demo_scenarios(dorun=True)
    output = rpcs.process_plots(proj, results, tool='tb', year=2018, pops='all', cascade=None, plot_options=None, dosave=None, calibration=False, online=True, plot_budget=True)
    sw.browser(jsons=output['graphs'])


if 'run_cascade_optimization' in torun:
    maxtime = 10
    if proj is None: proj = demoproj('hypertension')
    output = atca.run_cascade_optimization(proj, maxtime=maxtime, online=False)
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