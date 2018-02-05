from optimacore.system import SystemSettings as SS
from optimacore.framework_settings import WorkbookSettings as FS
from optimacore.databook_settings import DatabookSettings as DS
from optimacore.excel import ExcelSettings as ES

from optimacore.system import logger, OptimaException, accepts, prepareFilePath
from optimacore.excel import createStandardExcelFormats, createDefaultFormatVariables
from optimacore.framework import ProjectFramework

from collections import OrderedDict
from copy import deepcopy as dcp
from six import moves as sm
import xlsxwriter as xw

class WorkbookTypeException(OptimaException):
    def __init__(self, workbook_type, **kwargs):
        available_workbook_types = [SS.WORKBOOK_KEY_FRAMEWORK, SS.WORKBOOK_KEY_DATA]
        message = ("Unable to operate read and write processes for a workbook of type '{0}'. "
                   "Available options are: '{1}'".format(workbook_type, "' or '".join(available_workbook_types)))
        return super().__init__(message, **kwargs)

class KeyUniquenessException(OptimaException):
    def __init__(self, key, dict_type, **kwargs):
        if key is None: message = ("Key uniqueness failure. A key is used more than once in '{0}'.".format(dict_type))
        else: message = ("Key uniqueness failure. Key '{0}' is used more than once in '{1}'.".format(key, dict_type))
        return super().__init__(message, **kwargs)

class WorkbookInstructions(object):
    """ An object that stores instructions for how many items should be created during workbook construction. """
    
    def __init__(self, workbook_type = None):
        """ Initialize instructions that detail how to construct a workbook. """
        # Every relevant item must be included in a dictionary that lists how many should be created.
        self.num_items = OrderedDict()
        if workbook_type == SS.WORKBOOK_KEY_FRAMEWORK: item_type_specs = FS.ITEM_TYPE_SPECS
        else: raise WorkbookTypeException(workbook_type)
        for item_type in item_type_specs:
            self.num_items[item_type] = item_type_specs[item_type]["default_amount"]
                          
    @accepts(str,int)
    def updateNumberOfItems(self, item_type, number):
        """ Overwrite the number of items that will be constructed for the template workbook. """
        try: self.num_items[item_type] = number
        except:
            logger.error("An attempted update of workbook instructions to produce '{0}' instances of item type '{1}' failed.".format(number, item_type))
            raise

def writeHeaders(worksheet, item_type, start_row, start_col, framework = None, data = None, instructions = None, workbook_type = None, formats = None, format_variables = None):
    if workbook_type == SS.WORKBOOK_KEY_FRAMEWORK: item_type_spec = FS.ITEM_TYPE_SPECS[item_type]
    #table_types = FS.PAGE_TABLE_TYPES[page_key]
#elif workbook_type == SS.WORKBOOK_KEY_DATA:
    else: raise WorkbookTypeException(workbook_type)

    if formats is None: raise OptimaException("Excel formats have not been passed to workbook table construction.")
    if format_variables is None: format_variables = createDefaultFormatVariables()
    orig_format_variables = dcp(format_variables)
    format_variables = dcp(orig_format_variables)
    revert_format_variables = False

    row, col, header_column_map = start_row, start_col, dict()
    for attribute in item_type_spec["attributes"]:
        attribute_spec = item_type_spec["attributes"][attribute]
        if "ref_item_type" in attribute_spec:
            _, col, sub_map = writeHeaders(worksheet = worksheet, item_type = attribute_spec["ref_item_type"],
                                           start_row = row, start_col = col,
                                           framework = framework, data = data, instructions = instructions, workbook_type = workbook_type,
                                           formats = formats, format_variables = format_variables)
            len_map = len(header_column_map)
            len_sub_map = len(sub_map)
            header_column_map.update(sub_map)
            if not len(header_column_map) == len_map + len_sub_map: raise KeyUniquenessException(None, "header-column map")
        else:
            for format_variable_key in format_variables:
                if format_variable_key in attribute_spec:
                    revert_format_variables = True
                    format_variables[format_variable_key] = attribute_spec[format_variable_key]
            header = attribute_spec["header"]
            if header in header_column_map: raise KeyUniquenessException(header, "header-column map")
            header_column_map[header] = col
            worksheet.write(row, col, header, formats["center_bold"])
            if "comment" in attribute_spec:
                header_comment = attribute_spec["comment"]
                worksheet.write_comment(row, col, header_comment, 
                                        {"x_scale": format_variables[ES.KEY_COMMENT_XSCALE], 
                                            "y_scale": format_variables[ES.KEY_COMMENT_YSCALE]})
            worksheet.set_column(col, col, format_variables[ES.KEY_COLUMN_WIDTH])
            if revert_format_variables:
                format_variables = dcp(orig_format_variables)
                revert_format_variables = False
            col += 1
    row += 1
    next_row, next_col = row, col
    return next_row, next_col, header_column_map

