# -*- coding: utf-8 -*-
"""
Optima Core databook file.
Contains functions for creating databooks from project frameworks and then importing them.
"""

from optimacore.system import logger, applyToAllMethods, logUsage, accepts, returns, prepareFilePath, SystemSettings, OptimaException
from optimacore.framework_settings import FrameworkSettings
from optimacore.framework import ProjectFramework
from optimacore.databook_settings import DatabookSettings
from optimacore.excel import ExcelSettings, createStandardExcelFormats, createDefaultFormatVariables

from copy import deepcopy as dcp

from collections import OrderedDict

from six import moves as sm
import xlsxwriter as xw



def makeValueEntryBlock(worksheet, start_row, start_col, item_count, time_vector = None, formats = None):
    # Generate standard formats if they do not exist.
    if formats is None: formats = createStandardExcelFormats(databook)

    row = start_row
    col = start_col
    worksheet.write(row, col, "Assumption", formats["center_bold"])
    row = item_count
    last_row = row
    last_col = col
    return worksheet, last_row, last_col



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
@accepts(ProjectFramework,xw.worksheet.Worksheet,str,str,int,int)
def createDatabookSection(framework, datapage, page_key, section_key, start_row, start_col, instructions = None, formats = None, format_variables = None, temp_storage = None):
    """
    Creates a default section on a page within a databook, as defined in databook settings.
    
    Inputs:
        framework (ProjectFramework)                    - The project framework and associated specifications for databook construction.
        datapage (xw.worksheet.Worksheet)               - The Excel sheet in which to create databook sections.
        page_key (str)                                  - The key denoting the provided page, as defined in databook settings.
        section_key (str)                               - The key denoting the type of section to create, as defined in databook settings.
        start_row (int)                                 - The row number of the page at which to generate the default section.
        start_col (int)                                 - The column number of the page at which to generate the default section.
        instructions (DatabookInstructions)             - An object that contains instructions for how many databook items to create.
        formats (dict)                                  - A dictionary of standard Excel formats.
                                                          Is the output of function: createStandardExcelFormats()
                                                          Each key is a string and each value is an 'xlsxwriter.format.Format' object.
        format_variables (dict)                         - A dictionary of format variables, such as column width.
                                                          If left as None, they will be regenerated in this function.
                                                          The keys are listed in Excel settings and the values are floats.
        temp_storage (dict)                             - A container for databook values and formulae that should persist between sections.
                                                          The keys are databook section keys and the values are dictionaries.
    
    Outputs:
        datapage (xw.worksheet.Worksheet)       - The Excel sheet in which databook sections were created.
        next_section_row (int)                  - The row number of the page at which the next section should be created.
                                                  Warning: This is not necessarily the row following the current section.
        next_section_col (int)                  - The column number of the page at which the next section should be created.
                                                  Warning: This is not necessarily the column following the current section.
    """
    # Check if specifications for this section exist, associated with the appropriate page-key.
    try:
        # Decide whether the details for this section are drawn from static databook settings or dynamic framework specifications.
        # The relevant boolean tag should have been set appropriately during framework loading.
        if "refer_to_default" in framework.specs["datapage"][page_key][section_key] and framework.specs["datapage"][page_key][section_key]["refer_to_default"] is True:
            section_specs = DatabookSettings.SECTION_SPECS[section_key]
        else:
            section_specs = framework.specs["datapage"][page_key][section_key]
    except:
        logger.exception("A databook page with key '{0}' was instructed to create a section with key '{1}', despite no relevant section "
                         "specifications existing in default databook settings or derived framework specifications. Abandoning databook construction.".format(page_key,section_key))
        raise KeyError(section_key)

    # Generate standard formats if they do not exist.
    if formats is None: formats = createStandardExcelFormats(databook)
    
    # Initialize requisite values for the upcoming process.
    cell_format = formats["center"]
    row = start_row
    col = start_col

    # Determine if this section will be creating subsections.
    subsection_keys = []
    if not section_specs["subsection_keys"] is None: subsection_keys = section_specs["subsection_keys"]
    
    # CONTINUE HERE AND AT FUNCTION
    if section_specs["type"] == DatabookSettings.SECTION_TYPE_ENTRY:
        _, row, col = makeValueEntryBlock(worksheet = datapage, start_row = row, start_col = col, item_count = 0, time_vector = None, formats = formats)
    else:
        # Create header if required.
        header_name = section_specs["header"]
        if not header_name is None:
            datapage.write(row, col, header_name, formats["center_bold"])
        
        # Propagate page-wide format variable values to section-wide format variable values.
        # Create the format variables if they were not passed in from a page-wide context.
        # Overwrite the page-wide defaults if section-based specifics are available in framework settings.
        if format_variables is None: format_variables = createDefaultFormatVariables()
        else: format_variables = dcp(format_variables)
        for format_variable_key in format_variables:
            if format_variable_key in section_specs:
                format_variables[format_variable_key] = section_specs[format_variable_key]
        
        # Comment the section header if a comment was pulled into framework settings from a configuration file.
        if "comment" in section_specs:
            header_comment = section_specs["comment"]
            datapage.write_comment(row, col, header_comment, 
                                    {"x_scale": format_variables[ExcelSettings.KEY_COMMENT_XSCALE], 
                                    "y_scale": format_variables[ExcelSettings.KEY_COMMENT_YSCALE]})

        # Check if the section specifies any items to list out within its contents.
        if "iterated_type" in section_specs and not section_specs["iterated_type"] is None:
            item_key = section_specs["iterated_type"]
            num_items = instructions.num_items[item_key]
            for item_number in sm.range(num_items):

                section_type = section_specs["type"]
                row += 1
                rc = xw.utility.xl_rowcol_to_cell(row, col)
        
                # Decide what text should be written to each column.
                text = ""
                space = ""
                sep = ""
                validation_source = None
                # Name and label columns can prefix the item number and use fancy separators.
                if section_type in [DatabookSettings.SECTION_TYPE_COLUMN_LABEL, DatabookSettings.SECTION_TYPE_COLUMN_NAME]:
                    text = str(item_number)     # The default is the number of this item.
                    # Note: Once used exec function here but it is now avoided for Python3 compatibility.
                    if section_type == DatabookSettings.SECTION_TYPE_COLUMN_LABEL:
                        space = SystemSettings.DEFAULT_SPACE_LABEL
                        sep = SystemSettings.DEFAULT_SEPARATOR_LABEL
                    else:
                        space = SystemSettings.DEFAULT_SPACE_NAME
                        sep = SystemSettings.DEFAULT_SEPARATOR_NAME
                    if "prefix" in section_specs:
                        text = section_specs["prefix"] + space + text
                text_backup = text

                # If this section references another, overwrite every text value with that of the other section.
                if "ref_section" in section_specs:
                    ref_section = section_specs["ref_section"]
                    try: stored_refs = temp_storage[ref_section]
                    except: raise OptimaException("Databook construction failed when section with key '{0}' referenced a nonexistent section with key '{1}'. "
                                                    "It is possible the nonexistent section is erroneously scheduled to be created later.".format(section_key, ref_section))
                    text_page = ""
                    if not stored_refs["page_label"] == datapage.name:
                        text_page = "'{0}'!".format(stored_refs["page_label"])
                    text = "={0}{1}".format(text_page, stored_refs["list_cell"][item_number])
                    text_backup = stored_refs["list_text_backup"][item_number]

                # Store the contents of this section for referencing by other sections if required.
                if "is_ref" in section_specs and section_specs["is_ref"] is True:
                    if not section_key in temp_storage: temp_storage[section_key] = {"list_text":[],"list_text_backup":[],"list_cell":[]}
                    temp_storage[section_key]["page_label"] = datapage.name
                    temp_storage[section_key]["list_text"].append(text)
                    temp_storage[section_key]["list_text_backup"].append(text_backup)
                    temp_storage[section_key]["list_cell"].append(rc)
                               
                # Write relevant text to the section cell.
                # Note: Equations are only calculated when an application explicitly opens Excel files, so a non-zero 'backup' value must be provided.
                if text.startswith("="):
                    datapage.write_formula(rc, text, cell_format, text_backup)
                else:
                    datapage.write(rc, text, cell_format)
            
                # Validate the cell contents if required.
                if not validation_source is None:
                    datapage.data_validation(rc, {"validate": "list",
                                                  "source": validation_source})

        else:
            if len(subsection_keys) == 0:
                logger.warning("Section with key '{0}' on page '{1}' of the databook does not specify an 'iterated type' or any 'subsection keys', "
                               "so its contents will be left blank.".format(section_key,page_key))

    # Adjust width of section columns.
    # Note: Column width for a supersection is propagated to all subsections, unless there are specific subsection column width values in the databook format configuration file.
    datapage.set_column(start_col, col, format_variables[ExcelSettings.KEY_COLUMN_WIDTH])

    # Generate as many subsections as are required.
    # Track bounding box of section and subsections, in terms of last row and column, so that the next supersection does not overwrite awkward arrangements.
    # WARNING: Databook supersections are assumed to delegate all content creation to subsections, with subsections building from the start row and column of the supersection.
    #          This means subsections may overwrite all or part contents written by the supersection.
    max_row = row
    max_col = col
    sub_row, sub_col = start_row, start_col
    for subsection_key in subsection_keys:
        _, sub_row, sub_col, sub_last_row, sub_last_col = createDatabookSection(framework = framework, datapage = datapage, 
                                                                                page_key = page_key, section_key = subsection_key, 
                                                                                start_row = sub_row, start_col = sub_col, instructions = instructions, 
                                                                                formats = formats, format_variables = format_variables, temp_storage = temp_storage)
        max_row = max(max_row, sub_last_row)
        max_col = max(max_col, sub_last_col)

    # Store the last row and column reached by this section.
    last_row, last_col = max_row, max_col
    if section_specs["row_not_col"]:
        next_section_row = max_row + 2
        next_section_col = start_col
    else:
        next_section_row = start_row
        next_section_col = max_col + 1
    return datapage, next_section_row, next_section_col, last_row, last_col

