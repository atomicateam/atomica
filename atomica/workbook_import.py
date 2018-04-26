from atomica.system import SystemSettings as SS
from atomica.excel import ExcelSettings as ES

from atomica.system import logger, AtomicaException, accepts, displayName
from atomica.excel import extractHeaderColumnsMapping, extractExcelSheetValue
from atomica.structure_settings import DetailColumns, ConnectionMatrix, TimeDependentValuesEntry, SwitchType
from atomica.structure import KeyData
from atomica.workbook_utils import WorkbookTypeException, WorkbookRequirementException, getWorkbookPageKeys, getWorkbookPageSpec, getWorkbookItemTypeSpecs, getWorkbookItemSpecs

from sciris.core import odict, dcp

import os
import xlsxwriter as xw
import xlrd

def getTargetStructure(framework = None, data = None, workbook_type = None):
    """ Returns the structure to store definitions and values being read from workbook. """
    structure = None
    if workbook_type == SS.STRUCTURE_KEY_FRAMEWORK:
        if framework is None:
            raise WorkbookRequirementException(workbook_type = SS.STRUCTURE_KEY_FRAMEWORK, requirement_type = "ProjectFramework")
        else: structure = framework
    elif workbook_type == SS.STRUCTURE_KEY_DATA:
        if data is None:
            raise WorkbookRequirementException(workbook_type = SS.STRUCTURE_KEY_DATA, requirement_type = "ProjectData")
        else: structure = data
    else: raise WorkbookTypeException(workbook_type)
    return structure



def readContentsDC(worksheet, table, start_row, header_columns_map, item_type = None, stop_row = None, framework = None, data = None, workbook_type = None, superitem_type_name_pairs = None):
    
    if item_type is None: item_type = table.item_type
    item_type_specs = getWorkbookItemTypeSpecs(framework = framework, workbook_type = workbook_type)
    item_type_spec = item_type_specs[item_type]

    structure = getTargetStructure(framework = framework, data = data, workbook_type = workbook_type)
    if superitem_type_name_pairs is None: superitem_type_name_pairs = []

    row = start_row
    item_name = ""
    if stop_row is None: stop_row = worksheet.nrows
    while row < stop_row:
        name_col = header_columns_map[item_type_spec["attributes"]["name"]["header"]][0]    # Only the first column matters for a name.
        test_name = str(worksheet.cell_value(row, name_col))
        if not test_name == "": item_name = test_name
        if not item_name == "":
            try: structure.getSpec(item_name)
            except: structure.createItem(item_name = item_name, item_type = item_type, superitem_type_name_pairs = superitem_type_name_pairs)
            for attribute in item_type_spec["attributes"]:
                # No need to parse name.
                # Ignore explicitly excluded attributes or implicitly not-included attributes for table construction.
                if attribute == "name" or (table.exclude_not_include == (attribute in table.attribute_list)): continue
                attribute_spec = item_type_spec["attributes"][attribute]
                if "ref_item_type" in attribute_spec:
                    new_superitem_type_name_pairs = dcp(superitem_type_name_pairs)
                    new_superitem_type_name_pairs.append([item_type, item_name])
                    readContentsDC(worksheet = worksheet, table = table, item_type = attribute_spec["ref_item_type"],
                                   start_row = row, header_columns_map = header_columns_map, stop_row = row + 1,
                                   framework = framework, data = data, workbook_type = workbook_type,
                                   superitem_type_name_pairs = new_superitem_type_name_pairs)
                else:
                    try: start_col, last_col = header_columns_map[attribute_spec["header"]]
                    except:
                        logger.warning("Workbook import process could not locate attribute '{0}' for '{1}' item '{2}' "
                                       "when parsing a detail-columns table. Ignoring and proceeding to next attribute.".format(attribute, item_type, item_name))
                        continue
                    content_type = attribute_spec["content_type"]
                    filters = []
                    if not content_type is None:
                        if content_type.is_list: filters.append(ES.FILTER_KEY_LIST)
                        if isinstance(content_type, SwitchType): 
                            if content_type.default_on: filters.append(ES.FILTER_KEY_BOOLEAN_NO)
                            else: filters.append(ES.FILTER_KEY_BOOLEAN_YES)
                    # For ease of coding, values for this table can span multiple columns but not rows.
                    value = extractExcelSheetValue(worksheet, start_row = row, start_col = start_col, stop_col = last_col + 1, filters = filters)
                    if not value is None or (not content_type is None and not content_type.default_value is None): 
                        structure.setSpecValue(term = item_name, attribute = attribute, value = value, content_type = content_type)
            row += 1
    next_row = row
    return next_row

