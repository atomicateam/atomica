"""
SETTINGS
Store all the settings for a project.
Version: 2018mar26
"""

from atomica.system import AtomicaException, logger
from sciris.utils import defaultrepr, inclusiverange, isnumber # CK: warning, should replace printv with logger
from numpy import shape, array #arange, concatenate as cat, 

class ProjectSettings(object):
    def __init__(self, num_progs=None, num_pops=None, start=None, end_data=None, end=None, verbose=2):

        self.num_progs = num_progs if num_progs is not None else 4 # Default number of programs
        self.num_pops = num_pops if num_pops is not None else  1 # Default number of populations

        self.datastart = start if start is not None else 2000.0 # Default start year
        self.end_data = end_data if end_data is not None else 2020.0 # Default end year for data entry
        self.end = end if end is not None else 2030.0 # Default end year for projections
        self.now = 2018.0 # Default current year
        self.dt = 1.0 # Timestep
        
        # Other
#        self.defaultblue = (0.16, 0.67, 0.94) # The color of Atomica
#        self.verbose = verbose # Default verbosity for how much to print out -- see definitions in utils.py:printv()
#        self.safetymargin = 0.5 # Do not move more than this fraction of people on a single timestep
#        self.eps = 1e-3 # Must be small enough to be applied to prevalence, which might be ~0.1% or less
#        self.infmoney = 1e10 # A lot of money
        logger.info("Initialized project settings.")
    
    
    def __repr__(self):
        """ Print object """
        output =  defaultrepr(self)
        return output
    
    
    def makeTimeVector(self, start=None, end=None, dt=None):
        """ Calculate time vector"""
        if start is None: start = self.start
        if end is None: end = self.end
        if dt is None: dt = self.dt
        tvec = inclusiverange(start=start, stop=end, step=dt) # Can"t use arange since handles floating point arithmetic badly, e.g. compare arange(2000, 2020, 0.2) with arange(2000, 2020.2, 0.2)
        logger.info("Constructing time vector.")
        return tvec
    
    
#    def convertlimits(self, limits=None, tvec=None, dt=None, safetymargin=None, verbose=None):
#        """ Link to function below """
#        return convertlimits(settings=self, limits=limits, tvec=None, dt=dt, safetymargin=None, verbose=verbose)




#def getTimeVector(tvec=None, dt=None, justdt=False):
#    """ 
#    Function to encapsulate the logic of returning sensible tvec and dt based on flexible input.
#    If tvec and dt are both supplied, do nothing.
#    Will always work if tvec is not None, but will use default value for dt if dt==None and len(tvec)==1.
#    Usage:
#        tvec,dt = gettvecdt(tvec, dt)
#    """
#    defaultdt = 0.2 # WARNING, slightly dangerous to hard-code but should be ok, since very rare situation
#    if tvec is None: 
#        if justdt: return defaultdt # If it"s a constant, maybe don" need a time vector, and just return dt
#        else: raise AtomicaException("No time vector supplied, and unable to figure it out") # Usual case, crash
#    elif isnumber(tvec): tvec = array([tvec]) # Convert to 1-element array
#    elif shape(tvec): # Make sure it has a length -- if so, overwrite dt
#        if len(tvec)>=2: dt = tvec[1]-tvec[0] # Even if dt supplied, recalculate it from the time vector
#        else: dt = dt # Use input
#    else:
#        raise AtomicaException("Could not understand tvec of type '{0}'".format(type(tvec)))
#    if dt is None: dt = defaultdt # Or give up and use default
#    return tvec, dt
    
    

    
#def convertlimits(limits=None, tvec=None, dt=None, safetymargin=None, settings=None, verbose=None):
#    """ 
#    Method to calculate numerical limits from qualitative strings.
#    
#    Valid usages:
#        convertlimits() # Returns dict of max rates that can be called later
#        convertlimits("maxrate") # Returns maxrate = 0.9/dt, e.g. 4
#        convertlimits([0, "maxrate"]) # Returns e.g. [0, 4]
#        convertlimits(4) # Returns 4
#    
#    Version: 2016jan30
#    """
#    if verbose is None:
#        if settings is not None: verbose = settings.verbose
#        else: verbose=2
#    
#    printv("Converting to numerical limits...", 4, verbose)
#    if dt is None: 
#        if settings is not None: dt = settings.dt
#        else: raise AtomicaException("convertlimits() must be given either a timestep or a settings object")
#    if safetymargin is None:
#        if settings is not None: safetymargin = settings.safetymargin
#        else: 
#            printv("Note, using default safetymargin since could not find it", 4, verbose)
#            safetymargin = 0.8 # Not that important, so just set safety margin
#    
#    # Update dt 
#    dt = gettvecdt(tvec=tvec, dt=dt, justdt=True)
#    
#    # Actually define the rates
#    maxrate = safetymargin/dt
#    maxpopsize = 1e9
#    maxduration = 1000.
#    maxmeta = 1000.0
#    maxacts = 5000.0
#    maxyear = settings.end if settings is not None else 2030. # Set to a default maximum year
#    
#    # It"s a single number: just return it
#    if isnumber(limits): return limits
#    
#    # Just return the limits themselves as a dict if no input argument
#    if limits is None: 
#        return {"maxrate":maxrate, "maxpopsize":maxpopsize, "maxduration":maxduration, "maxmeta":maxmeta, "maxacts":maxacts, "maxyear":maxyear}
#    
#    # If it"s a string, convert to list, but remember this
#    isstring = (type(limits)==str)
#    if isstring: limits = [limits] # Convert to list
#    
#    # If it"s a tuple, convert to a list before converting back at the end
#    istuple = (type(limits)==tuple)
#    if istuple: limits = list(limits)
#    
#    # If list argument is given, replace text labels with numeric limits
#    for i,m in enumerate(limits):
#        if m=="maxrate": limits[i] = maxrate
#        elif m=="maxpopsize": limits[i] = maxpopsize
#        elif m=="maxduration": limits[i] = maxduration
#        elif m=="maxmeta": limits[i] = maxmeta
#        elif m=="maxacts": limits[i] = maxacts
#        elif m=="maxyear": limits[i] = maxyear
#        else: limits[i] = limits[i] # This leaves limits[i] untouched if it"s a number or something
#    
#    # Wrap up
#    if isstring: return limits[0] # Return just a scalar
#    if istuple: return tuple(limits) # Convert back to a tuple
#    else: return limits # Or return the whole list


