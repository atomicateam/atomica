# -*- coding: utf-8 -*-
"""
Atomica Excel utilities file.
Contains functionality specific to Excel input and output.
"""

from .system import SystemSettings as SS
from .system import log_usage, accepts, returns, AtomicaException

import xlsxwriter as xw
from xlsxwriter.utility import xl_rowcol_to_cell as xlrc
import xlrd
from sciris.weblib.scirisobjects import ScirisObject
import sciris.core as sc
import io
import openpyxl
from copy import copy # shallow copy
import time
import logging
logger = logging.getLogger(__name__)

def standard_formats(workbook):
    # Add standard formatting to a workbook and return the set of format objects
    # for use when writing within the workbook

    """ the formats used in the spreadsheet """
    darkgray = '#413839'
    originalblue = '#18C1FF'
    optionalorange = '#FFA500'
    BG_COLOR = originalblue
    OPT_COLOR = optionalorange
    BORDER_COLOR = 'white'

    PERCENTAGE = 'percentage'
    RATE = 'rate'
    DECIMAL = 'decimal'
    SCIENTIFIC = 'scientific'
    NUMBER = 'number'
    GENERAL = 'general'
    OPTIONAL = 'optional'

    formats = {}
    # locked formats
    formats['bold'] = workbook.add_format({'bold': 1})
    formats['center'] = workbook.add_format({'align': 'center'})
    formats['center_bold'] = workbook.add_format({'bold': 1, 'align': 'center'})
    formats['rc_title'] = {}
    formats['rc_title']['right'] = {}
    formats['rc_title']['right']['T'] = workbook.add_format({'bold': 1, 'align': 'right', 'text_wrap': True})
    formats['rc_title']['right']['F'] = workbook.add_format({'bold': 1, 'align': 'right', 'text_wrap': False})
    formats['rc_title']['left'] = {}
    formats['rc_title']['left']['T'] = workbook.add_format({'bold': 1, 'align': 'left', 'text_wrap': True})
    formats['rc_title']['left']['F'] = workbook.add_format({'bold': 1, 'align': 'left', 'text_wrap': False})
    # unlocked formats
    formats['unlocked'] = workbook.add_format({'locked': 0, 'bg_color': BG_COLOR, 'border': 1,'border_color': BORDER_COLOR})
    formats['center_unlocked'] = workbook.add_format({'align': 'center','locked': 0, 'bg_color': BG_COLOR, 'border': 1,'border_color': BORDER_COLOR})
    formats['percentage'] = workbook.add_format({'locked': 0, 'num_format': 0x09, 'bg_color': BG_COLOR, 'border': 1,'border_color': BORDER_COLOR})
    formats['rate'] = workbook.add_format({'locked': 0, 'num_format': 0x09, 'bg_color': BG_COLOR, 'border': 1,'border_color': BORDER_COLOR})
    formats['decimal'] = workbook.add_format({'locked': 0, 'num_format': 0x0a, 'bg_color': BG_COLOR, 'border': 1,'border_color': BORDER_COLOR})
    formats['scientific'] = workbook.add_format({'locked': 0, 'num_format': 0x0b, 'bg_color': BG_COLOR, 'border': 1,'border_color': BORDER_COLOR})
    formats['number'] = workbook.add_format({'locked': 0, 'num_format': 0x04, 'bg_color': BG_COLOR, 'border': 1,'border_color': BORDER_COLOR})
    formats['general'] = workbook.add_format({'locked': 0, 'num_format': 0x00, 'bg_color': BG_COLOR, 'border': 1,'border_color': BORDER_COLOR})
    formats['optional'] = workbook.add_format({'locked': 0, 'num_format': 0x00, 'bg_color': OPT_COLOR, 'border': 1,'border_color': BORDER_COLOR})
    formats['info_header'] = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'color': '#D5AA1D', 'fg_color': '#0E0655', 'font_size': 20})
    formats['grey'] = workbook.add_format({'fg_color': '#EEEEEE', 'text_wrap': True})
    formats['orange'] = workbook.add_format({'fg_color': '#FFC65E', 'text_wrap': True})
    formats['info_url'] = workbook.add_format({'fg_color': '#EEEEEE', 'text_wrap': True, 'color': 'blue', 'align': 'center'})
    formats['grey_bold'] = workbook.add_format({'fg_color': '#EEEEEE', 'bold': True})
    formats['merge_format'] = workbook.add_format({'bold': 1, 'align': 'center', 'text_wrap': True})

    return formats

