"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.25.16"
versiondate = "2022-10-04"
gitinfo = fast_gitinfo(__file__)
