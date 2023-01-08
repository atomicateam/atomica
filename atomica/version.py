"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.25.18"
versiondate = "2023-01-09"
gitinfo = fast_gitinfo(__file__)
