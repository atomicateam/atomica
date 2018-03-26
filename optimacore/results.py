"""
Defines the classes for storing results.
Version: 2018mar23
"""

#from optima import OptimaException, Link, Settings, odict, pchip, plotpchip, sigfig # Classes/functions
#from optima import uuid, today, makefilepath, getdate, printv, dcp, objrepr, defaultrepr, sanitizefilename, sanitize # Printing/file utilities
#from optima import quantile, findinds, findnearest, promotetolist, promotetoarray, checktype # Numeric utilities
#from numpy import array, nan, zeros, arange, shape, maximum, log
#from numbers import Number
#from xlsxwriter import Workbook


from optima import defaultrepr, odict, today


class Result(object):
    ''' Class to hold individual results '''
    def __init__(self, name=None):
        self.name = name # Name of this parameter
    
    def __repr__(self):
        ''' Print out useful information when called '''
        output = defaultrepr(self)
        return output


class Resultset(object):
    ''' Structure to hold results '''
    def __init__(self, raw=None, name=None, pars=None, simpars=None, project=None, settings=None, data=None, parsetname=None, progsetname=None, budget=None, coverage=None, budgetyears=None, domake=True, quantiles=None, keepraw=False, verbose=2, doround=True):
        # Basic info
        self.created = today()
        self.name = name if name else 'default' # May be blank if automatically generated, but can be overwritten
        self.main = odict() # For storing main results
        self.other = odict() # For storing other results -- not available in the interface
        
 