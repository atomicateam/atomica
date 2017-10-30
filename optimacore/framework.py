# -*- coding: utf-8 -*-
"""
Optima Core project framework file.
Contains all information describing the context of a project.
This includes a description of the Markov chain network underlying project dynamics.
"""

from optimacore.system import applyToAllMethods, logUsage, accepts, returns

@applyToAllMethods(logUsage)
class ProjectFramework(object):
    """  """
    
    def __init__(self):
        """  """
        pass
    
    def __repr__(self):
        """ String representation of the project framework. """
        return ""