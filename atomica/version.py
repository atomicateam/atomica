"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.25.17"
versiondate = "2022-10-05"
gitinfo = fast_gitinfo(__file__)
