"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

Version: 2018mar23
"""

#from optima import OptimaException, Link, printv, uuid, today, sigfig, getdate, dcp, smoothinterp, findinds, odict, Settings, sanitize, defaultrepr, isnumber, promotetoarray, vec2obj, asd, convertlimits
#from numpy import ones, prod, array, zeros, exp, log, append, nan, isnan, maximum, minimum, sort, concatenate as cat, transpose, mean, argsort
#from random import uniform

from sciris.utils import odict, today, getdate

class Programset(object):

    def __init__(self, name='default', programs=None, default_interaction='additive', project=None):
        ''' Initialize '''
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
