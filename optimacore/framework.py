# -*- coding: utf-8 -*-
"""
Optima Core project-framework file.
Contains all information describing the context of a project.
This includes a description of the Markov chain network underlying project dynamics.
"""

from optimacore.system import logger, applyToAllMethods, logUsage, accepts, returns, OptimaException
from optimacore.system import SystemSettings
from optimacore.framework_settings import FrameworkSettings
from optimacore.databook_settings import DatabookSettings
from optimacore.excel import ExcelSettings

import os
import xlrd
from collections import OrderedDict
from copy import deepcopy as dcp

from six import moves as sm
import xlsxwriter as xw

@accepts(xlrd.sheet.Sheet)
@returns(dict)
def extractHeaderPositionMapping(excel_page):
    """ Returns a dictionary mapping column headers in an Excel page to the column numbers in which they are found. """
    header_positions = dict()
    for col in sm.range(excel_page.ncols):
        header = str(excel_page.cell_value(0, col))
        if not header == "":
            if header in header_positions:
                error_message = "An Excel file page contains multiple headers called '{0}'.".format(header)
                logger.error(error_message)
                raise OptimaException(error_message)
            header_positions[header] = col
    return header_positions

@accepts(xlrd.sheet.Sheet,int,int)
def extractExcelSheetValue(excel_page, start_row, start_col, stop_row = None, stop_col = None, filter = None):
    """
    Returns a value extracted from an Excel page, but converted to type according to a filter.
    The value will be pulled from rows starting at 'start_row' and terminating before 'stop_row'; a similar restriction holds for columns.
    Empty-string values are always equivalent to a value of None being returned.
    """
    old_value = None
    row = start_row
    col = start_col
    if stop_row is None: stop_row = row + 1
    if stop_col is None: stop_col = col + 1
    rc_start = xw.utility.xl_rowcol_to_cell(start_row, start_col)
    rc = rc_start
    # If columns without headers follow this column in the Excel page, scan through them.
    # Ditto with rows without item names that follow this row in the Excel page.
    while row < stop_row:
        while col < stop_col:
            value = str(excel_page.cell_value(row, col))
            if value == "":
                value = None
            elif filter == FrameworkSettings.COLUMN_TYPE_LIST_COMP_CHARAC:
                value = [item.strip() for item in value.strip().split(ExcelSettings.LIST_SEPARATOR)]

            if (not old_value is None):     # If there is an old value, this is not the first important cell examined.
                if value is None:
                    value = old_value       # If the new value is not important, maintain the old value.
                else:
                    # Expand lists with additional cell contents if appropriate.
                    if filter == FrameworkSettings.COLUMN_TYPE_LIST_COMP_CHARAC:
                        value = old_value + value
                    # Otherwise, overwrite with a warning.
                    else:
                        rc = xw.utility.xl_rowcol_to_cell(row, col)
                        logger.warning("Value '{0}' at cell '{1}' on page '{2}' is still considered part of the item and specification (i.e. header) located at cell '{3}'. "
                                       "It will overwrite the previous value of '{4}'.".format(value, rc, excel_page.name, rc_start, old_value))
            old_value = value
            col += 1
        col = start_col
        row += 1

    # Convert to boolean values if specified by filter.
    # Empty strings and unidentified symbols are considered default values.
    if filter == FrameworkSettings.COLUMN_TYPE_SWITCH_DEFAULT_OFF:
        if value == SystemSettings.DEFAULT_SYMBOL_YES: value = True
        else:
            if not value == SystemSettings.DEFAULT_SYMBOL_NO:
                logger.warning("Did not recognize symbol on page '{0}', at cell '{1}'. "
                               "Assuming a default of '{2}'.".format(excel_page.name, rc, SystemSettings.DEFAULT_SYMBOL_NO))
            value = ""
    if filter == FrameworkSettings.COLUMN_TYPE_SWITCH_DEFAULT_ON:
        if value == SystemSettings.DEFAULT_SYMBOL_NO: value = False
        else:
            if not value == SystemSettings.DEFAULT_SYMBOL_YES:
                logger.warning("Did not recognize symbol on page '{0}', at cell '{1}'. "
                               "Assuming a default of '{2}'.".format(excel_page.name, rc, SystemSettings.DEFAULT_SYMBOL_YES))
            value = ""
    if value == "": value = None
    return value



