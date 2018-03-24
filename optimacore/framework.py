# -*- coding: utf-8 -*-
"""
Optima Core project-framework file.
Contains all information describing the context of a project.
This includes a description of the Markov chain network underlying project dynamics.
"""
from optimacore.system import SystemSettings as SS
from optimacore.structure_settings import FrameworkSettings as FS
from optimacore.structure_settings import DatabookSettings as DS

from optimacore.system import applyToAllMethods, logUsage
from optimacore.structure import CoreProjectStructure
from optimacore.structure_settings import TimeDependentValuesEntry
from optimacore.workbook_import import readWorkbook
from optimacore.workbook_export import writeWorkbook

#from collections import OrderedDict
#from copy import deepcopy as dcp
from optima import odict, dcp # TEMPORARY IMPORTS FROM OPTIMA HIV


@applyToAllMethods(logUsage)
class ProjectFramework(CoreProjectStructure):
    """ The object that defines the transition-network structure of models generated by a project. """
    
    def __init__(self, filename=None, **kwargs):
        """ Initialize the framework. """
        super(ProjectFramework, self).__init__(structure_key = SS.STRUCTURE_KEY_FRAMEWORK, **kwargs)
        if filename:
            readWorkbook(workbook_path=filename, framework=self, data=None, workbook_type=SS.STRUCTURE_KEY_FRAMEWORK)


    def completeSpecs(self):
        """
        A method for completing specifications that is called at the end of a file import.
        This delay is because some specifications rely on other definitions and values existing in the specs dictionary.
        """
        # Construct specifications for constructing a databook beyond the information contained in default databook settings.
        self.specs[FS.KEY_DATAPAGE] = odict()
        self.createDatabookSpecs()

    def createDatabookSpecs(self):
        """
        Generate framework-dependent databook settings that are a fusion of static databook settings and dynamic framework specifics.
        These are the ones that databook construction processes use when deciding layout.
        """
        # Copy default page keys over.
        for page_key in DS.PAGE_KEYS:
            self.specs[FS.KEY_DATAPAGE][page_key] = odict()
            
            # Do a scan over page tables in default databook settings.
            # If any are templated, i.e. are duplicated per instance of an item type, all tables must be copied over and duplicated where necessary.
            copy_over = False
            for table in DS.PAGE_SPECS[page_key]["tables"]:
                if isinstance(table, TimeDependentValuesEntry):
                    copy_over = True
                    break

            if copy_over:
                for page_attribute in DS.PAGE_SPECS[page_key]:
                    if not page_attribute == "tables": self.specs[FS.KEY_DATAPAGE][page_key][page_attribute] = DS.PAGE_SPECS[page_key][page_attribute]
                    else:
                        self.specs[FS.KEY_DATAPAGE][page_key]["tables"] = []
                        for table in DS.PAGE_SPECS[page_key]["tables"]:
                            if isinstance(table, TimeDependentValuesEntry):
                                item_type = table.item_type
                                for item_key in self.specs[item_type]:
                                    instantiated_table = dcp(table)
                                    instantiated_table.item_key = item_key
                                    self.specs[FS.KEY_DATAPAGE][page_key]["tables"].append(instantiated_table)
                            else:
                                self.specs[FS.KEY_DATAPAGE][page_key]["tables"].append(table)

            else: self.specs[FS.KEY_DATAPAGE][page_key]["refer_to_default"] = True
            
            
    def writeDatabook(self, filename, data=None, instructions=None):
        '''
        Export a databook 
        '''        
        writeWorkbook(workbook_path=filename, framework=self, data=data, instructions=instructions, workbook_type=SS.STRUCTURE_KEY_DATA)
        return None
        