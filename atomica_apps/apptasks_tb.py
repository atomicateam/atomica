"""
apptasks.py -- The Celery tasks module for this webapp
    
Last update: 7/16/18 (gchadder3)
"""

from . import config_tb as config
import matplotlib.pyplot as ppl
ppl.switch_backend(config.MATPLOTLIB_BACKEND)
from . import projects as prj
from .rpcs import load_project, save_project, get_plots
import scirisweb as sw

# Globals
task_func_dict = {} # Dictionary to hold all of the registered task functions in this module.
async_task = sw.make_async_tag(task_func_dict) # Task function registration decorator created using call to make_async_tag().
celery_instance = sw.make_celery_instance(config=config) # Create the Celery instance for this module.

# This is needed in Windows using celery Version 3.1.25 in order for the
# add_task_funcs() function below to successfully add the asynchronous task 
# functions defined in this module to tasks.py.  Why these lines enable this 
# I do not understand.
#@celery_instance.task
#def dummy_result():
#    return 'here be dummy result'

@async_task
def run_optimization(project_id, optim_name, plot_options=None, maxtime=None, saveresults=False):
    # Load the projects from the DataStore.
    prj.apptasks_load_projects(config)
    
    print('Running optimization...')
    proj = load_project(project_id, raise_exception=True)
    results = proj.run_optimization(optim_name, maxtime=maxtime)
    output,figs = get_plots(proj, results, plot_options=plot_options) # outputs=['alive','ddis']
    if saveresults:
        print('Saving project...')
        save_project(proj)    
    return output


# Add the asynchronous task functions in this module to the tasks.py module so run_task() can call them.
sw.add_task_funcs(task_func_dict)