# -*- coding: utf-8 -*-
"""
Optima Core project-framework input/output file.
Contains functions to create, import and export framework files.
This is primarily referenced by the ProjectFramework object.
"""

from optimacore.system import applyToAllMethods, logUsage, accepts
from optimacore.system import logger, SystemSettings, getOptimaCorePath

from collections import OrderedDict
from copy import deepcopy as dcp

import xlsxwriter as xw
try: import ConfigParser as configparser    # Python 2.
except ImportError: import configparser     # Python 3.


@logUsage
@accepts(configparser.ConfigParser,str,str)
def getConfigValue(config, section, option, list_form = False, mute_warnings = False):
    """
    Returns the value of an option of a section within a parsed configuration file.
    If the list form option is set as true, the return value is a list of strings, otherwise the value is a string.
    Lists are broken apart by a separator set in system settings, with all values being stripped of surrounding whitespace.
    """
    value = None
    if not config.has_section(section):
        if not mute_warnings: logger.warn("Framework configuration file has no section with label '{0}'.".format(section))
        raise configparser.NoSectionError(section)
    if not config.has_option(section, option):
        if not mute_warnings: logger.warn("Framework configuration file, section '{0}', has no option with label '{1}'.".format(section,option))
        raise configparser.NoOptionError(section,option)
    if list_form:
        value = [item.strip() for item in config.get(section, option).strip().split(SystemSettings.CONFIG_FRAMEWORK_LIST_SEPARATOR)]
    else:
        value = config.get(section, option).strip()
    return value

def loadConfigFile(undecorated_class):
    """
    Decorator that instructs a class to do an initial update of its attributes according to a configuration file.
    This is done at the import stage; failure means the class starts off incorrect and an import error is thrown.
    """
    try: undecorated_class.reloadConfigFile()
    except:
        logger.exception("Because a relevant configuration file failed to load, the initial state of class '{0}' is invalid. "
                         "Import failed.".format(undecorated_class.__name__))
        raise ImportError
    return undecorated_class

