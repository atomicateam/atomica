# Run various framework-related tests

import atomica as at
import os

def test_framework_blank_sheet():
    testdir = at.parent_dir()
    tmpdir = os.path.join(testdir, 'temp', '')
    F_path = testdir + 'framework_blank_sheet.xlsx'
    F = at.ProjectFramework(F_path)

if __name__ == '__main__':
    test_framework_blank_sheet()
