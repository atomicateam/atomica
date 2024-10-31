# Changelog

This file records changes to the codebase grouped by version release. Unreleased changes are generally only present during development (relevant parts of the changelog can be written and saved in that section before a version number has been assigned)

## [1.XX.0] - 2024

- `ProjectSettings` now computes the simulation time vector in a more robust way to reduce edge cases where the reported `sim_dt` doesn't match the input.
- `ParameterSet.load_calibration()` now clears any existing initialization if the calibration being loaded does not contain an initialization. Previously, the absence of an 'initialization' sheet in the calibration would be treated as not making any change to the initialization. This could cause calibrations to become mixed if a calibration without an initialization was loaded after a calibration with an initialization. Now, a missing initialization sheet is treated as meaning 'no initialization' and any existing initialization will be cleared when the calibration is loaded. 
- `Project.load_databook()` will no longer populate `Project.databook` when a `ProjectData` instance is supplied rather than a spreadsheet. The intention of `Project.databook` as opposed to `Project.data.to_spreadsheet()` is that the original databook may contain comments or other content that is not preserved when the databook is loaded into a `ProjectData` instance. Therefore, `Project.databook` serves as a record of the original inputs. However, in previous versions of Atomica, if a `ProjectData` instance was provided rather than a spreadsheet, `ProjectData.to_spreadsheet()` would be used to populate `Project.databook`. For large databooks, this can be computationally expensive and particularly affect the use case of passing in a preloaded databook to improve performance. Since the conversion of the `ProjectData` to a spreadsheet upon loading offers no functional difference to creating the spreadsheet from `Project.data` when required, Atomica no longer performs this conversion upfront.

*Backwards-compatibility notes*

- In some edge cases, the simulation time points in the output may be different. In those cases, the difference between simulation time points in the model output would not have matched the model input, although the correct time step would have been used to calculate parameter values. In these cases, there may be an extra time point in the model output. Re-running the model should produce results that are close to the original results.
- If accessing `Project.databook`, in some cases this may now be `None` rather than an `sc.Spreadsheet()`. If that occurs, `Project.data.to_spreadsheet()` should be used to produce an equivalent spreadsheet. 

## [1.28.7] - 2024-10-29

- If aggregating characteristics with a denominator, weighted aggregations use the denominator of the quantity rather than the total population size to perform the weighting. This can be useful for quantities that are proportions of things other than the population size e.g., proportion of active infections that are diagnosed
- If aggregating characteristics with a denominator, weighted aggregation will be used by default (rather than 'average')
- Output aggregation of durations now uses 'sum' instead of 'average' by default
- If no aggregation method is specified, the aggregation method will now be selected separately for each output
- Population aggregation of non-number units now uses 'weighted' by default rather than 'average'

*Backwards-compatibility notes*

- Results obtained when aggregating characteristics with a denominator using the 'weighted' method will change. To reproduce the previous results, it is necessary to perform the population size weighting manually by removing the aggregation, then extracting the population sizes, and using those to aggregate the outputs. This is considered to be a rare use case because the updated result is a more useful weighting compared to the previous result.
- Results obtained when aggregating characteristics with a denominator _without_ explicitly specifying a method will change, because 'weighted' aggregation is now used by default. 

## [1.28.6] - 2024-07-12

- Support entering `'total'` as the population name in auto-calibration measurables to calibrate aggregated values across populations in the model to aggregate values entered in the databook under a 'Total' population

## [1.28.5] - 2024-06-28

- Enable automated calibration of transfers and updated documentation to cover this feature

## [1.28.4] - 2024-05-27

- Added an option to save initial compartment sizes inside a `ParameterSet`. Importantly, this saved representation allows setting the initial _subcompartment_ sizes for a `TimedCompartment`. It therefore offers the possibility of initializing the model in a steady state computed from a previous simulation run, that would not be possible to initialize conventionally because standard initialization uniformly distributes people into the subcompartments of a timed compartment.  
- Added `ParameterSet.make_constant` to facilitate constructing copies of `ParameterSet` instances that are constant over time.

## [1.28.3] - 2024-05-16

- Updated `at.Project()` to explicitly take in the settings arguments for `sim_start`, `sim_end`, and `sim_dt`. These are now applied after databooks are loaded, fixing a bug where these arguments would get overwritten when loading the databook.

## [1.28.2] - 2024-04-05

- `at.calibrate` now supports passing any additional arguments into the optimization function e.g., `sc.asd` allowing additional options for customizing the optimization. 

## [1.28.1] - 2024-02-05

- Updated various Pandas operations to improve compatibility with Pandas 2.2.0
- Replaced 'probability' units with 'rate' units in many of the library example frameworks
- For many of those parameters, also removed the maximum upper limit value of 1 as such parameters should not generally have this limit
- Numerical indices are no longer inadvertently added to framework dataframes (compartments, characteristics, parameters, and interactions). 

*Backwards-compatibility notes*

- Removing the upper limit of 1 on parameters that were in 'probability' units may change the output of models using the library example frameworks. The updated results should be considered more realistic because the 'probability' parameters were actually behaving as rates, and therefore should not have had an upper limit imposed in the first place.

