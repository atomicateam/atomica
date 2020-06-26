"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo
version = "1.19.0"
versiondate = "2020-06-26"
gitinfo = fast_gitinfo(__file__)
