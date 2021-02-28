"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.24.0"
versiondate = "2020-12-14"
gitinfo = fast_gitinfo(__file__)
