"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.26.0"
versiondate = "2023-05-22"
gitinfo = fast_gitinfo(__file__)
