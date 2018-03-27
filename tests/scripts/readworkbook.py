# -*- coding: utf-8 -*-
"""
Created on Thu Mar  8 08:30:08 2018

@author: robynstuart
"""

## IMPORTS
from optimacore.project import Project
from optimacore.workbook_export import writeWorkbook
from optimacore.workbook_import import readWorkbook
from optimacore.system import SystemSettings as SS

from optimacore.structure_settings import FrameworkSettings as FS
from optimacore.structure_settings import DatabookSettings as DS

import sys
import pprint


### TEST
#proj = Project()
#readWorkbook(workbook_path = "./ukraine_frameworks_test.xlsx", framework = proj.framework, data = None, workbook_type = SS.STRUCTURE_KEY_FRAMEWORK)
#readWorkbook(workbook_path = "./ukraine_databook_test.xlsx", framework = proj.framework, data = proj.data, workbook_type = SS.STRUCTURE_KEY_DATA)

## TEST ALT
P = Project()
#writeWorkbook(workbook_path = "./frameworks/framework_test.xlsx", framework = None, data = None, instructions = None, workbook_type = SS.STRUCTURE_KEY_FRAMEWORK)
readWorkbook(workbook_path = os.path.join(testdir,'frameworks','framework_ukraine.xlsx'), framework = P.framework, data = None, workbook_type = SS.STRUCTURE_KEY_FRAMEWORK)
#writeWorkbook(workbook_path = "./databooks/databook_ukraine.xlsx", framework = proj.framework, data = None, instructions = None, workbook_type = SS.STRUCTURE_KEY_DATA)
#readWorkbook(workbook_path = "./databooks/databook_ukraine.xlsx", framework = proj.framework, data = proj.data, workbook_type = SS.STRUCTURE_KEY_DATA)

## PRINT
print("-"*100)
pprint.pprint(P.framework.specs)
print("-"*100)
pprint.pprint(P.data.specs)
print("-"*100)

