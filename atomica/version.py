"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.25.1"
versiondate = "2021-05-26"
gitinfo = fast_gitinfo(__file__)
