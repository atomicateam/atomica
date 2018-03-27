### Export a databook from a framework
from optimacore.project import Project
from optimacore.workbook_export import writeWorkbook
from optimacore.system import SystemSettings as SS
from optimacore.framework import ProjectFramework
from optimacore.workbook_export import makeInstructions
from optimacore.project_settings import ProjectSettings
from optimacore.system_io import saveobj, loadobj
from optimacore.utils import odict, tic, toc, blank

F = loadobj(os.path.join(tempdir,'testframework.frw'))
P = Project(framework=F) # Create a project with no data
databook_instructions, use_instructions = makeInstructions(framework=F, data=None, workbook_type=SS.STRUCTURE_KEY_DATA)
databook_instructions.num_items = odict([('prog', 3),       # Set the number of programs
                                         ('pop', 1), ])     # Set the number of populations
P.createDatabook(databook_path="./temp/databooks/databook_sir_blank.xlsx", instructions=databook_instructions, databook_type=SS.DATABOOK_DEFAULT_TYPE)
