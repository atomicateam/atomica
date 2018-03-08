# -*- coding: utf-8 -*-
"""
Created on Thu Mar  8 08:30:08 2018

@author: robynstuart
"""

## IMPORTS
from optimacore.project import Project
from optimacore.workbook_import import readWorkbook
from optimacore.system import SystemSettings as SS

from optimacore.structure_settings import FrameworkSettings as FS
from optimacore.structure_settings import DatabookSettings as DS

import sys
import pprint


## TEST
proj = Project()
readWorkbook(workbook_path = "./ukraine_frameworks_test.xlsx", framework = proj.framework, data = None, workbook_type = SS.WORKBOOK_KEY_FRAMEWORK)
readWorkbook(workbook_path = "./ukraine_databook_test.xlsx", framework = proj.framework, data = proj.data, workbook_type = SS.WORKBOOK_KEY_DATA)


## PRINT
print("-"*100)
pprint.pprint(proj.framework.specs)
print("-"*100)
pprint.pprint(proj.data.specs)
print("-"*100)

