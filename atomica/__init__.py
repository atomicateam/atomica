# -*- coding: utf-8 -*-
"""
Atomica module initialization file.

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
from .version import version, versiondate

# Print the license.
atomica_license = 'Atomica %s (%s) -- (c) the Atomica development team' % (version, versiondate)
print(atomica_license)

# Import things for the user
from . import ui
