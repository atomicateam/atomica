"""
Version:
"""

from atomica.workbook_export import writeWorkbook
from atomica.system import SystemSettings as SS
from atomica.workbook_export import makeInstructions
from atomica.project import Project
from atomica.framework import ProjectFramework
from sciris.utils import odict
from sciris.fileio import loadobj
import os

torun = [
'makeframeworkfile',
'makeframework',
'saveframework',
'loadframework',
'makedatabook',
'makeproject',
'saveproject',
'loadproject',
]

tmpdir = '.' + os.sep + 'temp' + os.sep


if 'makeframeworkfile' in torun:
    framework_instructions, use_instructions = makeInstructions(framework=None, data=None, workbook_type=SS.STRUCTURE_KEY_FRAMEWORK)
    framework_instructions.num_items = odict([('popatt', 4),        # Set the number of population attributes (not currently used)
                                              ('par', 10),          # Set the number of parameters
                                              ('comp', 4),          # Set the number of compartments
                                              ('popopt', 3),        # Set the number of ... ?
                                              ('progatt', 3),       # Set the number of program attributes (not current used) - what's the purpose of this?
                                              ('charac', 10),       # Set the number of characteristics, i.e., results
                                              ('progtype', 7), ])   # Set the number of program types - question, can we get rid of this?
    
    writeWorkbook(workbook_path=tmpdir+"framework_test.xlsx", framework=None, data=None, instructions=framework_instructions, workbook_type=SS.STRUCTURE_KEY_FRAMEWORK)


	
if 'makeframework' in torun:
    F = ProjectFramework(name="SIR", frameworkfilename="./frameworks/framework_sir.xlsx")


if 'saveframework' in torun:
    F.save(tmpdir+'testframework.frw')


if 'loadframework' in torun:
    F = loadobj(tmpdir+'testframework.frw')


if 'makedatabook' in torun:
    F = loadobj(tmpdir+'testframework.frw')
    P = Project(framework=F) # Create a project with no data
    databook_instructions, use_instructions = makeInstructions(framework=F, data=None, workbook_type=SS.STRUCTURE_KEY_DATA)
    databook_instructions.num_items = odict([('prog', 3),       # Set the number of programs
                                             ('pop', 1), ])     # Set the number of populations
    P.createDatabook(databook_path="./databooks/databook_sir_blank.xlsx", instructions=databook_instructions, databook_type=SS.DATABOOK_DEFAULT_TYPE)


if 'makeproject' in torun:
    P = Project(framework=F, databook="./databooks/databook_sir.xlsx")

if 'saveproject' in torun:
    P.save(tmpdir+'testproject.prj')


if 'loadproject' in torun:
    P = loadobj(tmpdir+'testproject.prj')

