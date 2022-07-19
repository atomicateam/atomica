"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.25.13"
versiondate = "2022-07-19"
gitinfo = fast_gitinfo(__file__)