@loadConfigFile
class FrameworkSettings(object):
    """
    Stores the definitions used in creating and reading framework files.
    Some of this is hard-coded and any changes risk disrupting framework operations.
    The rest is parsed from a framework configuration file during the module import phase.
    Note: As a codebase-specific settings class, there is no need to instantiate it as an object.
    """
    # Construct a dictionary with ordered keys representing pages.
    # Each page-key corresponds to a list of keys representing columns.
    # These orders describe how a framework template will be constructed.
    PAGE_COLUMN_KEYS = OrderedDict()
    PAGE_COLUMN_KEYS["poptype"] = ["attlabel","attname","optlabel","optname"]
    PAGE_COLUMN_KEYS["comp"] = ["label","name","sourcetag","sinktag","junctiontag"]
    PAGE_COLUMN_KEYS["trans"] = []
    
    COLUMN_ITEM_TYPES = ["label","name"]
    
    # Keys for float-valued variables related in some way to framework-file formatting.
    # They must have corresponding system-settings defaults.
    FORMAT_VARIABLE_KEYS = ["column_width","comment_xscale","comment_yscale"]
    
    # Hard-coded details for generating default page items, made as abstract as possible.
    PAGE_ITEM_KEYS = OrderedDict()
    PAGE_ITEM_KEYS["poptype"] = ["attitem","optitem"]
    PAGE_ITEM_KEYS["comp"] = ["compitem"]
    PAGE_ITEM_KEYS["trans"] = []
    PAGE_ITEM_ATTRIBUTES = ["label","name"]
    
    # A default dictionary of page-item specifics is constructed first, then overwritten as required.
    PAGE_ITEM_SPECS = OrderedDict()
    for page_key in PAGE_ITEM_KEYS:
        PAGE_ITEM_SPECS[page_key] = dict()
        for item_type in PAGE_ITEM_KEYS[page_key]:
            # Specify whether page-item construction should include or exclude filling out specified columns.
            # Then specify a list of column keys to be included or excluded when constructing a page item.
            # Most page-items involve all columns, so the default is to exclude no columns.
            PAGE_ITEM_SPECS[page_key][item_type] = {"inc_not_exc":False, "column_keys":None,
            # Many page-items will have a display label and code name, so appropriate column keys should be recorded.
                                                    "label_key":None, "name_key":None,
            # Some page-items can be divided into columns and other page-items; the keys of the latter should be listed.
                                                    "subitem_keys":None}
    # Define a default population attribute item.
    PAGE_ITEM_SPECS["poptype"]["attitem"]["inc_not_exc"] = True
    PAGE_ITEM_SPECS["poptype"]["attitem"]["column_keys"] = ["attlabel","attname"]
    PAGE_ITEM_SPECS["poptype"]["attitem"]["label_key"] = "attlabel"
    PAGE_ITEM_SPECS["poptype"]["attitem"]["name_key"] = "attname"
    PAGE_ITEM_SPECS["poptype"]["attitem"]["subitem_keys"] = ["optitem"]
    # Define a default population option item, which is a subitem of a population attribute.
    PAGE_ITEM_SPECS["poptype"]["optitem"]["column_keys"] = ["attlabel","attname"]
    PAGE_ITEM_SPECS["poptype"]["optitem"]["label_key"] = "optlabel"
    PAGE_ITEM_SPECS["poptype"]["optitem"]["name_key"] = "optname"
    
    
    PAGE_SPECS = OrderedDict()
    PAGE_COLUMN_SPECS = OrderedDict()
    
    
    @classmethod
    @logUsage
    def reloadConfigFile(cls):
        """
        Reads a framework configuration file and extends the settings to use the semantics and values provided.
        Method is titled with 'reload' as the process will have already been called once during initial import.
        Note: Currently references the default configuration file, but can be modified in the future.
        """
        config_path = getOptimaCorePath(subdir=SystemSettings.CODEBASE_DIRNAME)+SystemSettings.CONFIG_FRAMEWORK_FILENAME
        logger.info("Attempting to generate Optima Core framework settings from configuration file.")
        logger.info("Location... {0}".format(config_path))
        cp = configparser.ConfigParser()
        cp.read(config_path)
        
        # Flesh out page details.
        for page_key in cls.PAGE_COLUMN_KEYS:
            if page_key not in cls.PAGE_SPECS: cls.PAGE_SPECS[page_key] = dict()
            # Read in required page title.
            try: cls.PAGE_SPECS[page_key]["title"] = getConfigValue(config = cp, section = "page_"+page_key, option = "title")
            except:
                logger.exception("Framework configuration loading process failed. Every page in a framework file needs a title.")
                raise
            # Read in optional page format variables.
            for format_variable_key in cls.FORMAT_VARIABLE_KEYS:
                try: 
                    value_overwrite = float(getConfigValue(config = cp, section = "page_"+page_key, option = format_variable_key, mute_warnings = True))
                    cls.PAGE_SPECS[page_key][format_variable_key] = value_overwrite
                except ValueError: logger.warn("Framework configuration file for page-key '{0}' has an entry for '{1}' " 
                                               "that cannot be converted to a float. Using a default value.".format(page_key, format_variable_key))
                except: pass
            
            # Flesh out page column details.
            if page_key not in cls.PAGE_COLUMN_SPECS: cls.PAGE_COLUMN_SPECS[page_key] = OrderedDict()
            column_count = 0
            for column_key in cls.PAGE_COLUMN_KEYS[page_key]:
                if column_key not in cls.PAGE_COLUMN_SPECS[page_key]: cls.PAGE_COLUMN_SPECS[page_key][column_key] = dict()
                # Associate each column with a position number for easy reference.
                # This is a default number for template creation; column positions may be different in loaded framework files.
                cls.PAGE_COLUMN_SPECS[page_key][column_key]["default_num"] = column_count
                # Read in required column header.
                try: cls.PAGE_COLUMN_SPECS[page_key][column_key]["header"] = getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = "header")
                except:
                    logger.exception("Framework configuration loading process failed. Every column in a framework page needs a header.")
                    raise
                # Read in optional column comment.
                try: cls.PAGE_COLUMN_SPECS[page_key][column_key]["comment"] = getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = "comment")
                except: pass
                # Read in optional prefix that will prepend default text written into this column.
                try: cls.PAGE_COLUMN_SPECS[page_key][column_key]["item_prefix"] = getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = "item_prefix", mute_warnings = True)
                except: pass
                # Read in optional type of item that this column contains.
                try: 
                    value = getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = "item_type", mute_warnings = True)
                    if value not in cls.COLUMN_ITEM_TYPES:
                        logger.warn("Framework configuration file for page-key '{0}', column-key '{1}', has an entry for 'item_type' " 
                                    "that is not listed in framework settings. It will be noted but have no effect.".format(page_key, column_key))
                        logger.warn("Valid options: {0}".format(", ".join(cls.COLUMN_ITEM_TYPES)))
                    cls.PAGE_COLUMN_SPECS[page_key][column_key]["item_type"] = value
                except: pass
                # Read in optional column format variables.
                for format_variable_key in cls.FORMAT_VARIABLE_KEYS:
                    try: 
                        value_overwrite = float(getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = format_variable_key, mute_warnings = True))
                        cls.PAGE_COLUMN_SPECS[page_key][column_key][format_variable_key] = value_overwrite
                    except ValueError: logger.warn("Framework configuration file for page-key '{0}', column-key '{1}', has an entry for '{2}' " 
                                                   "that cannot be converted to a float. Using a default value.".format(page_key, column_key, format_variable_key))
                    except: pass
                column_count += 1
        
        logger.info("Optima Core framework settings successfully generated.") 
        return
    
        
    