class ScirisSpreadsheet(ScirisObject):
    ''' A class for reading and writing spreadsheet data in binary format, so a project contains the spreadsheet loaded '''
    # self.data corresponds to the binary data of the Excel file. If passed in a BytesIO object e.g. after writing to the bytestream,
    # the entire contents of the stream will be stored as the data. For IO, can construct a binary file in memory with io.BytesIO
    # and then read/write from it using openpyxl. Final step is to assign the data associated with it to the Spreadsheet
    def __init__(self, source):
        # source is a specification of where to get the data from
        # It can be
        # - A filename, which will get loaded
        # - A io.BytesIO which will get dumped into this instance

        super(ScirisSpreadsheet, self).__init__() # No need for a name, just want to get an UID so as to be storable in database

        self.filename = None
        self.load_date = sc.today()

        if isinstance(source,io.BytesIO):
            source.flush()
            source.seek(0)
            self.data = source.read()
        else:
            self.load(source)

    def __repr__(self):
        output = sc.desc(self)
        return output

    def load(self, filename=None):
        # This function reads a binary ile on disk and stores the content in self.data
        # It also records where the file was loaded from and the date
        if filename is not None:
            filepath = sc.makefilepath(filename=filename)
            self.filename = filepath
            self.load_date = sc.today()
            with open(filepath, mode='rb') as f:
                self.data = f.read()
        else:
            print('No filename specified; aborting.')
        return None

    def save(self, filename=None):
        # This function writes the contents of self.data to a given path on disk
        if filename is None:
            if self.filename is not None: filename = self.filename
        if filename is not None:
            filepath = sc.makefilepath(filename=filename)
            with open(filepath, mode='wb') as f:
                f.write(self.data)
            print('Spreadsheet saved to %s.' % filepath)
        return filepath

    def get_file(self):
        # Return a file-like object with the contents of the file
        # This can then be used to open the workbook from memory without writing anything to disk
        # - book = openpyxl.load_workbook(self.get_file())
        # - book = xlrd.open_workbook(file_contents=self.get_file().read())
        return io.BytesIO(self.data)

    def get_workbook(self):
        # Return an openpyxl Workbook object from this ScirisSpreadsheet's data
        f = self.get_file()
        return openpyxl.load_workbook(f,data_only=True) # Load in read-write mode so that we can correctly dump the file

    def set_workbook(self,workbook):
        # Set this ScirisSpreadsheet's data given an openpyxl Workbook object
        f = io.BytesIO()
        wb.save(f)
        f.flush()
        f.seek(0)
        self.data = f.read()
        self.load_date = sc.today()

    def transfer_extras(self,extras_source):
        # Format this ScirisSpreadsheet based on the extra meta-content in extras_source
        #
        # In reality, a new spreadsheet is created with values from this ScirisSpreadsheet
        # and cell-wise formatting from the extras_source ScirisSpreadsheet. If a cell exists in
        # this spreadsheet and not in the source, it will be retained as-is. If more cells exist in
        # the extras_source than in this spreadsheet, those cells will be dropped. If a sheet exists in
        # the extras_source and not in the current workbook, it will be added

        logger.info('Starting format transfer - this can take a long time')
        tic = time.time()

        assert isinstance(extras_source,ScirisSpreadsheet)

        final_workbook = openpyxl.Workbook(write_only=False)

        new_workbook = openpyxl.load_workbook(self.get_file(),data_only=True) # This is the value source workbook
        old_workbook = openpyxl.load_workbook(extras_source.get_file(),data_only=True) # A openpyxl workbook for the old content

        if not (set(new_workbook.sheetnames).difference(set(old_workbook.sheetnames))): # If every new sheet also appears in the old sheets, then use the old sheet order
            final_sheets = old_workbook.sheetnames
        else:
            # We need to merge the lists somehow. For now, just stick all the extra sheets at the end
            final_sheets = new_workbook.sheetnames + [x for x in old_workbook.sheetnames if x not in new_workbook.sheetnames]

        # final_sheets now contains the order of the sheets in the final workbook
        for sheet in final_sheets:

            if sheet in old_workbook.sheetnames and sheet in new_workbook.sheetnames:
                # Do the content transfer
                old_rows = list(old_workbook[sheet].rows)
                new_rows = list(new_workbook[sheet].rows)

                s = final_workbook.create_sheet(sheet)
                for i in range(0,min(len(old_rows),len(new_rows))):
                    # First we will copy all of the new cells in, including their formatting
                    new_row = new_rows[i]
                    old_row = old_rows[i]
                    final_row = []

                    # First, make all the new cells
                    for cell in new_rows[i]:
                        final_row.append(openpyxl.worksheet.write_only.WriteOnlyCell(s, value=cell.value))

                    # Then, copy over the formats from any cells that match
                    for j in range(0,min(len(new_row),len(old_row))):
                        copy_formats(old_row[j],final_row[j])

                    s.append(final_row)

                if len(new_rows) > len(old_rows):
                    for i in range(len(old_rows),len(new_rows)):
                        final_row = []
                        for cell in new_rows[i]:
                            final_row.append(copy_formats(cell,openpyxl.worksheet.write_only.WriteOnlyCell(s, value=cell.value)))
                        s.append(final_row)

            elif sheet in old_workbook.sheetnames:
                # Add old workbook sheet to final
                copy_worksheet(sheet,old_workbook,final_workbook)
            else:
                # Add new workbook sheet to final
                copy_worksheet(sheet,new_workbook,final_workbook)

        f = io.BytesIO()
        final_workbook.save(f)
        f.flush()
        f.seek(0)
        self.data = f.read()
        logger.info('Format transfer complete - took %.2fs' % (time.time()-tic))

