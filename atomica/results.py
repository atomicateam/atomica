"""
Defines the classes for storing results.
Version: 2018mar23
"""
from atomica.system import OptimaException, uuid
from atomica.utils import Link, odict, sigfig, today, makefilepath, getdate, printv, objrepr, defaultrepr, sanitizefilename, sanitize # Printing/file utilities
#from optima import quantile, findinds, findnearest, promotetolist, promotetoarray, checktype # Numeric utilities
#from numpy import array, nan, zeros, arange, shape, maximum, log
from numbers import Number
from copy import deepcopy as dcp
#from xlsxwriter import Workbook


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


class Multiresultset(Resultset):
    ''' Structure for holding multiple kinds of results, e.g. from an optimization, or scenarios '''
    def __init__(self, resultsetlist=None, name=None):
        # Basic info
        self.name = name if name else 'default'
        self.created = today()
        self.nresultsets = len(resultsetlist)
        self.resultsetnames = [result.name for result in resultsetlist] # Pull the names of the constituent resultsets
        self.keys = []
        self.budgets = odict()
        self.coverages = odict()
        self.budgetyears = odict() 
        self.setup = odict() # For storing the setup attributes (e.g. tvec)
        if type(resultsetlist)==list: pass # It's already a list, carry on
        elif type(resultsetlist) in [odict, dict]: resultsetlist = resultsetlist.values() # Convert from odict to list
        elif resultsetlist is None: raise OptimaException('To generate multi-results, you must feed in a list of result sets: none provided')
        else: raise OptimaException('Resultsetlist type "%s" not understood' % str(type(resultsetlist)))



def getresults(project=None, pointer=None, die=True):
    '''
    Function for returning the results associated with something. 'pointer' can eiher be a UID,
    a string representation of the UID, the actual pointer to the results, or a function to return the
    results.
    
    Example:
        results = P.parsets[0].getresults()
        calls
        getresults(P, P.parsets[0].resultsref)
        which returns
        P.results[P.parsets[0].resultsref]
    
    The "die" keyword lets you choose whether a failure to retrieve results returns None or raises an exception.    
    
    Version: 1.2 (2016feb06)
    '''
    # Nothing supplied, don't try to guess
    if pointer is None: 
        return None 
    
    # Normal usage, e.g. getresults(P, 3) will retrieve the 3rd set of results
    elif isinstance(pointer, (str, unicode, Number, type(uuid()))):
        if project is not None:
            resultnames = [res.name for res in project.results.values()]
            resultuids = [str(res.uid) for res in project.results.values()]
        else: 
            if die: raise OptimaException('To get results using a key or index, getresults() must be given the project')
            else: return None
        try: # Try using pointer as key -- works if name
            results = project.results[pointer]
            return results
        except: # If that doesn't match, keep going
            if pointer in resultnames: # Try again to extract it based on the name
                results = project.results[resultnames.index(pointer)]
                return results
            elif str(pointer) in resultuids: # Next, try extracting via the UID
                results = project.results[resultuids.index(str(pointer))]
                return results
            else: # Give up
                validchoices = ['#%i: name="%s", uid=%s' % (i, resultnames[i], resultuids[i]) for i in range(len(resultnames))]
                errormsg = 'Could not get result "%s": choices are:\n%s' % (pointer, '\n'.join(validchoices))
                if die: raise OptimaException(errormsg)
                else: return None
    
    # The pointer is the results object
    elif isinstance(pointer, (Resultset, Multiresultset)):
        return pointer # Return pointer directly if it's already a results set
    
    # It seems to be some kind of function, so try calling it -- might be useful for the database or something
    elif callable(pointer): 
        try: 
            return pointer()
        except:
            if die: raise OptimaException('Results pointer "%s" seems to be callable, but call failed' % str(pointer))
            else: return None
    
    # Could not figure out what to do with it
    else: 
        if die: raise OptimaException('Could not retrieve results \n"%s"\n from project \n"%s"' % (pointer, project))
        else: return None
        
 