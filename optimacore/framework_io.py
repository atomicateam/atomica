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
    Get the value of an option of a section within a parsed configuration file.
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

@applyToAllMethods(logUsage)
@loadConfigFile
class FrameworkSettings(object):
    """
    Stores the definitions used in creating and reading framework files.
    Some of this is hard-coded and any changes risk disrupting framework operations.
    The rest is parsed from a framework configuration file during the module import phase.
    Note: As a codebase-specific settings class, there is no need to instantiate it as an object.
    """
    
    TEMPLATE_KEYS_PAGE_COLUMNS = OrderedDict()
    TEMPLATE_KEYS_PAGE_COLUMNS["poptype"] = ["attlabel","attname","optlabel","optname"]
    TEMPLATE_KEYS_PAGE_COLUMNS["comp"] = ["label","name","sourcetag","sinktag","junctiontag"]
    
    FORMAT_VALUE_KEYS = ["column_width","comment_xscale","comment_yscale"]
    
    TEMPLATE_PAGE_SPECS = OrderedDict()
    
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
    
        for page_key in cls.TEMPLATE_KEYS_PAGE_COLUMNS:
            if page_key not in cls.TEMPLATE_PAGE_SPECS:
                cls.TEMPLATE_PAGE_SPECS[page_key] = dict()
            try: cls.TEMPLATE_PAGE_SPECS[page_key]["title"] = getConfigValue(config = cp, section = "page_"+page_key, option = "title")
            except:
                logger.exception("Every page in a framework file needs a title. Framework configuration loading process failed.")
                raise
            for format_value_key in cls.FORMAT_VALUE_KEYS:
                try: 
                    value_overwrite = float(getConfigValue(config = cp, section = "page_"+page_key, option = format_value_key, mute_warnings = True))
                    cls.TEMPLATE_PAGE_SPECS[page_key][format_value_key] = value_overwrite
                except ValueError: logger.warn("Framework configuration file for page-key '{0}' has an entry for '{1}' " 
                                               "that cannot be converted to a float. Using a default value.".format(page_key, format_value_key))
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

#%%

def createFrameworkPage(framework_file, page_key, formats, format_values):
    """  """
    page_name = FrameworkSettings.TEMPLATE_PAGE_SPECS[page_key]["title"]
    logger.info("Creating page: {0}".format(page_name))
    framework_page = framework_file.add_worksheet(page_name)
    
    # Get the set of keys that refer to framework-file page columns.
    column_keys = FrameworkSettings.TEMPLATE_KEYS_PAGE_COLUMNS[page_key]
    
    # Propagate file-wide formats to page-wide formats.
    # Overwrite page-wide formats if specified in config file.
    format_values = dcp(format_values)
    for format_value_key in format_values.keys():
        if format_value_key in FrameworkSettings.TEMPLATE_PAGE_SPECS[page_key]:
            format_values[format_value_key] = FrameworkSettings.TEMPLATE_PAGE_SPECS[page_key][format_value_key]
    
#    # Iterate through the column keys of a page and generate columns if possible.
#    # The bare minimum of a column is a header name.
#    col = 0
#    for column_key in column_keys:
#        try: header_name = getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = "name")
#        except:
#            logger.warn("Skipping column construction for key '{0}' on page '{1}'.".format(column_key, page_name))
#            continue
#        framework_page.write(0, col, header_name, format_center_bold)
#        
#        # Propagate page-wide formats to column-wide formats.
#        # Overwrite column-wide formats if specified in config file.
#        format_values_colwide = {}
#        for format_key in format_keys:
#            format_values_colwide[format_key] = format_values_pagewide[format_key]
#            try: 
#                value_overwrite = float(getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = format_key, mute_warnings = True))
#                format_values_colwide[format_key] = value_overwrite
#            except ValueError: logger.warn("Framework configuration file for page-key '{0}', column-key '{1}', has an entry for '{2}' " 
#                                           "that cannot be converted to a float. Using default.".format(framework_key, column_key, format_key))
#            except: pass
#        
#        # Comment the column header if a comment is available in the configuration file.
#        try: 
#            header_comment = getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = "comment")
#            framework_page.write_comment(0, col, header_comment, 
#                                         {"x_scale": format_values_colwide["comment_xscale"], 
#                                          "y_scale": format_values_colwide["comment_yscale"]})
#        except: pass
#    
#    
#        #
#    
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
#        framework_page.set_column(col, col, format_values_colwide["column_width"])
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
    Creates a template framework Excel file.
    
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
    
    # Get the set of keys that refer to framework-file pages.
    page_keys = FrameworkSettings.TEMPLATE_KEYS_PAGE_COLUMNS.keys()
    
    # Create a template file and non-variable standard formats.
    logger.info("Creating a template framework file: {0}".format(framework_path))
    framework_file = xw.Workbook(framework_path)
    
    formats = dict()
    formats["center_bold"] = framework_file.add_format({"align": "center", "bold": True})
    formats["center"] = framework_file.add_format({"align": "center"})
    
    # Establish framework-file format defaults by importing them from system settings.
    # Each key requires a corresponding system setting variable or an AttributeError will be thrown.
    format_values = dict()
    for format_value_key in FrameworkSettings.FORMAT_VALUE_KEYS:
        exec("format_values[\"{0}\"] = SystemSettings.EXCEL_IO_DEFAULT_{1}".format(format_value_key, format_value_key.upper()))
    
    # Iterate through framework-file keys and generate pages if possible.
    for page_key in page_keys:
        createFrameworkPage(framework_file = framework_file, page_key = page_key, 
                            formats = formats, format_values = format_values)
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