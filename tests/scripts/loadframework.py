# Load a framework object
from atomica.project import Project
from atomica.workbook_export import writeWorkbook
from atomica.system import SystemSettings as SS
from atomica.framework import ProjectFramework
from atomica.workbook_export import makeInstructions
from atomica.project_settings import ProjectSettings
from sciris.fileio import saveobj, loadobj
from sciris.utils import odict, tic, toc, blank
import os

F = loadobj(os.path.join('temp','testframework.frw'))