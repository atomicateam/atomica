"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo
version = "1.18.5"
versiondate = "2020-05-25"
gitinfo = fast_gitinfo(__file__)