@logUsage
@accepts(xw.worksheet.Worksheet,int,int,int)
def writeSequenceToExcelColumn(sheet, row_start, col, length, skip_rows = 0, prefix_list = None, cell_format = None):
    """
    Writes a consecutive integer sequence into the column of an Excel sheet.
    Starts from 0 and is of user-prescribed length.
    If a list of prefix strings is optionally provided, the sequence is repeated for each prefix.
    In this case, each iteration is prepended by the corresponding prefix.
    If a user specifies a number of rows to skip, this will be applied between each iteration of the sequence.
    """
    if prefix_list is None: prefix_list = [""]
    
    row = row_start
    for prefix in prefix_list:
        for count in xrange(length):
            sheet.write(row, col, prefix+str(count), cell_format)
            row += 1 + skip_rows
    return

@logUsage
@accepts(xw.Workbook)
def createStandardExcelFormats(excel_file):
    """ 
    Generates and returns a dictionary of standard excel formats attached to an excel file.
    Note: Can be modified or expanded as necessary to fit other definitions of 'standard'.
    """
    formats = dict()
    formats["center_bold"] = excel_file.add_format({"align": "center", "bold": True})
    formats["center"] = excel_file.add_format({"align": "center"})
    return formats

#%%

@logUsage
def createDefaultFormatVariables():
    """
    Establishes framework-file default values for format variables in a dictionary and returns it.
    The keys are in FrameworkSettings and must match corresponding values in SystemSettings, or an AttributeError will be thrown.
    """
    format_variables = dict()
    for format_variable_key in FrameworkSettings.FORMAT_VARIABLE_KEYS:
        exec("format_variables[\"{0}\"] = SystemSettings.EXCEL_IO_DEFAULT_{1}".format(format_variable_key, format_variable_key.upper()))
    return format_variables


