"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo
version = "1.23.1"
versiondate = "2020-09-11"
gitinfo = fast_gitinfo(__file__)
