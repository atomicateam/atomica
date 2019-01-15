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
from datetime import datetime
import logging
logger = logging.getLogger('atomica')

if not any([isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in logger.handlers]):
    # Only add handlers if they don't already exist in the module-level logger
    # User can still add a file handler to the
    h1 = logging.StreamHandler(sys.stdout)
    h2 = logging.StreamHandler(sys.stderr)
    # h2 sends warnings and above to STDERR, while h1 sends everything else to stdout
    h1.setLevel(0)  # Handle all
    warning_level = logging.WARNING
    h1.addFilter(type("ThresholdFilter", (object,), {"filter": lambda x, logRecord: logRecord.levelno < warning_level})())  # Display anything less than a warning
    h2.setLevel(logging.WARNING)

    logger.addHandler(h1)
    logger.addHandler(h2)

from .version import version as __version__, versiondate as __versiondate__
logger.critical('Atomica %s (%s) -- (c) the Atomica development team' % (__version__, __versiondate__))  # Log with the highest level
logger.critical(datetime.now())

try:
    from .version import gitinfo as __gitinfo__
    logger.critical('git branch: %s (%s)' % (__gitinfo__['branch'], _gitinfo__['hash']))
except:
    pass

# Finally, set default output level to INFO
logger.setLevel('INFO')

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
from .migration import *
from .utils import *
from .system import *