@logUsage
@accepts(ProjectFramework,xw.Workbook,str)
@returns(xw.Workbook)
def createDatabookPage(framework, databook, page_key, instructions = None, formats = None, format_variables = None, temp_storage = None):
    """
    Creates a page within the databook.
    
    Inputs:
        framework (ProjectFramework)                    - The project framework and associated specifications for databook construction.
        databook (xw.Workbook)                          - The Excel file in which to create the page.
        page_key (str)                                  - The key denoting a particular page, as defined in databook settings.
        instructions (DatabookInstructions)             - An object that contains instructions for how many databook items to create.
        formats (dict)                                  - A dictionary of standard Excel formats, ideally passed in along with the databook.
                                                          If left as None, it will be regenerated in this function.
                                                          Each key is a string and each value is an 'xlsxwriter.format.Format' object.
        format_variables (dict)                         - A dictionary of format variables, such as column width.
                                                          If left as None, they will be regenerated in this function.
                                                          The keys are listed in databook settings and the values are floats.
        temp_storage (dict)                             - A container for databook values and formulae that should persist between sections.
                                                          If left as None, it will be created in this function.
                                                          The keys are databook section keys and the values are dictionaries.
    """
    if instructions is None: instructions = DatabookInstructions()
    if temp_storage is None: temp_storage = dict()
    
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
    
    # Generate standard formats if they do not exist.
    if formats is None: formats = createStandardExcelFormats(databook)
    
    # Create the sections required on this page, excluding subsections.
    row = 0
    col = 0
    for section_key in framework.specs["datapage"][page_key]:
        # Extract the supersection key from section specifics, whether back in static databook settings or carried across to framework specifications.
        if "refer_to_default" in framework.specs["datapage"][page_key][section_key] and framework.specs["datapage"][page_key][section_key]["refer_to_default"] is True:
            supersection_key = DatabookSettings.SECTION_SPECS[section_key]["supersection_key"]
        else:
            supersection_key = framework.specs["datapage"][page_key][section_key]["supersection_key"]
        # Highest-level sections do not have supersections, so they can be constructed in the databook.
        if supersection_key is None:
            _, row, col, _, _ = createDatabookSection(framework = framework, datapage = datapage, page_key = page_key,
                                                      section_key = section_key, start_row = row, start_col = col,
                                                      instructions = instructions, formats = formats, 
                                                      format_variables = format_variables, temp_storage = temp_storage)
    return databook      

