# Load a project
from atomica.project import Project
from atomica.workbook_export import writeWorkbook
from atomica.system import SystemSettings as SS
from atomica.framework import ProjectFramework
from atomica.workbook_export import makeInstructions
from atomica.project_settings import ProjectSettings
from sciris.fileio import saveobj, loadobj
from atomica.utils import odict, tic, toc, blank

P = loadobj('./temp/testproject.prj')