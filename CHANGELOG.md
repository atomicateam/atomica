# Changelog

This file records changes to the codebase grouped by version release. Unreleased changes are generally only present during development (relevant parts of the changelog can be written and saved in that section before a version number has been assigned)

## [1.21.2] - 2020-09-07

- Drop version constraint for `openpyxl` to support both version 2.5 and >2.5

## [1.21.1] - 2020-07-06to

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