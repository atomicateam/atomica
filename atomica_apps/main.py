"""
main.py -- main module for the webapp.
    
Last update: 2018jun04
"""

import sciris.web as sw
from . import frameworks, projects, rpcs

def make_app(which=None):
    if which is None: which = 'tb'
    if which == 'tb':
        import config_tb as config
        import apptasks_tb as apptasks # analysis:ignore
    elif which == 'cascade':
        import config_cascade as config
        import apptasks_cascade as apptasks # analysis:ignore
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