def writeContents(worksheet, item_type, start_row, header_column_map, framework = None, data = None, instructions = None, workbook_type = None,
                  formats = None, temp_storage = None):
    if workbook_type == SS.WORKBOOK_KEY_FRAMEWORK: 
        item_type_specs = FS.ITEM_TYPE_SPECS
        item_type_spec = FS.ITEM_TYPE_SPECS[item_type]
        if framework is None:
            if instructions is None: instructions = WorkbookInstructions(workbook_type = workbook_type)
        else:
            print('WHOOPS')
    #table_types = FS.PAGE_TABLE_TYPES[page_key]
#elif workbook_type == SS.WORKBOOK_KEY_DATA:
    else: raise WorkbookTypeException(workbook_type)

    if formats is None: raise OptimaException("Excel formats have not been passed to workbook table construction.")
    cell_format = formats["center"]

    if temp_storage is None: temp_storage = dict()

    row, new_row = start_row, start_row
    for item_number in sm.range(instructions.num_items[item_type]):
        for attribute in item_type_spec["attributes"]:
            attribute_spec = item_type_spec["attributes"][attribute]
            if "ref_item_type" in attribute_spec:
                sub_row = writeContents(worksheet = worksheet, item_type = attribute_spec["ref_item_type"],
                                           start_row = row, header_column_map = header_column_map,
                                           framework = framework, data = data, instructions = instructions, workbook_type = workbook_type,
                                           formats = formats, temp_storage = temp_storage)
                new_row = max(new_row, sub_row)
            else:
                col = header_column_map[attribute_spec["header"]]
                rc = xw.utility.xl_rowcol_to_cell(row, col)

                content = ""
                space = ""
                sep = ""
                validation_source = None

                reference_type = None
                content_type = attribute_spec["content_type"]
                if isinstance(content_type, FS.SuperReference):
                    reference_type = dcp(content_type)
                    content_type = item_type_specs[reference_type.item_type]["attributes"][reference_type.attribute]["content_type"]
                if isinstance(content_type, FS.LabelType) or isinstance(content_type, FS.NameType):
                    content = str(item_number)     # The default is the number of this item.
                    if isinstance(content_type, FS.LabelType):
                        space = SS.DEFAULT_SPACE_LABEL
                        sep = SS.DEFAULT_SEPARATOR_LABEL
                    else:
                        space = SS.DEFAULT_SPACE_NAME
                        sep = SS.DEFAULT_SEPARATOR_NAME
                    if "prefix" in attribute_spec:
                        content = attribute_spec["prefix"] + space + content
                content_backup = content

                if not reference_type is None:
                    # 'Super' references link subitem attributes to corresponding superitem attributes.
                    # Because subitem displays are created instantly after superitems, the superitem referenced is the last one stored.
                    list_id = item_number
                    if isinstance(reference_type, FS.SuperReference): list_id = -1
                    try: stored_refs = temp_storage[reference_type.item_type][reference_type.attribute]
                    except:
                        logger.error("Workbook construction failed when item '{0}', attribute '{1}', attempt to reference nonexistent values, specifically item '{2}', attribute '{3}'. "
                                     "It is possible the referenced attribute values are erroneously scheduled to be created later.".format(item_type, attribute, reference_type.item_type, reference_type.attribute))
                        raise
                    content_page = ""
                    if not stored_refs["page_label"] == worksheet.name:
                        content_page = "'{0}'!".format(stored_refs["page_label"])
                    ref_content = "={0}{1}".format(content_page, stored_refs["list_cell"][list_id])
                    ref_content_backup = stored_refs["list_content_backup"][list_id]
                    if isinstance(reference_type, FS.SuperReference):
                        content = "=CONCATENATE({0},\"{1}\")".format(ref_content.lstrip("="), sep + content)
                        content_backup = ref_content_backup + sep + content_backup
                    else:
                        content = ref_content
                        content_backup = content_backup

                # Store the contents of this attribute for referencing by other attributes if required.
                if "is_ref" in attribute_spec and attribute_spec["is_ref"] is True:
                    if not item_type in temp_storage: temp_storage[item_type] = {}
                    if not attribute in temp_storage[item_type]: temp_storage[item_type][attribute] = {"list_content":[],"list_content_backup":[],"list_cell":[]}
                    # Make sure the attribute does not already have stored values associated with it.
                    if not len(temp_storage[item_type][attribute]["list_content"]) > item_number:
                        temp_storage[item_type][attribute]["list_content"].append(content)
                        temp_storage[item_type][attribute]["list_content_backup"].append(content_backup)
                        temp_storage[item_type][attribute]["list_cell"].append(rc)
                        temp_storage[item_type][attribute]["page_label"] = worksheet.name

                if content.startswith("="):
                    worksheet.write_formula(rc, content, cell_format, content_backup)
                else:
                    worksheet.write(rc, content, cell_format)

                if not validation_source is None:
                    framework_page.data_validation(rc, {"validate": "list",
                                                        "source": validation_source})
        row = max(new_row, row + 1)
    next_row = row
    return next_row

