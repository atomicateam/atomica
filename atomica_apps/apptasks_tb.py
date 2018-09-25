"""
apptasks_tb.py -- The Celery tasks module for this webapp
    
Last update: 2018sep23
"""

import sys
import sciris as sc
import scirisweb as sw
from . import rpcs
from . import config_tb as config
import matplotlib.pyplot as ppl
ppl.switch_backend(config.MATPLOTLIB_BACKEND)

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
async_task = sw.taskwrapper(task_func_dict) # Task function registration decorator created using call to taskwrapper().
celery_instance = sw.make_celery(config=config) # Create the Celery instance for this module.


@async_task
def run_tb_optimization(project_id, cache_id, optim_name=None, plot_options=None, maxtime=None, tool=None, plotyear=None, pops=None, cascade=None, dosave=True):
    print('Running optimization...')
    sc.printvars(locals(), ['project_id', 'optim_name', 'plot_options', 'maxtime', 'tool', 'plotyear', 'pops', 'cascade', 'dosave'], color='blue')
    datastore = rpcs.find_datastore(config=config)
    origproj = rpcs.load_project(project_id)
    results = origproj.run_optimization(optim_name, maxtime=float(maxtime), store_results=False)
    newproj = datastore.loadblob(uid=project_id, objtype='project', die=True)
    result_key = rpcs.cache_result(newproj, results, cache_id)
    return result_key


# Add the asynchronous task functions in this module to the tasks.py module so run_task() can call them.
sw.add_task_funcs(task_func_dict)