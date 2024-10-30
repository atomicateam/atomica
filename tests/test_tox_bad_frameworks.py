# This test checks that the error handling code is OK
# One problem with only testing valid inputs is that typos in error handling code
# (e.g. badly formatted messages) only happen in production. Thus we just test a subset
# of bad inputs here to make sure the correct error is raised

import atomica as at
import pytest

testdir = at.rootdir / "tests"  # Must be relative to current file to work with tox
fdir = testdir / "bad_frameworks"

# List available models based on which framework files exist
framework_files = list()
for f in fdir.iterdir():
    if f.name.endswith(".xlsx") and not f.name.startswith("~$"):
        framework_files.append(f)


@pytest.mark.parametrize("framework_file", framework_files)
def test_bad_framework(framework_file):
    with pytest.raises(at.InvalidFramework):
        at.ProjectFramework(framework_file)


if __name__ == "__main__":
    for framework_file in framework_files:
        print("Checking %s" % (framework_file))
        test_bad_framework(framework_file)
