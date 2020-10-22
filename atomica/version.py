"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo
version = "1.23.2"
versiondate = "2020-10-22"
gitinfo = fast_gitinfo(__file__)
