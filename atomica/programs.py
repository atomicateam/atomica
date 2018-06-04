"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

Version: 2018mar23
"""

from sciris.core import odict, today, getdate, desc, promotetolist, promotetoarray, indent, isnumber, sanitize, dataframe, checktype
from atomica.system import AtomicaException
from numpy.random import uniform
from numpy import array, nan, isnan


#--------------------------------------------------------------------
# ProgramSet class
#--------------------------------------------------------------------
class ProgramSet(object):

    def __init__(self, name="default", programs=None, covouts=None, default_cov_interaction="additive", default_imp_interaction="best"):
        """ Class to hold all programs and programmatic effects. """
        self.name = name
        self.programs = odict()
        self.default_cov_interaction = default_cov_interaction
        self.default_imp_interaction = default_imp_interaction
        self.covout = odict()
        if programs is not None: self.addprograms(programs)
        if covouts is not None: self.addcovouts(covouts)
#        else: self.updateprogset()
        self.defaultbudget = odict()
        self.created = today()
        self.modified = today()
        return None

    def __repr__(self):
        ''' Print out useful information'''
        output = desc(self)
        output += '    Program set name: %s\n'    % self.name
        output += '            Programs: %s\n'    % [prog for prog in self.programs]
        output += '        Date created: %s\n'    % getdate(self.created)
        output += '       Date modified: %s\n'    % getdate(self.modified)
        output += '============================================================\n'
        
        return output

    def make(self, progdata=None, project=None):
        '''Make a program set from a program data object.'''

        # Sort out inputs
        if progdata is None:
            if project.progdata is None:
                errormsg = 'You need to supply program data or a project with program data in order to make a program set.'
                raise AtomicaException(errormsg)
            else:
                progdata = project.progdata
                
        # Check if the populations match - if not, raise an error, if so, add the data
        if project is not None and set(progdata['pops']) != set(project.popnames):
            errormsg = 'The populations in the program data are not the same as those that were loaded from the epi databook: "%s" vs "%s"' % (progdata['pops'], set(project.popnames))
            raise AtomicaException(errormsg)
                
        nprogs = len(progdata['progs']['short'])
        programs = []
        
        # Read in the information for programs
        for np in range(nprogs):
            pkey = progdata['progs']['short'][np]
            data = {k: progdata[pkey][k] for k in ('spend', 'basespend')}
            data['year'] = progdata['years']
            p = Program(short=pkey,
                        name=progdata['progs']['short'][np],
                        target_pops=[val for i,val in enumerate(progdata['pops']) if progdata['progs']['target_pops'][i]],
                        target_comps=[val for i,val in enumerate(progdata['comps']) if progdata['progs']['target_comps'][i]],
                        capacity=progdata[pkey]['capacity'],
                        data=data
                        )
            programs.append(p)
        self.addprograms(progs=programs)
        
        # Update the unit costs (done separately as by year)
        ## TODO : REVISE THIS, THE FORMAT ISN'T RIGHT
        for np in range(nprogs):
            pkey = progdata['progs']['short'][np]
            for yrno,year in enumerate(progdata['years']):
                unitcost = [progdata[pkey]['unitcost'][blh][yrno] for blh in range(3)]
                if not (isnan(unitcost)).all():
                    self.programs[np].update(unitcost=sanitize(unitcost), year=year)
        
        # Read in the information for covout functions
        prognames = progdata['progs']['short']
        prog_effects = odict()
        for par,pardata in progdata['pars'].iteritems():
            prog_effects[par] = odict()
            for pop,popdata in pardata.iteritems():
                prog_effects[par][pop] = odict()
                for pno in range(len(prognames)):
                    vals = []
                    for blh in range(3):
                        val = popdata['prog_vals'][blh][pno]
                        if isnumber(val) and val is not nan: vals.append(val) 
                    if vals: prog_effects[par][pop][prognames[pno]] = vals
                if not prog_effects[par][pop]: prog_effects[par].pop(pop) # No effects, so remove
            if not prog_effects[par]: prog_effects.pop(par) # No effects, so remove
            
        self.addcovouts(progdata['pars'], prog_effects)
        return None

        
    def addprograms(self, progs=None, replace=False):
        ''' Add a list of programs '''
        
        # Process programs
        if progs is not None:
            progs = promotetolist(progs)
        else:
            errormsg = 'Programs to add should not be None'
            raise AtomicaException(errormsg)
        if replace:
            self.programs = odict()
        for prog in progs:
            if isinstance(prog, dict):
                prog = Program(**prog)
            if type(prog)!=Program:
                errormsg = 'Programs to add must be either dicts or program objects, not %s' % type(prog)
                raise AtomicaException(errormsg)
            
            # Save it
            self.programs[prog.short] = prog

        return None


    def rmprograms(self, progs=None, die=True):
        ''' Remove one or more programs from both the list of programs and also from the covout functions '''
        if progs is None:
            self.programs = odict() # Remove them all
        progs = promotetolist(progs)
        for prog in progs:
            try:
                self.programs.pop[prog]
            except:
                errormsg = 'Could not remove program named %s' % prog
                if die: raise AtomicaException(errormsg)
                else: print(errormsg)
            for co in self.covout.values(): # Remove from coverage-outcome functions too
                co.progs.pop(prog, None)
        return None


    def addcovout(self, par=None, pop=None, cov_interaction=None, imp_interaction=None, npi_val=None, max_val=None, prog=None, prognames=None):
        ''' add a single coverage-outcome parameter '''
        # Process inputs
        if cov_interaction is None: cov_interaction = self.default_cov_interaction
        if imp_interaction is None: imp_interaction = self.default_imp_interaction
        self.covout[(par, pop)] = Covout(par=par, pop=pop, cov_interaction=cov_interaction, imp_interaction=imp_interaction, npi_val=npi_val, max_val=max_val, prog=prog)
        return None


    def addcovouts(self, covouts=None, prog_effects=None):
        '''
        Add an odict of coverage-outcome parameters. Note, assumes a specific structure, as follows:
        covouts[parname][popname] = odict()
        '''
        # Process inputs
        if covouts is not None:
            if isinstance(covouts, list) or isinstance(covouts,type(array([]))):
                errormsg = 'Expecting a dictionary with specific structure, not a list'
                raise AtomicaException(errormsg)
        else:
            errormsg = 'Covout list not supplied.'
            raise AtomicaException(errormsg)
            
        for par,pardata in covouts.iteritems():
            if par in prog_effects.keys():
                for pop,popdata in covouts[par].iteritems():
                    if pop in prog_effects[par].keys():
                        # Sanitize inputs
                        npi_val = sanitize(popdata['npi_val'])
                        max_val = sanitize(popdata['max_val'])
                        self.addcovout(par=par, pop=pop, cov_interaction=popdata['interactions'][0], imp_interaction=popdata['interactions'][1], npi_val=npi_val, max_val=max_val, prog=prog_effects[par][pop])
        
        return None

    ## TODO : WRITE THESE
    def getpars(self, coverage=None, year=None):
        pass

    def defaultbudget(self, year=None):
        pass

    def reconcile(self):
        pass

    def compareoutcomes(self):
        pass


#--------------------------------------------------------------------
# Program class
#--------------------------------------------------------------------
class Program(object):
    ''' Defines a single program.'''

    def __init__(self,short=None, name=None, data=None, unitcost=None, year=None, capacity=None, target_pops=None, target_comps=None, target_pars=None):
        '''Initialize'''
        self.short = None
        self.name = None
        self.target_pars = None
        self.target_pops = None
        self.data       = None # Latest or estimated expenditure
        self.unitcost   = None 
        self.capacity   = None # Capacity of program (a number) - optional - if not supplied, cost function is assumed to be linear
        
        # Populate the values
        self.update(short=short, name=name, data=data, unitcost=unitcost, year=year, capacity=capacity, target_pops=target_pops, target_pars=target_pars)
        return None


    def __repr__(self):
        ''' Print out useful info'''
        output = desc(self)
        output += '          Program name: %s\n'    % self.short
        output += '  Targeted populations: %s\n'    % self.target_pops
        output += '   Targeted parameters: %s\n'    % self.target_pars
        output += '\n'
        return output
    


    def update(self, short=None, name=None, data=None, unitcost=None, capacity=None, year=None, target_pops=None, target_pars=None):
        ''' Add data to a program, or otherwise update the values. Same syntax as init(). '''
        
        def settargetpars(targetpars=None):
            ''' Handle targetpars -- a little complicated since it's a list of dicts '''
            targetparkeys = ['param', 'pop']
            targetpars = promotetolist(targetpars) # Let's make sure it's a list before going further
            for tp,targetpar in enumerate(targetpars):
                if isinstance(targetpar, dict): # It's a dict, as it needs to be
                    thesekeys = sorted(targetpar.keys())
                    if thesekeys==targetparkeys: # Keys are correct -- main usage case!!
                        targetpars[tp] = targetpar
                    else:
                        errormsg = 'Keys for a target parameter must be %s, not %s' % (targetparkeys, thesekeys)
                        raise AtomicaException(errormsg)
                elif isinstance(targetpar, basestring): # It's a single string: assume only the parameter is specified
                    targetpars[tp] = {'param':targetpar, 'pop':'tot'} # Assume 'tot'
                elif isinstance(targetpar, tuple): # It's a list, assume it's in the usual order
                    if len(targetpar)==2:
                        targetpars[tp] = {'param':targetpar[0], 'pop':targetpar[1]} # If a list or tuple, assume this order
                    else:
                        errormsg = 'When supplying a targetpar as a list or tuple, it must have length 2, not %s' % len(targetpar)
                        raise AtomicaException(errormsg)
                else:
                    errormsg = 'Targetpar must be string, tuple, or dict, not %s' % type(targetpar)
                    raise AtomicaException(errormsg)
            self.targetpars = targetpars # Actually set it
            return None
        
        def setunitcost(unitcost=None, year=None):
            '''
            Handle the unit cost, also complicated since have to convert to a dataframe. 
            
            Unit costs can be specified as a number, a tuple, or a dict. If a dict, they can be 
            specified with val as a tuple, or best, low, high as keys. Examples:
            
            setunitcost(21) # Assumes current year and that this is the best value
            setunitcost(21, year=2014) # Specifies year
            setunitcost(year=2014, unitcost=(11, 31)) # Specifies year, low, and high
            setunitcost({'year':2014', 'best':21}) # Specifies year and best
            setunitcost({'year':2014', 'val':(21, 11, 31)}) # Specifies year, best, low, and high
            setunitcost({'year':2014', 'best':21, 'low':11, 'high':31) # Specifies year, best, low, and high
            '''
            
            # Preprocessing
            unitcostkeys = ['year', 'best', 'low', 'high']
            if year is None: year = 2018. # TEMPORARY
            if self.unitcost is None: self.unitcost = dataframe(cols=unitcostkeys) # Create dataframe
            
            # Handle cases
            if isinstance(unitcost, dataframe): 
                self.unitcost = unitcost # Right format already: use directly
            elif checktype(unitcost, 'arraylike'): # It's a list of....something, either a single year with uncertainty bounds or multiple years
                if isnumber(unitcost[0]): # It's a number (or at least the first entry is): convert to values and use
                    best,low,high = Val(unitcost).get('all') # Convert it to a Val to do proper error checking and set best, low, high correctly
                    self.unitcost.addrow([year, best, low, high])
                else: # It's not a list of numbers, so have to iterate
                    for uc in unitcost: # Actually a list of unit costs
                        if isinstance(uc, dict): 
                            setunitcost(uc) # It's a dict: iterate recursively to add unit costs
                        else:
                            errormsg = 'Could not understand list of unit costs: expecting list of floats or list of dicts, not list containing %s' % uc
                            raise AtomicaException(errormsg)
            elif isinstance(unitcost, dict): # Other main usage case -- it's a dict
                if any([key not in unitcostkeys+['val'] for key in unitcost.keys()]):
                    errormsg = 'Mismatch between supplied keys %s and key options %s' % (unitcost.keys(), unitcostkeys)
                    raise AtomicaException(errormsg)
                val = unitcost.get('val') # First try to get 'val'
                if val is None: # If that fails, get other arguments
                    val = [unitcost.get(key) for key in ['best', 'low', 'high']] # Get an array of values...
                best,low,high = Val(val).get('all') # ... then sanitize them via Val
                self.unitcost.addrow([unitcost.get('year',year), best, low, high]) # Actually add to dataframe
            else:
                errormsg = 'Expecting unit cost of type dataframe, list/tuple/array, or dict, not %s' % type(unitcost)
                raise AtomicaException(errormsg)
            return None

        
        def setdata(data=None, year=None):
            ''' Handle the spend-coverage, data, also complicated since have to convert to a dataframe '''
            datakeys = ['year', 'spend', 'basespend']
            if self.data is None: self.data = dataframe(cols=datakeys) # Create dataframe
            if year is None: year = 2018. # TEMPORARY
            
            if isinstance(data, dataframe): 
                self.data = data # Right format already: use directly
            elif isinstance(data, dict):
                data = {key:promotetolist(data.get(key)) for key in datakeys} # Get full row
                if data['year'] is not None:
                    for n,year in enumerate(data['year']):
                        currentdata = self.data.findrow(year,asdict=True) # Get current row as a dictionary
                        if currentdata is not None:
                            for key in data.keys():
                                if data[key][n] is None: data[key][n] = currentdata[key] # Replace with old data if new data is None
                        thesedata = [data['year'][n], data['spend'][n], data['basespend'][n]] # Get full row - WARNING, FRAGILE TO ORDER!
                        self.data.addrow(thesedata) # Add new data
            elif isinstance(data, list): # Assume it's a list of dicts
                for datum in data:
                    if isinstance(datum, dict):
                        setdata(datum) # It's a dict: iterate recursively
                    else:
                        errormsg = 'Could not understand list of data: expecting list of dicts, not list containing %s' % datum
                        raise AtomicaException(errormsg)
            else:
                errormsg = 'Can only add data as a dataframe, dict, or list of dicts; this is not valid: %s' % data
                raise AtomicaException(errormsg)

            return None
        
        # Actually set everything
        if short       is not None: self.short          = short # short name
        if name        is not None: self.name           = name # full name
        if target_pops is not None: self.target_pops    = promotetolist(target_pops, 'string') # key(s) for targeted populations

        if capacity    is not None: self.capacity       = Val(sanitize(capacity)[-1]) # saturation coverage value - TODO, ADD YEARS

#        if target_pars is not None: settargetpars(target_pars) # targeted parameters

        if unitcost    is not None: setunitcost(unitcost, year) # unit cost(s)
        if data        is not None: setdata(data, year) # spend and coverage data
        
        # Finally, check everything
        if self.short is None: # self.short must exist
            errormsg = 'You must supply a short name for a program'
            raise AtomicaException(errormsg)
        if self.name is None:       self.name = self.short # If name not supplied, use short
        if self.target_pops is None: self.target_pops = [] # Empty list
        if self.target_pars is None: self.target_pars = [] # Empty list
            
        return None
    
    
    def adddata(self, data=None, year=None, spend=None, basespend=None):
        ''' Convenience function for adding data. Use either data as a dict/dataframe, or use kwargs, but not both '''
        if data is None:
            data = {'year':float(year), 'spend':spend, 'basespend':basespend}
        self.update(data=data)
        return None
        
        
    def addpars(self, unitcost=None, capacity=None, year=None):
        ''' Convenience function for adding saturation and unit cost. year is ignored if supplied in unitcost. '''
        # Convert inputs
        if year is not None: year=float(year)
        if unitcost is not None: unitcost=promotetolist(unitcost)
        self.update(unitcost=unitcost, capacity=capacity, year=year)
        return None
    
    
    def getspend(self, year=None, total=False, die=False):
        ''' Convenience function for getting the current spending '''
        if year is None: year = 2018. # TEMPORARY
        try:
            thisdata = self.data.findrow(year, closest=True, asdict=True) # Get data
            spend = thisdata['spend']
            if spend is None: spend = 0 # If not specified, assume 0
            if total: 
                basespend = thisdata['basespend'] # Add baseline spending
                if basespend is None: basespend = 0 # Likewise assume 0
                spend += basespend
            return spend
        except Exception as E:
            if die:
                errormsg = 'Retrieving spending failed: %s' % E.message
                raise AtomicaException(errormsg)
            else:
                return None
    
    
    def getunitcost(self, year=None, die=False):
        ''' Convenience function for getting the current unit cost '''
        if year is None: year = 2018. # TEMPORARY
        try:
            thisdata = self.unitcost.findrow(year, closest=True, asdict=True) # Get data
            unitcost = thisdata['best']
            return unitcost
        except Exception as E:
            if die:
                errormsg = 'Retrieving unit cost failed: %s' % E.message
                raise AtomicaException(errormsg)
            else: # If not found, don't die, just return None
                return None
    
#import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
    def optimizable(self, doprint=False, partial=False):
        '''
        Return whether or not a program can be optimized.
        
        Arguments:
            doprint = whether or not to print out why a program can't be optimized
            partial = flag programs that are only partially ready for optimization (some data entered), skipping those that have no data entered
        '''
        valid = True # Assume the best
        tests = {}
        try:
            tests['targetpops invalid'] = len(self.target_pops)<1
            tests['targetpars invalid'] = len(self.target_pars)<1
            tests['unitcost invalid']   = not(isnumber(self.getunitcost()))
            tests['capacity invalid']   = self.capacity is None
            if any(tests.values()):
                valid = False # It's looking like it can't be optimized
                if partial and all(tests.values()): valid = True # ...but it's probably just an other program, so skip it
                if not valid and doprint:
                    print('Program not optimizable for the following reasons: %s' % '\n'.join([key for key,val in tests.items() if val]))
                
        except Exception as E:
            valid = False
            if doprint:
                print('Program not optimizable because an exception was encountered: %s' % E.message)
        
        return valid
        

    def hasbudget(self):
        return True if not (isnan(array([x for x in self.data['spend']]))).all() else False #TODO, FIGURE OUT WHY SIMPLER WAY DOESN'T WORK!!!

# TODO: WRITE THESE
    def getcoverage(self, budget=None, t=None, parset=None, results=None, total=True, proportion=False, toplot=False, sample='best'):
        '''Returns coverage for a time/spending vector'''
        pass

    def getbudget(self, t=None, parset=None, results=None, proportion=False, toplot=False, sample='best'):
        '''Returns budget for a coverage vector'''
        pass


#--------------------------------------------------------------------
# Covout
#--------------------------------------------------------------------
class Covout(object):
    '''
    Coverage-outcome object 

    Example:
    Covout(par='contacts',
           pop='Adults',
           npi_val=120,
           max_val=[10,5,15],
           progs={'Prog1':[15,10,10], 'Prog2':20}
           )
    '''
    
    def __init__(self, par=None, pop=None, cov_interaction=None, imp_interaction=None, npi_val=None, max_val=None, prog=None):
        self.par = par
        self.pop = pop
        self.cov_interaction = cov_interaction
        self.imp_interaction = imp_interaction
        self.npi_val = Val(npi_val)
        self.max_val = Val(max_val)
        self.progs = odict()
        if prog is not None: self.add(prog=prog)
        return None
    
    def __repr__(self):
#        output = desc(self)
        output  = indent('   Parameter: ', self.par)
        output += indent('  Population: ', self.pop)
        output += indent('     NPI val: ', self.npi_val.get('all'))
        output += indent('     Max val: ', self.max_val.get('all'))
        output += indent('    Programs: ', ', '.join(['%s: %s' % (key,val.get('all')) for key,val in self.progs.items()]))
        output += '\n'
        return output
        
    
    def add(self, prog=None, val=None):
        ''' 
        Accepts either
        self.add([{'FSW':[0.3,0.1,0.4]}, {'SBCC':[0.1,0.05,0.15]}])
        or
        self.add('FSW', 0.3)
        '''
        if isinstance(prog, dict):
            for key,val in prog.items():
                self.progs[key] = Val(val)
        elif isinstance(prog, (list, tuple)):
            for key,val in prog:
                self.progs[key] = Val(val)
        elif isinstance(prog, basestring) and val is not None:
            self.progs[prog] = Val(val)
        else:
            errormsg = 'Could not understand prog=%s and val=%s' % (prog, val)
            raise AtomicaException(errormsg)
        return None
            

#--------------------------------------------------------------------
# Val
#--------------------------------------------------------------------
class Val(object):
    '''
    A single value including uncertainty
    
    Can be set the following ways:
    v = Val(0.3)
    v = Val([0.2, 0.4])
    v = Val([0.3, 0.2, 0.4])
    v = Val(best=0.3, low=0.2, high=0.4)
    
    Can be called the following ways:
    v() # returns 0.3
    v('best') # returns 0.3
    v(what='best') # returns 0.3
    v('rand') # returns value between low and high (assuming uniform distribution)
    
    Can be updated the following ways:
    v(0.33) # resets best
    v([0.22, 0.44]) # resets everything
    v(best=0.33) # resets best
    
    '''
    
    def __init__(self, best=None, low=None, high=None, dist=None):
        ''' Allow the object to be initialized, but keep the same infrastructure for updating '''
        self.best = None
        self.low = None
        self.high = None
        self.dist = None
        self.update(best=best, low=low, high=high, dist=dist)
        return None
    
    
    def __repr__(self):
        output = desc(self)
        return output
    
    
    def __call__(self, *args, **kwargs):
        ''' Convenience function for both update and get '''
        
        # If it's None or if the key is a string (e.g. 'best'), get the values:
        if len(args)+len(kwargs)==0 or 'what' in kwargs or (len(args) and type(args[0])==str):
            return self.get(*args, **kwargs)
        else: # Otherwise, try to set the values
            self.update(*args, **kwargs)
    
    def __getitem__(self, *args, **kwargs):
        ''' Allows you to call e.g. val['best'] instead of val('best') '''
        return self.get(*args, **kwargs)
    
    
    def update(self, best=None, low=None, high=None, dist=None):
        ''' Actually set the values -- very convoluted, but should be flexible and work :)'''
        
        # Reset these values if already supplied
        if best is None and self.best is not None: best = self.best
        if low  is None and self.low  is not None: low  = self.low 
        if high is None and self.high is not None: high = self.high 
        if dist is None and self.dist is not None: dist = self.dist
        
        # Handle values
        if best is None: # Best is not supplied, so use high and low, e.g. Val(low=0.2, high=0.4)
            if low is None or high is None:
                errormsg = 'If not supplying a best value, you must supply both low and high values'
                raise AtomicaException(errormsg)
            else:
                best = (low+high)/2. # Take the average
        elif isinstance(best, dict):
            self.update(**best) # Assume it's a dict of args, e.g. Val({'best':0.3, 'low':0.2, 'high':0.4})
        else: # Best is supplied
            best = promotetoarray(best)
            if len(best)==1: # Only a single value supplied, e.g. Val(0.3)
                best = best[0] # Convert back to number
                if low is None: low = best # If these are missing, just replace them with best
                if high is None: high = best
            elif len(best)==2: # If length 2, assume high-low supplied, e.g. Val([0.2, 0.4])
                if low is not None and high is not None:
                    errormsg = 'If first argument has length 2, you cannot supply high and low values'
                    raise AtomicaException(errormsg)
                low = best[0]
                high = best[1]
                best = (low+high)/2.
            elif len(best)==3: # Assume it's called like Val([0.3, 0.2, 0.4])
                low, best, high = sorted(best) # Allows values to be provided in any order
            else:
                errormsg = 'Could not understand input of best=%s, low=%s, high=%s' % (best, low, high)
                raise AtomicaException(errormsg)
        
        # Handle distributions
        validdists = ['uniform']
        if dist is None: dist = validdists[0]
        if dist not in validdists:
            errormsg = 'Distribution "%s" not valid; choices are: %s' % (dist, validdists)
            raise AtomicaException(errormsg) 
        
        # Store values
        self.best = float(best)
        self.low  = float(low)
        self.high = float(high)
        self.dist = dist
        if not low<=best<=high:
            errormsg = 'Values are out of order (check that low=%s <= best=%s <= high=%s)' % (low, best, high)
            raise AtomicaException(errormsg) 
        
        return None
    
    
    def get(self, what=None, n=1):
        '''
        Get the value from this distribution. Examples (with best=0.3, low=0.2, high=0.4):
        
        val.get() # returns 0.3
        val.get('best') # returns 0.3
        val.get(['low', 'best',' high']) # returns [0.2, 0.3, 0.4]
        val.get('rand') # returns, say, 0.3664
        val.get('all') # returns [0.3, 0.2, 0.4]
        
        The seed() call should ensure pseudorandomness.
        '''
        
        if what is None or what is 'best': val = self.best# Haha this is funny but works
        elif what is 'low':                val = self.low
        elif what is 'high':               val = self.high
        elif what is 'all':                val = [self.best, self.low, self.high]
        elif what in ['rand','random']:
            if self.dist=='uniform':       val = uniform(low=self.low, high=self.high, size=n)
            else:
                errormsg = 'Distribution %s is not implemented, sorry' % self.dist
                raise AtomicaException(errormsg)
        elif type(what)==list:             val = [self.get(wh) for wh in what]# Allow multiple values to be used
        else:
            errormsg = 'Could not understand %s, expecting a valid string (e.g. "best") or list' % what
            raise AtomicaException(errormsg)
        return val
    
    

