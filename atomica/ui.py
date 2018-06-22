# Set to True to print out as modules are being imported
_debug = True

# The Atomica "user interface" -- import everything from submodules
if _debug: print('Importing version...')
from .core.version import * # No dependencies
if _debug: print('Importing system...')
from .core.system import *  # No dependencies
if _debug: print('Importing Excel...')
from .core.excel import *  # Depends on system
if _debug: print('Importing structure settings...')
from .core.structure_settings import *  # Depends on Excel
from .core.structure_settings import FrameworkSettings as FS
if _debug: print('Importing structure...')
from .core.structure import *  # Depends on structure_settings
if _debug: print('Importing workbook utils...')
from .core.workbook_utils import *  # Depends on structure_settings
if _debug: print('Importing workbook export...')
from .core.workbook_export import *  # Depends on workbook_utils
if _debug: print('Importing framework...')
from .core.framework import *  # Depends on workbook_import
if _debug: print('Importing project...')
from .core.project import *  # Depends on workbook_export
if _debug: print('Importing calibration...')
from .core.calibration import * # Depends on ???
if _debug: print('Importing scenarios...')
from .core.scenarios import * # Depends on ???
if _debug: print('Importing defaults...')
from .core.defaults import * # Depends on ???
if _debug: print('Importing plotting...')
from .core.plotting import * # Depends on...?
if _debug: print('Done importing Atomica.')