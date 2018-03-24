# -*- coding: utf-8 -*-
"""
Tests the basic functionality of Core
Created on Fri Mar 23 16:37:15 2018
"""

## TEMPORARY IMPORTS
#from optima import odict
from optima import tic, toc, blank
#from numpy import array

## IMPORTS
from optimacore.project import Project
from optimacore.workbook_export import writeWorkbook
from optimacore.workbook_import import readWorkbook
from optimacore.system import SystemSettings as SS
from optimacore.structure_settings import FrameworkSettings as FS
from optimacore.structure_settings import DatabookSettings as DS
from optimacore.framework import ProjectFramework

## OTHER IMPORTS
import sys
import pprint

## DEFINE WHAT TO RUN
torun = ['makeframeworkfile',
         'makeframework',
         'makedatabook',
#         'makeproject',
         ]

def done(t=0):
    print('Done.')
    toc(t)
    blank()

blank()
print('Running tests:')
for i,test in enumerate(torun): print(('%i.  '+test) % (i+1))
blank()



##############################################################################
## The tests
##############################################################################

T = tic()



### MAKE A FRAMEWORK FILE
if 'makeframeworkfile' in torun:
    writeWorkbook(workbook_path="./frameworks/framework_test.xlsx", framework=None, data=None, instructions=None, workbook_type=SS.STRUCTURE_KEY_FRAMEWORK)

### MAKE A FRAMEWORK
if 'makeframework' in torun:
    F = ProjectFramework(filename="./frameworks/framework_sir.xlsx")

### EXPORT A DATABOOK FROM A FRAMEWORK
if 'makedatabook' in torun:
    writeWorkbook(workbook_path = "./databooks/databook_sir.xlsx", framework=F, data=None, instructions=None, workbook_type=SS.STRUCTURE_KEY_DATA)

### INITIALISE A PROJECT WITH A FRAMEWORK FILE
if 'makeproject' in torun:
    P = Project(framework=F, )
    #readWorkbook(workbook_path = "./frameworks/framework_ukraine.xlsx", framework = P.framework, data = None, workbook_type = SS.STRUCTURE_KEY_FRAMEWORK)




print('\n\n\nDONE: ran %i tests' % len(torun))
toc(T)



#readWorkbook(workbook_path = "./ukraine_frameworks_test.xlsx", framework = proj.framework, data = None, workbook_type = SS.STRUCTURE_KEY_FRAMEWORK)
#readWorkbook(workbook_path = "./ukraine_databook_test.xlsx", framework = proj.framework, data = proj.data, workbook_type = SS.STRUCTURE_KEY_DATA)

## TEST ALT
#P = Project()
#readWorkbook(workbook_path = "./databooks/databook_ukraine.xlsx", framework = proj.framework, data = proj.data, workbook_type = SS.STRUCTURE_KEY_DATA)

## PRINT
#print("-"*100)
#pprint.pprint(P.framework.specs)
#print("-"*100)
#pprint.pprint(P.data.specs)
#print("-"*100)

#
#
#
#
#F.compartments = ['S','I','R']
#F.transitions = array([[1,1,0],[0,1,1],[0,0,1]])
#F.characteristics = odict([('All infected',['S','I']),
#                           ('All people',['S','I','R'])])
#                           


