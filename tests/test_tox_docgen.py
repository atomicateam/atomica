"""
Check whether automated model documentation template generation works
"""

import os
import atomica as at
import sciris as sc
import pytest

testdir = at.rootdir / "tests"
tmpdir = testdir / "temp"
frameworks = list()
for f in at.LIBRARY_PATH.iterdir():
    if f.name.endswith("_framework.xlsx") and not f.name.startswith("~$"):
        frameworks.append(f)


@pytest.mark.parametrize("fname", frameworks)
def test_docgen(fname):
    F = at.ProjectFramework(fname)
    at.generate_framework_doc(F, fname=tmpdir / (fname.stem + "_doc.md"))


if __name__ == "__main__":
    for fname in frameworks:
        test_docgen(fname)
