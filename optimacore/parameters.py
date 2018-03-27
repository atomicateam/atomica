"""
This module defines the Parameters classes, which are used for single parameters,
and the Parameterset class, which is for the full set of parameters.

Version: 2018mar23
"""

from optimacore.system import OptimaException
from optimacore.project_settings import convertlimits
from optimacore.utils import odict, Link, today, defaultrepr, getdate, isnumber, printv, smoothinterp, getvaliddata, sanitize, findinds, inclusiverange, promotetolist, gettvecdt # This currently exists in settings, not utils. Move to utils? Or so something with settings?
from copy import deepcopy as dcp
from numpy import array, zeros, isnan, nan, isfinite, median, shape

defaultsmoothness = 1.0 # The number of years of smoothing to do by default

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
    
    
    def makepars(self, data=None, framework=None, fix=True, verbose=2, start=None, end=None):
        '''Method to make the parameters from data'''
        
        self.popkeys = data.specs['pop'].keys() # Store population keys more accessibly
        self.pars = makepars(data=data.specs, framework=framework, verbose=verbose) # Initialize as list with single entry

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
    

class Timepar(Par):
    ''' The definition of a single time-varying parameter, which may or may not vary by population '''
    
    def __init__(self, t=None, y=None, **defaultargs):
        Par.__init__(self, **defaultargs)
        if t is None: t = odict()
        if y is None: y = odict()
        self.t = t # Time data, e.g. [2002, 2008]
        self.y = y # Value data, e.g. [0.3, 0.7]
    
    def keys(self):
        ''' Return the valid keys for using with this parameter '''
        return self.y.keys()
    
    def sample(self, randseed=None):
        ''' Recalculate msample '''
        return None
    
    def interp(self, tvec=None, dt=None, smoothness=None, asarray=True, sample=None, randseed=None):
        """ Take parameters and turn them into model parameters """
        
        # Validate input
        if tvec is None: 
            errormsg = 'Cannot interpolate parameter "%s" with no time vector specified' % self.name
            raise OptimaException(errormsg)
        tvec, dt = gettvecdt(tvec=tvec, dt=dt) # Method for getting these as best possible
        if smoothness is None: smoothness = int(defaultsmoothness/dt) # Handle smoothness
        
        # Figure out sample
        if not sample:
            m = self.m
        else:
            if sample=='new' or self.msample is None: self.sample(randseed=randseed) # msample doesn't exist, make it
            m = self.msample
        
        # Set things up and do the interpolation
        npops = len(self.keys())
        if self.by=='pship': asarray= False # Force odict since too dangerous otherwise
        if asarray: output = zeros((npops,len(tvec)))
        else: output = odict()
        for pop,key in enumerate(self.keys()): # Loop over each population, always returning an [npops x npts] array
            yinterp = m * smoothinterp(tvec, self.t[pop], self.y[pop], smoothness=smoothness) # Use interpolation
            yinterp = applylimits(par=self, y=yinterp, limits=self.limits, dt=dt)
            if asarray: output[pop,:] = yinterp
            else:       output[key]   = yinterp
        if npops==1 and self.by=='tot' and asarray: return output[0,:] # npops should always be 1 if by==tot, but just be doubly sure
        else: return output



#################################################################################################################################
### Define methods to turn data into parameters
#################################################################################################################################


def data2timepar(parname=None, data=None, keys=None, defaultind=0, verbose=2, **defaultargs):
    """ Take data and turn it into default parameters"""
    # Check that at minimum, name and short were specified, since can't proceed otherwise
#    import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
    try: 
        name, short = defaultargs['label'], parname
    except: 
        errormsg = 'Cannot create a time parameter without name and label.'
        raise OptimaException(errormsg)
        
    par = Timepar(m=1.0, y=odict(), t=odict(), **defaultargs) # Create structure
    par.name = name
    par.short = short
    for key in keys:
        par.y[key] = data['values'].getValue(key)
        if data['values'].getValue('t') is not None: # TODO this whole thing only works for constants... need to revamp data storage
            par.t[key] = data['values'].getValue('t')
        else:
            par.t[key] = 2018. # TODO, remove this, it's SUPER TEMPORARY -- a way to assign a year to constants/assumptions