def readDetailColumns(worksheet, table, start_row, framework = None, data = None, workbook_type = None):

    row = start_row
    header_columns_map = extractHeaderColumnsMapping(worksheet, row = row)
    row += 1
    row = readContentsDC(worksheet = worksheet, table = table, start_row = row, header_columns_map = header_columns_map,
                       framework = framework, data = data, workbook_type = workbook_type)
    next_row = row
    return next_row

def readConnectionMatrix(worksheet, table, start_row, framework = None, data = None, workbook_type = None):
    
    item_type_specs = getWorkbookItemTypeSpecs(framework = framework, workbook_type = workbook_type)
    structure = getTargetStructure(framework = framework, data = data, workbook_type = workbook_type)

    header_row, header_col, last_col = None, 0, None
    row, col = start_row, header_col + 1
    keep_scanning_rows = True
    while keep_scanning_rows and row < worksheet.nrows:
        # Scan for the header row of the matrix, recognising the top-left cell may be empty, hence the non-zero start column.
        if header_row is None:
            check_label = str(worksheet.cell_value(row, col))
            if not check_label == "":
                header_row = row
                # Upon finding the header row, locate its last column.
                col += 1
                while last_col is None and col < worksheet.ncols:
                    check_label = str(worksheet.cell_value(row, col))
                    if check_label == "": last_col = col - 1
                    col += 1
                if last_col is None: last_col = worksheet.ncols - 1
        else:
            for col in range(header_col + 1, last_col + 1):
                val = str(worksheet.cell_value(row, col))
                if not val == "":
                    source_item = str(worksheet.cell_value(row, header_col))
                    target_item = str(worksheet.cell_value(header_row, col))
                    if table.storage_item_type is None:
                        structure.setSpecValue(term = source_item, attribute = table.storage_attribute, value = val, subkey = target_item)
                    else:
                        # Allow connection matrices to use name tags before they are used for detailed items.
                        # Only allow this for non-subitems.
                        if not item_type_specs[table.storage_item_type]["superitem_type"] is None:
                            raise AtomicaException("Cannot import data from connection matrix where values are names of subitems, type '{0}'.".format(table.storage_item_type))
                        try: structure.getSpec(val)
                        except: structure.createItem(item_name = val, item_type = table.storage_item_type)
                        structure.appendSpecValue(term = val, attribute = table.storage_attribute, value = (source_item,target_item))
        row += 1
    next_row = row
    return next_row

def readTimeDependentValuesEntry(worksheet, item_type, item_key, iterated_type, value_attribute, start_row, framework = None, data = None, workbook_type = None):
    
    item_specs = getWorkbookItemSpecs(framework = framework, workbook_type = workbook_type)
    structure = getTargetStructure(framework = framework, data = data, workbook_type = workbook_type)

    row, id_col = start_row, 0
    keep_scanning = True
    header_row = None
    time_series = None
    while keep_scanning and row < worksheet.nrows:
        label = str(worksheet.cell_value(row, id_col))
        if not label == "":
            # The first label encounter is of the item that heads this table; verify it matches the item name associated with the table.
            if header_row is None:
                if not label == item_specs[item_type][item_key]["label"]:
                    raise AtomicaException("A time-dependent value entry table was expected in sheet '{0}' for item code-named '{1}'. "
                                          "Workbook parser encountered a table headed by label '{2}' instead.".format(worksheet.name, item_key, label))
                else:
                    # Do a quick scan of all row headers to determine keys for a TimeSeries object.
                    quick_scan = True
                    quick_row = row + 1
                    keys = []
                    while quick_scan and quick_row < worksheet.nrows:
                        quick_label = str(worksheet.cell_value(quick_row, id_col))
                        if quick_label == "": quick_scan = False
                        else: keys.append(structure.getSpecName(quick_label))
                        quick_row += 1
                    structure.createItem(item_name = item_key, item_type = item_type)
                    structure.setSpecValue(term = item_key, attribute = "label", value = label)
                    time_series = KeyData(keys = keys)
                    structure.setSpecValue(term = item_key, attribute = value_attribute, value = time_series)
                header_row = row
            # All other label encounters are of an iterated type.
            else:
                col = id_col + 1
                while col < worksheet.ncols:
                    val = str(worksheet.cell_value(row, col))
                    if not val in [SS.DEFAULT_SYMBOL_INAPPLICABLE, SS.DEFAULT_SYMBOL_OR, ""]:
                        header = str(worksheet.cell_value(header_row, col))
                        if header == ES.QUANTITY_TYPE_HEADER:
                            structure.getSpec(term = item_key)[value_attribute].setFormat(key = structure.getSpecName(label), value_format = val.lower())
                            col += 1
                            continue
                        try: val = float(val)
                        except: raise AtomicaException("Workbook parser encountered invalid value '{0}' in cell '{1}' of sheet '{2}'.".format(val, xw.utility.xl_rowcol_to_cell(row, col), worksheet.name))
                        if header == ES.ASSUMPTION_HEADER:
                            structure.getSpec(term = item_key)[value_attribute].setValue(key = structure.getSpecName(label), value = val)
                        else:
                            try: time = float(header)
                            except: raise AtomicaException("Workbook parser encountered invalid time header '{0}' in cell '{1}' of sheet '{2}'.".format(header, xw.utility.xl_rowcol_to_cell(header_row, col), worksheet.name))
                            structure.getSpec(term = item_key)[value_attribute].setValue(key = structure.getSpecName(label), value = val, t = time)
                    col += 1

        else:
            if not header_row is None: keep_scanning = False
        row += 1
    next_row = row
    return next_row

