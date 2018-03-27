### Test instructions

The script `testall.py` will run every script in the `scripts` folder. A report will be printed showing `stdout` for each test, and the traceback for any errors that occurred. 

At the top of the script, some folder paths such as `testdir` and `tempdir` are defined. These can be used in the scripts. The `tempdir` will be deleted at the end of the test run if all tests completed successfully.

Lastly, `testall.py` can take an optional argument of a filename to run only that script. For example

- `python testall.py` will run all tests
- `python testall.py loadframework.py` will only run `loadframework.py`