#    for row,key in enumerate(keys):
#        try:
#            validdata = ~isnan(data[short][row]) # WARNING, this could all be greatly simplified!!!! Shouldn't need to call this and sanitize()
#            par.t[key] = getvaliddata(data['years'], validdata, defaultind=defaultind) 
#            if sum(validdata): 
#                par.y[key] = sanitize(data[short][row])
#            else:
#                printv('data2timepar(): no data for parameter "%s", key "%s"' % (name, key), 3, verbose) # Probably ok...
#                par.y[key] = array([0.0]) # Blank, assume zero -- WARNING, is this ok?
#                par.t[key] = array([0.0])
#        except:
#            errormsg = 'Error converting time parameter "%s", key "%s"' % (name, key)
#            printv(errormsg, 1, verbose)
#            raise

    return par


def makepars(data=None, framework=None, verbose=2, die=True, fixprops=None):
    """
    Translates the raw data (which were read from the spreadsheet) into
    parameters that can be used in the model. These data are then used to update 
    the corresponding model (project). 
    
    Version: 2018mar23
    """
    
    printv('Converting data to parameters...', 1, verbose)
    
    ###############################################################################
    ## Loop over quantities
    ###############################################################################
    
    pars = odict()
    
    # Set up population keys
    pars['popkeys'] = data['pop'].keys() # Get population keys
    totkey = ['tot'] # Define a key for when not separated by population
    popkeys = pars['popkeys'] # Convert to a normal string and to lower case...maybe not necessary
    
    # Read in parameters automatically
    try: 
        rawpars = framework.specs['par'] # Read the parameters structure
    except OptimaException as E: 
        errormsg = 'Could not load parameter specs: "%s"' % repr(E)
        raise OptimaException(errormsg)
        
    for parname,par in rawpars.iteritems(): # Iterate over all automatically read in parameters
        printv('Converting data parameter "%s"...' % parname, 3, verbose)
        
        try: # Optionally keep going if some parameters fail
        
#            # Shorten key variables
#            by = par['by']
#            fromdata = par['fromdata']
#            
#            # Decide what the keys are
#            if   by=='tot' : keys = totkey
#            elif by=='pop' : keys = popkeys
#            else: keys = [] 
#            
#            if fromdata: pars[parname] = data2timepar(parname=parname, data=data['par'][parname], keys=keys, **par) 
#            else: pars[parname] = Timepar(m=1.0, y=odict([(key,array([nan])) for key in keys]), t=odict([(key,array([0.0])) for key in keys]), **par) # Create structure

            # TEMPORARY!!! - all parameters are assumed to be Timepars made from data and by population
            keys = popkeys
            pars[parname] = data2timepar(parname=parname, data=data['par'][parname], keys=keys, **par) 
            
        except Exception as E:
            import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
            errormsg = 'Failed to convert parameter %s:\n%s' % (parname, repr(E))
            if die: raise OptimaException(errormsg)
            else: printv(errormsg, 1, verbose)
        
    return pars


