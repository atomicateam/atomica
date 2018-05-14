# ATOMICA CHANGELOG

All notable changes to this project are documented in this file.
The format adheres to Semantic Versioning.

## 0.6.1 (2018-05-11): High-order Program Processes

Features
- Without settling on a programs structure yet, wrapper processes are established.
  These include budget scenarios and optimizations.

Edits
- PEP8 compliance worked towards in the majority of the codebase.

## 0.6.0 (2018-04-27): Establishing Complex Workflow

Features
- A new file is set up to port and test workflow from Optima TB: test_tb.py
- Custom databook pages enabled in the framework file, plus a bonus hidden metadata page.
- Time vector management updated, with ProjectSettings in charge of simulation time vectors.
  WorkbookInstructions controls data time ranges.
- Calibration, autocalibration and parameter scenarios established.

Edits
- Stylistic changes in the process of being applied, primarily taking method/function names to snake case.

## 0.5.1 (2018-04-11): Improved Model Construction

Features
- Framework files now have a databook ordering column, with a value of '-1' suppressing table construction in databooks.
- Compartments can be associated with time-dependent values, just like characteristics.
- Parameters can be described as functions of other parameters, characteristics and compartments.
  These are dynamically updated during a model run.
- Databook values can now be attributed with quantity types, a.k.a. formats, with inter-conversions enabled.

## 0.5.0 (2018-03-29): Drafting Simulation Workflow

Features
- Very unrefined batches of code from Optima HIV/TB have been ported across.
  This tentatively allows simulation workflow, i.e. conversion from data to parameter set and subsequent model processing.

Edits
- Codebase has been named Atomica, with code history edited to reflect this..
- Many utility functions are currently imported from Sciris.

## 0.4.2 (2018-03-14): Workbook Interface Refinement

Edits
- Forced initialization of attribute structure for any item in structure specifications dictionary.
  In turn, for validation, removed functionality that averts missing item type and attributes by creating them on the fly.

## 0.4.1 (2018-03-08): Workbook Matrix Interfacing

Features
- Developed table IO for connection matrices.

Edits
- Split workbook IO file into two for import and export so as to make code more manageable.
  Introduced another workbook utilities file for common functionality.

## 0.4.0 (2018-03-06): Databook Time-Dependent Value Interfacing

Features
- Developed a base structure for both `ProjectData` and `ProjectFramework` named `CoreProjectStructure` in: structure.py
  Fleshed out the semantics dictionary for easier access to specifications.
- Developed table IO for time-dependent values, including a TimeSeries object.

Edits
- Unnecessary files have been deleted due to workbook IO consolidation.
- `ContentType` classes have been refactored and renamed.

## 0.3.4 (2018-02-13): Workbook Construction Consolidation

Features
- Templated out a `ProjectData` structure to store model values for a corresponding `ProjectFramework` structure.

Edits
- Major changes applied, with `FrameworkSettings` and `DataSettings` now deriving from new class `BaseStructuralSettings`.
  Many features from previous versions have been upturned during this refactoring, such as the GUI process.
- Consolidated workbook IO into file: workbook.py
- Classes have been introduced as key wrappers to denote table type and content type during workbook construction.
- Detail-column tables in a framework file allow values to be extended across columns, but no longer allows this for rows.

## 0.3.3 (2018-02-01): Basic Databook Items

Features
- Improved wrapped `createDatabookFunc()` to produce a list of populations in a databook.
- Characteristics and parameters are also listed out.

Edits
- Pulled Excel-based functionality and format variables into file: excel.py
  Variables specifically are stored in object `ExcelSettings`.

## 0.3.2 (2018-01-16): Initial Databook Construction

Features
- Templated `Project.create_databook()` method to construct an Excel databook spreadsheet from the current loaded `Project.framework`.
- Coded `DatabookInstructions` class to specify how many of each item, e.g. population and program, to produce in a databook.
- Hard-coded the keys for the databook file via a `DataSettings` class.
  Set up a configuration-loading decorator and class method for `DataSettings`.
  This loading is done upon initial importing.
- Created sub-GUI class named `GUIDatabookCreation` to generate databooks from project frameworks.
  The user can select a number of databook items to create, which updates a GUI-attached `DatabookInstructions` object on the fly.

Edits
- Overhauled semantics to distinguish between a `ProjectFramework` 'item' and its 'item type' detailed in `FrameworkSettings`.
- Moved configuration-loading functionality into separate file: parser.py
  This allows it to be used by both `FrameworkSettings` and `DataSettings`.

## 0.3.1 (2018-01-11): Initial Framework Loading

