# -*- coding: utf-8 -*-
"""
Optima Core framework test file.
Tests the creation, importing and exporting of model framework files.
"""

import unittest

from optimacore.project import Project
from optimacore.framework_io import createFrameworkTemplate

class FrameworkTest(unittest.TestCase):
    """  """
    
    def setUp(self):
        self.proj = Project()
        self.template_filepath = "./frameworks/framework_template.xlsx"
        self.example_filepath = "./frameworks/framework_example.xlsx"

    def tearDown(self):
        self.proj = None
        
    def test_creation(self):
        """  """
        createFrameworkTemplate(self.template_filepath)
        return None
    
    def test_import_template(self):
        """  """
        self.proj.getFramework().importFromFile(self.template_filepath)
        print(self.proj.getFramework().specs)
        return None
    
    def test_import_example(self):
        """  """
        self.proj.getFramework().importFromFile(self.example_filepath)
        print(self.proj.getFramework().specs["comp"])
        return None
        
if __name__ == '__main__':
    unittest.main()