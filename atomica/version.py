"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo
version = "1.18.0"
versiondate = "2020-02-02"
gitinfo = fast_gitinfo(__file__)
