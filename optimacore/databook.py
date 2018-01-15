# -*- coding: utf-8 -*-
"""
Optima Core databook file.
Contains functions for creating databooks from project frameworks and then importing them.
"""

from optimacore.system import logger, applyToAllMethods, logUsage, accepts, returns, prepareFilePath, SystemSettings
from optimacore.framework_settings import FrameworkSettings
from optimacore.framework import ProjectFramework
from optimacore.databook_settings import DatabookSettings

from collections import OrderedDict

import xlsxwriter as xw

@applyToAllMethods(logUsage)
class DatabookInstructions(object):
    """
    An object that stores instructions for how many databook items should be created during databook construction.
    These databook items are high-level user-detailed instantiations beyond the modeler-defined framework, e.g. populations and programs.
    The details of these item 'instances' are of course restricted within the constraints provided by the framework.
    TODO: Decide whether this class is over-engineered or can later be polymorphically combined in an 'instructions' file with FrameworkInstructions.
    """
    
    def __init__(self, databook_type = SystemSettings.DATABOOK_DEFAULT_TYPE):
        """ Initialize instructions that detail how to construct a databook. """
        self.name = str()
        # Every databook item must be included in a dictionary that lists how many should be created.
        self.num_items = OrderedDict()
        for item_type in DatabookSettings.ITEM_TYPES:
            self.num_items[item_type] = int()
        self.loadPreset(databook_type = databook_type)
        
    @accepts(str)
    def loadPreset(self, databook_type):
        """ Based on hard-coded databook types, determine how many databook items should be created. """
        logger.info("Loading databook instructions of type '{0}'.".format(databook_type))
        if databook_type == SystemSettings.DATABOOK_DEFAULT_TYPE:
            self.name = databook_type       # The name of the object is currently just the databook type.
            self.num_items[FrameworkSettings.KEY_POPULATION] = 7
            self.num_items[FrameworkSettings.KEY_PROGRAM] = 10
        return
                          
    @accepts(str,int)
    def updateNumberOfItems(self, item_type, number):
        """ Overwrite the number of items that this object will instruct a template framework creation to produce. """
        try: self.num_items[item_type] = number
        except:
            logger.exception("An attempted update of databook instructions '{0}' to produce '{1}' instances of item type '{2}' failed.".format(self.name, number, item_type))
            raise
        return

@logUsage
@accepts(ProjectFramework,str)
def createDatabookFunc(framework, databook_path, instructions = None, databook_type = SystemSettings.DATABOOK_DEFAULT_TYPE):
    """
    Generate a data-input Excel spreadsheet corresponding to a project framework.

    Inputs:
        databook_path (str)                             - Directory path for intended databook.
                                                          Must include filename with extension '.xlsx'.
        instructions (DatabookInstructions)             - An object that contains instructions for how many databook items to create.
        databook_type (str)                             - A string that denotes the type of databook, e.g. how many items to include.
                                                          This acts as a preset ID fed into a DatabookInstructions object upon initialization.
                                                          It is only used if instructions were not explicitly provided to this method.
    """
    if instructions is None: instructions = DatabookInstructions(databook_type = databook_type)

    logger.info("Creating a project databook: {0}".format(databook_path))
    prepareFilePath(databook_path)
    workbook = xw.Workbook(databook_path)

    ws_pops = workbook.add_worksheet("Populations")

    workbook.close()