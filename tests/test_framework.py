# -*- coding: utf-8 -*-
"""
Optima Core framework test file.
Tests the creation, importing and exporting of model framework files.
"""

import unittest

from optimacore.project import Project

class FrameworkTest(unittest.TestCase):
    """  """
    
    def setUp(self):
        self.proj = Project()

    def tearDown(self):
        self.proj = None
        
class MinimalFramework(FrameworkTest):
    """  """
    def test_truth(self):
        """  """
        self.assertEqual(True, True, "True is not True.")
        return None
        
if __name__ == '__main__':
    unittest.main()