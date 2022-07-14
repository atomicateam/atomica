"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.25.12"
versiondate = "2022-07-15"
gitinfo = fast_gitinfo(__file__)
