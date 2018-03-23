# -*- coding: utf-8 -*-
"""
Created on Fri Mar 23 16:37:15 2018

@author: robynstuart
"""

from core import Framework
from optima import odict
from numpy import array

F = Framework()
F.compartments = ['S','I','R']
F.transitions = array([[1,1,0],[0,1,1],[0,0,1]])
F.characteristics = odict([('All infected',['S','I']),
                           ('All people',['S','I','R'])])
                           
