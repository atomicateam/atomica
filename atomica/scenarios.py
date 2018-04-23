'''
Define classes and functions for handling scenarios
Version: 2018mar26
'''

### Imports
#from numpy import append, array, inf
#from optima import AtomicaException, Multiresultset # Core classes/functions
#from optima import dcp, today, findinds, vec2obj, isnumber, promotetoarray # Utilities
from atomica.system import AtomicaException
from atomica.results import getresults
from sciris.core import defaultrepr, printv, odict, Link # TODO - replace utilities imports 

class Scen(object):
    ''' 
    The scenario base class.
    Not to be used directly, instead use Parscen or Progscen 
    '''
    def __init__(self, name=None, parsetname=-1, progsetname=-1, t=None, active=True):
        self.name = name
        self.parsetname  = parsetname
        self.progsetname = progsetname
        self.t = t
        self.active = active
        self.resultsref = None
        self.scenparset = None # Store the actual parset generated
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = defaultrepr(self)
        return output

    def getresults(self):
        ''' Returns the results '''
        if self.resultsref is not None and self.projectref() is not None:
            results = getresults(project=self.projectref(), pointer=self.resultsref)
            return results
        else:
            print('WARNING, no results associated with this scenario')
    
    

class Parscen(Scen):
    ''' An object for storing a single parameter scenario '''
    def __init__(self, pars=None, **defaultargs):
        Scen.__init__(self, **defaultargs)
        if pars is None: pars = []
        self.pars = pars



class Progscen(Scen):
    ''' The program scenario base class -- not to be used directly, instead use Budgetscen or Coveragescen '''
    def __init__(self, progsetname=-1, **defaultargs):
        Scen.__init__(self, **defaultargs)
        self.progsetname = progsetname # Programset


class Budgetscen(Progscen):
    ''' Stores a single budget scenario. Initialised with a budget. Coverage added during makescenarios()'''
    def __init__(self, budget=None, **defaultargs):
        Progscen.__init__(self, **defaultargs)
        self.budget = budget


class Coveragescen(Progscen):
    ''' Stores a single coverage scenario. Initialised with a coverage. Budget added during makescenarios()'''
    def __init__(self, coverage=None, **defaultargs):
        Progscen.__init__(self, **defaultargs)
        self.coverage = coverage


def runscenarios(project=None, verbose=2, name=None, defaultparset=-1, debug=False, nruns=None, base=None, ccsample=None, randseed=None, **kwargs):
    """
    Run all the scenarios.
    Version: 2018mar26
    """
    
    printv('Running scenarios NOT IMPLEMENTED YET...', 1, verbose)
    pass




def makescenarios(project=None, scenlist=None, verbose=2, ccsample=False, randseed=None):
    """ Convert dictionary of scenario parameters into parset to model parameters """

    scenparsets = odict()
    return scenparsets





def baselinescenario(parset=None, verbose=2):
    """ Define the baseline scenario -- "Baseline" by default """
    if parset is None: raise AtomicaException('You need to supply a parset to generate default scenarios')
    
    scenlist = [Parscen()]
    
    ## Current conditions
    scenlist[0].name = 'Baseline'
    scenlist[0].parset = parset
    scenlist[0].pars = [] # No changes
    
    return scenlist



