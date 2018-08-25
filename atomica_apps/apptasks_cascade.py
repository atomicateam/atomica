"""
apptasks.py -- The Celery tasks module for this webapp
    
Last update: 7/16/18 (gchadder3)
"""


from . import config_cascade as config
import matplotlib.pyplot as ppl
ppl.switch_backend(config.MATPLOTLIB_BACKEND)
from . import projects as prj
from .rpcs import load_project, save_project, get_cascade_plot
import scirisweb as sw


task_func_dict = {} # Dictionary to hold all of the registered task functions in this module.

# Task function registration decorator created using call to make_async_tag().
async_task = sw.make_async_tag(task_func_dict)

# Create the Celery instance for this module.
celery_instance = sw.make_celery_instance(config=config)

# This is needed in Windows using celery Version 3.1.25 in order for the
# add_task_funcs() function below to successfully add the asynchronous task 
# functions defined in this module to tasks.py.  Why these lines enable this 
# I do not understand.
#@celery_instance.task
#def dummy_result():
#    return 'here be dummy result'

@async_task
def run_cascade_optimization(project_id, optim_name, plot_options=None, saveresults=False, plotyear=None, pops=None,cascade=None):
    # Load the projects from the DataStore.
    prj.apptasks_load_projects(config)
    
    print('Running optimization...')
    proj = load_project(project_id, raise_exception=True)
    results = proj.run_optimization(optim_name)
    proj.results['optimization'] = results # WARNING, will want to save separately!
    output = get_cascade_plot(proj, results, year=plotyear, pops=pops, cascade=cascade, plot_budget=True)
#    if saveresults:
    print('Saving project...')
    save_project(proj)    
    return output


# Add the asynchronous task functions in this module to the tasks.py module 
# so run_task() can call them.
sw.add_task_funcs(task_func_dict)