"""
This module defines the Parameters classes, which are used for single parameters,
and the Parameterset class, which is for the full set of parameters.

Version: 2018mar23
"""

from optima import odict, Link, today, defaultrepr, getdate, dcp, isnumber, printv, OptimaException
from numpy import array, exp


#################################################################################################################################
### Define the parameter set
#################################################################################################################################

class Parameterset(object):
    ''' Class to hold all parameters and information on how they were generated, and perform operations on them'''
    
    def __init__(self, name='default', project=None, start=None, end=None):
        self.name = name # Name of the parameter set, e.g. 'default'
        self.projectref = Link(project) # Store pointer for the project, if available
        self.created = today() # Date created
        self.modified = today() # Date modified
        self.pars = None
        self.popkeys = [] # List of populations
        self.start = start # Start data
        self.end = end # Enddata
        
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output  = defaultrepr(self)
        output += 'Parameter set name: %s\n'    % self.name
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += '============================================================\n'
        return output
    
    
    def getresults(self, die=True):
        ''' Method for getting the results '''
        pass
   
    
    def parkeys(self):
        ''' Return a list of the keys in pars that are actually parameter objects '''
        parslist = []
        for key,par in self.pars.items():
            if issubclass(type(par), Par):
                parslist.append(key)
        return parslist
    
    
    def makepars(self, data=None, fix=True, verbose=2, start=None, end=None):
        '''Method to make the parameters from data'''
        return None


    def interp(self, keys=None, start=None, end=2030, dt=0.2, tvec=None, smoothness=20, asarray=True, samples=None, verbose=2):
        """ Prepares model parameters to run the simulation. """
        printv('Making model parameters...', 1, verbose),
        return None
    
    
    def printpars(self, output=False):
        outstr = ''
        count = 0
        for par in self.pars.values():
            if hasattr(par,'p'): print('WARNING, population size not implemented!')
            if hasattr(par,'y'):
                if hasattr(par.y, 'keys'):
                    count += 1
                    if len(par.keys())>1:
                        outstr += '%3i: %s\n' % (count, par.name)
                        for key in par.keys():
                            outstr += '     %s = %s\n' % (key, par.y[key])
                    elif len(par.keys())==1:
                        outstr += '%3i: %s = %s\n\n' % (count, par.name, par.y[0])
                    elif len(par.keys())==0:
                        outstr += '%3i: %s = (empty)' % (count, par.name)
                    else:
                        print('WARNING, not sure what to do with %s: %s' % (par.name, par.y))
                else:
                    count += 1
                    outstr += '%3i: %s = %s\n\n' % (count, par.name, par.y)
        print(outstr)
        if output: return outstr
        else: return None


    def listattributes(self):
        ''' Go through all the parameters and make a list of their possible attributes '''
        
        maxlen = 20
        pars = self.pars
        
        print('\n\n\n')
        print('CONTENTS OF PARS, BY TYPE:')
        partypes = []
        for key in pars: partypes.append(type(pars[key]))
        partypes = set(partypes)
        count1 = 0
        count2 = 0
        for partype in set(partypes): 
            count1 += 1
            print('  %i..%s' % (count1, str(partype)))
            for key in pars:
                if type(pars[key])==partype:
                    count2 += 1
                    print('      %i.... %s' % (count2, str(key)))
        
        print('\n\n\n')
        print('ATTRIBUTES:')
        attributes = {}
        for key in self.parkeys():
            theseattr = pars[key].__dict__.keys()
            for attr in theseattr:
                if attr not in attributes.keys(): attributes[attr] = []
                attributes[attr].append(getattr(pars[key], attr))
        for key in attributes:
            print('  ..%s' % key)
        print('\n\n')
        for key in attributes:
            count = 0
            print('  ..%s' % key)
            items = []
            for item in attributes[key]:
                try: 
                    string = str(item)
                    if string not in items: 
                        if len(string)>maxlen: string = string[:maxlen]
                        items.append(string) 
                except: 
                    items.append('Failed to append item')
            for item in items:
                count += 1
                print('      %i....%s' % (count, str(item)))
        return None




#################################################################################################################################
### Define the Parameter class
#################################################################################################################################

class Par(object):
    '''
    The base class for epidemiological model parameters.
    Version: 2018mar23
    '''
    def __init__(self, short=None, name=None, limits=(0.,1.), by=None, manual='', fromdata=None, m=1.0, prior=None, verbose=None, **defaultargs): # "type" data needed for parameter table, but doesn't need to be stored
        self.short = short # The short used within the code 
        self.name = name # The full name, e.g. "HIV testing rate"
        self.limits = limits # The limits, e.g. (0,1) -- a tuple since immutable
        self.by = by # Whether it's by population, partnership, or total
        self.manual = manual # Whether or not this parameter can be manually fitted: options are '', 'meta', 'pop', 'exp', etc...
        self.fromdata = fromdata # Whether or not the parameter is made from data
        self.m = m # Multiplicative metaparameter, e.g. 1
        self.msample = None # The latest sampled version of the metaparameter -- None unless uncertainty has been run, and only used for uncertainty runs 
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = defaultrepr(self)
        return output
    

