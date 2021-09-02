"""
Atomica version file.

Standard location for module version number and date.
"""

from .utils import fast_gitinfo

version = "1.25.7"
versiondate = "2021-09-02"
gitinfo = fast_gitinfo(__file__)
