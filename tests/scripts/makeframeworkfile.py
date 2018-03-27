# First, generate an "Instructions" object which allows you to specify details of the framework file. Question, why isn't there an easier way to do this??? I should be able to pass in a dictionary to writeWorkbook.
from atomica.project import Project
from atomica.workbook_export import writeWorkbook
from atomica.system import SystemSettings as SS
from atomica.framework import ProjectFramework
from atomica.workbook_export import makeInstructions
from atomica.project_settings import ProjectSettings
from sciris.fileio import saveobj, loadobj
from sciris.utils import odict, tic, toc, blank

framework_instructions, use_instructions = makeInstructions(framework=None, data=None, workbook_type=SS.STRUCTURE_KEY_FRAMEWORK)
framework_instructions.num_items = odict([('popatt', 4),        # Set the number of population attributes (not currently used)
                                          ('par', 10),          # Set the number of parameters
                                          ('comp', 4),          # Set the number of compartments
                                          ('popopt', 3),        # Set the number of ... ?
                                          ('progatt', 3),       # Set the number of program attributes (not current used) - what's the purpose of this?
                                          ('charac', 10),       # Set the number of characteristics, i.e., results
                                          ('progtype', 7), ])   # Set the number of program types - question, can we get rid of this?

writeWorkbook(workbook_path="./temp/frameworks/framework_test.xlsx", framework=None, data=None, instructions=framework_instructions, workbook_type=SS.STRUCTURE_KEY_FRAMEWORK)
