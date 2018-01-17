# -*- coding: utf-8 -*-
"""
Optima Core project definition file.
Implements a class to investigate a context represented by a complex Markov chain.
The archetypal example is an epidemic within a geographical location, where entities move between disease states.
"""

from optimacore.system import applyToAllMethods, logUsage, accepts, returns
from optimacore.system import logger, SystemSettings
from optimacore.framework import ProjectFramework
from optimacore.databook import createDatabookFunc
from optimacore.excel import ExcelSettings

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
        self.framework = ProjectFramework()
        
        self.setName(name)

    def createDatabook(self, databook_path = None, instructions = None, databook_type = SystemSettings.DATABOOK_DEFAULT_TYPE):
        """
        Generate a data-input Excel spreadsheet corresponding to the framework of this project.
        An object in the form of DatabookInstructions can optionally be passed in to describe how many databook items should be templated.
        """
        if databook_path is None: databook_path = "./databook_" + self.name + ExcelSettings.FILE_EXTENSION
        createDatabookFunc(framework = self.getFramework(), databook_path = databook_path, instructions = instructions, databook_type = databook_type)
    
    @accepts(str)
    def setName(self, name):
        """ Set primary human-readable identifier for the project. """
        self.name = name
    
    @returns(str)
    def getName(self):
        """ Get primary human-readable identifier for the project. """
        return self.name
    
    @accepts(ProjectFramework)
    def setFramework(self, framework):
        """ Set the underlying context framework for the project. """
        self.framework = framework
    
    @returns(ProjectFramework)
    def getFramework(self):
        """ Get the underlying context framework for the project. """
        return self.framework

#    def __repr__(self):
#        """ String representation of the project. """
#        return ""