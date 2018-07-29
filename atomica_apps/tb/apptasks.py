"""
apptasks.py -- The Celery tasks module for this webapp
    
Last update: 7/16/18 (gchadder3)
"""

#
# Imports
#

import time
import config
from sciris.weblib.tasks import make_celery_instance, add_task_funcs, make_register_async_task
import atomica.ui as au
import projects as prj
from rpcs import load_project, save_project, get_plots

#
# Globals
#

# Dictionary to hold all of the registered task functions in this module.
task_func_dict = {}

# Task function registration decorator created using call to 
# make_register_async_task().
register_async_task = make_register_async_task(task_func_dict)

# Create the Celery instance for this module.
celery_instance = make_celery_instance(config=config)

# This is needed in Windows using celery Version 3.1.25 in order for the
# add_task_funcs() function below to successfully add the asynchronous task 
# functions defined in this module to tasks.py.  Why these lines enable this 
# I do not understand.
#@celery_instance.task
#def dummy_result():
#    return 'here be dummy result'

@register_async_task
def run_optimization(project_id, optim_name):
    # Load the projects from the DataStore.
    prj.apptasks_load_projects(config)
    raise Exception('Not working!!!!!!!!')
    
    print('Running optimization...')
    proj = load_project(project_id, raise_exception=True)
    json = proj.optim(optim_name).json
    optimized_result = proj.run_optimization(optim_name)
    unoptimized_result = proj.run_sim(parset=json['parset_name'], progset=json['parset_name'], progset_instructions=au.ProgramInstructions(start_year=json['start_year']), result_name="Baseline")
    results = [unoptimized_result, optimized_result]
    graphs = get_plots(proj, results) # outputs=['alive','ddis']
    print('Saving project...')
    save_project(proj)    
    return {'graphs':graphs}

@register_async_task
def async_add(x, y):
    time.sleep(10)
    return x + y

@register_async_task
def async_sub(x, y):
    time.sleep(10)
    return x - y

@register_async_task
def test_error():
    time.sleep(10)
    return 1 / 0

# Add the asynchronous task functions in this module to the tasks.py module 
# so run_task() can call them.
add_task_funcs(task_func_dict)