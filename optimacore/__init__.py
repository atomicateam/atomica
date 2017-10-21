# -*- coding: utf-8 -*-
"""
Optima Core module initialization file.
The module can be imported in the following manner:

    from optimacore import Project
    or
    import optimacore as op
    or
    from optimacore import *

License:

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Determine the version number and date of the module.
from ._version import __version__, __updated__

# Print the license.
optima_license = 'Optima Core %s (%s) -- (c) Optima Consortium' % (__version__, __updated__)
print(optima_license)