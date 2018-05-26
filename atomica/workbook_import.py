import os
import numpy as np

import xlrd
from sciris.core import odict, dcp, isnumber
from xlsxwriter.utility import xl_rowcol_to_cell as xlrc

from atomica.excel import ExcelSettings as ES
from atomica.excel import extract_header_columns_mapping, extract_excel_sheet_value
from atomica.structure import KeyData
from atomica.structure_settings import DetailColumns, ConnectionMatrix, TimeDependentValuesEntry, SwitchType, \
    QuantityFormatType
from atomica.system import SystemSettings as SS
from atomica.system import logger, AtomicaException, accepts, display_name
from atomica.workbook_utils import WorkbookTypeException, WorkbookRequirementException, get_workbook_page_keys, \
    get_workbook_page_specs, get_workbook_page_spec, get_workbook_item_type_specs, get_workbook_item_specs


def get_target_structure(framework=None, data=None, workbook_type=None):
    """ Returns the structure to store definitions and values being read from workbook. """
    if workbook_type == SS.STRUCTURE_KEY_FRAMEWORK:
        if framework is None:
            raise WorkbookRequirementException(workbook_type=SS.STRUCTURE_KEY_FRAMEWORK,
                                               requirement_type="ProjectFramework")
        else:
            structure = framework
    elif workbook_type == SS.STRUCTURE_KEY_DATA:
        if data is None:
            raise WorkbookRequirementException(workbook_type=SS.STRUCTURE_KEY_DATA, requirement_type="ProjectData")
        else:
            structure = data
    else:
        raise WorkbookTypeException(workbook_type)
    return structure


def read_contents_dc(worksheet, table, start_row, header_columns_map, item_type=None, stop_row=None, framework=None,
                     data=None, workbook_type=None, superitem_type_name_pairs=None):
    if item_type is None:
        item_type = table.item_type
    item_type_specs = get_workbook_item_type_specs(framework=framework, workbook_type=workbook_type)
    item_type_spec = item_type_specs[item_type]

    structure = get_target_structure(framework=framework, data=data, workbook_type=workbook_type)
    if superitem_type_name_pairs is None:
        superitem_type_name_pairs = []

    row = start_row
    item_name = ""
    if stop_row is None:
        stop_row = worksheet.nrows
    while row < stop_row:
        name_col = header_columns_map[item_type_spec["attributes"]["name"]["header"]][
            0]  # Only the first column matters for a name.
        test_name = str(worksheet.cell_value(row, name_col))
        if not test_name == "":
            item_name = test_name
        if not item_name == "":
            try:
                structure.get_spec(item_name)
            except Exception:
                structure.create_item(item_name=item_name, item_type=item_type,
                                      superitem_type_name_pairs=superitem_type_name_pairs)
            for attribute in item_type_spec["attributes"]:
                # No need to parse name.
                # Ignore explicitly excluded attributes or implicitly not-included attributes for table construction.
                if attribute == "name" or (table.exclude_not_include == (attribute in table.attribute_list)):
                    continue
                attribute_spec = item_type_spec["attributes"][attribute]
                if "ref_item_type" in attribute_spec:
                    new_superitem_type_name_pairs = dcp(superitem_type_name_pairs)
                    new_superitem_type_name_pairs.append([item_type, item_name])
                    read_contents_dc(worksheet=worksheet, table=table, item_type=attribute_spec["ref_item_type"],
                                     start_row=row, header_columns_map=header_columns_map, stop_row=row + 1,
                                     framework=framework, data=data, workbook_type=workbook_type,
                                     superitem_type_name_pairs=new_superitem_type_name_pairs)
                else:
                    try:
                        start_col, last_col = header_columns_map[attribute_spec["header"]]
                    except KeyError:
                        logger.warning("Workbook import process could not locate attribute '{0}' for '{1}' item '{2}' "
                                       "when parsing a detail-columns table. Ignoring and proceeding to next "
                                       "attribute.".format(attribute, item_type, item_name))
                        continue
                    content_type = attribute_spec["content_type"]
                    filters = []
                    if content_type is not None:
                        if content_type.is_list:
                            filters.append(ES.FILTER_KEY_LIST)
                        if isinstance(content_type, SwitchType):
                            if content_type.default_on:
                                filters.append(ES.FILTER_KEY_BOOLEAN_NO)
                            else:
                                filters.append(ES.FILTER_KEY_BOOLEAN_YES)
                    # For ease of coding, values for this table can span multiple columns but not rows.
                    value = extract_excel_sheet_value(worksheet, start_row=row, start_col=start_col,
                                                      stop_col=last_col + 1, filters=filters)
                    if isinstance(content_type, QuantityFormatType) and value is not None:
                        value = value.lower()  # A catch to ensure formats are stored as lower-case strings.
                    if value is not None or (content_type is not None and content_type.default_value is not None):
                        structure.set_spec_value(term=item_name, attribute=attribute, value=value,
                                                 content_type=content_type)
            row += 1
    next_row = row
    return next_row