def writeDetailColumns(worksheet, core_item_type, start_row, start_col, framework = None, data = None, instructions = None, workbook_type = None, 
                       formats = None, format_variables = None, temp_storage = None):

    if temp_storage is None: temp_storage = dict()

    row, col = start_row, start_col
    row, _, header_column_map = writeHeaders(worksheet = worksheet, item_type = core_item_type, start_row = row, start_col = col,
                          framework = framework, data = data, instructions = instructions, workbook_type = workbook_type,
                          formats = formats, format_variables = format_variables)
    row = writeContents(worksheet = worksheet, item_type = core_item_type, start_row = row, header_column_map = header_column_map,
                           framework = framework, data = data, instructions = instructions, workbook_type = workbook_type,
                           formats = formats, temp_storage = temp_storage)
    next_row, next_col = row, col
    return next_row, next_col


def writeTable(worksheet, table_type, start_row, start_col, framework = None, data = None, instructions = None, workbook_type = None, 
               formats = None, format_variables = None, temp_storage = None):

    # Check workbook type. Gather relevant details.
    if workbook_type not in [SS.WORKBOOK_KEY_FRAMEWORK, SS.WORKBOOK_KEY_DATA]:
        raise WorkbookTypeException(workbook_type)

    if temp_storage is None: temp_storage = dict()

    if isinstance(table_type, FS.DetailColumns):
        core_item_type = table_type.item_type
        row, col = writeDetailColumns(worksheet = worksheet, core_item_type = core_item_type, start_row = start_row, start_col = start_col,
                                      framework = framework, data = data, instructions = instructions, workbook_type = workbook_type,
                                      formats = formats, format_variables = format_variables, temp_storage = temp_storage)
    
    next_row, next_col = row, col
    return next_row, next_col





def writeWorksheet(workbook, page_key, framework = None, data = None, instructions = None, workbook_type = None, 
                   formats = None, format_variables = None, temp_storage = None):

    # Check workbook type. Gather relevant details.
    if workbook_type == SS.WORKBOOK_KEY_FRAMEWORK:
        page_spec = FS.PAGE_SPECS[page_key]
        #table_types = FS.PAGE_TABLE_TYPES[page_key]
    #elif workbook_type == SS.WORKBOOK_KEY_DATA:
    else:
        raise WorkbookTypeException(workbook_type)

    # Construct worksheet.
    page_name = page_spec["title"]
    logger.info("Creating page: {0}".format(page_name))
    worksheet = workbook.add_worksheet(page_name)

    # Propagate file-wide format variable values to page-wide format variable values.
    # Create the format variables if they were not passed in from a file-wide context.
    # Overwrite the file-wide defaults if page-based specifics are available in framework settings.
    if format_variables is None: format_variables = createDefaultFormatVariables()
    else: format_variables = dcp(format_variables)
    for format_variable_key in format_variables:
        if format_variable_key in page_spec:
            format_variables[format_variable_key] = page_spec[format_variable_key]
    
    # Generate standard formats if they do not exist and construct headers for the page.
    if formats is None: formats = createStandardExcelFormats(workbook)

    if temp_storage is None: temp_storage = dict()

    # Iteratively construct tables.
    row, col = 0, 0
    for table_type in page_spec["table_types"]:
        row, col = writeTable(worksheet = worksheet, table_type = table_type, start_row = row, start_col = col,
                              framework = framework, data = data, instructions = instructions, workbook_type = workbook_type,
                              formats = formats, format_variables = format_variables, temp_storage = temp_storage)

@accepts(str)
def writeWorkbook(workbook_path, framework = None, data = None, instructions = None, workbook_type = None):

    # Check workbook type. Gather relevant details.
    available_workbook_types = [SS.WORKBOOK_KEY_FRAMEWORK, SS.WORKBOOK_KEY_DATA]
    if workbook_type == SS.WORKBOOK_KEY_FRAMEWORK:
        page_keys = FS.PAGE_KEYS
    #elif workbook_type == SS.WORKBOOK_KEY_DATA:
    #    if framework is None:
    #        logger.warning("Databook construction cannot proceed without a ProjectFramework being provided. An empty workbook has been produced.")
    #        return
    #    page_keys = framework[FS.KEY_DATAPAGE].keys()
    else:
        raise WorkbookTypeException(workbook_type)

    # Construct workbook and related formats.
    prepareFilePath(workbook_path)
    workbook = xw.Workbook(workbook_path)
    formats = createStandardExcelFormats(workbook)
    format_variables = createDefaultFormatVariables()

    # Create a storage dictionary for values and formulae that may persist between sections.
    temp_storage = dict()
    
    # Iteratively construct worksheets.
    for page_key in page_keys:
        writeWorksheet(workbook = workbook, page_key = page_key, 
                       framework = framework, data = data, instructions = instructions, workbook_type = workbook_type,
                       formats = formats, format_variables = format_variables, temp_storage = temp_storage)

    workbook.close()