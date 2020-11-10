"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.23.3"
versiondate = "2020-11-10"
gitinfo = fast_gitinfo(__file__)
