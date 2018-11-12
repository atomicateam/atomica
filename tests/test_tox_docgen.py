"""
Check whether automated model documentation template generation works
"""

import atomica as at

def test_docgen():
    F = at.ProjectFramework(at.LIBRARY_PATH + 'tb_framework.xlsx')

    tmpdir = at.atomica_path(['tests','temp'])
    at.generate_framework_doc(F, tmpdir + 'tb_doc.md')

if __name__ == '__main__':
    test_docgen()

