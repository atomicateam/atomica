"""
Atomica root module

The Atomica module is the entry point for running simulations and performing analysis
using Atomica.

"""

# License:
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Lesser General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Display version information using logging

import sys
import logging

logger = logging.getLogger("atomica")

if not logger.handlers:
    # Only add handlers if they don't already exist in the module-level logger
    # This means that it's possible for the user to completely customize *a* logger called 'atomica'
    # prior to importing Atomica, and the user's custom logger won't be overwritten as long as it has
    # at least one handler already added. The use case was originally to suppress messages on import, but since
    # importing is silent now, it doesn't matter so much.
    debug_handler = logging.StreamHandler(sys.stdout)  # info_handler will handle all messages below WARNING sending them to STDOUT
    info_handler = logging.StreamHandler(sys.stdout)  # info_handler will handle all messages below WARNING sending them to STDOUT
    warning_handler = logging.StreamHandler(sys.stderr)  # warning_handler will send all messages at or above WARNING to STDERR

    debug_handler.setLevel(0)  # Handle all lower levels - the output should be filtered further by setting the logger level, not the handler level
    info_handler.setLevel(logging.INFO)  # Handle all lower levels - the output should be filtered further by setting the logger level, not the handler level
    warning_handler.setLevel(logging.WARNING)

    debug_handler.addFilter(type("ThresholdFilter", (object,), {"filter": lambda x, logRecord: logRecord.levelno < logging.INFO})())  # Display anything INFO or higher
    info_handler.addFilter(type("ThresholdFilter", (object,), {"filter": lambda x, logRecord: logRecord.levelno < logging.WARNING})())  # Don't display WARNING or higher

    debug_formatter = logging.Formatter("%(levelname)s {%(filename)s:%(lineno)d} - %(message)s")
    debug_handler.setFormatter(debug_formatter)

    logger.addHandler(debug_handler)
    logger.addHandler(info_handler)
    logger.addHandler(warning_handler)
    logger.setLevel("INFO")  # Set the overall log level

from .version import version as __version__, versiondate as __versiondate__, gitinfo as __gitinfo__

# Check scipy version
import scipy
import sciris as sc

if sc.compareversions(scipy.__version__, "1.2.1") < 0:
    raise Exception(f"Atomica requires Scipy 1.2.1 or later - installed version is {scipy.__version__}")

# Increase Framework performance by not calling garbage collection all the time
import pandas as pd

pd.set_option("mode.chained_assignment", None)

# Suppress openpyxl deprecation warnings
import warnings

warnings.filterwarnings(action="ignore", category=UserWarning, module=".*openpyxl")


# The Atomica user interface -- import from submodules
from .calibration import *
from .cascade import *
from .data import *
from .demos import *
from .framework import *
from .function_parser import *
from .migration import migrations, register_migration
from .model import *
from .optimization import *
from .parameters import *
from .plotting import *
from .programs import *
from .project import *
from .reconciliation import *
from .results import *
from .scenarios import *
from .system import *
from .utils import *
