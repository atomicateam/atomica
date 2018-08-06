"""
main.py -- main module for the webapp.
    
Last update: 2018jun04
"""

import sciris.web as sw
from . import config_tb, config_cascade, frameworks, projects, rpcs, apptasks_tb, apptasks_cascade

def make_app(which=None):
    if which is None: which = 'tb'
    if which == 'tb':
        config = config_tb
    elif which == 'cascade':
        config = config_cascade
    else:
        raise Exception('"%s" not understood; which must be "tb" or "cascade"' % which)
    app = sw.ScirisApp(__file__, app_config=config) 	# Create the ScirisApp object.  NOTE: app.config will thereafter contain all of the configuration parameters, including for Flask.
    app.add_RPC_dict(rpcs.RPC_dict) # Register the RPCs in the project.py module.
    return app

def run(which=None):
    app = make_app(which=which) # Make the app
    frameworks.init_frameworks(app) # Initialize the frameworks.
    projects.init_projects(app) # Initialize the projects.
    app.run_server() # Run the client page with Flask and a Twisted server.
    return None

if __name__ == '__main__':
    run()
