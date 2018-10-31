# Set to True to print out as modules are being imported
from .utils import *
from .migration import *
from .results import *
from .cascade import *
from .optimization import *
from .reconciliation import *  # Depends on system
from .programs import ProgramInstructions, ProgramSet  # Depends on...?
from .plotting import *  # Depends on...?
from .defaults import *  # Depends on ???
from .scenarios import *  # Depends on ???
from .calibration import *  # Depends on ???
from .project import *
from .framework import *
from .structure import *
from .system import *  # No dependencies
from .version import *  # No dependencies
_debug = False

# The Atomica "user interface" -- import everything from submodules
if _debug:
    print('Importing version...')
if _debug:
    print('Importing system...')
if _debug:
    print('Importing structure...')
if _debug:
    print('Importing framework...')
if _debug:
    print('Importing project...')
if _debug:
    print('Importing calibration...')
if _debug:
    print('Importing scenarios...')
if _debug:
    print('Importing defaults...')
if _debug:
    print('Importing plotting...')
if _debug:
    print('Importing program instructions...')
if _debug:
    print('Importing reconciliation...')
if _debug:
    print('Importing optimization...')
if _debug:
    print('Importing cascade...')
if _debug:
    print('Importing results...')
if _debug:
    print('Importing migration...')
if _debug:
    print('Importing utils...')
if _debug:
    print('Done importing Atomica.')
