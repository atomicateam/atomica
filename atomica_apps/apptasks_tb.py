"""
apptasks.py -- The Celery tasks module for this webapp
    
Last update: 2018aug26
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
print '** apptasks_tb.py _init_tasks() call'  # TODO: remove this post-debugging
celery_instance = sw.make_celery_instance(config=config) # Create the Celery instance for this module.

# This is needed in Windows using celery Version 3.1.25 in order for the
# add_task_funcs() function below to successfully add the asynchronous task 
# functions defined in this module to tasks.py.  Why these lines enable this 
# I do not understand.
#@celery_instance.task
#def dummy_result():
#    return 'here be dummy result'

@async_task
def run_optimization(project_id, optim_name, plot_options=None, maxtime=None, tool=None, plotyear=None, pops=None, cascade=None, dosave=True):
    # Load the projects from the DataStore.
    prj.apptasks_load_projects(config)
    print('Running optimization...')
    proj = rpcs.load_project(project_id, raise_exception=True)
    results = proj.run_optimization(optim_name, maxtime=maxtime)
    proj.results['optimization'] = results # WARNING, will want to save separately!
#    output = rpcs.process_plots(proj, results, tool='tb', year=plotyear, pops=pops, cascade=cascade, plot_options=plot_options, dosave=dosave)
    output = rpcs.process_plots(proj, results, tool='tb', year=plotyear, pops=pops, cascade=cascade, plot_options=plot_options)
    print('Saving project...')
    rpcs.save_project(proj)    
    return output


# Add the asynchronous task functions in this module to the tasks.py module so run_task() can call them.
sw.add_task_funcs(task_func_dict)