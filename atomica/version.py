"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.24.3"
versiondate = "2021-03-25"
gitinfo = fast_gitinfo(__file__)
