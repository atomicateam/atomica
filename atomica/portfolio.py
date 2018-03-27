# -*- coding: utf-8 -*-
"""
Optima Core portfolio definition file.
Implements a container class for Optima projects of all types.
"""

from atomica.system import applyToAllMethods, logUsage, accepts

@applyToAllMethods(logUsage)
class Portfolio(object):
    """ The Optima Core portfolio class, a higher-level container for Optima Core projects. """

    def __init__(self, name = "default"):
        """ Initialize the portfolio. """
        self.name = str()
        
        self.setName(name)
    
    @accepts(str)
    def setName(self, name):
        """ Set primary human-readable identifier for the portfolio. """
        self.name = name
    
    @returns(str)
    def getName(self):
        """ Get primary human-readable identifier for the portfolio. """
        return self.name

    def __repr__(self):
        """ String representation of the portfolio. """
        return ""