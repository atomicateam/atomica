# Test that parameter derivatives work
# Indirectly test that frameworks with no compartments work

import numpy as np
import atomica as at
import os


def test_table_parsing():

    testdir = at.parent_dir()  # Must be relative to current file to work with tox

    F = at.ProjectFramework(testdir / "test_table_parsing.xlsx")


if __name__ == "__main__":
    test_table_parsing()
