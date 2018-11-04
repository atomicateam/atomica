These tests will automatically be run by tox/pytest

We cannot assume that these files are being run directly from the repository, if Atomica has been installed
via pip. If only installed via pip, then Atomica won't exist in this repo folder and `atomica_path` will refer
to the `site-packages` directory instead of the repo. Therefore, inside the test, we must do

    au.LIBRARY_PATH - to locate the library xlsx files
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) - to locate the `tests` directory
