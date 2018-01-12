# -*- coding: utf-8 -*-
"""
Optima Core databook file.
Contains functions for creating databooks from project frameworks and then importing them.
"""

from optimacore.system import logUsage, accepts, returns, logger, prepareFilePath
from optimacore.framework import ProjectFramework

import xlsxwriter as xw

@logUsage
@accepts(ProjectFramework,str)
def createDatabookFunc(framework, databook_path):
    """ Generate a data-input Excel spreadsheet corresponding to a project framework. """

    logger.info("Creating a project databook: {0}".format(databook_path))
    prepareFilePath(databook_path)
    workbook = xw.Workbook(databook_path)

    ws_pops = workbook.add_worksheet("Populations")

    workbook.close()