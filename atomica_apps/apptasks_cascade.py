"""
apptasks.py -- The Celery tasks module for this webapp
    
Last update: 2018aug26
"""

from . import config_cascade as config
import matplotlib.pyplot as ppl
ppl.switch_backend(config.MATPLOTLIB_BACKEND)
import scirisweb as sw
from . import projects as prj
from . import rpcs

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
def run_cascade_optimization(project_id, cache_id, optim_name=None, plot_options=None, maxtime=None, tool=None, plotyear=None, pops=None, cascade=None, dosave=True, online=True):
    print('Running optimization...')
    import sciris as sc
    sc.printvars(locals(), ['project_id', 'optim_name', 'plot_options', 'maxtime', 'tool', 'plotyear', 'pops', 'cascade', 'dosave', 'online'], color='blue')
    if online: # Assume project_id is actually an ID
        prj.apptasks_load_projects(config) # Load the projects from the DataStore.
        proj = rpcs.load_project(project_id, raise_exception=True)
    else: # Otherwise try using it as a project
        proj = project_id
    results = proj.run_optimization(optim_name, maxtime=float(maxtime))
#    proj.results['optimization'] = results # WARNING, will want to save separately!
#    proj.results[cache_id] = results   # TODO: remove this after caching done right  
    # NOTE: some possibility we may need a concurrency lock for next two lines.
    results_cache = rpcs.apptasks_load_results_cache()
    
    # NOTE: I believe this is the unsafe line that is breaking the ability to 
    # queue tasks together.  I think the problem is that when you are adding a new 
    # cache_id, data_store.handle_dict gets changed and then saved, which is 
    # likely to cause havoc.  When all old cache_ids are in place, the problem 
    # doesn't happen.
    results_cache.store(cache_id, project_id, results)
    
    output = rpcs.process_plots(proj, results, tool='cascade', year=plotyear, pops=pops, cascade=cascade, plot_options=plot_options, dosave=dosave, online=online, plot_budget=True)
    if online:
        print('Saving project...')
        rpcs.save_project(proj)    
    return output


# Add the asynchronous task functions in this module to the tasks.py module so run_task() can call them.
sw.add_task_funcs(task_func_dict)