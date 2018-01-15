# -*- coding: utf-8 -*-
"""
Optima Core databook settings file.
Contains metadata describing the construction of a project databook.
The definitions are hard-coded, while interface semantics are drawn from a configuration file.
"""

from optimacore.system import logUsage, accepts, OptimaException
from optimacore.system import logger, SystemSettings, getOptimaCorePath
from optimacore.framework_settings import FrameworkSettings
from optimacore.parser import loadConfigFile, getConfigValue, configparser

from collections import OrderedDict

@loadConfigFile
class DatabookSettings(object):
    """
    Stores the definitions used in creating and reading databook files.
    Structure is hard-coded and any changes risk disrupting databook IO operations.
    UI semantics are parsed from a databook configuration file during the module import phase.
    Note: As a codebase-specific settings class, there is no need to instantiate it as an object.
    """
    # TODO: Work out how to reference the keys here within the configuration file, so as to keep the two aligned.
    
    # Construct an ordered list of keys representing items defined in a databook.
    ITEM_TYPES = [FrameworkSettings.KEY_POPULATION, FrameworkSettings.KEY_PROGRAM]

    # A mapping from item type descriptors to type-key.
    ITEM_TYPE_DESCRIPTOR_KEY = dict()
                     
    # Construct a dictionary of specifications detailing databook item types.
    ITEM_TYPE_SPECS = OrderedDict()
    for item_type in ITEM_TYPES:
        if item_type in ITEM_TYPE_SPECS: raise OptimaException("Key uniqueness failure. Databook settings specify the same key '{0}' for more than one item type.".format(item_type))
        # Provide a string-valued descriptor, i.e. a user-interface label for the type.
        ITEM_TYPE_SPECS[item_type] = {"descriptor":item_type}
        ITEM_TYPE_DESCRIPTOR_KEY[ITEM_TYPE_SPECS[item_type]["descriptor"]] = item_type   # Map default descriptors to keys.
    
    @classmethod
    @logUsage
    def reloadConfigFile(cls):
        """
        Reads a framework configuration file and extends the settings to use the semantics and values provided.
        Method is titled with 'reload' as the process will have already been called once during initial import.
        Note: Currently references the default configuration file, but can be modified in the future.
        """
        config_path = getOptimaCorePath(subdir=SystemSettings.CODEBASE_DIRNAME) + SystemSettings.CONFIG_DATABOOK_FILENAME
        logger.info("Attempting to generate Optima Core databook settings from configuration file.")
        logger.info("Location... {0}".format(config_path))
        cp = configparser.ConfigParser()
        cp.read(config_path)
            
        # Flesh out item-type details.
        for item_type in cls.ITEM_TYPE_SPECS:
            try: descriptor = getConfigValue(config = cp, section = "itemtype_"+item_type, option = "descriptor")
            except:
                logger.warning("Databook configuration file cannot find a descriptor for item type '{0}', so the descriptor will be the key itself.".format(item_type))
                continue
            old_descriptor = cls.ITEM_TYPE_SPECS[item_type]["descriptor"]
            del cls.ITEM_TYPE_DESCRIPTOR_KEY[old_descriptor]
            cls.ITEM_TYPE_SPECS[item_type]["descriptor"] = descriptor
            cls.ITEM_TYPE_DESCRIPTOR_KEY[descriptor] = item_type

        print(cls.ITEM_TYPE_SPECS)
        
        logger.info("Optima Core databook settings successfully generated.") 
        return