def readTable(worksheet, table, start_row, start_col, framework = None, data = None, workbook_type = None):

    # Check workbook type.
    if workbook_type not in [SS.STRUCTURE_KEY_FRAMEWORK, SS.STRUCTURE_KEY_DATA]: raise WorkbookTypeException(workbook_type)

    row, col = start_row, start_col
    if isinstance(table, DetailColumns):
        row = readDetailColumns(worksheet = worksheet, table = table, start_row = row,
                                framework = framework, data = data, workbook_type = workbook_type)
    if isinstance(table, ConnectionMatrix):
        row = readConnectionMatrix(worksheet = worksheet, table = table, start_row = row,
                                framework = framework, data = data, workbook_type = workbook_type)
    if isinstance(table, TimeDependentValuesEntry):
        row = readTimeDependentValuesEntry(worksheet = worksheet, item_type = table.item_type, item_key = table.item_key,
                                           iterated_type = table.iterated_type, value_attribute = table.value_attribute, start_row = start_row, 
                                           framework = framework, data = data, workbook_type = workbook_type)
    
    next_row, next_col = row, col
    return next_row, next_col

def readWorksheet(workbook, page_key, framework = None, data = None, workbook_type = None):

    page_spec = getWorkbookPageSpec(page_key = page_key, framework = framework, workbook_type = workbook_type)
    if len(page_spec["tables"]) == 0: return
    try: 
        page_title = page_spec["label"]
        worksheet = workbook.sheet_by_name(page_title)
        logger.info("Importing page: {0}".format(page_title))
    except:
        if "can_skip" in page_spec and page_spec["can_skip"] is True:
            logger.warn("Workbook does not contain an optional page titled '{0}'.".format(page_title))
            return
        logger.error("Workbook does not contain a required page titled '{0}'.".format(page_title))
        raise

    # Iteratively parse tables.
    row, col = 0, 0
    for table in page_spec["tables"]:
        row, col = readTable(worksheet = worksheet, table = table, start_row = row, start_col = col,
                             framework = framework, data = data, workbook_type = workbook_type)

def readReferenceWorksheet(workbook, workbook_type = None):
    """ Reads a hidden worksheet for metadata and other values that are useful to store but are not directly part of framework/data. """
        
    page_title = "metadata".title()
    try:
        worksheet = workbook.sheet_by_name(page_title)
        logger.info("Importing page: {0}".format(page_title))
    except:
        logger.warn("No metadata page exists in this workbook.")
        return None
    
    metadata = dict()
    row = 0
    while row < worksheet.nrows:
        value = str(worksheet.cell_value(row, 1))
        try: value = float(value)
        except: pass
        metadata[str(worksheet.cell_value(row, 0))] = value
        row += 1
    return metadata


@accepts(str)
def readWorkbook(workbook_path, framework=None, data=None, workbook_type=None):

    page_keys = getWorkbookPageKeys(framework = framework, workbook_type = workbook_type)

    logger.info("Importing a {0}: {1}".format(displayName(workbook_type), workbook_path))

    workbook_path = os.path.abspath(workbook_path)
    try: workbook = xlrd.open_workbook(workbook_path)
    except:
        logger.error("Workbook was not found.")
        raise

    # Check workbook type and initialise output
    if not workbook_type in [SS.STRUCTURE_KEY_FRAMEWORK, SS.STRUCTURE_KEY_DATA]:
        raise WorkbookTypeException(workbook_type)

    # Iteratively parse worksheets.
    for page_key in page_keys:
        readWorksheet(workbook = workbook, page_key = page_key, 
                      framework = framework, data = data, workbook_type = workbook_type)
            
    structure = getTargetStructure(framework = framework, data = data, workbook_type = workbook_type)
    structure.completeSpecs(framework = framework)
    structure.frameworkfilename = workbook_path
    
    metadata = readReferenceWorksheet(workbook = workbook, workbook_type = workbook_type)
    
    return metadata
