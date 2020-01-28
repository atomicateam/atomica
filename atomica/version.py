"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo
version = "1.17.1"
versiondate = "2020-01-28"
gitinfo = fast_gitinfo(__file__)
