"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.10.0"
versiondate = "2019-03-07"
gitinfo = fast_gitinfo(__file__)
