"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

Version: 2018mar23
"""

from sciris.core import odict, today, getdate, defaultrepr, promotetolist, promotetoarray, indent, isnumber, sanitize
from atomica.system import AtomicaException
from numpy.random import uniform
from numpy import array, nan


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
        output = defaultrepr(self)
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
            data = {k: progdata[pkey][k] for k in ('cost', 'num_covered')}
            data['t'] = progdata['years']
            p = Program(short=pkey,
                        name=progdata['progs']['short'][np],
                        target_pops=[val for i,val in enumerate(progdata['pops']) if progdata['progs']['target_pops'][i]],
                        target_comps=[val for i,val in enumerate(progdata['comps']) if progdata['progs']['target_comps'][i]],
                        unitcost=progdata[pkey]['unitcost'],
                        capacity=progdata[pkey]['capacity'],
                        data=data
                        )
            programs.append(p)
        self.addprograms(progs=programs)
        
        # Read in the information for covout functions
        prognames = progdata['progs']['short']
        prog_effects = odict()
        for par,pardata in progdata['pars'].iteritems():
            prog_effects[par] = odict()
            for pop,popdata in pardata.iteritems():
                prog_effects[par][pop] = odict()
                for pno in range(len(prognames)):
                    bval = popdata['prog_vals'][0][pno]
                    lval = popdata['prog_vals'][1][pno]
                    hval = popdata['prog_vals'][2][pno]
                    vals = [val for val in [bval,lval,hval] if isnumber(val) and val is not nan]
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


    def hasallcovoutpars(self, detail=False, verbose=2):
        ''' Checks whether all the **required** coverage-outcome parameters are there for coverage-outcome rships'''
        result = True
        details = []
        for thispar in self.covout.keys():
            if not hasattr(self.covout.values()[thispar],'npi_val'):
                print('WARNING: %s NPI value is missing' % (thispar))
            else:
                if not self.covout.values()[thispar].npi_val.get() and self.covout.values()[thispar].npi_val.get()!=0:
                    result = False
                    details.append(thispar)
                for thisprog in self.progs_by_targetpar(thispartype)[thispop]: 
                    printv('Checking %s program' % thisprog.short, 4, verbose)
                    progeffect = self.covout[thispartype][thispop].ccopars.get(thisprog.short, None)
                    if not(progeffect) and progeffect!=0:
                        printv('WARNING: %s %s %s program effect is none' % (thispartype, str(thispop), thisprog.short), 4, verbose)
                        result = False
                        details.append(pars[thispartype].name)
                    else:
                        printv('%s %s %s program effect is %s' % (thispartype, str(thispop), thisprog.short, progeffect), 4, verbose)
        if detail: return list(set(details))
        else: return result


        
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
        self.unitcost   = None # dataframe -- note, 'year' if supplied (not necessary) is stored inside here
        self.capacity   = None # Capacity of program (a number) - optional - if not supplied, cost function is assumed to be linear
        
        # Populate the values
        self.update(short=short, name=name, data=data, unitcost=unitcost, year=year, capacity=capacity, target_pops=target_pops, target_pars=target_pars)
        return None


    def __repr__(self):
        ''' Print out useful info'''
        output = defaultrepr(self)
        output += '          Program name: %s\n'    % self.short
        output += '  Targeted populations: %s\n'    % self.target_pops
        output += '   Targeted parameters: %s\n'    % self.target_pars
        output += '\n'
        return output
    

    def update(self, short=None, name=None, data=None, capacity=None, unitcost=None, year=None, target_pops=None, target_pars=None):
        ''' Add data to a program, or otherwise update the values '''
        
        if short       is not None: self.short       = short
        if name        is not None: self.name        = name 
        if capacity    is not None: self.capacity    = capacity
        if target_pops is not None: self.target_pops = target_pops
        if data        is not None: self.data        = data
        if unitcost    is not None: self.unitcost    = unitcost
#        if targetpars is not None: settargetpars(targetpars) # targeted parameters
        
        # Finally, check everything
        if self.short is None: # self.short must exist
            errormsg = 'You must supply a short name for a program'
            raise AtomicaException(errormsg)
        if self.name is None:       self.name = self.short # If name not supplied, use short
        if self.target_pops is None: self.target_pops = [] # Empty list
        if self.target_pars is None: self.target_pars = [] # Empty list
            
        return None


    def optimizable(self):
        return True if self.targetpars else False


    def hasbudget(self):
        return True if self.ccdata['cost'] else False


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
#        output = defaultrepr(self)
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
        output = defaultrepr(self)
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
    
    

