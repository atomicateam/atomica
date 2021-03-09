"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.24.1"
versiondate = "2021-03-09"
gitinfo = fast_gitinfo(__file__)