@logUsage
@accepts(xw.worksheet.Worksheet,str,dict)
def createFrameworkPageHeaders(framework_page, page_key, formats, format_variables = None):
    """
    Creates headers for a page within a framework file, adding comments and resizing wherever instructed.
    
    Inputs:
        framework_page (xw.worksheet.Worksheet) - The Excel sheet in which to create headers.
        page_key (str)                          - The key denoting the provided page, as defined in framework settings.
        formats (dict)                          - A dictionary of standard Excel formats.
                                                  Is the output of function: createStandardExcelFormats()
                                                  Each key is a string and each value is an 'xlsxwriter.format.Format' object.
        format_variables (dict)                 - A dictionary of format variables, such as column width.
                                                  If left as None, they will be regenerated in this function.
                                                  The keys are listed in framework settings and the values are floats.
    """
    # Get the set of keys that refer to framework-file page columns.
    # Iterate through the keys and construct each corresponding column header.
    column_keys = FrameworkSettings.PAGE_COLUMN_KEYS[page_key]
    for column_key in column_keys:
        col = FrameworkSettings.PAGE_COLUMN_SPECS[page_key][column_key]["default_num"]
        header_name = FrameworkSettings.PAGE_COLUMN_SPECS[page_key][column_key]["header"]
        framework_page.write(0, col, header_name, formats["center_bold"])
        
        # Propagate pagewide format variable values to column-wide format variable values.
        # Create the format variables if they were not passed in from a page-wide context.
        # Overwrite the page-wide defaults if column-based specifics are available in framework settings.
        if format_variables is None: format_variables = createDefaultFormatVariables()
        else: format_variables = dcp(format_variables)
        for format_variable_key in format_variables.keys():
            if format_variable_key in FrameworkSettings.PAGE_COLUMN_SPECS[page_key][column_key]:
                format_variables[format_variable_key] = FrameworkSettings.PAGE_COLUMN_SPECS[page_key][column_key][format_variable_key]
        
        # Comment the column header if a comment was pulled into framework settings from a configuration file.
        if "comment" in FrameworkSettings.PAGE_COLUMN_SPECS[page_key][column_key]:
            header_comment = FrameworkSettings.PAGE_COLUMN_SPECS[page_key][column_key]["comment"]
            framework_page.write_comment(0, col, header_comment, 
                                         {"x_scale": format_variables["comment_xscale"], 
                                          "y_scale": format_variables["comment_yscale"]})
    
        # Adjust column width and continue to the next one.
        framework_page.set_column(col, col, format_variables["column_width"])
    return framework_page


@logUsage
def createFrameworkPageItem(framework_page, page_key, item_key, start_row, formats, item_number = None,
                            superitem_attributes = None):

    if not item_key in FrameworkSettings.PAGE_ITEM_SPECS[page_key]:
        logger.exception("A framework page with key '{0}' was instructed to create a page-item with key '{1}', despite no relevant page-item "
                         "specifications existing in framework settings. Abandoning framework file construction.".format(page_key,item_key))
        raise KeyError(item_key)
    
    cell_format = formats["center"]
    row = start_row
    
    if item_number is None: item_number = 0
    
    item_specs = FrameworkSettings.PAGE_ITEM_SPECS[page_key][item_key]
    
    # Determine which columns to fill out with default values for this page item.
    column_keys = FrameworkSettings.PAGE_COLUMN_KEYS[page_key]
    item_column_keys = []
    if not item_specs["column_keys"] is None: item_column_keys = item_specs["column_keys"]
    if item_specs["inc_not_exc"]: column_keys = item_column_keys
    
    subitem_keys = []
    if not item_specs["subitem_keys"] is None: subitem_keys = item_specs["subitem_keys"]
              
    item_attributes = dict()
    for attribute in FrameworkSettings.PAGE_ITEM_ATTRIBUTES:
        item_attributes[attribute] = {"cell":None, "value":None, "backup":None}
    if superitem_attributes is None: superitem_attributes = dcp(item_attributes)
        
    for column_key in column_keys:
        if (not item_specs["inc_not_exc"]) and column_key in item_column_keys: continue
        column_specs = FrameworkSettings.PAGE_COLUMN_SPECS[page_key][column_key]
        space = ""
        sep = ""
        try:
            exec("space = SystemSettings.DEFAULT_SPACE_{0}".format(column_specs["item_type"].upper()))
            exec("sep = SystemSettings.DEFAULT_SEPARATOR_{0}".format(column_specs["item_type"].upper()))
        except: pass
        col = column_specs["default_num"]
        text = str(item_number)
        if "item_prefix" in column_specs:
            text = column_specs["item_prefix"] + space + text
        text_backup = text
        
        for attribute in FrameworkSettings.PAGE_ITEM_ATTRIBUTES:
            if column_key == item_specs[attribute+"_key"]:
                backup = superitem_attributes[attribute]["backup"]
                if not backup is None: 
                    text_backup = backup + sep + text_backup
                    
                cell = superitem_attributes[attribute]["cell"]
                value = superitem_attributes[attribute]["value"]
                if not cell is None:
                    text = "=CONCATENATE({0},\"{1}\")".format(cell,sep+text)
                elif not value is None:
                    if value.startswith("="):
                        text = "=CONCATENATE({0},\"{1}\")".format(value.lstrip("="),sep+text)
                    else:
                        text = value + sep + text
                else:
                    pass
                item_attributes[attribute]["cell"] = xw.utility.xl_rowcol_to_cell(row, col)
                item_attributes[attribute]["value"] = text
                item_attributes[attribute]["backup"] = text_backup
        if text.startswith("="):
            framework_page.write_formula(row, col, text, cell_format, text_backup)
        else:
            framework_page.write(row, col, text, cell_format)
    
    for subitem_key in subitem_keys:
        for subitem_number in xrange(4):
            _, row = createFrameworkPageItem(framework_page = framework_page, page_key = page_key,
                                                   item_key = subitem_key, start_row = row, 
                                                   formats = formats, item_number = subitem_number,
                                                   superitem_attributes = item_attributes)
    next_row = max(start_row + 1, row)
    return framework_page, next_row


