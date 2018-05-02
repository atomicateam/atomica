"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

Version: 2018mar23
"""

from sciris.core import odict, today, getdate, defaultrepr

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

class Program(object):
    ''' Defines a single program.'''

    def __init__(self, short, name=None, targetpars=None, targetpops=None, ccpars=None, ccdata=None):
        '''Initialize'''
        self.short = short
        self.name = name
        self.targetpars = targetpars
        self.targetpops = targetpops
        self.ccdata = ccdata if ccdata else {'t':[],'cost':[],'coverage':[]}


    def __repr__(self):
        ''' Print out useful info'''
        output = defaultrepr(self)
        output += '          Program name: %s\n'    % self.short
        output += '  Targeted populations: %s\n'    % self.targetpops
        output += '   Targeted parameters: %s\n'    % self.targetpars
        output += '\n'
        return output
    

    def optimizable(self):
        return True if self.targetpars else False


    def hasbudget(self):
        return True if self.ccdata['cost'] else False


    def getcoverage(self, x, t, parset=None, results=None, total=True, proportion=False, toplot=False, sample='best'):
        '''Returns coverage for a time/spending vector'''

        # Validate inputs
        x = promotetoarray(x)
        t = promotetoarray(t)

        poptargeted = self.gettargetpopsize(t=t, parset=parset, results=results, total=False)

        totaltargeted = sum(poptargeted.values())
        totalreached = self.costcovfn.evaluate(x=x, popsize=totaltargeted, t=t, toplot=toplot, sample=sample)

        if total: return totalreached/totaltargeted if proportion else totalreached
        else:
            popreached = odict()
            targetcomposition = self.targetcomposition if self.targetcomposition else self.gettargetcomposition(t=t,parset=parset) 
            for targetpop in self.targetpops:
                popreached[targetpop] = totalreached*targetcomposition[targetpop]
                if proportion: popreached[targetpop] /= poptargeted[targetpop]

            return popreached


    def getbudget(self, x, t, parset=None, results=None, proportion=False, toplot=False, sample='best'):
        '''Returns budget for a coverage vector'''

        poptargeted = self.gettargetpopsize(t=t, parset=parset, results=results, total=False)
        totaltargeted = sum(poptargeted.values())
        if not proportion: reqbudget = self.costcovfn.evaluate(x=x,popsize=totaltargeted,t=t,inverse=True,toplot=False,sample=sample)
        else: reqbudget = self.costcovfn.evaluate(x=x*totaltargeted,popsize=totaltargeted,t=t,inverse=True,toplot=False,sample=sample)
        return reqbudget
