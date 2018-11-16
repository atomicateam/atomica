"""
Check whether automated model documentation template generation works
"""

import atomica as at
import os

def test_docgen():
    F = at.ProjectFramework(at.LIBRARY_PATH + 'tb_framework.xlsx')

    testdir = at.parent_dir()
    tmpdir = os.path.join(testdir,'temp','')

    at.generate_framework_doc(F, tmpdir + 'tb_doc.md')

if __name__ == '__main__':
    test_docgen()

