# -*- coding: utf-8 -*-
"""
Optima Core project definition file.
Implements a class to investigate a context represented by a complex Markov chain.
The archetypal example is an epidemic within a geographical location, where entities move between disease states.
"""

from optimacore.system import SystemSettings as SS
from optimacore.excel import ExcelSettings as ES

from optimacore.system import applyToAllMethods, logUsage, accepts
from optimacore.framework import ProjectFramework
from optimacore.data import ProjectData
from optimacore.workbook_export import writeWorkbook

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
        self.data = ProjectData()
        
        self.setName(name)

    def createDatabook(self, databook_path = None, instructions = None, databook_type = SS.DATABOOK_DEFAULT_TYPE):
        """
        Generate an empty data-input Excel spreadsheet corresponding to the framework of this project.
        An object in the form of DatabookInstructions can optionally be passed in to describe how many databook items should be templated.
        """
        if databook_path is None: databook_path = "./databook_" + self.name + ES.FILE_EXTENSION
        writeWorkbook(workbook_path = databook_path, framework = self.framework, data = None, instructions = instructions, workbook_type = SS.STRUCTURE_KEY_DATA)
    
    @accepts(str)
    def setName(self, name):
        """ Set primary human-readable identifier for the project. """
        self.name = name