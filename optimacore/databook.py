# -*- coding: utf-8 -*-
"""
Optima Core databook file.
Contains functions for creating databooks from project frameworks and then importing them.
"""

from optimacore.system import logger, applyToAllMethods, logUsage, accepts, returns, prepareFilePath, SystemSettings
from optimacore.framework_settings import FrameworkSettings
from optimacore.framework import ProjectFramework
from optimacore.databook_settings import DatabookSettings
from optimacore.excel import createStandardExcelFormats, createDefaultFormatVariables

from copy import deepcopy as dcp

from collections import OrderedDict

from six import moves as sm
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
            self.num_items[DatabookSettings.KEY_POPULATION] = 7
            self.num_items[DatabookSettings.KEY_PROGRAM] = 10
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
@accepts(xw.Workbook,str)
@returns(xw.Workbook)
def createDatabookPage(databook, page_key, instructions = None, formats = None, format_variables = None):
    """
    Creates a page within the databook.
    
    Inputs:
        databook (xw.Workbook)                          - The Excel file in which to create the page.
        page_key (str)                                  - The key denoting a particular page, as defined in databook settings.
        instructions (DatabookInstructions)             - An object that contains instructions for how many databook items to create.
        formats (dict)                                  - A dictionary of standard Excel formats, ideally passed in along with the databook.
                                                          If left as None, it will be regenerated in this function.
                                                          Each key is a string and each value is an 'xlsxwriter.format.Format' object.
        format_variables (dict)                         - A dictionary of format variables, such as column width.
                                                          If left as None, they will be regenerated in this function.
                                                          The keys are listed in databook settings and the values are floats.
    """
    if instructions is None: instructions = DatabookInstructions()
    
    # Determine the title of this page and generate it.
    # This should have been successfully extracted from a configuration file during databook-settings definition.
    page_name = DatabookSettings.PAGE_SPECS[page_key]["title"]
    logger.info("Creating page: {0}".format(page_name))
    datapage = databook.add_worksheet(page_name)
    
    # Propagate file-wide format variable values to page-wide format variable values.
    # Create the format variables if they were not passed in from a file-wide context.
    # Overwrite the file-wide defaults if page-based specifics are available in databook settings.
    if format_variables is None: format_variables = createDefaultFormatVariables()
    else: format_variables = dcp(format_variables)
    for format_variable_key in format_variables:
        if format_variable_key in DatabookSettings.PAGE_SPECS[page_key]:
            format_variables[format_variable_key] = DatabookSettings.PAGE_SPECS[page_key][format_variable_key]
    
    # Generate standard formats if they do not exist and construct headers for the page.
    if formats is None: formats = createStandardExcelFormats(databook)
    #createFrameworkPageHeaders(framework_page = framework_page, page_key = page_key, 
    #                           formats = formats, format_variables = format_variables)
    
    ## Create the number of base items required on this page.
    ## Officially, the initial item key per page is that of the core item-type, but this generic code works for all items without superitems.
    #row = 1
    #for item_type in FrameworkSettings.PAGE_ITEM_TYPES[page_key]:
    #    if FrameworkSettings.ITEM_TYPE_SPECS[item_type]["superitem_type"] is None:
    #        for item_number in sm.range(instructions.num_items[item_type]):
    #            _, row = createFrameworkPageItem(framework_page = framework_page, page_key = page_key,
    #                                             item_type = item_type, start_row = row, 
    #                                             instructions = instructions, formats = formats, item_number = item_number)
    return databook      

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
    databook = xw.Workbook(databook_path)
    formats = createStandardExcelFormats(databook)
    format_variables = createDefaultFormatVariables()
    
    # Get the set of keys that refer to databook pages.
    # Iterate through them and generate the corresponding pages.
    for page_key in DatabookSettings.PAGE_KEYS:
        createDatabookPage(databook = databook, page_key = page_key, instructions = instructions, 
                           formats = formats, format_variables = format_variables)

    ## Create population sheet.
    #page_title = "Populations"
    #ws_pops = databook.add_worksheet(page_title)

    #ws_pops.write(0, 0, "Full Name")        # This is technically the 'label' column.
    #ws_pops.write(0, 1, "Abbreviation")     # This is technically the 'name' column.

    ## While writing default population labels and names, they are stored for future reference as well.
    #pop_labels_default = []
    #pop_names_default = []
    #for pop_id in sm.range(instructions.num_items[DatabookSettings.KEY_POPULATION]):
    #    pop_label = "Population " + str(pop_id + 1)
    #    pop_name = pop_label[0:3] + str(pop_id + 1)
    #    pop_labels_default.append(pop_label)
    #    pop_names_default.append(pop_name)
    #    rc_pop_label = xw.utility.xl_rowcol_to_cell(pop_id + 1, 0)
    #    ws_pops.write(pop_id + 1, 0, pop_label)
    #    ws_pops.write(pop_id + 1, 1, "=LEFT({0},3)&\"{1}\"".format(rc_pop_label, pop_id + 1), None, pop_name)

    ## Excel formulae strings that point to population names and labels are likewise stored.
    #pop_labels_formula = []
    #pop_names_formula = []
    #for pop_id in sm.range(instructions.num_items[DatabookSettings.KEY_POPULATION]):
    #    rc_pop_label = xw.utility.xl_rowcol_to_cell(pop_id + 1, 0, True, True)
    #    rc_pop_name = xw.utility.xl_rowcol_to_cell(pop_id + 1, 1, True, True)
    #    pop_labels_formula.append("='{0}'!{1}".format(page_title, rc_pop_label))
    #    pop_names_formula.append("='{0}'!{1}".format(page_title, rc_pop_name))

    databook.close()