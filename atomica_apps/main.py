"""
main.py -- main module for the webapp.
    
Last update: 2018jun04
"""

import sciris as sc
import scirisweb as sw
from . import frameworks, projects, rpcs

def make_app(which=None, **kwargs):
    T = sc.tic()
    if which is None: which = 'tb'
    if which == 'tb':
        name = 'Optima TB'
        import config_tb as config
    elif which == 'cascade':
        name = 'Cascade Analysis Tools'
        import config_cascade as config
    else:
        raise Exception('"%s" not understood; which must be "tb" or "cascade"' % which)
    app = sw.ScirisApp(name=name, filepath=__file__, config=config, **kwargs) # Create the ScirisApp object.  NOTE: app.config will thereafter contain all of the configuration parameters, including for Flask.
    app.add_RPC_dict(rpcs.RPC_dict) # Register the RPCs in the project.py module.
    frameworks.init_frameworks(app) # Initialize the frameworks.
    projects.init_projects(app) # Initialize the projects.
    rpcs.init_results_cache(app) # Initialize results cache.
    print('>> Webapp initialization complete (elapsed time: %0.2f s)' % sc.toc(T, output=True))
    return app

def run(which=None, **kwargs):
    app = make_app(which=which, **kwargs) # Make the app
    app.run() # Run the client page with Flask and a Twisted server.
    return None

if __name__ == '__main__':
    run()