def read_detail_columns(worksheet, table, start_row, framework=None, data=None, workbook_type=None):
    row = start_row
    header_columns_map = extract_header_columns_mapping(worksheet, row=row)
    row += 1
    row = read_contents_dc(worksheet=worksheet, table=table, start_row=row, header_columns_map=header_columns_map,
                           framework=framework, data=data, workbook_type=workbook_type)
    next_row = row
    return next_row


def read_connection_matrix(worksheet, table, start_row, framework=None, data=None, workbook_type=None):
    item_type_specs = get_workbook_item_type_specs(framework=framework, workbook_type=workbook_type)
    structure = get_target_structure(framework=framework, data=data, workbook_type=workbook_type)

    header_row, header_col, last_col = None, 0, None
    row, col = start_row, header_col + 1
    keep_scanning_rows = True
    while keep_scanning_rows and row < worksheet.nrows:
        # Scan for header row of the matrix, recognising top-left cell may be empty, hence the non-zero start column.
        if header_row is None:
            check_label = str(worksheet.cell_value(row, col))
            if not check_label == "":
                header_row = row
                # Upon finding the header row, locate its last column.
                col += 1
                while last_col is None and col < worksheet.ncols:
                    check_label = str(worksheet.cell_value(row, col))
                    if check_label == "":
                        last_col = col - 1
                    col += 1
                if last_col is None:
                    last_col = worksheet.ncols - 1
        else:
            for col in range(header_col + 1, last_col + 1):
                val = str(worksheet.cell_value(row, col))
                if not val == "":
                    source_item = str(worksheet.cell_value(row, header_col))
                    target_item = str(worksheet.cell_value(header_row, col))
                    if table.storage_item_type is None:
                        structure.set_spec_value(term=source_item, attribute=table.storage_attribute, value=val,
                                                 subkey=target_item)
                    else:
                        # Allow connection matrices to use name tags before they are used for detailed items.
                        # Only allow this for non-subitems.
                        if not item_type_specs[table.storage_item_type]["superitem_type"] is None:
                            raise AtomicaException("Cannot import data from connection matrix where values are "
                                                   "names of subitems, type '{0}'.".format(table.storage_item_type))
                        try:
                            structure.get_spec(val)
                        except Exception:
                            structure.create_item(item_name=val, item_type=table.storage_item_type)
                        structure.append_spec_value(term=val, attribute=table.storage_attribute,
                                                    value=(source_item, target_item))
        row += 1
    next_row = row
    return next_row


