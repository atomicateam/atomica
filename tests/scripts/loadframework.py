# Load a framework object
from optimacore.project import Project
from optimacore.workbook_export import writeWorkbook
from optimacore.system import SystemSettings as SS
from optimacore.framework import ProjectFramework
from optimacore.workbook_export import makeInstructions
from optimacore.project_settings import ProjectSettings
from optima import odict, saveobj, loadobj
from optima import tic, toc, blank

F = loadobj(os.path.join(tempdir,'testframework.frw'))