"""
apptasks.py -- The Celery tasks module for this webapp
    
Last update: 2018sep04
"""

from . import config_tb as config
import matplotlib.pyplot as ppl
ppl.switch_backend(config.MATPLOTLIB_BACKEND)
import scirisweb as sw
from . import projects as prj
from . import rpcs


# Globals
task_func_dict = {} # Dictionary to hold all of the registered task functions in this module.
async_task = sw.make_async_tag(task_func_dict) # Task function registration decorator created using call to make_async_tag().
celery_instance = sw.make_celery_instance(config=config) # Create the Celery instance for this module.


@async_task
def run_tb_optimization(project_id, cache_id, optim_name=None, plot_options=None, maxtime=None, tool=None, plotyear=None, pops=None, cascade=None, dosave=True, online=True):
    print('Running optimization...')
    import sciris as sc
    sc.printvars(locals(), ['project_id', 'optim_name', 'plot_options', 'maxtime', 'tool', 'plotyear', 'pops', 'cascade', 'dosave', 'online'], color='blue')

    if online: # Assume project_id is actually an ID
        prj.apptasks_load_projects(config) # Load the projects from the DataStore.
        proj = rpcs.load_project(project_id, raise_exception=True)
    else: # Otherwise try using it as a project
        proj = project_id
    results = proj.run_optimization(optim_name, maxtime=float(maxtime), store_results=False)
    
    # Put the results into the ResultsCache.
    rpcs.put_results_cache_entry(cache_id, results, apptasks_call=True)
    
    output = rpcs.make_plots(proj, results, tool='tb', year=plotyear, pops=pops, cascade=cascade, plot_options=plot_options, dosave=dosave, online=online, plot_budget=True)
    if online:
        print('Saving project...')
        rpcs.save_project(proj)    
    return output


# Add the asynchronous task functions in this module to the tasks.py module so run_task() can call them.
sw.add_task_funcs(task_func_dict)