"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.25.14"
versiondate = "2022-08-16"
gitinfo = fast_gitinfo(__file__)