def makesimpars(pars, name=None, keys=None, start=None, end=None, dt=None, tvec=None, settings=None, smoothness=None, asarray=True, sample=None, tosample=None, randseed=None, verbose=2):
    ''' 
    A function for taking a single set of parameters and returning the interpolated versions.
    Version: 2018mar26
    '''
    
    # Handle inputs and initialization
    simpars = odict() 
    simpars['parsetname'] = name
    if keys is None: keys = pars.keys() # Just get all keys
    if type(keys)==str: keys = [keys] # Listify if string
    if tvec is not None: simpars['tvec'] = tvec
    elif settings is not None: simpars['tvec'] = settings.maketvec(start=start, end=end, dt=dt)
    else: simpars['tvec'] = inclusiverange(start=start, stop=end, step=dt) # Store time vector with the model parameters
    if len(simpars['tvec'])>1: dt = simpars['tvec'][1] - simpars['tvec'][0] # Recalculate dt since must match tvec
    simpars['dt'] = dt  # Store dt
    if smoothness is None: smoothness = int(defaultsmoothness/dt)
    tosample = promotetolist(tosample) # Convert to list
    
    # Copy default keys by default
#    for key in generalkeys: simpars[key] = dcp(pars[key])
#    for key in staticmatrixkeys: simpars[key] = dcp(array(pars[key]))

    # Loop over requested keys
    for key in keys: # Loop over all keys
        if isinstance(pars[key], Par): # Check that it is actually a parameter
            simpars[key] = dcp(pars[key])
            thissample = sample # Make a copy of it to check it against the list of things we are sampling
            if tosample[0] is not None and key not in tosample: thissample = False # Don't sample from unselected parameters -- tosample[0] since it's been promoted to a list
            try:
                simpars[key] = pars[key].interp(tvec=simpars['tvec'], dt=dt, smoothness=smoothness, asarray=asarray, sample=thissample, randseed=randseed)
            except OptimaException as E: 
                errormsg = 'Could not figure out how to interpolate parameter "%s"' % key
                errormsg += 'Error: "%s"' % repr(E)
                raise OptimaException(errormsg)


    return simpars




def applylimits(y, par=None, limits=None, dt=None, warn=True, verbose=2):
    ''' 
    A function to  apply limits (supplied as [low, high] list or tuple) to an output.
    Needs dt as input since that determines maxrate.
    Version: 2018mar23
    '''
    
    # If parameter object is supplied, use it directly
    parname = ''
    if par is not None:
        if limits is None: limits = par.limits
        parname = par.name
        
    # If no limits supplied, don't do anything
    if limits is None:
        printv('No limits supplied for parameter "%s"' % parname, 4, verbose)
        return y
    
    if dt is None:
        if warn: raise OptimaException('No timestep specified: required for convertlimits()')
        else: dt = 0.2 # WARNING, should probably not hard code this, although with the warning, and being conservative, probably OK
    
    # Convert any text in limits to a numerical value
    limits = convertlimits(limits=limits, dt=dt, verbose=verbose)
    
    # Apply limits, preserving original class -- WARNING, need to handle nans
    if isnumber(y):
        if ~isfinite(y): return y # Give up
        newy = median([limits[0], y, limits[1]])
        if warn and newy!=y: printv('Note, parameter value "%s" reset from %f to %f' % (parname, y, newy), 3, verbose)
    elif shape(y):
        newy = array(y) # Make sure it's an array and not a list
        infiniteinds = findinds(~isfinite(newy))
        infinitevals = newy[infiniteinds] # Store these for safe keeping
        if len(infiniteinds): newy[infiniteinds] = limits[0] # Temporarily reset -- value shouldn't matter
        newy[newy<limits[0]] = limits[0]
        newy[newy>limits[1]] = limits[1]
        newy[infiniteinds] = infinitevals # And stick them back in
        if warn and any(newy!=array(y)):
            printv('Note, parameter "%s" value reset from:\n%s\nto:\n%s' % (parname, y, newy), 3, verbose)
    else:
        if warn: raise OptimaException('Data type "%s" not understood for applying limits for parameter "%s"' % (type(y), parname))
        else: newy = array(y)
    
    if shape(newy)!=shape(y):
        errormsg = 'Something went wrong with applying limits for parameter "%s":\ninput and output do not have the same shape:\n%s vs. %s' % (parname, shape(y), shape(newy))
        raise OptimaException(errormsg)
    
    return newy

