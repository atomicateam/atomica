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
    
    # Keys for float-valued variables related in some way to framework-file formatting.
    # They must have corresponding system-settings defaults.
    FORMAT_VARIABLE_KEYS = ["column_width","comment_xscale","comment_yscale"]
    
    PAGE_SPECS = OrderedDict()
    PAGE_COLUMN_SPECS = OrderedDict()
    
    @classmethod
    def reloadConfigFile(cls):
        """
        Reads a framework configuration file and extends the settings to use the semantics and values provided.
        Is titled with 'reload' as the method will have already been called once during initial import.
        Note: Currently references the default configuration file, but can be modified in the future.
        """
        config_path = getOptimaCorePath(subdir=SystemSettings.CODEBASE_DIRNAME)+SystemSettings.CONFIG_FRAMEWORK_FILENAME
        logger.info("Attempting to generate Optima Core framework settings from configuration file.")
        logger.info("Location... {0}".format(config_path))
                                       
        cp = configparser.ConfigParser()
        cp.read(config_path)
    
        for page_key in cls.PAGE_COLUMN_KEYS:
            if page_key not in cls.PAGE_SPECS: cls.PAGE_SPECS[page_key] = dict()
            try: cls.PAGE_SPECS[page_key]["title"] = getConfigValue(config = cp, section = "page_"+page_key, option = "title")
            except:
                logger.exception("Framework configuration loading process failed. Every page in a framework file needs a title.")
                raise
            for format_variable_key in cls.FORMAT_VARIABLE_KEYS:
                try: 
                    value_overwrite = float(getConfigValue(config = cp, section = "page_"+page_key, option = format_variable_key, mute_warnings = True))
                    cls.PAGE_SPECS[page_key][format_variable_key] = value_overwrite
                except ValueError: logger.warn("Framework configuration file for page-key '{0}' has an entry for '{1}' " 
                                               "that cannot be converted to a float. Using a default value.".format(page_key, format_variable_key))
                except: pass
            
            if page_key not in cls.PAGE_COLUMN_SPECS: cls.PAGE_COLUMN_SPECS[page_key] = OrderedDict()
            for column_key in cls.PAGE_COLUMN_KEYS[page_key]:
                if column_key not in cls.PAGE_COLUMN_SPECS[page_key]: cls.PAGE_COLUMN_SPECS[page_key][column_key] = dict()
                try: cls.PAGE_COLUMN_SPECS[page_key][column_key]["header"] = getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = "header")
                except:
                    logger.exception("Framework configuration loading process failed. Every column in a framework page needs a header.")
                    raise
                try: cls.PAGE_COLUMN_SPECS[page_key][column_key]["comment"] = getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = "comment")
                except: pass
                for format_variable_key in cls.FORMAT_VARIABLE_KEYS:
                    try: 
                        value_overwrite = float(getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = format_variable_key, mute_warnings = True))
                        cls.PAGE_COLUMN_SPECS[page_key][column_key][format_variable_key] = value_overwrite
                    except ValueError: logger.warn("Framework configuration file for page-key '{0}', column-key '{1}', has an entry for '{2}' " 
                                                   "that cannot be converted to a float. Using a default value.".format(page_key, column_key, format_variable_key))
                    except: pass
        
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
    col = 0
    for column_key in column_keys:
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
        col += 1
    return

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
    return
    
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
    return
    

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