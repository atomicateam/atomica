# -*- coding: utf-8 -*-
"""
Optima Core framework test file.
Tests the creation, importing and exporting of model framework files.
"""

import unittest

from optimacore.project import Project
from optimacore.framework_io import createFrameworkTemplate

import sys
import pprint

class EverythingTest(unittest.TestCase):
    """  """
    
    def setUp(self):
        self.proj = Project()
        self.framework_template_filepath = "./frameworks/framework_template.xlsx"
        self.framework_example_filepath = "./frameworks/framework_example.xlsx"
        self.databook_empty_filepath = "./databooks/databook_empty.xlsx"
        self.databook_template_filepath = "./databooks/databook_template.xlsx"

    def tearDown(self):
        self.proj = None

    def test_databook_empty_creation(self):
        """  """
        self.proj.createDatabook(databook_path = self.databook_empty_filepath)
        return None
        
    def test_framework_template_creation(self):
        """  """
        createFrameworkTemplate(framework_path = self.framework_template_filepath)
        return None
    
    def test_framework_template_import(self):
        """  """
        self.proj.getFramework().importFromFile(framework_path = self.framework_template_filepath)
        #pprint.pprint(self.proj.getFramework().specs)
        return None

    def test_databook_template_creation(self):
        """  """
        self.proj.createDatabook(databook_path = self.databook_template_filepath)
        return None
    
    def test_framework_example_import(self):
        """  """
        self.proj.getFramework().importFromFile(framework_path = self.framework_example_filepath)
        #pprint.pprint(self.proj.getFramework().specs)
        return None
        
if __name__ == '__main__':
    unittest.defaultTestLoader.sortTestMethodsUsing = None   # Disable test case sorting so that state persists in definitional order.
    unittest.main()