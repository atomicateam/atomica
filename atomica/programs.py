"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

Version: 2018mar23
"""

from sciris.core import odict, today, getdate, defaultrepr

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
        output += 'Targeted populations: %s\n'    % self.targetpops
        output += '        Date created: %s\n'    % getdate(self.created)
        output += '       Date modified: %s\n'    % getdate(self.modified)
        output += '                 UID: %s\n'    % self.uid
        output += '============================================================\n'
        
        return output


#--------------------------------------------------------------------
# Program class
#--------------------------------------------------------------------
class Program(object):
    ''' Defines a single program.'''

    def __init__(self, short, name=None, targetpars=None, targetpops=None, ccpars=None, ccdata=None):
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
        
        def settargetpars(targetpars=None):
            pass
        
        def setdata(data=None, year=None):
            ''' Handle the spend-coverage, data, also complicated since have to convert to a dataframe '''
            datakeys = ['year', 'spend', 'coverage']
            if self.data is None: self.data = dataframe(cols=datakeys) # Create dataframe
            if year is None: year = Settings().now # If no year is supplied, reset it
            
            if isinstance(data, dataframe): 
                self.data = data # Right format already: use directly
            elif isinstance(data, dict):
                newdata = [data.get(key) for key in datakeys] # Get full row
                year = newdata[0] if newdata[0] is not None else year # Probably a simpler way of doing this, but use the year if it's supplied, else use the default
                currentdata = self.data.getrow(year, asdict=True) # Get current row as a dictionary
                if currentdata:
                    for i,key in enumerate(data.keys()):
                        if newdata[i] is None: newdata[i] = currentdata[key] # Replace with old data if new data is None
                self.data.addrow(newdata) # Add new data
            elif isinstance(data, list): # Assume it's a list of dicts
                for datum in data:
                    if isinstance(datum, dict):
                        setdata(datum) # It's a dict: iterate recursively to add unit costs
                    else:
                        errormsg = 'Could not understand list of data: expecting list of dicts, not list containing %s' % datum
                        raise OptimaException(errormsg)
            else:
                errormsg = 'Can only add data as a dataframe, dict, or list of dicts; this is not valid: %s' % data
                raise AtomicaException(errormsg)

            return None
        
        # Actually set everything
        if short      is not None: self.short      = short
        if name       is not None: self.name       = name 
        if capacity   is not None: self.capacity   = capacity
        if targetpops is not None: self.targetpops = promotetolist(targetpops, 'string') # key(s) for targeted populations
#        if targetpars is not None: settargetpars(targetpars) # targeted parameters
        if unitcost   is not None: setunitcost(unitcost, year) # unit cost(s)
        if data       is not None: setdata(data, year) # unit cost(s)
        
        # Finally, check everything
        if self.short is None: # self.short must exist
            errormsg = 'You must supply a short name for a program'
            raise OptimaException(errormsg)
        if self.name is None:       self.name = self.short # If name not supplied, use short
        if self.targetpops is None: self.targetpops = [] # Empty list
        if self.targetpars is None: self.targetpars = [] # Empty list
            
        return None




    def optimizable(self):
        return True if self.targetpars else False


    def hasbudget(self):
        return True if self.ccdata['cost'] else False


    def getcoverage(self, x, t, parset=None, results=None, total=True, proportion=False, toplot=False, sample='best'):
        '''Returns coverage for a time/spending vector'''
        pass

    def getbudget(self, x, t, parset=None, results=None, proportion=False, toplot=False, sample='best'):
        '''Returns budget for a coverage vector'''
        pass


#--------------------------------------------------------------------
# Functions 
#--------------------------------------------------------------------

def make_progset(progdata, project):
    