def read_time_dependent_values_entry(worksheet, item_type, item_key, value_attribute, start_row,
                                     framework=None, data=None, workbook_type=None):
    item_specs = get_workbook_item_specs(framework=framework, workbook_type=workbook_type)
    structure = get_target_structure(framework=framework, data=data, workbook_type=workbook_type)

    row, id_col = start_row, 0
    keep_scanning = True
    header_row = None
    while keep_scanning and row < worksheet.nrows:
        label = str(worksheet.cell_value(row, id_col))
        if not label == "":
            # The first label encounter is of the item that heads this table.
            # Verify it matches the item name associated with the table.
            if header_row is None:
                if not label == item_specs[item_type][item_key]["label"]:
                    raise AtomicaException(
                        "A time-dependent value entry table was expected in sheet '{0}' for item code-named '{1}'. "
                        "Workbook parser encountered a table headed by label '{2}' instead.".format(worksheet.name,
                                                                                                    item_key, label))
                else:
                    # Do a quick scan of all row headers to determine keys for a TimeSeries object.
                    quick_scan = True
                    quick_row = row + 1
                    keys = []
                    while quick_scan and quick_row < worksheet.nrows:
                        quick_label = str(worksheet.cell_value(quick_row, id_col))
                        if quick_label == "":
                            quick_scan = False
                        else:
                            keys.append(structure.get_spec_name(quick_label))
                        quick_row += 1
                    structure.create_item(item_name=item_key, item_type=item_type)
                    structure.set_spec_value(term=item_key, attribute="label", value=label)
                    time_series = KeyData(keys=keys)
                    structure.set_spec_value(term=item_key, attribute=value_attribute, value=time_series)
                header_row = row
            # All other label encounters are of an iterated type.
            else:
                col = id_col + 1
                while col < worksheet.ncols:
                    val = str(worksheet.cell_value(row, col))
                    if val not in [SS.DEFAULT_SYMBOL_INAPPLICABLE, SS.DEFAULT_SYMBOL_OR, ""]:
                        header = str(worksheet.cell_value(header_row, col))
                        if header == ES.QUANTITY_TYPE_HEADER:
                            structure.get_spec(term=item_key)[value_attribute].set_format(
                                key=structure.get_spec_name(label), value_format=val.lower())
                            col += 1
                            continue
                        try:
                            val = float(val)
                        except ValueError:
                            raise AtomicaException("Workbook parser encountered invalid value '{0}' in cell '{1}' "
                                                   "of sheet '{2}'.".format(val, xlrc(row, col), worksheet.name))
                        if header == ES.ASSUMPTION_HEADER:
                            structure.get_spec(term=item_key)[value_attribute].set_value(
                                key=structure.get_spec_name(label), value=val)
                        else:
                            try:
                                time = float(header)
                            except ValueError:
                                raise AtomicaException("Workbook parser encountered invalid time header '{0}' in cell "
                                                       "'{1}' of sheet '{2}'.".format(header, xlrc(header_row, col),
                                                                                      worksheet.name))
                            structure.get_spec(term=item_key)[value_attribute].set_value(
                                key=structure.get_spec_name(label), value=val, t=time)
                    col += 1

        else:
            if header_row is not None:
                keep_scanning = False
        row += 1
    next_row = row
    return next_row


def read_table(worksheet, table, start_row, start_col, framework=None, data=None, workbook_type=None):
    # Check workbook type.
    if workbook_type not in [SS.STRUCTURE_KEY_FRAMEWORK, SS.STRUCTURE_KEY_DATA]:
        raise WorkbookTypeException(workbook_type)

    row, col = start_row, start_col
    if isinstance(table, DetailColumns):
        row = read_detail_columns(worksheet=worksheet, table=table, start_row=row,
                                  framework=framework, data=data, workbook_type=workbook_type)
    if isinstance(table, ConnectionMatrix):
        row = read_connection_matrix(worksheet=worksheet, table=table, start_row=row,
                                     framework=framework, data=data, workbook_type=workbook_type)
    if isinstance(table, TimeDependentValuesEntry):
        row = read_time_dependent_values_entry(worksheet=worksheet, item_type=table.item_type, item_key=table.item_key,
                                               value_attribute=table.value_attribute,
                                               start_row=start_row,
                                               framework=framework, data=data, workbook_type=workbook_type)

    next_row, next_col = row, col
    return next_row, next_col


def read_worksheet(workbook, page_key, framework=None, data=None, workbook_type=None):
    page_spec = get_workbook_page_spec(page_key=page_key, framework=framework, workbook_type=workbook_type)
    if len(page_spec["tables"]) == 0:
        return
    page_title = page_spec["label"]
    try:
        worksheet = workbook.sheet_by_name(page_title)
        logger.info("Importing page: {0}".format(page_title))
    except xlrd.biffh.XLRDError:
        if "can_skip" in page_spec and page_spec["can_skip"] is True:
            logger.warning("Workbook does not contain an optional page titled '{0}'.".format(page_title))
            return
        logger.error("Workbook does not contain a required page titled '{0}'.".format(page_title))
        raise

    # Iteratively parse tables.
    row, col = 0, 0
    for table in page_spec["tables"]:
        row, col = read_table(worksheet=worksheet, table=table, start_row=row, start_col=col,
                              framework=framework, data=data, workbook_type=workbook_type)


