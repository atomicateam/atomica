"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.24.4"
versiondate = "2021-05-06"
gitinfo = fast_gitinfo(__file__)
