# OPTIMA CORE CHANGELOG

All notable changes to this project are documented in this file.
The format adheres to Semantic Versioning.

## 0.3.1 (2018-01-04): Initial Framework Loading

Features
- Developed `importFromFile()` method to generate a dictionary of specifications for page-items in initial form.
- Developed a `ProjectFramework.semantics` attribute as a basis for linking user-supplied terms to specifications.

Edits
- Slimmed down FrameworkSettings notation by eliminating page keys for items and columns.

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
- Coded `FrameworkTemplateInstructions` class to specify how many of each page-item to produce in template.
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
- Created a 'tests' subfolder to store Optima Core unit tests.
- Created a 'frameworks' subfolder in 'tests' to contain framework file examples.

Edits
- Coded function `getOptimaCorePath()` to retrieve module installation path.
- The logging configuration file is now drawn from a fixed absolute path, regardless of application directory.
  The logging output file still ends up in the working path.

## 0.1.3 (2017-10-26): Initial Logging Framework

Features
- Created logging configuration file: logging.ini
- Generated a logger named 'optimacore' that prints debug statements to file.
  The file path can be varied with system setting variable `LOGGER_DEBUG_OUTPUT_PATH`.
- Updated `print` statements in `logUsage()` function as `logger.debug` calls.

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
- Coded class decorator `applyToAllMethods()` to apply a function across all methods of a class.
- Coded function decorator `logUsage()` to timestamp usage and measure elapsed time.
- Coded class `SystemSettings` and introduced flag for including date in timestamps.

## 0.1.0 (2017-10-17): Module Initialization

Features
- Created optimacore subfolder for the codebase.
- Created setup.py file (in the root optimacore directory) for optimacore installation.
  Heavily based on Optima HIV/TB.
- Created _version.py file to track version numbers and dates.
  Must be manually updated.
- Created \_\_init\_\_.py file for the module. 
  Heavily based on Optima HIV/TB.
- Added files for documentation: README.md and CHANGELOG.md