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
from openpyxl.comments import Comment

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

    # Conditional formats used for Y/N boolean matrix
    formats['unlocked_boolean_true'] = workbook.add_format({'bg_color': OPT_COLOR})
    formats['unlocked_boolean_false'] = workbook.add_format({'bg_color': BG_COLOR})

    return formats

class AtomicaSpreadsheet(object):
    ''' A class for reading and writing data in binary format, so a project contains the spreadsheet loaded '''
    # This object provides an interface for managing the contents of files (particularly spreadsheets) as Python objects
    # that can be stored in the FE database. Basic usage is as follows:
    #
    # ss = AtomicaSpreadsheet('input.xlsx') # Load a file into this object
    # ss.add_to_datastore() # Can use database methods inherited from ScirisObject
    # f = ss.get_file() # Retrieve an in-memory file-like IO stream from the data
    # book = openpyxl.load_workbook(f) # This stream can be passed straight to openpyxl
    # book.create_sheet(...)
    # book.save(f) # The workbook can be saved back to this stream
    # ss.insert(f) # We can update the contents of the AtomicaSpreadsheet with the newly written workbook
    # ss.add_to_datastore() # Presumably would want to store the changes in the database too
    # ss.save('output.xlsx') # Can also write the contents back to disk
    #
    # As shown above, no disk IO needs to happen to manipulate the spreadsheets with openpyxl (or xlrd/xlsxwriter)

    def __init__(self, source=None):
        # source is a specification of where to get the data from
        # It can be anything supported by AtomicaSpreadsheet.insert() which are
        # - A filename, which will get loaded
        # - A io.BytesIO which will get dumped into this instance

        self.filename = None
        self.data = None
        self.load_date = None

        if source is not None:
            self.insert(source)

    def __repr__(self):
        output = sc.desc(self)
        return output

    def insert(self, source):
        # This function sets the `data` attribute given a file-like data source
        #
        # INPUTS:
        # - source : This contains the contents of the file. It can be
        #   - A string, which is interpreted as a filename
        #   - A file-like object like a BytesIO, the entire contents of which will be read
        #
        # This function reads a binary ile on disk and stores the content in self.data
        # It also records where the file was loaded from and the date
        if isinstance(source,io.BytesIO):
            source.flush()
            source.seek(0)
            self.data = source.read()
        else:
            filepath = sc.makefilepath(filename=source)
            self.filename = filepath
            self.load_date = sc.today()
            with open(filepath, mode='rb') as f:
                self.data = f.read()

        self.load_date = sc.today()

    def save(self, filename=None):
        # This function writes the contents of self.data to a file on disk
        if filename is None:
            if self.filename is not None:
                filename = self.filename
            else:
                raise Exception('Cannot determine filename')

        filepath = sc.makefilepath(filename=filename)
        with open(filepath, mode='wb') as f:
            f.write(self.data)
        print('Spreadsheet saved to %s.' % filepath)

        return filepath

    def get_file(self):
        # Return a file-like object with the contents of the file
        # This can then be used to open the workbook from memory without writing anything to disk e.g.
        # - book = openpyxl.load_workbook(self.get_file())
        # - book = xlrd.open_workbook(file_contents=self.get_file().read())
        return io.BytesIO(self.data)


def transfer_comments(target,comment_source):
    # Format this AtomicaSpreadsheet based on the extra meta-content in comment_source
    #
    # In reality, a new spreadsheet is created with values from this AtomicaSpreadsheet
    # and cell-wise formatting from the comment_source AtomicaSpreadsheet. If a cell exists in
    # this spreadsheet and not in the source, it will be retained as-is. If more cells exist in
    # the comment_source than in this spreadsheet, those cells will be dropped. If a sheet exists in
    # the comment_source and not in the current workbook, it will be added

    assert isinstance(comment_source, AtomicaSpreadsheet)

    this_workbook = openpyxl.load_workbook(target.get_file(),data_only=False) # This is the value source workbook
    old_workbook = openpyxl.load_workbook(comment_source.get_file(),data_only=False) # A openpyxl workbook for the old content

    for sheet in this_workbook.worksheets:

        # If this sheet isn't in the old workbook, do nothing
        if sheet.title not in old_workbook.sheetnames:
            continue

        # Transfer comments
        for row in old_workbook[sheet.title].rows:
            for cell in row:
                if cell.comment:
                    sheet[cell.coordinate].comment = Comment(cell.comment.text, '')

    f = io.BytesIO()
    this_workbook.save(f)
    f.flush()
    f.seek(0)
    target.data = f.read()

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
