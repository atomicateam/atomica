"""
SETTINGS
Store all the settings for a project.
Version: 2018mar26
"""

from atomica.system import AtomicaException, logger
from sciris.utils import defaultrepr, inclusiverange, isnumber # CK: warning, should replace printv with logger
from numpy import shape, array #arange, concatenate as cat, 
import numpy as np

class ProjectSettings(object):
    def __init__(self, sim_start=None, sim_end=None, sim_dt=None):
        
        self.sim_start = sim_start if sim_start is not None else 2000.0
        self.sim_end = sim_end if sim_end is not None else 2030.0
        self.sim_dt = sim_dt if sim_dt is not None else 1.0/4

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

    @property
    def tvec(self):
        return np.arange(self.sim_start, self.sim_end + self.sim_dt / 2, self.sim_dt)
    
    def updateTimeVector(self, start=None, end=None, dt=None):
        """ Calculate time vector. """
        if not start is None: self.sim_start = start
        if not end is None: self.sim_end = end
        if not dt is None: self.sim_dt = dt
    
    
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


