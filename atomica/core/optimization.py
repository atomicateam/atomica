"""
Functions for running optimizations.
Version: 2018mar26
"""

import sciris.core as sc
#import Link, today, getdate, objrepr  # Utilities

from .system import AtomicaException


#######################################################################################################
# The container class
#######################################################################################################
class Optim(object):
    """ An object for storing an optimization """

    def __init__(self, project=None, name='default', objectives=None, constraints=None, parsetname=None,
                 progsetname=None, timevarying=None, tvsettings=None):
        if project is None:
            raise AtomicaException('To create an optimization, you must supply a project')
        if parsetname is None:
            parsetname = -1  # If none supplied, assume defaults
        if progsetname is None:
            progsetname = -1
        # if objectives is None: objectives  = defaultobjectives(project=project,  progsetname=progsetname, verbose=0)
        # if constraints is None: constraints = defaultconstraints(project=project, progsetname=progsetname, verbose=0)
        # if tvsettings is None: tvsettings  = defaulttvsettings(timevarying=timevarying) # Create time-varying settings
        self.name = name  # Name of the optimization, e.g. 'default'
        self.projectref = sc.Link(project)  # Store pointer for the project, if available
        self.created = sc.today()  # Date created
        self.modified = sc.today()  # Date modified
        self.parsetname = parsetname  # Parameter set name
        self.progsetname = progsetname  # Program set name
        self.objectives = objectives  # List of dicts holding Parameter objects -- only one if no uncertainty
        self.constraints = constraints  # List of populations
        self.tvsettings = tvsettings  # The settings for being time-varying
        self.resultsref = None  # Store pointer to results

    def __repr__(self):
        """ Print out useful information when called"""
        output = sc.desc(self)
        output += ' Optimization name: %s\n' % self.name
        output += 'Parameter set name: %s\n' % self.parsetname
        output += '  Program set name: %s\n' % self.progsetname
        output += '      Time-varying: %s\n' % self.tvsettings['timevarying']
        output += '      Date created: %s\n' % sc.getdate(self.created)
        output += '     Date modified: %s\n' % sc.getdate(self.modified)
        output += '============================================================\n'
        return output

    def get_results(self):
        """ A method for getting the results """
        if self.resultsref is not None and self.projectref() is not None:
            results = None  # get_results(project=self.projectref(), pointer=self.resultsref)
            return results
        else:
            print('WARNING, no results associated with this optimization')
            return None