def copy_formats(cell,new_cell):
    if cell.has_style:
        new_cell.font = copy(cell.font)
        new_cell.border = copy(cell.border)
        new_cell.fill = copy(cell.fill)
        new_cell.number_format = copy(cell.number_format)
        new_cell.protection = copy(cell.protection)
        new_cell.alignment = copy(cell.alignment)
        new_cell.comment = cell.comment
    return new_cell

def copy_worksheet(sheet_name,old_workbook,new_workbook):
    s = new_workbook.create_sheet(sheet_name)
    for row in old_workbook[sheet_name].rows:
        new_row = []
        for cell in row:
            new_cell = openpyxl.worksheet.write_only.WriteOnlyCell(s, value=cell.value)
            copy_formats(cell,new_cell)
            new_row.append(new_cell)
        s.append(new_row)

def read_tables(worksheet):
    # This function takes in a openpyxl worksheet, and returns tables
    # A table consists of a block of rows with any #ignore rows skipped
    # This function will start at the top of the worksheet, read rows into a buffer
    # until it gets to the first entirely empty row
    # And then returns the contents of that buffer as a table. So a table is a list of openpyxl rows
    # This function continues until it has exhausted all of the rows in the sheet

    buffer = []
    tables = []
    for row in worksheet.rows:

        # Skip any rows starting with '#ignore'
        if row[0].value and row[0].value.startswith('#ignore'):
            continue  # Move on to the next row if row skipping is marked True

        # Find out whether we need to add the row to the buffer
        for cell in row:
            if cell.value:  # If the row has a non-empty cell, add the row to the buffer
                buffer.append(row)
                break
        else: # If the row was empty, then yield the buffer and flag that it should be cleared at the next iteration
            if buffer:
                tables.append(buffer) # Only append the buffer if it is not empty
            buffer = []

    # After the last row, if the buffer has some un-flushed contents, then yield it
    if buffer:
        tables.append(buffer)

    return tables

