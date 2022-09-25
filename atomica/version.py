"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.25.15"
versiondate = "2022-09-26"
gitinfo = fast_gitinfo(__file__)
