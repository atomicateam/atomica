# -*- coding: utf-8 -*-
"""
Optima Core project-framework input/output file.
Contains functions to create, import and export framework files.
This is primarily referenced by the ProjectFramework object.
"""

from optimacore.system import logger, logUsage, accepts, getOptimaCorePath
from optimacore.system import SystemSettings

import xlsxwriter as xw
try: import ConfigParser as configparser    # Python 2.
except ImportError: import configparser     # Python 3.


@logUsage
@accepts(str)
def createFrameworkTemplate(framework_path):
    """
    Creates a template framework Excel file.
    Returns True for process success.
    """
    
    logger.info("Creating a template framework file: {0}".format(framework_path))
    
    cp = configparser.ConfigParser()
    cp.read(getOptimaCorePath(subdir="optimacore")+SystemSettings.CONFIG_FRAMEWORK_FILENAME)
    
    framework_file = xw.Workbook(framework_path)
    format_bold = framework_file.add_format({'bold': True})
    
    # Establish framework file format defaults.
    file_column_width = SystemSettings.EXCEL_IO_DEFAULT_COLUMN_WIDTH
    file_comment_xscale = SystemSettings.EXCEL_IO_DEFAULT_COMMENT_XSCALE
    file_comment_yscale = SystemSettings.EXCEL_IO_DEFAULT_COMMENT_YSCALE
    
    framework_keys = [item for item in cp.get('sheets', 'keys').strip().split(',')]
    for framework_key in framework_keys:
        sheet_name = cp.get("sheet_"+framework_key, "name").strip()
        header_keys = [item for item in cp.get("sheet_"+framework_key, "headers").strip().split(',')]
        
        # Propagate file-wide formats to page-wide formats.
        page_column_width = file_column_width
        page_comment_xscale = file_comment_xscale
        page_comment_yscale = file_comment_yscale
        
        # Overwrite page-wide formates if specified in config file.
        try: page_column_width = float(cp.get("sheet_"+framework_key, "col_width"))
        except ValueError: logger.warn("Framework configuration file for page-key '{0}' has an entry for 'col_width' " 
                                       "that cannot be converted to a float. Using default.".format(framework_key))
        except: pass
        
        framework_sheet = framework_file.add_worksheet(sheet_name)
        col = 0
        for header_key in header_keys:
            header_name = cp.get("header_"+header_key, "name").strip()
            header_comment = cp.get("header_"+header_key, "comment").strip()
            
            # Propagate page-wide formats to columns.
            column_width = page_column_width
            comment_xscale = page_comment_xscale
            comment_yscale = page_comment_yscale
            
            framework_sheet.write(0, col, header_name, format_bold)
            framework_sheet.write_comment(0, col, header_comment, 
                                          {"x_scale": comment_xscale, 
                                           "y_scale": comment_yscale})
            framework_sheet.set_column(col, col, column_width)
            col += 1

    return
    