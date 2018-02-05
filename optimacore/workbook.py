from optimacore.system import SystemSettings as SS
from optimacore.framework_settings import WorkbookSettings as FS
from optimacore.databook_settings import DatabookSettings as DS

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

def writeDetailColumns(worksheet, core_item_type, start_row, start_col, framework = None, data = None, instructions = None, workbook_type = None):

    def writeHeaders(item_type, start_row, start_col, framework = None, data = None, instructions = None, workbook_type = None):
        if workbook_type == SS.WORKBOOK_KEY_FRAMEWORK: item_type_spec = FS.ITEM_TYPE_SPECS[item_type]
        #table_types = FS.PAGE_TABLE_TYPES[page_key]
    #elif workbook_type == SS.WORKBOOK_KEY_DATA:
        else: raise WorkbookTypeException(workbook_type)
        row, col, header_column_map = start_row, start_col, dict()
        for attribute in item_type_spec["attributes"]:
            if "ref_item_type" in item_type_spec["attributes"][attribute]:
                _, col, sub_map = writeHeaders(item_type = item_type_spec["attributes"][attribute]["ref_item_type"],
                                               start_row = row, start_col = col,
                                               framework = framework, data = data, instructions = instructions, workbook_type = workbook_type)
                len_map = len(header_column_map)
                len_sub_map = len(sub_map)
                header_column_map.update(sub_map)
                if not len(header_column_map) == len_map + len_sub_map: raise KeyUniquenessException(None, "header-column map")
            else:
                header = item_type_spec["attributes"][attribute]["header"]
                if header in header_column_map: raise KeyUniquenessException(header, "header-column map")
                header_column_map[header] = col
                worksheet.write(row, col, header)
                col += 1
        row += 1
        next_row, next_col = row, col
        return next_row, next_col, header_column_map

    def writeContents(item_type, start_row, header_column_map, framework = None, data = None, instructions = None, workbook_type = None):
        if workbook_type == SS.WORKBOOK_KEY_FRAMEWORK: 
            item_type_spec = FS.ITEM_TYPE_SPECS[item_type]
            if framework is None:
                if instructions is None: instructions = WorkbookInstructions(workbook_type = workbook_type)
            else:
                print('WHOOPS')
        #table_types = FS.PAGE_TABLE_TYPES[page_key]
    #elif workbook_type == SS.WORKBOOK_KEY_DATA:
        else: raise WorkbookTypeException(workbook_type)
        row, col, new_row = start_row, start_col, start_row
        for num_item in sm.range(instructions.num_items[item_type]):
            for attribute in item_type_spec["attributes"]:
                if "ref_item_type" in item_type_spec["attributes"][attribute]:
                    sub_row, _ = writeContents(item_type = item_type_spec["attributes"][attribute]["ref_item_type"],
                                               start_row = row, header_column_map = header_column_map,
                                               framework = framework, data = data, instructions = instructions, workbook_type = workbook_type)
                    new_row = max(new_row, sub_row)
                else:
                    content = num_item
                    col = header_column_map[item_type_spec["attributes"][attribute]["header"]]
                    worksheet.write(row, col, content)
            row = max(new_row, row + 1)
        next_row, next_col = row, col
        return next_row, next_col

    row, col = start_row, start_col
    row, _, header_column_map = writeHeaders(item_type = core_item_type, start_row = row, start_col = col,
                          framework = framework, data = data, instructions = instructions, workbook_type = workbook_type)
    row, _ = writeContents(item_type = core_item_type, start_row = row, header_column_map = header_column_map,
                           framework = framework, data = data, instructions = instructions, workbook_type = workbook_type)
    next_row, next_col = row, col
    return next_row, next_col


def writeTable(worksheet, table_type, start_row, start_col, framework = None, data = None, instructions = None, workbook_type = None):
    
    # Check workbook type. Gather relevant details.
    if workbook_type not in [SS.WORKBOOK_KEY_FRAMEWORK, SS.WORKBOOK_KEY_DATA]:
        raise WorkbookTypeException(workbook_type)

    if isinstance(table_type, FS.DetailColumns):
        core_item_type = table_type.item_type
        row, col = writeDetailColumns(worksheet = worksheet, core_item_type = core_item_type, start_row = start_row, start_col = start_col,
                                      framework = framework, data = data, instructions = instructions, workbook_type = workbook_type)
    
    next_row, next_col = row, col
    return next_row, next_col





def writeWorksheet(workbook, page_key, framework = None, data = None, instructions = None, workbook_type = None, formats = None, format_variables = None):

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

    # Iteratively construct tables.
    row, col = 0, 0
    for table_type in page_spec["table_types"]:
        row, col = writeTable(worksheet = worksheet, table_type = table_type, start_row = row, start_col = col,
                              framework = framework, data = data, instructions = instructions, workbook_type = workbook_type)

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
    
    # Iteratively construct worksheets.
    for page_key in page_keys:
        writeWorksheet(workbook = workbook, page_key = page_key, 
                       framework = framework, data = data, instructions = instructions, workbook_type = workbook_type,
                       formats = formats, format_variables = format_variables)

    workbook.close()