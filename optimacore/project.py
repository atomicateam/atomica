# -*- coding: utf-8 -*-
"""
Optima Core project definition file.
Implements a class to investigate a context represented by a complex Markov chain.
The archetypal example is an epidemic within a geographical location, where entities move between disease states.
"""

from optimacore.system import applyToAllMethods, logUsage

@applyToAllMethods(logUsage)
class Project(object):
    """
    The fundamental high-level Optima object representing a complex Markov chain context.
    It stores the cascade framework, i.e. Markov chain network definitions, as well as data provided by a user.
    Almost all Optima Core functionality is provided by this class, including dynamic simulations and optimization analyses.
    """

    def __init__(self, name = "default"):
        """ Initialize the project. """
        self.name = str()
        
        self.setName(name)
    
    def setName(self, name):
        """ Set primary human-readable identifier for the project. """
        self.name = name
    
    def getName(self):
        """ Get primary human-readable identifier for the project. """
        return self.name

    def __repr__(self):
        """ String representation of the project. """
        return ""