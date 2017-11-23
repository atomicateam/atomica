# -*- coding: utf-8 -*-
"""
Optima Core project-framework input/output file.
Contains functions to create, import and export framework files.
This is primarily referenced by the ProjectFramework object.
"""

from optimacore.system import applyToAllMethods, logUsage, accepts, returns
from optimacore.system import logger, SystemSettings, getOptimaCorePath, OptimaException

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
    
    COLUMN_ITEM_TYPES = ["label","name","switch"]
    
    # Keys for float-valued variables related in some way to framework-file formatting.
    # They must have corresponding system-settings defaults.
    FORMAT_VARIABLE_KEYS = ["column_width","comment_xscale","comment_yscale"]
    
    # Hard-coded details for generating default page-items, made as abstract as possible.
    PAGE_ITEM_KEYS = OrderedDict()
    PAGE_ITEM_KEYS["poptype"] = ["attitem","optitem"]
    PAGE_ITEM_KEYS["comp"] = ["compitem"]
    PAGE_ITEM_KEYS["trans"] = []
    PAGE_ITEM_ATTRIBUTES = ["label","name"]
    
    # A default dictionary of page-item specifics is constructed first, then overwritten as required.
    # Warning: These values are considered hard-coded and thus relatively unvalidated.
    #          Incorrect modifications can result in undesirable behaviour including broken Excel links and subitem recursions.
    PAGE_ITEM_SPECS = OrderedDict()
    for page_key in PAGE_ITEM_KEYS:
        PAGE_ITEM_SPECS[page_key] = dict()
        for item_type in PAGE_ITEM_KEYS[page_key]:
            # Specify whether page-item construction should include or exclude filling out specified columns.
            # Then specify a list of column keys to be included or excluded when constructing a page-item.
            # Many page-items involve all columns, so the default is to exclude no columns.
            PAGE_ITEM_SPECS[page_key][item_type] = {"inc_not_exc":False, "column_keys":None,
            # Many page-items will have a display label and code name, so appropriate column keys should be recorded.
                                                    "label_key":None, "name_key":None,
            # Some page-items can be divided into columns and other page-items; the keys of the latter should be listed.
            # While page-items have no restriction in producing page-items, it is also useful to mark ones that are only ever subitems. 
                                                    "subitem_keys":None,
                                                    "is_subitem":False}
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
    PAGE_ITEM_SPECS["poptype"]["optitem"]["is_subitem"] = True
    
    
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
                try: cls.PAGE_COLUMN_SPECS[page_key][column_key]["prefix"] = getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = "prefix", mute_warnings = True)
                except: pass
                # Read in required type of item that this column contains.
                try: 
                    value = getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = "type")
                    if value not in cls.COLUMN_ITEM_TYPES:
                        error_string = ("Framework configuration file for page-key '{0}', column-key '{1}', has an entry for 'type' " 
                                        "that is not listed in framework settings.".format(page_key, column_key))
                        logger.error(error_string)
                        logger.error("Valid options: {0}".format(", ".join(cls.COLUMN_ITEM_TYPES)))
                        raise OptimaException(error_string)
                    cls.PAGE_COLUMN_SPECS[page_key][column_key]["type"] = value
                except: 
                    logger.exception("Framework configuration loading process failed. Every column in a framework page needs a valid type.")
                    raise
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
def createEmptyPageItemAttributes():
    """
    Generates a dictionary of page-item attributes, e.g. name and label, that is empty of values.
    The primary key lists the attributes of a page-item.
    
    Subkeys:        Values:
        cell            The location of a page-item attribute in 'A1' format.
        value           The value of the page-item attribute, possibly in unresolved format, i.e. involving equations and cell references.
                        Useful so that changing the value of the referenced cell propagates immediately.
        backup          The value of the page-item attribute in resolved format, i.e. without equations and cell references.
                        Required in case the resulting Excel file is constructed and loaded without viewing externally.
                        Opening in an external application is required in order to process the equations and references.
    """
    item_attributes = dict()
    for attribute in FrameworkSettings.PAGE_ITEM_ATTRIBUTES:
        item_attributes[attribute] = {"cell":None, "value":None, "backup":None}
    return item_attributes



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
@accepts(xw.worksheet.Worksheet,str,str,int,dict)
def createFrameworkPageItem(framework_page, page_key, item_key, start_row, formats, 
                            item_number = None, superitem_attributes = None):
    """
    Creates a default item on a page within a framework file, as defined in framework settings.
    
    Inputs:
        framework_page (xw.worksheet.Worksheet) - The Excel sheet in which to create page-items.
        page_key (str)                          - The key denoting the provided page, as defined in framework settings.
        item_key (str)                          - The key denoting the page-item to create, as defined in framework settings.
        start_row (int)                         - The row number of the page at which to generate the default page-item.
        formats (dict)                          - A dictionary of standard Excel formats.
                                                  Is the output of function: createStandardExcelFormats()
                                                  Each key is a string and each value is an 'xlsxwriter.format.Format' object.
        item_number (int)                       - A number to identify this item, ostensibly within a list, used for default text write-ups.
        superitem_attributes (dict)             - A dictionary of attribute values relating to the superitem constructing this page-item, if one exists.
                                                  Is the output of function: createEmptyPageItemAttributes()
    
    Outputs:
        framework_page (xw.worksheet.Worksheet) - The Excel sheet in which page-items were created.
        next_row (int)                          - The next row number of the page after the page-item.
                                                  Is useful to provide for page-items that involve subitems and multiple rows.
    """
    # Check if specifications for this page-item exist, associated with the appropriate page-key.
    if not item_key in FrameworkSettings.PAGE_ITEM_SPECS[page_key]:
        logger.exception("A framework page with key '{0}' was instructed to create a page-item with key '{1}', despite no relevant page-item "
                         "specifications existing in framework settings. Abandoning framework file construction.".format(page_key,item_key))
        raise KeyError(item_key)
    item_specs = FrameworkSettings.PAGE_ITEM_SPECS[page_key][item_key]
    
    # Initialise requisite values for the upcoming process.
    cell_format = formats["center"]
    row = start_row
    if item_number is None: item_number = 0
    
    # Determine which columns will be filled out with default values for this page-item.
    # Determine if any subitems need to be constructed as well and space out a page-item attribute dictionary for subitems.
    column_keys = FrameworkSettings.PAGE_COLUMN_KEYS[page_key]
    item_column_keys = []
    if not item_specs["column_keys"] is None: item_column_keys = item_specs["column_keys"]
    if item_specs["inc_not_exc"]: column_keys = item_column_keys
    subitem_keys = []
    if not item_specs["subitem_keys"] is None: subitem_keys = item_specs["subitem_keys"]
    item_attributes = createEmptyPageItemAttributes()
        
    # Iterate through page columns if part of a page-item and fill them with default values according to type.
    for column_key in column_keys:
        if (not item_specs["inc_not_exc"]) and column_key in item_column_keys: continue
        column_specs = FrameworkSettings.PAGE_COLUMN_SPECS[page_key][column_key]
        column_type = column_specs["type"]
        col = column_specs["default_num"]
        rc = xw.utility.xl_rowcol_to_cell(row, col)
        
        # Decide what text should be written to each column.
        text = str(item_number)     # The default is the number of this item.
        space = ""
        sep = ""
        validation_source = None
        # Name and label columns can prefix the item number and use fancy separators.
        if column_type in ["name","label"]:
            try:
                exec("space = SystemSettings.DEFAULT_SPACE_{0}".format(column_type.upper()))
                exec("sep = SystemSettings.DEFAULT_SEPARATOR_{0}".format(column_type.upper()))
            except: pass
            if "prefix" in column_specs:
                text = column_specs["prefix"] + space + text
        elif column_type in ["switch"]:
            validation_source = [SystemSettings.DEFAULT_SYMBOL_NO, SystemSettings.DEFAULT_SYMBOL_YES]
            text = validation_source[0]
        text_backup = text
        
        # Check if this page-item has a superitem and if the column being constructed is considered an important attribute.
        # If so, the column text may be improved to reference any corresponding attributes of its superitem.
        if not superitem_attributes is None:
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
        
        # Update attribute dictionary if constructing a column that is marked in framework settings as a page-item attribute.
        for attribute in FrameworkSettings.PAGE_ITEM_ATTRIBUTES:
            if column_key == item_specs[attribute+"_key"]:
                item_attributes[attribute]["cell"] = xw.utility.xl_rowcol_to_cell(row, col)
                item_attributes[attribute]["value"] = text
                item_attributes[attribute]["backup"] = text_backup
                               
        # Write relevant text to each column.
        # Note: Equations are only calculated when an application explicitly opens Excel files, so a non-zero 'backup' value must be provided.
        if text.startswith("="):
            framework_page.write_formula(rc, text, cell_format, text_backup)
        else:
            framework_page.write(rc, text, cell_format)
            
        # Validate the cell contents if required.
        if not validation_source is None:
            framework_page.data_validation(rc, {'validate': 'list',
                                                'source': validation_source})
    
    # Generate as many subitems as are required to be attached to this page-item.
    for subitem_key in subitem_keys:
        for subitem_number in xrange(4):
            _, row = createFrameworkPageItem(framework_page = framework_page, page_key = page_key,
                                                   item_key = subitem_key, start_row = row, 
                                                   formats = formats, item_number = subitem_number,
                                                   superitem_attributes = item_attributes)
    next_row = max(start_row + 1, row)  # Make sure that the next row is always at least the row after the row of the current item.
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
    
    # Create the number of base items required on this page.
    row = 1
    for item_key in FrameworkSettings.PAGE_ITEM_SPECS[page_key]:
        if not FrameworkSettings.PAGE_ITEM_SPECS[page_key][item_key]["is_subitem"]:
            for item_number in xrange(3):
                _, row = createFrameworkPageItem(framework_page = framework_page, page_key = page_key,
                                                 item_key = item_key, start_row = row, 
                                                 formats = formats, item_number = item_number)
    return framework_file


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