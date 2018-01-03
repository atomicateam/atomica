# -*- coding: utf-8 -*-
"""
Optima Core project-framework file.
Contains all information describing the context of a project.
This includes a description of the Markov chain network underlying project dynamics.
"""

from optimacore.system import logger, applyToAllMethods, logUsage, accepts, returns, OptimaException
from optimacore.system import SystemSettings
from optimacore.framework_settings import FrameworkSettings

import os
import xlrd
from collections import OrderedDict

@accepts(xlrd.sheet.Sheet)
@returns(dict)
def extractHeaderPositionMapping(excel_page):
    """ Returns a dictionary mapping column headers in an Excel page to the column numbers in which they are found. """
    header_positions = dict()
    for col in xrange(excel_page.ncols):
        header = str(excel_page.cell_value(0, col))
        if not header == "":
            if header in header_positions:
                error_message = "An Excel file page contains multiple headers called '{0}'.".format(header)
                logger.error(error_message)
                raise OptimaException(error_message)
            header_positions[header] = col
    return header_positions

@applyToAllMethods(logUsage)
class ProjectFramework(object):
    """ The object that defines the transition-network structure of models generated by a project. """
    
    def __init__(self):
        """ Initialize the framework. """
        # Specifications are keyed by pages that have defined page-item types.
        # Each fundamental page-item and its subitems provide the data to construct specifications.
        # Each set of specifications associated with a core item type is a dictionary keyed by the code name of an item.
        # The page-item specification dictionaries are kept in order as defined within the file.
        self.specs = dict()
        for page_key in FrameworkSettings.PAGE_KEYS:
            self.specs[page_key] = OrderedDict()
        
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
    def extractItemSpecsFromPage(self, framework_page, page_key, item_key, start_row, header_positions = None):
        """
        Extracts specifications for an item from a page in a framework file.
        
        Inputs:
            framework_page (xlrd.sheet.Sheet)               - The Excel sheet from which to extract page-item specifications.
            page_key (str)                                  - The key denoting the provided page, as defined in framework settings.
            item_key (str)                                  - The key denoting the page-item to extract, as defined in framework settings.
            start_row (int)                                 - The row number of the page from which to read the page-item.
            header_positions (dict)                         - A dictionary mapping column headers to column numbers in the Excel page.
                                                              Is the output of function: extractHeaderPositionMapping()
        
        Outputs:
            framework_page (xlrd.sheet.Sheet)       - The Excel sheet from which page-item specifications were extracted.
            next_row (int)                          - The next row number of the page after the rows containing page-item details.
                                                      Is useful to provide for page-items that involve subitems and multiple rows.
        """
        if header_positions is None: header_positions = extractHeaderPositionMapping(framework_page)
        
        item_specs = FrameworkSettings.ITEM_SPECS[item_key]
        
        row = start_row
        try:
            name_key = item_specs["key_name"]
            name_header = FrameworkSettings.COLUMN_SPECS[name_key]["header"]
            name_pos = header_positions[name_header]
            name = str(framework_page.cell_value(row, name_pos))
            label_key = item_specs["key_label"]
            label_header = FrameworkSettings.COLUMN_SPECS[label_key]["header"]
            label_pos = header_positions[label_header]
            label = str(framework_page.cell_value(row, label_pos))
        except:
            error_message = ("Problem encountered when extracting a name and label for page-item with key '{0}' "
                             "on page with key '{1}'. ".format(page_key, item_key))
            logger.error(error_message)
            raise OptimaException(error_message)
            
        if not name == "":
            for term in [name, label]:
                self.addTermToSemantics(term = term)
            self.specs[page_key][name] = {"label":label}
            
            column_keys = FrameworkSettings.PAGE_COLUMN_KEYS[page_key]
            item_column_keys = []
            if not item_specs["column_keys"] is None: item_column_keys = item_specs["column_keys"]
            if item_specs["inc_not_exc"]: column_keys = item_column_keys
        
            for column_key in column_keys:
                if (not item_specs["inc_not_exc"]) and column_key in item_column_keys: continue
                if column_key not in [name_key, label_key]:
                    column_header = FrameworkSettings.COLUMN_SPECS[column_key]["header"]
                    column_pos = header_positions[column_header]
                    value = str(framework_page.cell_value(row, column_pos))
                    column_type = FrameworkSettings.COLUMN_SPECS[column_key]["type"]
                    if value == "": continue
                    if column_type == FrameworkSettings.COLUMN_TYPE_KEY_SWITCH_DEFAULT_OFF:
                        if value == SystemSettings.DEFAULT_SYMBOL_YES: value = True
                        else:
                            if not value == SystemSettings.DEFAULT_SYMBOL_NO:
                                logger.warn("Did not recognize symbol '{0}' used for switch-based column with header '{1}' on page with key '{2}'. "
                                            "Assuming a default of '{3}'.".format(value, column_header, page_key, SystemSettings.DEFAULT_SYMBOL_NO))
                            continue
                    if column_type == FrameworkSettings.COLUMN_TYPE_KEY_SWITCH_DEFAULT_ON:
                        if value == SystemSettings.DEFAULT_SYMBOL_NO: value = False
                        else:
                            if not value == SystemSettings.DEFAULT_SYMBOL_YES:
                                logger.warn("Did not recognize symbol '{0}' used for switch-based column with header '{1}' on page with key '{2}'. "
                                            "Assuming a default of '{3}'.".format(value, column_header, page_key, SystemSettings.DEFAULT_SYMBOL_YES))
                            continue
                    self.specs[page_key][name][column_key] = value
            
        next_row = row + 1 #max(start_row + 1, row)
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
            try: core_item_key = FrameworkSettings.PAGE_ITEM_KEYS[page_key][0]
            except:
                logger.warning("Framework settings do not list a page-item key associated with the page titled '{0}'. "
                               "Continuing to the next page.".format(page_title))
                continue
                             
            # Check that the fundamental page-item on this page has requisite name and label columns to scan.
            try: 
                core_name_key = FrameworkSettings.ITEM_SPECS[core_item_key]["key_name"]
                core_name_header = FrameworkSettings.COLUMN_SPECS[core_name_key]["header"]
            except:
                logger.exception("Cannot locate the column header on framework page '{0}' associated with 'names' "
                                 "for the page-item keyed by '{1}'.".format(page_title, core_item_key))
                raise
            try: 
                core_label_key = FrameworkSettings.ITEM_SPECS[core_item_key]["key_label"]
                core_label_header = FrameworkSettings.COLUMN_SPECS[core_label_key]["header"]
            except:
                logger.exception("Cannot locate the column header on framework page '{0}' associated with 'labels' "
                                 "for the page-item keyed by '{1}'.".format(page_title, core_item_key))
                raise
                
            # Scan through the rows of the page and update relevant specification dictionaries.
            row = 1
            while row < framework_page.nrows:
                _, row = self.extractItemSpecsFromPage(framework_page = framework_page, page_key = page_key, item_key = core_item_key, start_row = row, header_positions = header_positions)                                        
            
        logger.info("Optima Core framework successfully imported.")
        
        return
    
#    @accepts(str)
#    @returns(bool)
#    def exportToFile(self, framework_path):
#        """
#        Attempts to save existing project framework details to a framework Excel file.
#        """
#        return
    
    