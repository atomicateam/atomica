# Set to True to print out as modules are being imported
_debug = False

# The Atomica "user interface" -- import everything from submodules
if _debug: print('Importing version...')
from .version import * # No dependencies
if _debug: print('Importing system...')
from .system import *  # No dependencies
if _debug: print('Importing structure...')
from .structure import *
if _debug: print('Importing framework...')
from .framework import *
if _debug: print('Importing project...')
from .project import *
if _debug: print('Importing calibration...')
from .calibration import * # Depends on ???
if _debug: print('Importing scenarios...')
from .scenarios import * # Depends on ???
if _debug: print('Importing defaults...')
from .defaults import * # Depends on ???
if _debug: print('Importing plotting...')
from .plotting import * # Depends on...?
if _debug: print('Importing program instructions...')
from .programs import ProgramInstructions, ProgramSet # Depends on...?
if _debug: print('Importing reconciliation...')
from .reconciliation import * # Depends on system
if _debug: print('Importing optimization...')
from .optimization import *
if _debug: print('Importing cascade...')
from .cascade import *
if _debug: print('Importing results...')
from .results import *
if _debug: print('Done importing Atomica.')