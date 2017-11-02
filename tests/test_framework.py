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

    def tearDown(self):
        self.proj = None
        
class MinimalFramework(FrameworkTest):
    """  """
    def test_creation(self):
        """  """
        createFrameworkTemplate("./frameworks/framework_template.xlsx")
        return None
        
if __name__ == '__main__':
    unittest.main()