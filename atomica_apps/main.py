"""
main.py -- main module for the webapp.
    
Last update: 2018sep23
"""

import sciris as sc
import scirisweb as sw
from . import rpcs

def make_app(which=None, **kwargs):
    T = sc.tic()
    if which is None: which = 'tb'
    if which == 'tb':
        name = 'Optima TB'
        from . import config_tb as config
        from . import apptasks_tb as apptasks # analysis:ignore
    elif which == 'cascade':
        name = 'Cascade Analysis Tools'
        from . import config_cascade as config
        from . import apptasks_cascade as apptasks # analysis:ignore
    else:
        raise Exception('"%s" not understood; which must be "tb" or "cascade"' % which)
    rpcs.find_datastore(config=config) # Set up the datastore
    app = sw.ScirisApp(name=name, filepath=__file__, config=config, RPC_dict=rpcs.RPC_dict, **kwargs) # Create the ScirisApp object.  NOTE: app.config will thereafter contain all of the configuration parameters, including for Flask.
    sw.make_default_users(app)
    print('>> Webapp initialization complete (elapsed time: %0.2f s)' % sc.toc(T, output=True))
    return app

def run(which=None, **kwargs):
    app = make_app(which=which, **kwargs) # Make the app
    app.run() # Run the client page with Flask and a Twisted server.
    return None

if __name__ == '__main__':
    run()
