# -*- coding: utf-8 -*-
"""
Optima Core Excel utilities file.
Contains functionality specific to Excel input and output.
"""

from optimacore.system import logUsage, accepts

import xlsxwriter as xw

class ExcelSettings(object):
    """ Stores settings relevant to Excel file input and output. """

    FILE_EXTENSION = ".xlsx"
    LIST_SEPARATOR = ","

    # Keys for float-valued variables related in some way to Excel file formatting.
    # They must have corresponding default values.
    # TODO: Work out how to reference the keys here within the configuration file, so as to keep the two aligned.
    KEY_COLUMN_WIDTH = "column_width"
    KEY_COMMENT_XSCALE = "comment_xscale"
    KEY_COMMENT_YSCALE = "comment_yscale"
    FORMAT_VARIABLE_KEYS = [KEY_COLUMN_WIDTH, KEY_COMMENT_XSCALE, KEY_COMMENT_YSCALE]

    EXCEL_IO_DEFAULT_COLUMN_WIDTH = 20
    EXCEL_IO_DEFAULT_COMMENT_XSCALE = 3
    EXCEL_IO_DEFAULT_COMMENT_YSCALE = 3

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
    format_variables[ExcelSettings.KEY_COLUMN_WIDTH] = ExcelSettings.EXCEL_IO_DEFAULT_COLUMN_WIDTH
    format_variables[ExcelSettings.KEY_COMMENT_XSCALE] = ExcelSettings.EXCEL_IO_DEFAULT_COMMENT_XSCALE
    format_variables[ExcelSettings.KEY_COMMENT_YSCALE] = ExcelSettings.EXCEL_IO_DEFAULT_COMMENT_YSCALE
    return format_variables
