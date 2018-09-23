"""
apptasks_cascade.py -- The Celery tasks module for this webapp
    
Last update: 2018sep23
"""

import sys
import sciris as sc
import scirisweb as sw
from . import rpcs
from . import config_cascade as config
import matplotlib.pyplot as ppl
ppl.switch_backend(config.MATPLOTLIB_BACKEND)


print('')
print('#########################################')
print('Starting Cascade Analysis Tools Celery...')
print('#########################################')

# Process arguments
for i,arg in enumerate(sys.argv[1:]):
    try:
        if arg.find('=')>0:
            k = arg.split("=")[0]
            v = arg.split("=")[1]
            K = k.upper()
            if hasattr(config, K):
                setattr(config, K, v)
                print('Including kwarg: "%s" = %s' % (K,v))
            else:
                print('Skipping attribute "%s" = %s, not found' % (K,v))
    except Exception as E:
        errormsg = 'Failed to parse argument key="%s", value="%s": %s' % (K, v, str(E))
        raise Exception(errormsg)

# Globals
task_func_dict = {} # Dictionary to hold all of the registered task functions in this module.
async_task = sw.make_async_tag(task_func_dict) # Task function registration decorator created using call to make_async_tag().
celery_instance = sw.make_celery_instance(config=config) # Create the Celery instance for this module.


@async_task
def run_cascade_optimization(project_id, cache_id, optim_name=None, plot_options=None, maxtime=None, tool=None, plotyear=None, pops=None, cascade=None, dosave=True, online=True):
    print('Running optimization...')
    sc.printvars(locals(), ['project_id', 'optim_name', 'plot_options', 'maxtime', 'tool', 'plotyear', 'pops', 'cascade', 'dosave', 'online'], color='blue')
    datastore = rpcs.find_datastore(config=config)
    orig_proj = rpcs.load_project(project_id)
    results = orig_proj.run_optimization(optim_name, maxtime=float(maxtime), store_results=False)
    proj = rpcs.load_project(project_id) # Reload the project in case it's changed in the mean time
    proj.results[cache_id] = results
    proj = rpcs.cache_results(proj)
    key = datastore.saveblob(uid=project_id, objtype='project', obj=proj)
    output = rpcs.make_plots(proj, results, tool='cascade', year=plotyear, pops=pops, cascade=cascade, plot_options=plot_options, dosave=dosave, online=online, plot_budget=True)
    rpcs.save_project(proj)
    return output


# Add the asynchronous task functions in this module to the tasks.py module so run_task() can call them.
sw.add_task_funcs(task_func_dict)