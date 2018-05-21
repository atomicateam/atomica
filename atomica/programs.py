"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

Version: 2018mar23
"""

from sciris.core import odict, today, getdate, defaultrepr, dataframe, promotetolist
from atomica.system import AtomicaException


class ProgramInstructions(object):
    def __init__(self):
        """ Set up a structure that stores instructions for a model on how to use programs. """

        pass

    # if progs_start is None:
    #     options['progs_start'] = 2015.0
    # else:
    #     options['progs_start'] = progs_start
    # options['progs_end'] = np.inf
    # options['init_alloc'] = odict()
    # options['constraints'] = {'limits': odict(), 'max_yearly_change': odict(), 'impacts': odict()}
    #
    # if not progset is None:
    #     for prog in progset.progs:
    #         options['init_alloc'][prog.label] = prog.getDefaultBudget(year=progs_start)
    #         options['constraints']['limits'][prog.label] = {'vals': [0.0, np.inf], 'rel': True}
    #         if prog.func_specs['type'] == 'cost_only':
    #             options['constraints']['limits'][prog.label]['vals'] = [1.0, 1.0]
    #         else:
    #             # All programs that are not fixed-cost can have a default ramp constraint.
    #             # This should be fine for fixed-cost programs too, but is redundant and does not need to be explicit.
    #             options['constraints']['max_yearly_change'][prog.label] = {'val': np.inf, 'rel': True}
    #     for impact in progset.impacts.keys():
    #         options['constraints']['impacts'][impact] = {'vals': [0.0, np.inf]}
    # options['orig_alloc'] = dcp(options['init_alloc'])
    #
    # options['constraints']['total'] = sum(options['init_alloc'].values())
    # options['objectives'] = {settings.charac_pop_count: {'weight': -1, 'year': 2030.0}}
    # options[
    #     'saturate_with_default_budgets'] = True  # Set True so that optimization redistributes funds across entire progset.
    #
    # return options

#--------------------------------------------------------------------
# ProgramSet class
#--------------------------------------------------------------------
class ProgramSet(object):

    def __init__(self, name="default", programs=None, default_interaction="additive"):
        """ Class to hold all programs. """
        self.name = name
        self.default_interaction = default_interaction
        self.programs = odict()
        if programs is not None: self.addprograms(programs)
        else: self.updateprogset()
        self.defaultbudget = odict()
        self.created = today()
        self.modified = today()

    def __repr__(self):
        ''' Print out useful information'''
        output = defaultrepr(self)
        output += '    Program set name: %s\n'    % self.name
        output += '            Programs: %s\n'    % [prog for prog in self.programs]
        output += '        Date created: %s\n'    % getdate(self.created)
        output += '       Date modified: %s\n'    % getdate(self.modified)
        output += '============================================================\n'
        
        return output

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
        
        
#--------------------------------------------------------------------
# Program class
#--------------------------------------------------------------------
class Program(object):
    ''' Defines a single program.'''

    def __init__(self,short=None, name=None, data=None, unitcost=None, year=None, capacity=None, targetpops=None, targetpars=None):
        '''Initialize'''
        self.short = None
        self.name = None
        self.targetpars = None
        self.targetpops = None
        self.data       = None # Latest or estimated expenditure
        self.unitcost   = None # dataframe -- note, 'year' if supplied (not necessary) is stored inside here
        self.capacity   = None # Capacity of program (a number) - optional - if not supplied, cost function is assumed to be linear
        
        # Populate the values
        self.update(short=short, name=name, data=data, unitcost=unitcost, year=year, capacity=capacity, targetpops=targetpops, targetpars=targetpars)
        return None


    def __repr__(self):
        ''' Print out useful info'''
        output = defaultrepr(self)
        output += '          Program name: %s\n'    % self.short
        output += '  Targeted populations: %s\n'    % self.targetpops
        output += '   Targeted parameters: %s\n'    % self.targetpars
        output += '\n'
        return output
    

    def update(self, short=None, name=None, data=None, capacity=None, unitcost=None, year=None, targetpops=None, targetpars=None):
        ''' Add data to a program, or otherwise update the values '''
        
        if short      is not None: self.short      = short
        if name       is not None: self.name       = name 
        if capacity   is not None: self.capacity   = capacity
        if targetpops is not None: self.targetpops = targetpops
        if data       is not None: self.data = data
        if unitcost   is not None: self.unitcost = unitcost
#        if targetpars is not None: settargetpars(targetpars) # targeted parameters
        
        # Finally, check everything
        if self.short is None: # self.short must exist
            errormsg = 'You must supply a short name for a program'
            raise AtomicaException(errormsg)
        if self.name is None:       self.name = self.short # If name not supplied, use short
        if self.targetpops is None: self.targetpops = [] # Empty list
        if self.targetpars is None: self.targetpars = [] # Empty list
            
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
# Functions 
#--------------------------------------------------------------------

    

