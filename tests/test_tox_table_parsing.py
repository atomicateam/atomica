# Test that parameter derivatives work
# Indirectly test that frameworks with no compartments work

import numpy as np
import atomica as at
import os

testdir = at.rootdir / "tests"  # Must be relative to current file to work with tox


def test_table_parsing():
    F = at.ProjectFramework(testdir / "test_table_parsing.xlsx")


def test_table_parsing2():
    F = at.ProjectFramework(testdir / "test_table_parsing2.xlsx")

    assert len(F.sheets["extra 0"]) == 2
    assert len(F.sheets["extra 0"][0]) == 2
    assert len(F.sheets["extra 0"][1]) == 2

    assert len(F.sheets["extra 1"]) == 1
    assert F.sheets["extra 1"][0].empty
    assert F.sheets["extra 1"][0].columns.tolist() == ["heading 1", "heading 2"]

    assert len(F.sheets["extra 2"]) == 3
    assert len(F.sheets["extra 2"][0]) == 0
    assert len(F.sheets["extra 2"][1]) == 1
    assert len(F.sheets["extra 2"][2]) == 0

    assert len(F.sheets["extra 3"]) == 1
    assert len(F.sheets["extra 3"][0]) == 1

    assert len(F.sheets["extra 4"]) == 2
    assert len(F.sheets["extra 4"][0]) == 0
    assert len(F.sheets["extra 4"][1]) == 1


if __name__ == "__main__":
    # test_table_parsing()
    test_table_parsing2()