def read_reference_worksheet(workbook):
    """
    Reads a hidden worksheet for metadata and other values that are useful to store.
    These values are not directly part of framework/data.
    """

    page_title = "metadata".title()
    try:
        worksheet = workbook.sheet_by_name(page_title)
        logger.info("Importing page: {0}".format(page_title))
    except xlrd.biffh.XLRDError:
        logger.warn("No metadata page exists in this workbook.")
        return None

    metadata = dict()
    row = 0
    while row < worksheet.nrows:
        value = str(worksheet.cell_value(row, 1))
        try:
            value = float(value)
        except ValueError:
            pass
        metadata[str(worksheet.cell_value(row, 0))] = value
        row += 1
    return metadata


@accepts(str)
def read_workbook(workbook_path, framework=None, data=None, workbook_type=None):
    page_keys = get_workbook_page_keys(framework=framework, workbook_type=workbook_type)
    page_specs = get_workbook_page_specs(framework=framework, workbook_type=workbook_type)
    page_keys = sorted(page_keys,
                       key=lambda x: page_specs[x]["read_order"] if not page_specs[x]["read_order"] is None else 0)

    logger.info("Importing a {0}: {1}".format(display_name(workbook_type), workbook_path))

    workbook_path = os.path.abspath(workbook_path)
    try:
        workbook = xlrd.open_workbook(workbook_path)
    except:
        raise AtomicaException("Workbook was not found.")

    # Check workbook type and initialise output
    if workbook_type not in [SS.STRUCTURE_KEY_FRAMEWORK, SS.STRUCTURE_KEY_DATA]:
        raise WorkbookTypeException(workbook_type)

    # Iteratively parse worksheets.
    for page_key in page_keys:
        read_worksheet(workbook=workbook, page_key=page_key,
                       framework=framework, data=data, workbook_type=workbook_type)

    structure = get_target_structure(framework=framework, data=data, workbook_type=workbook_type)
    structure.complete_specs(framework=framework)
    structure.frameworkfilename = workbook_path

    metadata = read_reference_worksheet(workbook=workbook)

    return metadata



#%% COMPLETELY SEPARATE CODE TO READ IN A WORKBOOK WITH PROGRAMS DATA - NEEDS TO BE MERGED WITH THE ABOVE

def getyears(sheetdata):
    ''' Get years from a worksheet'''
    years = [] # Initialize epidemiology data years
    for col in range(sheetdata.ncols):
        thiscell = sheetdata.cell_value(1,col) # 1 is the 2nd row which is where the year data should be
        if thiscell=='' and len(years)>0: #  We've gotten to the end
            lastdatacol = col # Store this column number
            break # Quit
        elif thiscell != '': # Nope, more years, keep going
            years.append(float(thiscell)) # Add this year
    
    return lastdatacol, years
   
   
def blank2nan(thesedata):
    ''' Convert a blank entry to a nan '''
    return list(map(lambda val: np.nan if val=='' else val, thesedata))
    

def validatedata(thesedata, sheetname, thispar, row, checkupper=False, checklower=True, checkblank=True, startcol=0):
    ''' Do basic validation on the data: at least one point entered, between 0 and 1 or just above 0 if checkupper=False '''
    
    # Check that only numeric data have been entered
    for column,datum in enumerate(thesedata):
        if not isnumber(datum):
            errormsg = 'Invalid entry in sheet "%s", parameter "%s":\n' % (sheetname, thispar) 
            errormsg += 'row=%i, column=%s, value="%s"\n' % (row+1, xlrd.colname(column+startcol), datum)
            errormsg += 'Be sure all entries are numeric'
            if ' ' or '\t' in datum: errormsg +=' (there seems to be a space or tab)'
            raise AtomicaException(errormsg)
    
    # Now check integrity of data itself
    validdata = np.array(thesedata)[~np.isnan(thesedata)]
    if len(validdata):
        valid = np.array([True]*len(validdata)) # By default, set everything to valid
        if checklower: valid *= np.array(validdata)>=0
        if checkupper: valid *= np.array(validdata)<=1
        if not valid.all():
            invalid = validdata[valid==False]
            errormsg = 'Invalid entry in sheet "%s", parameter "%s":\n' % (sheetname, thispar) 
            errormsg += 'row=%i, invalid="%s", values="%s"\n' % (row+1, invalid, validdata)
            errormsg += 'Be sure that all values are >=0 (and <=1 if a probability)'
            raise AtomicaException(errormsg)
    elif checkblank: # No data entered
        errormsg = 'No data or assumption entered for sheet "%s", parameter "%s", row=%i' % (sheetname, thispar, row) 
        raise AtomicaException(errormsg)
    else:
        return None


