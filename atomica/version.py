"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo
version = "1.14.0"
versiondate = "2019-08-01"
gitinfo = fast_gitinfo(__file__)
