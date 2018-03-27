### Make a framework by importing a framework file, then optionally save it
from optimacore.project import Project
from optimacore.workbook_export import writeWorkbook
from optimacore.system import SystemSettings as SS
from optimacore.framework import ProjectFramework
from optimacore.workbook_export import makeInstructions
from optimacore.project_settings import ProjectSettings
from optimacore.system_io import saveobj, loadobj
from optimacore.utils import odict, tic, toc, blank

F = ProjectFramework(name="SIR", frameworkfilename="./frameworks/framework_sir.xlsx")