@logUsage
@accepts(xw.Workbook,str)
def createFrameworkPage(framework_file, page_key, formats = None, format_variables = None):
    """
    Creates a page within the framework file.
    
    Inputs:
        framework_file (xw.Workbook)            - The Excel file in which to create the page.
        page_key (str)                          - The key denoting a particular page, as defined in framework settings.
        formats (dict)                          - A dictionary of standard Excel formats, ideally passed in along with the framework file.
                                                  If left as None, it will be regenerated in this function.
                                                  Each key is a string and each value is an 'xlsxwriter.format.Format' object.
        format_variables (dict)                 - A dictionary of format variables, such as column width.
                                                  If left as None, they will be regenerated in this function.
                                                  The keys are listed in framework settings and the values are floats.
    """
    # Determine the title of this page and generate it.
    # This should have been successfully extracted from a configuration file during framework-settings definition.
    page_name = FrameworkSettings.PAGE_SPECS[page_key]["title"]
    logger.info("Creating page: {0}".format(page_name))
    framework_page = framework_file.add_worksheet(page_name)
    
    # Propagate file-wide format variable values to page-wide format variable values.
    # Create the format variables if they were not passed in from a file-wide context.
    # Overwrite the file-wide defaults if page-based specifics are available in framework settings.
    if format_variables is None: format_variables = createDefaultFormatVariables()
    else: format_variables = dcp(format_variables)
    for format_variable_key in format_variables.keys():
        if format_variable_key in FrameworkSettings.PAGE_SPECS[page_key]:
            format_variables[format_variable_key] = FrameworkSettings.PAGE_SPECS[page_key][format_variable_key]
    
    # Generate standard formats if they do not exist and construct headers for the page.
    if formats is None: formats = createStandardExcelFormats(framework_file)
    createFrameworkPageHeaders(framework_page = framework_page, page_key = page_key, 
                               formats = formats, format_variables = format_variables)
    
    row = 1
    for item_key in FrameworkSettings.PAGE_ITEM_SPECS[page_key]:
        for item_number in xrange(3):
            _, row = createFrameworkPageItem(framework_page = framework_page, page_key = page_key,
                                             item_key = item_key, start_row = row, 
                                             formats = formats, item_number = item_number)
    
    return framework_file
    