@applyToAllMethods(logUsage)
class ProjectFramework(object):
    """ The object that defines the transition-network structure of models generated by a project. """
    
    def __init__(self):
        """ Initialize the framework. """
        self.name = str()
        # Specifications are keyed by pages that have defined page-item types.
        # Each fundamental page-item and its subitems provide the data to construct specifications.
        # Each set of specifications associated with a core item type is a dictionary keyed by the code name of an item.
        # The page-item specification dictionaries are kept in order as defined within the file.
        self.specs = dict()
        for page_key in FrameworkSettings.PAGE_KEYS:
            self.specs[page_key] = OrderedDict()

        # Construct specifications for constructing a databook beyond the information contained in default databook settings.
        self.specs["datapage"] = OrderedDict()
        
        # Keep a dictionary linking any user-provided term with a reference to the appropriate specifications.
        self.semantics = dict()
        
    @accepts(str)
    def addTermToSemantics(self, term):
        """ Insert a user-provided term into the semantics dictionary maintained by the project framework and ensure it is unique. """
        if term in self.semantics:
            error_message = ("Framework has a term '{0}' that was defined previously. "
                             "Duplicate terms are not allowed.".format(term))
            logger.error(error_message)
            raise OptimaException(error_message)
        self.semantics[term] = dict()   # TODO: UPDATE THE VALUE WITH REFERENCES ONCE THE SPECS DICT IS COMPLETE.

    @accepts(xlrd.sheet.Sheet,str,str,int)
    def extractItemSpecsFromPage(self, framework_page, page_key, item_type, start_row, stop_row = None, header_positions = None, destination_specs = None):
        """
        Extracts specifications for an item from a page in a framework file.
        The name and label of an item must exist on the start row, but all other related specifications details can exist in subsequent 'unnamed' rows.
        Likewise, specifications relating to a column header can exist in subsequent columns unmarked by headers.
        
        Inputs:
            framework_page (xlrd.sheet.Sheet)               - The Excel sheet from which to extract page-item specifications.
            page_key (str)                                  - The key denoting the provided page, as defined in framework settings.
            item_type (str)                                 - The key denoting the type of item to extract, as defined in framework settings.
            start_row (int)                                 - The row number of the page from which to read the page-item.
            stop_row (int)                                  - The row number of the page at which page-item extraction is no longer read.
                                                              This is useful for cutting off subitems of subitems that have overflowed into the rows of the next superitem.
            header_positions (dict)                         - A dictionary mapping column headers to column numbers in the Excel page.
                                                              Is the output of function: extractHeaderPositionMapping()
            destination_specs (OrderedDict)                 - A reference to a level of the ProjectFramework specifications dictionary.
                                                              This allows for subitems to be extracted into child branches of the superitem specifications dictionary.
        
        Outputs:
            framework_page (xlrd.sheet.Sheet)       - The Excel sheet from which page-item specifications were extracted.
            next_row (int)                          - The next row number of the page after the rows containing page-item details.
                                                      Is useful to provide for page-items that involve subitems and multiple rows.
        """
        if header_positions is None: header_positions = extractHeaderPositionMapping(framework_page)
        if destination_specs is None: destination_specs = self.specs[page_key]
        
        item_type_specs = FrameworkSettings.ITEM_TYPE_SPECS[item_type]
        
        # Every item needs a label and name on its starting row; check to see if corresponding columns exist.
        row = start_row
        try:
            name_key = item_type_specs["key_name"]
            name_header = FrameworkSettings.COLUMN_SPECS[name_key]["header"]
            name_pos = header_positions[name_header]
            name = str(framework_page.cell_value(row, name_pos))
            label_key = item_type_specs["key_label"]
            label_header = FrameworkSettings.COLUMN_SPECS[label_key]["header"]
            label_pos = header_positions[label_header]
            label = str(framework_page.cell_value(row, label_pos))
        except:
            error_message = ("Problem encountered when extracting a name and label for item type '{0}' "
                             "on page with key '{1}'. ".format(item_type, page_key))
            logger.error(error_message)
            raise OptimaException(error_message)

        # Work out the row at which the next named item exists, if any.
        if stop_row is None: stop_row = framework_page.nrows
        row_test = row + 1
        while row_test < stop_row:
            if str(framework_page.cell_value(row_test, name_pos)) == "":
                row_test += 1
            else:
                stop_row = row_test
                break
            
        # Provided that the item has a code name, extract other specifications details from other appropriate sections.
        if not name == "":
            if label == "":
                error_message = ("An item of type '{0}', on page with key '{1}', was encountered with name '{2}' "
                                 "but no label specified on the same row.".format(item_type, page_key, name))
                logger.error(error_message)
                raise OptimaException(error_message)
            for term in [name, label]:
                self.addTermToSemantics(term = term)
            destination_specs[name] = {"label":label}
            
            column_keys = FrameworkSettings.PAGE_COLUMN_KEYS[page_key]
            item_type_column_keys = []
            if not item_type_specs["column_keys"] is None: item_type_column_keys = item_type_specs["column_keys"]
            if item_type_specs["inc_not_exc"]: column_keys = item_type_column_keys
            subitem_types = []
            if not item_type_specs["subitem_types"] is None: subitem_types = item_type_specs["subitem_types"]

            # Iterate through all item-related columns when extracting specifications values.
            for column_key in column_keys:
                if (not item_type_specs["inc_not_exc"]) and column_key in item_type_column_keys: continue
                if column_key not in [name_key, label_key]:
                    column_header = FrameworkSettings.COLUMN_SPECS[column_key]["header"]
                    column_type = FrameworkSettings.COLUMN_SPECS[column_key]["type"]
                    col = header_positions[column_header]

                    # Work out the next column for which a header exists, if any.
                    stop_col = framework_page.ncols
                    col_test = col + 1
                    while col_test < stop_col:
                        if str(framework_page.cell_value(0, col_test)) == "":
                            col_test += 1
                        else:
                            stop_col = col_test
                            break

                    value = extractExcelSheetValue(excel_page = framework_page, start_row = row, stop_row = stop_row, 
                                                                                start_col = col, stop_col = stop_col, filter = column_type)
                    if not value is None:
                        destination_specs[name][column_key] = value
            
            # Parse the specifications of any subitems that exist within the rows attributed to this item.
            for subitem_type in subitem_types:
                if not subitem_type in destination_specs[name]: destination_specs[name][subitem_type] = OrderedDict()
                row_subitem = start_row
                while row_subitem < stop_row:
                    _, row_subitem = self.extractItemSpecsFromPage(framework_page = framework_page, page_key = page_key, item_type = subitem_type, start_row = row_subitem, stop_row = stop_row,
                                                                   header_positions = header_positions, destination_specs = destination_specs[name][subitem_type])
            
        next_row = stop_row
        return framework_page, next_row

    @accepts(str)
    def importFromFile(self, framework_path):
        """ Attempts to load project framework details from a framework Excel file. """
        framework_path = os.path.abspath(framework_path)
        logger.info("Attempting to import an Optima Core framework from a file.")
        logger.info("Location... {0}".format(framework_path))
        try: framework_file = xlrd.open_workbook(framework_path)
        except:
            logger.exception("Framework file was not found.")
            raise

        # Reset the framework contents.
        self.__init__()
            
        # Cycle through framework file pages and read them in.
        for page_key in FrameworkSettings.PAGE_KEYS:
            try: 
                page_title = FrameworkSettings.PAGE_SPECS[page_key]["title"]
                framework_page = framework_file.sheet_by_name(page_title)
            except:
                logger.exception("Framework file does not contain a required page titled '{0}'.".format(page_title))
                raise
            
            # Establish a mapping from column header to column positions.
            header_positions = extractHeaderPositionMapping(framework_page)
            
            # Determine the fundamental page-item associated with this page.
            try: core_item_type = FrameworkSettings.PAGE_ITEM_TYPES[page_key][0]
            except:
                logger.warning("Framework settings do not list a page-item key associated with the page titled '{0}'. "
                               "Continuing to the next page.".format(page_title))
                continue
                             
            # Check that the fundamental page-item on this page has requisite name and label columns to scan.
            try: 
                core_name_key = FrameworkSettings.ITEM_TYPE_SPECS[core_item_type]["key_name"]
                core_name_header = FrameworkSettings.COLUMN_SPECS[core_name_key]["header"]
            except:
                logger.exception("Cannot locate the column header on framework page '{0}' associated with 'names' "
                                 "for item of type '{1}'.".format(page_title, core_item_type))
                raise
            try: 
                core_label_key = FrameworkSettings.ITEM_TYPE_SPECS[core_item_type]["key_label"]
                core_label_header = FrameworkSettings.COLUMN_SPECS[core_label_key]["header"]
            except:
                logger.exception("Cannot locate the column header on framework page '{0}' associated with 'labels' "
                                 "for item of type '{1}'.".format(page_title, core_item_type))
                raise
                
            # Scan through the rows of the page and update relevant specification dictionaries.
            row = 1
            while row < framework_page.nrows:
                _, row = self.extractItemSpecsFromPage(framework_page = framework_page, page_key = page_key, item_type = core_item_type, start_row = row, header_positions = header_positions)                                        
        
        # Update databook instructions specifically.
        # Start off by assuming all characteristics will be displayed on the default page.
        self.specs["datapage"][DatabookSettings.KEY_CHARACTERISTIC] = OrderedDict()
        for charac_key in self.specs[FrameworkSettings.KEY_CHARACTERISTIC]:
            core_section_key = DatabookSettings.PAGE_SECTION_KEYS[DatabookSettings.KEY_CHARACTERISTIC][0]
            self.specs["datapage"][DatabookSettings.KEY_CHARACTERISTIC][charac_key] = dcp(DatabookSettings.SECTION_SPECS[core_section_key])
            # TODO: Use semantic referencing here.
            self.specs["datapage"][DatabookSettings.KEY_CHARACTERISTIC][charac_key]["header"] = self.specs[FrameworkSettings.KEY_CHARACTERISTIC][charac_key]["label"]
        
        #from pprint import pprint
        #pprint(self.specs)

        # TODO: Have a better naming scheme for the object rather than the path of its imported file.
        self.setName(framework_path)
        logger.info("Optima Core framework successfully imported.")
        
        return

    @accepts(str)
    def setName(self, name):
        """ Set primary human-readable identifier for the project framework. """
        self.name = name
    
    @returns(str)
    def getName(self):
        """ Get primary human-readable identifier for the project framework. """
        return self.name
    
#    @accepts(str)
#    @returns(bool)
#    def exportToFile(self, framework_path):
#        """
#        Attempts to save existing project framework details to a framework Excel file.
#        """
#        return
    
    