## [1.28.0] - 2023-12-03

- Added ability to provide a row in the databook for 'all' (or 'All') populations, as shorthand for entering the same value in every population. This option serves as a fallback value if population-specific values have also been provided.
- Added optional `n_cols` argument to `at.plot_series` to allow series plots to appear in a single figure using subplots

## [1.27.0] - 2023-11-07

- `ProjectData.get_ts()` now correctly handles retrieving timeseries data from interactions and transfers with underscores in their name
- `ProjectData` now validates that transfer and interaction names are unique
- Improved handling Excel cell references if population names and framework variable full names overlap
- Added ability to place '#ignore' directives in places other than the first column of a spreadsheet, to selectively ignore parts of lines. Added documentation to cover this functionality.
- Fixed a bug where cells that were documented as being ignored actually populated content

## [1.26.7] - 2023-10-20

- Warning messages now print the file/line they were generated from
- Added extra documentation on parallels with explicit ODE compartment models

## [1.26.6] - 2023-09-26

- Improve error message if calibration file contains duplicate entries

## [1.26.5] - 2023-08-29

- Transfer parameters no longer raise an error if specified in 'Duration' units
- Transfer parameters in rate units are no longer limited to a maximum value of 1

*Backwards-compatibility notes*

- Transfers in rate units with a databook value greater than 1 were internally limited to a value of 1 previously. Models with such transfers will produce different results. This is expected to be uncommon, as most models have transfer parameters with values less than 1.

## [1.26.4] - 2023-08-25

- Some numerical errors in `model.py` (particularly relating to errors/warnings in parameter functions) are now caught and printed with more informative error messages. 

## [1.26.3] - 2023-07-18

- Change the table parsing routine again to resolve further edge cases, restore removal of leading and trailing spaces from cells in the framework, and improve performance. The original `None` behaviour has consequently been restored (undoing the change in 1.26.2) although it is still recommended that `pandas.isna()` is used instead of checking for `None`.

## [1.26.2] - 2023-06-07

- Switch to `sc.gitinfo` from Sciris. The git commit hash recorded in Atomica objects will now only contain the first 7 characters. Code that uses `at.fast_gitinfo` should use `sc.gitinfo` instead.
- Improve robustness of the table parsing routine used by `at.Framework`. In some cases, the data type of empty cells is now `NaN` rather than `None`. This affects any code that either checks for the contents being `None` or which relies on `None` being treated as `False` in conditional statements e.g., `if <contents>:`.  Affected code should instead use `pandas.isna()` which handles `None`, `NaN`, and `pd.NA`. 

## [1.26.1] - 2023-05-29

- Improve numerical robustness of `SpendingPackageAdjustment` under certain edge cases
- Fix bug in cumulative plot labelling that could result in the axis label containing more than one 'Cumulative' prefix

## [1.26.0] - 2023-05-22

- Allow initializing compartments and characteristics with a 0 value by setting a default value without needing to add the quantity to the databook. This simplifies initialization of models that have large numbers of compartments that should always be initialized with a 0 value, without needing to add many databook entries or extra initialization characteristics. 

## [1.25.18] - 2023-01-09

- Allow framework variables with single characters (previously, all code names had to be at least two characters long)
- Improve handling of automatic number of workers if a number is provided instead of a collection of inputs
- Add `optim_args` argument to `at.optimize` which allows arguments to be passed to optimization functions such as ASD

## [1.25.17] - 2022-10-05

- The "Databook pages" sheet in the framework is now optional, if a compartment, characteristic or parameter has a "Databook page" that does not appear in the "Databook pages" sheet (or if the "Databook pages" sheet is missing entirely) then the specified page will be created with the specified name as both the code name and full name. As the "Databook pages" sheet is created and populated with these names during framework validation, downstream code expecting the sheet to exist should not require any changes.

## [1.25.15] - 2022-09-26

- Fix array size error for junctions belonging to a duration group (some otherwise valid frameworks previously raised an error when running the model)
- Fix missing cells/NaNs in equivalent spending caused by numerical precision errors

## [1.25.14] - 2022-08-16

- Unpin `matplotlib` version in `setup.py`

## [1.25.13] - 2022-07-19

- Improve exported results link labelling for transfers

## [1.25.12] - 2022-07-15

- Implemented variable total spend in `SpendingPackageAdjustment`
- Optimized performance for `SpendingPackageAdjustment` if proportions are fixed by adding a `fix_props` flag that skips adding `Adjustables` for the proportions
- Improved framework validation robustness when dataframe cells contain NA-like values (`np.nan` or `pd.NA`) instead of just `None`   

## [1.25.11] - 2022-07-05

- Program number eligible defaults to 0 if target compartments are missing (rather than raising a key error)
- `ProgramSet` spreadsheet constructor is now a class method to allow inheritance
- Fixed bug where program overwrites that impact a transition parameter via at least one intermediate parameter did not impact outcomes
- Improved `SpendingPackageAdjustment` performance although varying total spend is not yet supported 

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