Features
- Developed `importFromFile()` method to generate a dictionary of specifications for page-items in initial form.
- Ensured that item specifications other than 'name' and 'label' can be drawn from subsequent appropriate rows and columns.
- Developed a `ProjectFramework.semantics` attribute as a basis for linking user-supplied terms to specifications.

Edits
- Slimmed down FrameworkSettings notation by eliminating page keys for items and columns.
- Made codebase compatible with Python3 by importing module `six` and removing `exec` functions.

## 0.3.0 (2017-11-29): Initial GUI Construction

Features
- Created a file for implementing a graphical user interface: gui.py
  This is manually run via a script in the 'tests' directory: run_gui.py
- Created a `GUIDemo` widget and a sub-GUI class named `GUIFrameworkTemplate` to generate template frameworks.
  The user can select a number of page-items to create, which updates a GUI-attached `FrameworkTemplateInstructions` object on the fly.
- Began initial coding for `ProjectFramework` method `importFromFile()`.
  This is simultaneously tested with template creation by: test_framework.py

## 0.2.3 (2017-11-27): Improved Framework Templating Pre-filling

Features
- Coded `FrameworkTemplateInstructions` class to specify how many of each page-item to produce in the template.
- Hard coded standard page-item definitions in terms of using names and labels.

Edits
- Made page columns tagged by type in the `FrameworkSettings` class.
- Moved `FrameworkSettings` and associated functions to a new file: framework_settings.py

## 0.2.2 (2017-11-23): Initial Framework Templating Pre-filling

Features
- Began initial pre-filling functionality for framework file template.
- Hard-coded the keys for the framework template file via a `FrameworkSettings` class.
  Set up a configuration-loading decorator and class method for `FrameworkSettings`.
  This loading is done upon initial importing.
- Hard-coded structures for default page-items.
- Coded up an initial generator for these via `createFrameworkPageItem()`.

Edits
- Reorganized: framework_io.py

## 0.2.1 (2017-11-20): Initial Framework File Templating

Features
- Created project framework input/output functions file: framework_io.py
- Coded initial form of `createFrameworkTemplate()` for creating a framework file with commented headers.
- Created basic framework semantics configuration file: template_framework.ini
         
Edits
- Enforced that the 'decorator' module must be downloaded as part of 'setup.py' installation.
  This fixes a bug in propagating function/method signatures up chains of decorators.    
         
## 0.2.0 (2017-10-30): Project Framework Design

Features
- Created project framework stub file: framework.py
- Created a 'tests' subfolder to store Atomica unit tests.
- Created a 'frameworks' subfolder in 'tests' to contain framework file examples.

Edits
- Coded function `getAtomicaPath()` to retrieve module installation path.
- The logging configuration file is now drawn from a fixed absolute path, regardless of application directory.
  The logging output file still ends up in the working path.

## 0.1.3 (2017-10-26): Initial Logging Framework

Features
- Created logging configuration file: logging.ini
- Generated a logger named 'atomica' that prints debug statements to file.
  The file path can be varied with system setting variable `LOGGER_DEBUG_OUTPUT_PATH`.
- Updated `print` statements in `log_usage()` function as `logger.debug` calls.

Edits
- Removed date-inclusion system variable as that is currently in the domain of logging.ini.

## 0.1.2 (2017-10-23): Initial Validation Framework

Features
- Coded decorator `accepts()` along with `ArgumentTypeError`.
  This ensures method/function arguments have specified types.
- Coded decorator `returns()` along with `ReturnTypeError`.
  This ensures method/function returns have a specified type.

## 0.1.1 (2017-10-22): Systematic Decorator Framework

Features
- Created class stub files: porfolio.py and project.py
- Fleshed out `Portfolio` and `Project` with a `name` attribute.
  Methods `setName` and `getName` included. 
- Created system.py file for module-wide 'static' variables and functions.
- Coded class decorator `apply_to_all_methods()` to apply a function across all methods of a class.
- Coded function decorator `log_usage()` to timestamp usage and measure elapsed time.
- Coded class `SystemSettings` and introduced flag for including date in timestamps.

## 0.1.0 (2017-10-17): Module Initialization

Features
- Created atomica subfolder for the codebase.
- Created setup.py file (in the root atomica directory) for atomica installation.
  Heavily based on Optima HIV/TB.
- Created _version.py file to track version numbers and dates.
  Must be manually updated.
- Created \_\_init\_\_.py file for the module. 
  Heavily based on Optima HIV/TB.
- Added files for documentation: README.md and CHANGELOG.md