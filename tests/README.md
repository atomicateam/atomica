## Automated testing

The tests in this directory with file names starting with `test_tox_*`  will automatically be run by tox/pytest.

We cannot assume that these files are being run directly from the repository, if Atomica has been installed
via pip. If only installed via pip, then Atomica won't exist in this repo folder and `atomica_path` will refer
to the `site-packages` directory instead of the repo. Therefore, inside the test, we must use 

- `au.LIBRARY_PATH` to locate the library `xlsx` files
- `at.parent_dir()` inside the test script, to locate the test dir

In practice, it can be useful to simply define the following two variables at the start of a test script:

```python
testdir = at.rootdir/'tests'
tmpdir = testdir / "temp"
```