def load_progbook(filename, verbose=2):
    '''
    Loads programs book (i.e. reads its contents into the data).
    '''
    ## Basic setup
    data = odict() # Create structure for holding data
    data['meta'] = odict()
    data['meta']['sheets'] = ['Populations & programs','Program data'] # TODO - remove hardcoding

    ## Read in databook 
    try: workbook = xlrd.open_workbook(filename) # Open workbook
    except: 
        errormsg = 'Failed to load program spreadsheet: file "%s" not found or other problem' % filename
        raise AtomicaException(errormsg)
    
    ## Calculate columns for which data are entered, and store the year ranges
    sheetdata = workbook.sheet_by_name('Program spend data') # Load this workbook
    lastdatacol, data['years'] = getyears(sheetdata)
    assumptioncol = lastdatacol + 1 # Figure out which column the assumptions are in; the "OR" space is in between
    
    ## Load program information
    sheetdata = workbook.sheet_by_name('Populations & programs') # Load 
    data['progs'] = odict()
    data['progs']['short'] = []
    data['progs']['name'] = []
    data['progs']['target_pops'] = []
    data['progs']['target_comps'] = []
    
    colindices = []
    for row in range(sheetdata.nrows): 
        if sheetdata.cell_value(row,0)!='':
            for col in range(2,sheetdata.ncols):
                cell_val = sheetdata.cell(row, col).value
                if cell_val!='': colindices.append(col-1)
        else:
            thesedata = sheetdata.row_values(row, start_colx=2) 
        
            if row==1:
                data['pops'] = thesedata[3:colindices[0]]
                data['comps'] = thesedata[colindices[1]:]
            else:
                if thesedata[0]:
                    progname = str(thesedata[0])
                    data['progs']['short'].append(progname)
                    data['progs']['name'].append(str(thesedata[1]))
                    data['progs']['target_pops'].append(thesedata[3:colindices[0]])
                    data['progs']['target_comps'].append(thesedata[colindices[1]:])
                    data[progname] = odict()
                    data[progname]['name'] = str(thesedata[1])
                    data[progname]['target_pops'] = thesedata[3:colindices[0]]
                    data[progname]['target_comps'] = thesedata[colindices[1]:]
                    data[progname]['cost'] = []
                    data[progname]['num_covered'] = []
                    data[progname]['unitcost'] = odict()
                    data[progname]['capacity'] = odict()
                    
    
    namemap = {'Total spend': 'cost',
               'Unit cost':'unitcost',
               'Number covered': 'num_covered',
               'Capacity constraints': 'capacity'} 
    sheetdata = workbook.sheet_by_name('Program spend data') # Load 
    
    
    for row in range(sheetdata.nrows): 
        sheetname = sheetdata.cell_value(row,0) # Sheet name
        progname = sheetdata.cell_value(row, 1) # Get the name of the program

        if progname != '': # The first column is blank: it's time for the data
            thesedata = blank2nan(sheetdata.row_values(row, start_colx=3, end_colx=lastdatacol)) # Data starts in 3rd column, and ends lastdatacol-1
            assumptiondata = sheetdata.cell_value(row, assumptioncol)
            if assumptiondata != '': # There's an assumption entered
                thesedata = [assumptiondata] # Replace the (presumably blank) data if a non-blank assumption has been entered
            if sheetdata.cell_value(row, 2) in namemap.keys(): # It's a regular variable without ranges
                thisvar = namemap[sheetdata.cell_value(row, 2)]  # Get the name of the indicator
                data[progname][thisvar] = thesedata # Store data
            else:
                thisvar = namemap[sheetdata.cell_value(row, 2).split(' - ')[0]]  # Get the name of the indicator
                thisestimate = sheetdata.cell_value(row, 2).split(' - ')[1]
                data[progname][thisvar][thisestimate] = thesedata # Store data
            checkblank = False if thisvar in ['num_covered', 'capacity'] else True # Don't check optional indicators, check everything else
            validatedata(thesedata, sheetname, thisvar, row, checkblank=checkblank)
            
    return data




