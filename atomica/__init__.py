"""
Atomica root module

The Atomica module is the entry point for running simulations and performing analysis
using Atomica. It consists of the following submodules:

    .. autosummary::
        :toctree: _autosummary

        calibration
        cascade
        data
        defaults
        excel
        framework
        migration
        model
        optimization
        parameters
        function_parser
        plotting
        programs
        project
        reconciliation
        results
        scenarios
        system
        utils

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
logger = logging.getLogger('atomica')

if not logger.hasHandlers():
    # Only add handlers if they don't already exist in the module-level logger
    # This means that it's possible for the user to completely customize *a* logger called 'atomica'
    # prior to importing Atomica, and the user's custom logger won't be overwritten as long as it has
    # at least one handler already added. The use case was originally to suppress messages on import, but since
    # importing is silent now, it doesn't matter so much.
    h1 = logging.StreamHandler(sys.stdout) # h1 will handle all messages below WARNING sending them to STDOUT
    h2 = logging.StreamHandler(sys.stderr) # h2 will send all messages at or above WARNING to STDERR

    h1.setLevel(0)  # Handle all lower levels - the output should be filtered further by setting the logger level, not the handler level
    warning_level = logging.WARNING
    h1.addFilter(type("ThresholdFilter", (object,), {"filter": lambda x, logRecord: logRecord.levelno < warning_level})())  # Display anything less than a warning
    h2.setLevel(logging.WARNING)

    logger.addHandler(h1)
    logger.addHandler(h2)
    logger.setLevel('INFO') # Set the overall log level

from .version import version as __version__, versiondate as __versiondate__, gitinfo as __gitinfo__

# Check scipy version
import scipy
import sciris as sc
if sc.compareversions(scipy.__version__, '1.2.1') < 0:
    raise Exception(f'Atomica requires Scipy 1.2.1 or later - installed version is {scipy.__version__}')

# Increase Framework performance by not calling garbage collection all the time
import pandas as pd
pd.set_option('mode.chained_assignment', None)

# The Atomica user interface -- import from submodules
from .framework import *
from .project import *
from .calibration import *
from .scenarios import *
from .defaults import *
from .plotting import *
from .programs import *
from .reconciliation import *
from .optimization import *
from .cascade import *
from .results import *
from .migration import migrations, register_migration
from .utils import *
from .system import *
