"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.25.9"
versiondate = "2022-03-21"
gitinfo = fast_gitinfo(__file__)