class ExcelSettings(object):
    """ Stores settings relevant to Excel file input and output. """

    FILE_EXTENSION = ".xlsx"
    LIST_SEPARATOR = ","

    # Filter keys that denote special extraction rules when reading in Excel sheets.
    FILTER_KEY_LIST = "filter_list"
    FILTER_KEY_BOOLEAN_YES = "boolean_yes"  # Extracted value is True for a yes symbol and False for anything else.
    FILTER_KEY_BOOLEAN_NO = "boolean_no"  # Extracted value is False for a no symbol and True for anything else.

    # Keys for float-valued variables related in some way to Excel file formatting.
    # They must have corresponding default values.
    # TODO: Work out how to reference the keys here within the configuration file, so as to keep the two aligned.
    KEY_COLUMN_WIDTH = "column_width"
    KEY_COMMENT_XSCALE = "comment_xscale"
    KEY_COMMENT_YSCALE = "comment_yscale"
    FORMAT_VARIABLE_KEYS = [KEY_COLUMN_WIDTH, KEY_COMMENT_XSCALE, KEY_COMMENT_YSCALE]

    FORMAT_KEY_CENTER = "center"
    FORMAT_KEY_CENTER_BOLD = "center_bold"

    EXCEL_IO_DEFAULT_COLUMN_WIDTH = 20
    EXCEL_IO_DEFAULT_COMMENT_XSCALE = 3
    EXCEL_IO_DEFAULT_COMMENT_YSCALE = 3

    # Details for the value entry block function.
    # TODO: Consider shifting this to table specs in structure settings.
    ASSUMPTION_HEADER = "constant".title()
    ASSUMPTION_COLUMN_WIDTH = 10
    ASSUMPTION_COMMENT_XSCALE = 3
    ASSUMPTION_COMMENT_YSCALE = 3
    ASSUMPTION_COMMENT = ("This column should be filled with default values used by the model.\n"
                          "If the option to provide time-dependent values exists, then "
                          "this can be considered a time-independent assumption.\n"
                          "In this case, if any time-dependent values are entered, the "
                          "Excel sheet will attempt to explicitly mark the corresponding "
                          "cell as inapplicable.\n"
                          "Time-dependent values always trump assumptions.")
    QUANTITY_TYPE_HEADER = "quantity_type".replace("_", " ").title()
    QUANTITY_TYPE_COLUMN_WIDTH = 15
    QUANTITY_TYPE_COMMENT_XSCALE = 3
    QUANTITY_TYPE_COMMENT_YSCALE = 3
    QUANTITY_TYPE_COMMENT = ("This column displays the type of quantity that the databook is "
                             "requesting, e.g. probability, duration, number, etc.\n"
                             "In some cases, the user may select the format for the data, "
                             "to align with data collection pragmatics, and appropriate "
                             "conversions will be done internally to the model.")


# Utility functions for writing.

@log_usage
@accepts(xw.Workbook)
def create_standard_excel_formats(excel_file):
    """ 
    Generates and returns a dictionary of standard excel formats attached to an excel file.
    Note: Can be modified or expanded as necessary to fit other definitions of 'standard'.
    """
    formats = dict()
    formats[ExcelSettings.FORMAT_KEY_CENTER_BOLD] = excel_file.add_format({"align": "center", "bold": True})
    formats[ExcelSettings.FORMAT_KEY_CENTER] = excel_file.add_format({"align": "center"})
    return formats


@log_usage
def create_default_format_variables():
    """
    Establishes framework-file default values for format variables in a dictionary and returns it.
    Note: Once used exec function here but it is now avoided for Python3 compatibility.
    """
    format_variables = dict()
    format_variables[ExcelSettings.KEY_COLUMN_WIDTH] = ExcelSettings.EXCEL_IO_DEFAULT_COLUMN_WIDTH
    format_variables[ExcelSettings.KEY_COMMENT_XSCALE] = ExcelSettings.EXCEL_IO_DEFAULT_COMMENT_XSCALE
    format_variables[ExcelSettings.KEY_COMMENT_YSCALE] = ExcelSettings.EXCEL_IO_DEFAULT_COMMENT_YSCALE
    return format_variables


