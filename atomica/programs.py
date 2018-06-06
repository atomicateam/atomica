"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

Version: 2018mar23
"""

from sciris.core import odict, today, getdate, defaultrepr, dataframe, promotetolist
from atomica.system import AtomicaException
from sciris.utils import uuid
from atomica.utils import NamedItem

#--------------------------------------------------------------------
# ProgramSet class
#--------------------------------------------------------------------
class ProgramSet(NamedItem):

    def __init__(self, name="default", programs=None, default_interaction="additive"):
        """ Class to hold all programs. """
        NamedItem.__init__(self,name)

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
class Program(NamedItem):
    ''' Defines a single program.'''

    def __init__(self,short=None, name=None, data=None, unitcost=None, year=None, capacity=None, targetpops=None, targetpars=None):
        '''Initialize'''
        NamedItem.__init__(self,name)

        self.short = None
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

    