#    # Iterate through the column keys of a page and generate columns if possible.
#    # The bare minimum of a column is a header name.
#    col = 0
#    for column_key in column_keys:
#        # Fill the column with default sequences of values if appropriate, starting in the row after the header.
#        if page_key == "poptype":
#            if column_key == "attlabel":
#                writeSequenceToExcelColumn(sheet = framework_page, row_start = 1, col = col, skip_rows = num_options_per_pop_attribute - 1,
#                                           length = num_pop_attributes, prefix_list = ["Attribute "], cell_format = format_center)
#            if column_key == "attname":
#                writeSequenceToExcelColumn(sheet = framework_page, row_start = 1, col = col, skip_rows = num_options_per_pop_attribute - 1,
#                                           length = num_pop_attributes, prefix_list = ["att_"], cell_format = format_center)
#            if column_key == "optlabel":
#                prefix_list = ["Attribute "+str(x)+" - Option " for x in xrange(num_pop_attributes)]
#                writeSequenceToExcelColumn(sheet = framework_page, row_start = 1, col = col,
#                                           length = num_options_per_pop_attribute, prefix_list = prefix_list, cell_format = format_center)
#            if column_key == "optname":
#                prefix_list = ["att_"+str(x)+"_opt_" for x in xrange(num_pop_attributes)]
#                writeSequenceToExcelColumn(sheet = framework_page, row_start = 1, col = col,
#                                           length = num_options_per_pop_attribute, prefix_list = prefix_list, cell_format = format_center)
#        if page_key == "comp":
#            if column_key == "label":
#                writeSequenceToExcelColumn(sheet = framework_page, row_start = 1, col = col,
#                                           length = num_compartments, prefix_list = ["Compartment "], cell_format = format_center)
#            if column_key == "name":
#                writeSequenceToExcelColumn(sheet = framework_page, row_start = 1, col = col,
#                                           length = num_compartments, prefix_list = ["comp_"], cell_format = format_center)
#                
#        
#        # Adjust column size and continue to the next one.
#        framework_page.set_column(col, col, format_variables_colwide["column_width"])
#        col += 1
#        
#    return

#%%

@logUsage
@accepts(str)
def createFrameworkTemplate(framework_path, template_type = SystemSettings.FRAMEWORK_DEFAULT_TYPE,
                                            num_pop_attributes = 0,
                                            num_options_per_pop_attribute = 0,
                                            num_compartments = 0):
    """
    Creates a template framework file in Excel.
    
    Inputs:
        framework_path (str)                    - Directory path for intended framework template.
                                                  Must include filename with extension '.xlsx'.
        template_type (str)                     - A string that denotes the type of template, e.g. what pages to include.
                                                  This acts as a preset id, which instructs what default values in file construction should be.
                                                  A user can specify kwargs to overwrite the template defaults, but the template type denotes baseline values.
        num_pop_attributes (int)                - The number of attributes to include in a population-types page.
        num_options_per_pop_attribute (int)     - The number of options to provide for each attribute.
    """
    # EXAMPLE
    if template_type == SystemSettings.FRAMEWORK_DEFAULT_TYPE:
        num_pop_attributes = 3
        num_options_per_pop_attribute = 4
        num_compartments = 10
    
    # Create a template file and standard formats attached to this file.
    # Also generate default-valued format variables as a dictionary.
    logger.info("Creating a template framework file: {0}".format(framework_path))
    framework_file = xw.Workbook(framework_path)
    formats = createStandardExcelFormats(framework_file)
    format_variables = createDefaultFormatVariables()
    
    # Get the set of keys that refer to framework-file pages.
    # Iterate through them and generate the corresponding pages.
    page_keys = FrameworkSettings.PAGE_COLUMN_KEYS.keys()
    for page_key in page_keys:
        createFrameworkPage(framework_file = framework_file, page_key = page_key, 
                            formats = formats, format_variables = format_variables)
    return framework_file
    

##%%
#
#class FrameworkSettings():
#    page_keys
#    page_column_keys
#
#def createFrameworkPageItem():
#    ...
#
#def createFrameworkPage():
#    createFrameworkPageHeaders()
#    for item in items:
#        createFrameworkPageItem(page_key)
#
#def createFrameworkTemplate(framework_path, framework_details):
#    for page_key in page_keys:
#        createFrameworkPage(page_key)