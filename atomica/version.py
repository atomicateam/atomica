"""
Atomica version file.

Standard location for module version number and date.
"""

try:
    import sciris as sc
    gitinfo = sc.gitinfo(__file__, verbose=False)
except ImportError as E:
    gitinfo = f'Sciris import failed; git info unavailable: {E}'
    print(gitinfo)

version = "1.12.1"
versiondate = "2019-08-20"


