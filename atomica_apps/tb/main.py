"""
main.py -- main module for the Optima Nutrition webapp.
    
Last update: 2018jun04
"""

import atomica_apps.tb as tb
import sciris.web as sw

def make_app():
    app = sw.ScirisApp(__file__, app_config=tb.config) 	# Create the ScirisApp object.  NOTE: app.config will thereafter contain all of the configuration parameters, including for Flask.
    app.add_RPC_dict(tb.rpcs.RPC_dict) # Register the RPCs in the project.py module.
    return app

def run():
    app = make_app() # Make the app
    tb.projects.init_projects(app) # Initialize the projects.
    app.run_server() # Run the client page with Flask and a Twisted server.
    return None

if __name__ == '__main__':
    run()
