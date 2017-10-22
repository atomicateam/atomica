# OPTIMA CORE CHANGELOG

All notable changes to this project are documented in this file.
The format adheres to Semantic Versioning.

## 0.1.2 (2017-10-22): Validation Framework

Features
- Coded decorator `accepts()` along with `ArgumentValidationError`.
  This ensures method/function arguments have a specified type.

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