def create_value_entry_block(excel_page, start_row, start_col, num_items,
                             time_vector=None, default_values=None, quantity_types=None,
                             condition_list=None, formats=None):
    """
    Create a block where users enter values in a 'constant' column or as time-dependent array.
    A list of Excel-string conditions can be provided that decide, if true, that a row appears.
    """
    # Generate standard formats if they do not exist.
    if formats is None:
        logger.warning("Formats were not passed to worksheet value-entry block construction.")
        formats = {ExcelSettings.FORMAT_KEY_CENTER_BOLD: None, ExcelSettings.FORMAT_KEY_CENTER: None}

    if time_vector is None:
        time_vector = []
    if default_values is None:
        default_values = [0.0] * num_items
    if condition_list is None:
        condition_list = [None] * num_items

    # Start with the headers and column formats.
    row, col = start_row, start_col
    # If a list of quantity types exists for the data, create a corresponding column.
    if quantity_types is not None:
        excel_page.write(row, col, ExcelSettings.QUANTITY_TYPE_HEADER, formats[ExcelSettings.FORMAT_KEY_CENTER_BOLD])
        excel_page.write_comment(row, col, ExcelSettings.QUANTITY_TYPE_COMMENT,
                                 {"x_scale": ExcelSettings.QUANTITY_TYPE_COMMENT_XSCALE,
                                  "y_scale": ExcelSettings.QUANTITY_TYPE_COMMENT_YSCALE})
        excel_page.set_column(col, col, ExcelSettings.QUANTITY_TYPE_COLUMN_WIDTH)
        col += 1
    excel_page.write(row, col, ExcelSettings.ASSUMPTION_HEADER, formats[ExcelSettings.FORMAT_KEY_CENTER_BOLD])
    excel_page.write_comment(row, col, ExcelSettings.ASSUMPTION_COMMENT,
                             {"x_scale": ExcelSettings.ASSUMPTION_COMMENT_XSCALE,
                              "y_scale": ExcelSettings.ASSUMPTION_COMMENT_YSCALE})
    excel_page.set_column(col, col, ExcelSettings.ASSUMPTION_COLUMN_WIDTH)
    year_col = 0
    if len(time_vector) > 0:
        col += 2
        year_col = col
        for t_val in time_vector:
            excel_page.write(row, col, t_val, formats[ExcelSettings.FORMAT_KEY_CENTER_BOLD])
            col += 1

    # Flesh out the contents.
    for item_number in range(num_items):
        col = start_col
        row += 1
        if quantity_types is not None:
            quantity_content = quantity_types[0]
            if condition_list[item_number] is not None:
                quantity_content = "=IF({0},{1},{2})".format(condition_list[item_number], "\"" + quantity_content + "\"", "\"\"")
                excel_page.write(row, col, quantity_content, None, quantity_types[0])
            else:
                excel_page.write(row, col, quantity_types[0])
            excel_page.data_validation(xlrc(row, col),
                                       {"validate": "list", "source": quantity_types})
            col += 1
        if len(time_vector) > 0:
            rc_start = xlrc(row, year_col)
            rc_end = xlrc(row, year_col + len(time_vector) - 1)
            def_content = "=IF(SUMPRODUCT(--({0}:{1}<>\"{2}\"))=0,{3},\"{4}\")".format(rc_start, rc_end, str(),
                                                                                       default_values[item_number],
                                                                                       SS.DEFAULT_SYMBOL_INAPPLICABLE)
            or_content = SS.DEFAULT_SYMBOL_OR
            if condition_list[item_number] is not None:
                def_content = "=IF({0},{1},{2})".format(condition_list[item_number], def_content.lstrip("="), "\"\"")
                or_content = "=IF({0},{1},{2})".format(condition_list[item_number], "\"" + or_content + "\"", "\"\"")
                excel_page.write(row, col + 1, or_content, formats[ExcelSettings.FORMAT_KEY_CENTER],
                                 SS.DEFAULT_SYMBOL_OR)
            else:
                excel_page.write(row, col + 1, or_content, formats[ExcelSettings.FORMAT_KEY_CENTER])
            excel_page.write(row, col, def_content, None, default_values[item_number])
        else:
            def_content = default_values[item_number]
            if condition_list[item_number] is not None:
                def_content = "=IF({0},{1},{2})".format(condition_list[item_number], def_content, "\"\"")
                excel_page.write(row, col, def_content, None, default_values[item_number])
            else:
                excel_page.write(row, col, def_content)

    last_row, last_col = row, start_col + 1 + len(time_vector)
    return last_row, last_col