@logUsage
@accepts(ProjectFramework,str)
def createDatabookFunc(framework, databook_path, instructions = None, databook_type = SystemSettings.DATABOOK_DEFAULT_TYPE):
    """
    Generate a data-input Excel spreadsheet corresponding to a project framework.

    Inputs:
        framework (ProjectFramework)                    - The project framework and associated specifications for databook construction.
        databook_path (str)                             - Directory path for intended databook.
                                                          Must include filename with extension '.xlsx'.
        instructions (DatabookInstructions)             - An object that contains instructions for how many databook items to create.
        databook_type (str)                             - A string that denotes the type of databook, e.g. how many items to include.
                                                          This acts as a preset ID fed into a DatabookInstructions object upon initialization.
                                                          It is only used if instructions were not explicitly provided to this method.
    """
    if instructions is None: instructions = DatabookInstructions(databook_type = databook_type)

    # Create an empty databook and standard formats attached to this file.
    # Also generate default-valued format variables as a dictionary.
    logger.info("Creating a project databook: {0}".format(databook_path))
    prepareFilePath(databook_path)
    databook = xw.Workbook(databook_path)
    formats = createStandardExcelFormats(databook)
    format_variables = createDefaultFormatVariables()

    # Create a storage dictionary for values and formulae that may persist between sections.
    temp_storage = dict()
    
    # Get the set of keys that refer to databook pages.
    # Iterate through them and generate the corresponding pages.
    count = 0
    for page_key in framework.specs["datapage"]:
        createDatabookPage(framework = framework, databook = databook, page_key = page_key, instructions = instructions, 
                           formats = formats, format_variables = format_variables, temp_storage = temp_storage)
        count += 1
    if count == 0: logger.warning("No instructions for databook page construction were found in framework specifications, "
                                  "suggesting that the referenced ProjectFramework is entirely empty. The resulting databook is correspondingly blank.")

    databook.close()