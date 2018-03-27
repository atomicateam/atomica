### Initialise a project with data and a framework file
from optimacore.project import Project
from optimacore.workbook_export import writeWorkbook
from optimacore.system import SystemSettings as SS
from optimacore.framework import ProjectFramework
from optimacore.workbook_export import makeInstructions
from optimacore.project_settings import ProjectSettings
from optima import odict, saveobj, loadobj
from optima import tic, toc, blank

F = ProjectFramework(name="SIR", frameworkfilename="./frameworks/framework_sir.xlsx")
P = Project(framework=F) # Create a project with no data
databook_instructions, use_instructions = makeInstructions(framework=F, data=None, workbook_type=SS.STRUCTURE_KEY_DATA)
databook_instructions.num_items = odict([('prog', 3),       # Set the number of programs
                                         ('pop', 1), ])     # Set the number of populations
P.createDatabook(databook_path="./temp/databooks/databook_sir_blank.xlsx", instructions=databook_instructions, databook_type=SS.DATABOOK_DEFAULT_TYPE)
P = Project(framework=F, databook="databooks/databook_sir.xlsx")
# Note, P.runsim() currently returns interpolated parameters, not an actual model result. Model doesn't exist yet

