# -*- coding: utf-8 -*-
"""
Optima Core project-framework input/output file.
Contains functions to create, import and export framework files.
This is primarily referenced by the ProjectFramework object.
"""

from optimacore.system import applyToAllMethods, logUsage, accepts, returns
from optimacore.system import logger, SystemSettings, prepareFilePath
from optimacore.framework_settings import FrameworkSettings

from copy import deepcopy as dcp
from collections import OrderedDict

from six import moves as sm
import xlsxwriter as xw
    

@applyToAllMethods(logUsage)
class FrameworkTemplateInstructions(object):
    """ An object that stores instructions for how many page-items should be created during template framework construction. """
    
    def __init__(self, template_type = SystemSettings.FRAMEWORK_DEFAULT_TYPE):
        """ Initialize instructions that detail how to construct a template framework. """
        self.name = str()
        # Every page-item must be included in a dictionary that lists how many should be created.
        self.num_items = OrderedDict()
        for page_key in FrameworkSettings.PAGE_ITEM_TYPES:
            for item_type in FrameworkSettings.PAGE_ITEM_TYPES[page_key]:
                self.num_items[item_type] = int()
        self.loadPreset(template_type = template_type)
        
    @accepts(str)
    def loadPreset(self, template_type):
        """ Based on hard-coded template types, determine how many page-items should be created. """
        logger.info("Loading template framework instructions of type '{0}'.".format(template_type))
        if template_type == SystemSettings.FRAMEWORK_DEFAULT_TYPE:
            self.name = template_type       # The name of the object is currently just the template type.
            self.num_items["attitem"] = 4
            self.num_items["optitem"] = 3
            self.num_items["compitem"] = 10
            self.num_items["characitem"] = 7
            self.num_items["paritem"] = 20
            self.num_items["progitem"] = 6
            self.num_items["progattitem"] = 3
        return
                          
    @accepts(str,int)
    def updateNumberOfItems(self, item_type, number):
        """ Overwrite the number of items that this object will instruct a template framework creation to produce. """
        try: self.num_items[item_type] = number
        except:
            logger.exception("An attempted update of framework instructions '{0}' to produce '{1}' instances of item type '{2}' failed.".format(self.name, number, item_type))
            raise
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
    Note: Once used exec function here but it is now avoided for Python3 compatibility.
    """
    format_variables = dict()
    format_variables["column_width"] = SystemSettings.EXCEL_IO_DEFAULT_COLUMN_WIDTH
    format_variables["comment_xscale"] = SystemSettings.EXCEL_IO_DEFAULT_COMMENT_XSCALE
    format_variables["comment_yscale"] = SystemSettings.EXCEL_IO_DEFAULT_COMMENT_YSCALE
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
    for attribute in FrameworkSettings.ITEM_TYPE_ATTRIBUTES:
        item_attributes[attribute] = {"cell":None, "value":None, "backup":None}
    return item_attributes



@logUsage
@accepts(xw.worksheet.Worksheet,str,dict)
@returns(xw.worksheet.Worksheet)
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
        col = FrameworkSettings.COLUMN_SPECS[column_key]["default_pos"]
        header_name = FrameworkSettings.COLUMN_SPECS[column_key]["header"]
        framework_page.write(0, col, header_name, formats["center_bold"])
        
        # Propagate pagewide format variable values to column-wide format variable values.
        # Create the format variables if they were not passed in from a page-wide context.
        # Overwrite the page-wide defaults if column-based specifics are available in framework settings.
        if format_variables is None: format_variables = createDefaultFormatVariables()
        else: format_variables = dcp(format_variables)
        for format_variable_key in format_variables:
            if format_variable_key in FrameworkSettings.COLUMN_SPECS[column_key]:
                format_variables[format_variable_key] = FrameworkSettings.COLUMN_SPECS[column_key][format_variable_key]
        
        # Comment the column header if a comment was pulled into framework settings from a configuration file.
        if "comment" in FrameworkSettings.COLUMN_SPECS[column_key]:
            header_comment = FrameworkSettings.COLUMN_SPECS[column_key]["comment"]
            framework_page.write_comment(0, col, header_comment, 
                                         {"x_scale": format_variables["comment_xscale"], 
                                          "y_scale": format_variables["comment_yscale"]})
    
        # Adjust column width and continue to the next one.
        framework_page.set_column(col, col, format_variables["column_width"])
    return framework_page


@logUsage
@accepts(xw.worksheet.Worksheet,str,str,int,dict)
def createFrameworkPageItem(framework_page, page_key, item_type, start_row, formats, 
                            instructions = None, item_number = None, superitem_attributes = None):
    """
    Creates a default item on a page within a framework file, as defined in framework settings.
    
    Inputs:
        framework_page (xw.worksheet.Worksheet)         - The Excel sheet in which to create page-items.
        page_key (str)                                  - The key denoting the provided page, as defined in framework settings.
        item_type (str)                                 - The key denoting the type of item to create, as defined in framework settings.
        start_row (int)                                 - The row number of the page at which to generate the default page-item.
        formats (dict)                                  - A dictionary of standard Excel formats.
                                                          Is the output of function: createStandardExcelFormats()
                                                          Each key is a string and each value is an 'xlsxwriter.format.Format' object.
        instructions (FrameworkTemplateInstructions)    - An object that contains instructions for how many page-items to create.
        item_number (int)                               - A number to identify this item, ostensibly within a list, used for default text write-ups.
        superitem_attributes (dict)                     - A dictionary of attribute values relating to the superitem constructing this page-item, if one exists.
                                                          Is the output of function: createEmptyPageItemAttributes()
    
    Outputs:
        framework_page (xw.worksheet.Worksheet) - The Excel sheet in which page-items were created.
        next_row (int)                          - The next row number of the page after the page-item.
                                                  Is useful to provide for page-items that involve subitems and multiple rows.
    """
    # Check if specifications for this page-item exist, associated with the appropriate page-key.
    if not item_type in FrameworkSettings.PAGE_ITEM_TYPES[page_key]:
        logger.exception("A framework page with key '{0}' was instructed to create an item of type '{1}', despite no relevant page-item "
                         "specifications existing in framework settings. Abandoning framework file construction.".format(page_key,item_type))
        raise KeyError(item_type)
    item_type_specs = FrameworkSettings.ITEM_TYPE_SPECS[item_type]
    
    # Initialize requisite values for the upcoming process.
    cell_format = formats["center"]
    row = start_row
    if item_number is None: item_number = 0
    
    # Determine which columns will be filled out with default values for this page-item.
    # Determine if any subitems need to be constructed as well and space out a page-item attribute dictionary for subitems.
    column_keys = FrameworkSettings.PAGE_COLUMN_KEYS[page_key]
    item_type_column_keys = []
    if not item_type_specs["column_keys"] is None: item_type_column_keys = item_type_specs["column_keys"]
    if item_type_specs["inc_not_exc"]: column_keys = item_type_column_keys
    subitem_types = []
    if not item_type_specs["subitem_types"] is None: subitem_types = item_type_specs["subitem_types"]
    item_attributes = createEmptyPageItemAttributes()
        
    # Iterate through page columns if part of a page-item and fill them with default values according to type.
    for column_key in column_keys:
        if (not item_type_specs["inc_not_exc"]) and column_key in item_type_column_keys: continue
        column_specs = FrameworkSettings.COLUMN_SPECS[column_key]
        column_type = column_specs["type"]
        col = column_specs["default_pos"]
        rc = xw.utility.xl_rowcol_to_cell(row, col)
        
        # Decide what text should be written to each column.
        text = ""
        space = ""
        sep = ""
        validation_source = None
        # Name and label columns can prefix the item number and use fancy separators.
        if column_type in [FrameworkSettings.COLUMN_TYPE_LABEL, FrameworkSettings.COLUMN_TYPE_NAME]:
            text = str(item_number)     # The default is the number of this item.
            # Note: Once used exec function here but it is now avoided for Python3 compatibility.
            if column_type == FrameworkSettings.COLUMN_TYPE_LABEL:
                space = SystemSettings.DEFAULT_SPACE_LABEL
                sep = SystemSettings.DEFAULT_SEPARATOR_LABEL
            else:
                space = SystemSettings.DEFAULT_SPACE_NAME
                sep = SystemSettings.DEFAULT_SEPARATOR_NAME
            if "prefix" in column_specs:
                text = column_specs["prefix"] + space + text
        # Switch columns display and Excel-validate symbols corresponding to boolean values of True and False.
        elif column_type in [FrameworkSettings.COLUMN_TYPE_SWITCH_DEFAULT_OFF, FrameworkSettings.COLUMN_TYPE_SWITCH_DEFAULT_ON]:
            validation_source = [SystemSettings.DEFAULT_SYMBOL_NO, SystemSettings.DEFAULT_SYMBOL_YES]
            if column_type == FrameworkSettings.COLUMN_TYPE_SWITCH_DEFAULT_ON: validation_source.reverse()
            text = validation_source[0]
        text_backup = text

        # A compartment-characteristic list column specially references names of previously-defined compartments and characteristics.
        # Note: These references are somewhat hardcoded.
        if column_type == FrameworkSettings.COLUMN_TYPE_LIST_COMP_CHARAC:
            title_comp = FrameworkSettings.PAGE_SPECS[FrameworkSettings.KEY_COMPARTMENT]["title"]
            col_comp = FrameworkSettings.COLUMN_SPECS[FrameworkSettings.KEY_COMPARTMENT_NAME]["default_pos"]
            rc_comp = xw.utility.xl_rowcol_to_cell(row, col_comp)
            text = "=CONCATENATE('{0}'!{1}".format(title_comp,rc_comp)
            text_backup = FrameworkSettings.COLUMN_SPECS[FrameworkSettings.KEY_COMPARTMENT_NAME]["prefix"] + SystemSettings.DEFAULT_SPACE_NAME + str(item_number)
            if row > 1:
                col_charac = FrameworkSettings.COLUMN_SPECS[FrameworkSettings.KEY_CHARACTERISTIC_NAME]["default_pos"]
                rc_charac = xw.utility.xl_rowcol_to_cell(row-1, col_charac)
                text += ",\", \",{0}".format(rc_charac)
                text_backup += (SystemSettings.EXCEL_LIST_SEPARATOR + " " + 
                         FrameworkSettings.COLUMN_SPECS[FrameworkSettings.KEY_CHARACTERISTIC_NAME]["prefix"] + SystemSettings.DEFAULT_SPACE_NAME + str(item_number-1))
        
            text += ")"
        
        # Check if this page-item has a superitem and if the column being constructed is considered an important attribute.
        # If so, the column text may be improved to reference any corresponding attributes of its superitem.
        if not superitem_attributes is None:
            for attribute in FrameworkSettings.ITEM_TYPE_ATTRIBUTES:
                if column_key == item_type_specs["key_"+attribute]:
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
        for attribute in FrameworkSettings.ITEM_TYPE_ATTRIBUTES:
            if column_key == item_type_specs["key_"+attribute]:
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
    for subitem_type in subitem_types:
        for subitem_number in sm.range(instructions.num_items[subitem_type]):
            _, row = createFrameworkPageItem(framework_page = framework_page, page_key = page_key,
                                                   item_type = subitem_type, start_row = row, 
                                                   formats = formats, item_number = subitem_number,
                                                   superitem_attributes = item_attributes)
    next_row = max(start_row + 1, row)  # Make sure that the next row is always at least the row after the row of the current item.
    return framework_page, next_row


@logUsage
@accepts(xw.Workbook,str)
@returns(xw.Workbook)
def createFrameworkPage(framework_file, page_key, instructions = None, formats = None, format_variables = None):
    """
    Creates a page within the framework file.
    
    Inputs:
        framework_file (xw.Workbook)                    - The Excel file in which to create the page.
        page_key (str)                                  - The key denoting a particular page, as defined in framework settings.
        instructions (FrameworkTemplateInstructions)    - An object that contains instructions for how many page-items to create.
        formats (dict)                                  - A dictionary of standard Excel formats, ideally passed in along with the framework file.
                                                          If left as None, it will be regenerated in this function.
                                                          Each key is a string and each value is an 'xlsxwriter.format.Format' object.
        format_variables (dict)                         - A dictionary of format variables, such as column width.
                                                          If left as None, they will be regenerated in this function.
                                                          The keys are listed in framework settings and the values are floats.
    """
    if instructions is None: instructions = FrameworkTemplateInstructions()
    
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
    for format_variable_key in format_variables:
        if format_variable_key in FrameworkSettings.PAGE_SPECS[page_key]:
            format_variables[format_variable_key] = FrameworkSettings.PAGE_SPECS[page_key][format_variable_key]
    
    # Generate standard formats if they do not exist and construct headers for the page.
    if formats is None: formats = createStandardExcelFormats(framework_file)
    createFrameworkPageHeaders(framework_page = framework_page, page_key = page_key, 
                               formats = formats, format_variables = format_variables)
    
    # Create the number of base items required on this page.
    # Officially, the initial item key per page is that of the core item-type, but this generic code works for all items without superitems.
    row = 1
    for item_type in FrameworkSettings.PAGE_ITEM_TYPES[page_key]:
        if FrameworkSettings.ITEM_TYPE_SPECS[item_type]["superitem_type"] is None:
            for item_number in sm.range(instructions.num_items[item_type]):
                _, row = createFrameworkPageItem(framework_page = framework_page, page_key = page_key,
                                                 item_type = item_type, start_row = row, 
                                                 instructions = instructions, formats = formats, item_number = item_number)
    return framework_file            


@logUsage
@accepts(str)
def createFrameworkTemplate(framework_path, instructions = None, template_type = SystemSettings.FRAMEWORK_DEFAULT_TYPE):
    """
    Creates a template framework file in Excel.
    
    Inputs:
        framework_path (str)                            - Directory path for intended framework template.
                                                          Must include filename with extension '.xlsx'.
        instructions (FrameworkTemplateInstructions)    - An object that contains instructions for how many page-items to create.
        template_type (str)                             - A string that denotes the type of template, e.g. how many page items to include.
                                                          This acts as a preset id fed into a FrameworkTemplateInstructions object upon initialization.
                                                          It is only used if instructions were not explicitly provided to this method.
    """
    if instructions is None: instructions = FrameworkTemplateInstructions(template_type = template_type)
    
    # Create a template file and standard formats attached to this file.
    # Also generate default-valued format variables as a dictionary.
    logger.info("Creating a template framework file: {0}".format(framework_path))
    prepareFilePath(framework_path)
    framework_file = xw.Workbook(framework_path)
    formats = createStandardExcelFormats(framework_file)
    format_variables = createDefaultFormatVariables()
    
    # Get the set of keys that refer to framework-file pages.
    # Iterate through them and generate the corresponding pages.
    for page_key in FrameworkSettings.PAGE_KEYS:
        createFrameworkPage(framework_file = framework_file, page_key = page_key, instructions = instructions, 
                            formats = formats, format_variables = format_variables)
    framework_file.close()