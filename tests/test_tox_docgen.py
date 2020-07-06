"""
Check whether automated model documentation template generation works
"""

import os
import atomica as at
import sciris as sc


def test_docgen():
    F = at.ProjectFramework(at.LIBRARY_PATH / 'tb_framework.xlsx')

    testdir = at.parent_dir()
    tmpdir = testdir/'temp'
    fname = sc.makefilepath(filename='tb_doc.md', folder=tmpdir)

    at.generate_framework_doc(F, fname=fname)


if __name__ == '__main__':
    test_docgen()