# Utility functions for reading.

@accepts(xlrd.sheet.Sheet)
@returns(dict)
def extract_header_columns_mapping(excel_page, row=0):
    """
    Returns a dictionary mapping column headers in an Excel page to the column numbers in which they are found.
    The columns must be contiguous and are returned as a two-element list of first and last column.
    """
    header_columns_map = dict()
    current_header = None
    for col in range(excel_page.ncols):
        header = str(excel_page.cell_value(row, col))
        if not header == "":
            if header not in header_columns_map:
                header_columns_map[header] = [col, col]
            elif not current_header == header:
                error_message = "An Excel file page contains multiple headers called '{0}'.".format(header)
                logger.error(error_message)
                raise AtomicaException(error_message)
            current_header = header
        if current_header is not None:
            header_columns_map[current_header][-1] = col
    return header_columns_map


@accepts(xlrd.sheet.Sheet, int, int)
def extract_excel_sheet_value(excel_page, start_row, start_col, stop_row=None, stop_col=None, filters=None):
    """
    Returns a value extracted from an Excel page, but converted to type according to a list of filters.
    The value will be pulled from rows starting at 'start_row' and terminating before reading 'stop_row'.
    A similar restriction holds for columns.
    Note that 'stop_row' and its column equivalent is one further along than a 'last_row' and its equivalent.
    Empty-string values are always equivalent to a value of None being returned.
    """
    if filters is None:
        filters = []
    value, old_value = None, None
    row, col = start_row, start_col
    if stop_row is None:
        stop_row = row + 1
    if stop_col is None:
        stop_col = col + 1
    rc_start = xlrc(start_row, start_col)
    rc = rc_start
    # If columns without headers follow this column in the Excel page, scan through them.
    # Ditto with rows without item names that follow this row in the Excel page.
    while row < stop_row:
        while col < stop_col:
            value = str(excel_page.cell_value(row, col))
            if value == "":
                value = None
            elif ExcelSettings.FILTER_KEY_LIST in filters:
                value = [item.strip() for item in value.strip().split(ExcelSettings.LIST_SEPARATOR)]

            if old_value is not None:  # If there is an old value, this is not the first important cell examined.
                if value is None:
                    value = old_value  # If the new value is not important, maintain the old value.
                else:
                    # Expand lists with additional cell contents if appropriate.
                    if ExcelSettings.FILTER_KEY_LIST in filters:
                        value = old_value + value
                    # Otherwise, ignore with a warning.
                    else:
                        rc = xlrc(row, col)
                        logger.warning("Value '{0}' at cell '{1}' on page '{2}' is still considered part of the item "
                                       "and specification (i.e. header) located at cell '{3}'. It will be "
                                       "ignored for the previous value of '{4}'.".format(value, rc, excel_page.name,
                                                                                         rc_start, old_value))
                        value = old_value
            old_value = value
            col += 1
        col = start_col
        row += 1

    # Convert to boolean values if specified by filter.
    # Empty strings and unidentified symbols are considered default values.
    if ExcelSettings.FILTER_KEY_BOOLEAN_YES in filters:
        if value == SS.DEFAULT_SYMBOL_YES:
            value = True
        else:
            if value not in [SS.DEFAULT_SYMBOL_NO, ""]:
                logger.warning("Did not recognize symbol on page '{0}', at cell '{1}'. "
                               "Assuming a default of '{2}'.".format(excel_page.name, rc, SS.DEFAULT_SYMBOL_NO))
            value = ""
    if ExcelSettings.FILTER_KEY_BOOLEAN_NO in filters:
        if value == SS.DEFAULT_SYMBOL_NO:
            value = False
        else:
            if value not in [SS.DEFAULT_SYMBOL_YES, ""]:
                logger.warning("Did not recognize symbol on page '{0}', at cell '{1}'. "
                               "Assuming a default of '{2}'.".format(excel_page.name, rc, SS.DEFAULT_SYMBOL_YES))
            value = ""
    if value == "":
        value = None
    return value
