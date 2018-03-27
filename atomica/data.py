# -*- coding: utf-8 -*-
"""
Atomica data file.
Sets out a structure to store context-specific databook-imported values relating to a model.
"""
from atomica.system import SystemSettings as SS

from atomica.system import applyToAllMethods, logUsage
from atomica.structure import CoreProjectStructure

@applyToAllMethods(logUsage)
class ProjectData(CoreProjectStructure):
    """ Object that details the transition-network structure of models generated by a project. """    
    def __init__(self, **kwargs):
        """ Initialize the data container. """
        super(ProjectData, self).__init__(structure_key = SS.STRUCTURE_KEY_DATA, **kwargs)