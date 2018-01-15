# -*- coding: utf-8 -*-
"""
Optima Core databook file.
Contains functions for creating databooks from project frameworks and then importing them.
"""

from optimacore.system import logUsage, accepts, returns, logger, prepareFilePath
from optimacore.framework import ProjectFramework

import xlsxwriter as xw

#@applyToAllMethods(logUsage)
#class DatabookInstructions(object):
#    """
#    An object that stores instructions for how many databook items should be created during databook construction.
#    These databook items are high-level user-selected instantiations beyond the modeler-defined framework, e.g. populations and programs.
#    This is not to say that the instantiations will not be defined within the constraints provided by the framework.
#    """
    
#    def __init__(self, databook_type = SystemSettings.DATABOOK_DEFAULT_TYPE):
#        """ Initialize instructions that detail how to construct a databook. """
#        self.name = str()
#        # Every page-item must be included in a dictionary that lists how many should be created.
#        self.num_items = OrderedDict()
#        for page_key in FrameworkSettings.PAGE_ITEM_TYPES:
#            for item_key in FrameworkSettings.PAGE_ITEM_TYPES[page_key]:
#                self.num_items[item_key] = int()
#        self.loadPreset(template_type = template_type)
        
#    @accepts(str)
#    def loadPreset(self, databook_type):
#        """ Based on hard-coded databook types, determine how many databook items should be created. """
#        logger.info("Loading databook instructions of type '{0}'.".format(databook_type))
#        if template_type == SystemSettings.DATABOOK_DEFAULT_TYPE:
#            self.name = databook_type       # The name of the object is currently just the databook type.
#            self.num_items["attitem"] = 4
#            self.num_items["optitem"] = 3
#            self.num_items["compitem"] = 10
#            self.num_items["characitem"] = 7
#            self.num_items["paritem"] = 20
#            self.num_items["progitem"] = 6
#            self.num_items["progattitem"] = 3
#        return
                          
#    @accepts(str,int)
#    def updateNumberOfItems(self, item_key, number):
#        """ Overwrite the number of items that this object will instruct a template framework creation to produce. """
#        try: self.num_items[item_key] = number
#        except:
#            logger.exception("An attempted update of framework instructions '{0}' to produce '{1}' instances of item-key '{2}' failed.".format(self.name, number, item_key))
#            raise
#        return

@logUsage
@accepts(ProjectFramework,str)
def createDatabookFunc(framework, databook_path):
    """ Generate a data-input Excel spreadsheet corresponding to a project framework. """

    logger.info("Creating a project databook: {0}".format(databook_path))
    prepareFilePath(databook_path)
    workbook = xw.Workbook(databook_path)

    ws_pops = workbook.add_worksheet("Populations")

    workbook.close()