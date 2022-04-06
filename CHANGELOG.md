# Changelog

This file records changes to the codebase grouped by version release. Unreleased changes are generally only present during development (relevant parts of the changelog can be written and saved in that section before a version number has been assigned)

## [1.25.10] - 2022-04-06

- Fix bug in program fractional coverage where not all programs were constrained to a peak coverage of 1

## [1.25.7] - 2021-09-02

- Update calls to `sc.asd()` to be compatible with Sciris v1.2.3
- Update installation instructions to use `pip` rather than `setup.py` directly
- Improve handling of unspecified timescales in plotting routines

## [1.25.6] - 2021-07-26

- Unfreeze `pandas` dependency because they have fixed some regressions that affected `atomica`

## [1.25.5] - 2021-07-08

- Replace deprecated ``sc.SItickformatter`` usage
- Fix bug in program coverage overwrite timestep scaling. Coverage overwrites must always be provided in dimensionless units

## [1.25.4] - 2021-06-28

- Improved framework validation (informative errors raised in some additional cases)
- Calibrations can be loaded for mismatched frameworks/databooks - missing or extra entries will be skipped without raising an error

## [1.25.3] - 2021-06-03

- Implemented `Population.__contains__` to easily check whether variables are defined in a population
- Improved error message when plotting if requesting an output that is not defined in all populations

## [1.25.2] - 2021-05-26

- Add `ParameterSet.y_factors` as a property attribute to quickly access and set y-factors. 

## [1.25.1] - 2021-05-26

- Fix bug in `ProgramSet.remove_program()` - this function would previously raise an error

## [1.25.0] - 2021-05-06

- Added methods `ParameterSet.calibration_spreadsheet()`, `ParameterSet.save_calibration()` and `ParameterSet.load_calibration()` to allow saving calibration scale factors to spreadsheets that can be edited externally.

## [1.24.4] - 2021-05-06

- Fix plotting routines that were previously checking for missing timescales by checking for `None` values, and were thus missing `np.nan` values. This change was introduced around version 1.24.1 when framework validation now guarantees that the parameter timescale is a numeric type. This causes missing timescales to be populated with `nan` rather than `None`.
- Add library framework for malaria 

*Backwards-compatibility notes*

- Any code checking for missing timescales by checking for a `None` value should instead use `pd.isna()` to check for `nan` _or_ `None` values 

## [1.24.3] - 2021-03-25

- Fixes a bug in validation that ensures parameters in 'proportion' units cannot have a timescale. Previously frameworks with this error would incorrectly pass validation

## [1.24.1] - 2021-03-09

- Added validation of plots sheet in framework file
- Allow validating a framework multiple times
- Fix an edge case with timed transitions and split transition matrices

*Backwards-compatibility notes*

- In rare cases, if an existing framework file contains an error that was not previously detected, it may now produce an error when loaded. Such errors indicate problems in the framework that should be debugged as usual. 

## [1.23.4] - 2020-12-14

- Fix bug where program outcomes were not correctly applied if overwriting a function parameter that does not impact any transitions

## [1.23.3] - 2020-11-10

- Added `at.stop_logging()` and an optional `reset` argument to `at.start_logging()`

## [1.23.2] - 2020-10-22

- `at.ProgramSet` now stores all compartments with a `non_targetable` flag `in at.ProgramSet.comps` so that it can read/write workbooks for models that use coverage scenarios only. 

## [1.23.0] - 2020-10-22

- Exporting results now includes some time-aggregated quantities (summed over the year, rather than providing annualized values as of Jan 1) 

## [1.22.1] - 2020-09-11

- Added log level commands to `calibrate()` and `reconcile()` so that they respect `at.Quiet()` in the same way as `optimize()` already does.

## [1.22.0] - 2020-09-09

- Update documentation to support Sphinx 3
- Added `__all__` variables to modules so that module variables are no longer accidentally imported into the top-level Atomica module. 
- Renamed `defaults.py` module `demos.py`

*Backwards-compatibility notes*

- Code that relied on module variables being imported to Atomica may now fail. For example, `atomica.version` was accidentally set to the version string rather than referencing the `atomica.version` module. Such code should be updated by finding the relevant module variable and referencing that instead - for example, replacing `atomica.version` with `atomica.version.version`.
- Plotting settings are no longer imported to `atomica.settings` by accident - instead, they should be accessed via `atomica.plotting.settings` only. The same usage pattern applies to settings in other modules like calibration and cascades. 

## [1.21.3] - 2020-09-08

- `Project.calibrate()` no longer saves the new calibration to the project by default

*Backwards-compatibility notes*

- Add the explicit argument `save_to_project=True` to `calibrate()` to match previous behaviour

## [1.21.2] - 2020-09-07

- Drop version constraint for `openpyxl` to support both version 2.5 and >2.5

## [1.21.1] - 2020-07-06

- Add equality operator to `at.Timeseries`
- Support passing in arrays to the `at.TimeSeries` constructor

## [1.21] - 2020-06-27

- Refactored `ProgramSet.save(filename, folder)` to `ProgramSet.save(fname)` so that it now matches `ProjectData` and `ProjectFramework`
- `at.atomica_path` returns a `Path` object. The `trailingsep` argument has been removed as it is not relevant when returning a path. Legacy code may experience a `TypeError: unsupported operand type(s) for +: 'WindowsPath' and 'str'` or similar if the output of `at.atomica_path` is concatenated by addition. In general, this can be resolved by replacing `+` with `/` e.g.
`at.LIBRARY_PATH+'foo.xlsx'` becomes `at.LIBRARY_PATH/'foo.xlsx'`. 
- `at.parent_dir` returns a `Path` object
- `Project.load_databook` now supports passing in a `ProjectData` instance (as does the `Project` constructor) 
- Remove unused `num_interpops` argument from `Project.create_databook()`
- Add support for '>' in transition matrix to represent junction residual

## [1.19.0] - 2020-06-26

- Renamed `calibration.py:perform_autofit()` to `calibration.py:calibrate()`
- Added debug-level log messages, which can be viewed by setting `atomica.logger.setLevel(1)`
- Added changelog
