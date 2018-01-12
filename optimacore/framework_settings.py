# -*- coding: utf-8 -*-
"""
Optima Core project-framework settings file.
Contains metadata describing the construction of a model framework.
The definitions are hard-coded, while interface semantics are drawn from a configuration file.
"""

from optimacore.system import logUsage, accepts, OptimaException
from optimacore.system import logger, SystemSettings, getOptimaCorePath

from collections import OrderedDict

try: import ConfigParser as configparser    # Python 2.
except ImportError: import configparser     # Python 3.


@logUsage
@accepts(configparser.ConfigParser,str,str)
def getConfigValue(config, section, option, list_form = False, mute_warnings = False):
    """
    Returns the value of an option of a section within a parsed configuration file.
    If the list form option is set as true, the return value is a list of strings, otherwise the value is a string.
    Lists are broken apart by a separator set in system settings, with all values being stripped of surrounding whitespace.
    """
    value = None
    if not config.has_section(section):
        if not mute_warnings: logger.warning("Framework configuration file has no section with label '{0}'.".format(section))
        raise configparser.NoSectionError(section)
    if not config.has_option(section, option):
        if not mute_warnings: logger.warning("Framework configuration file, section '{0}', has no option with label '{1}'.".format(section,option))
        raise configparser.NoOptionError(section,option)
    if list_form:
        value = [item.strip() for item in config.get(section, option).strip().split(SystemSettings.CONFIG_FRAMEWORK_LIST_SEPARATOR)]
    else:
        value = config.get(section, option).strip()
    return value

def loadConfigFile(undecorated_class):
    """
    Decorator that instructs a class to do an initial update of its attributes according to a configuration file.
    This is done at the import stage; failure means the class starts off incorrect and an import error is thrown.
    """
    try: undecorated_class.reloadConfigFile()
    except:
        logger.exception("Because a relevant configuration file failed to load, the initial state of class '{0}' is invalid. "
                         "Import failed.".format(undecorated_class.__name__))
        raise ImportError
    return undecorated_class

@loadConfigFile
class FrameworkSettings(object):
    """
    Stores the definitions used in creating and reading framework files.
    Structure is hard-coded and any changes risk disrupting framework operations.
    UI semantics are parsed from a framework configuration file during the module import phase.
    Note: As a codebase-specific settings class, there is no need to instantiate it as an object.
    """
    # TODO: Work out how to reference the keys here within the configuration file, so as to keep the two aligned.
    # Construct an ordered list of keys representing pages.
    KEY_COMPARTMENT = "comp"
    KEY_CHARACTERISTIC = "charac"
    PAGE_KEYS = ["poptype", KEY_COMPARTMENT, "trans", KEY_CHARACTERISTIC, "par", "progtype"]

    # Create key semantics for types that columns can be.
    COLUMN_TYPE_KEY_LABEL = "label"
    COLUMN_TYPE_KEY_NAME = "name"
    COLUMN_TYPE_KEY_SWITCH_DEFAULT_OFF = "switch_off"
    COLUMN_TYPE_KEY_SWITCH_DEFAULT_ON = "switch_on"
    COLUMN_TYPE_KEY_LIST_COMP_CHARAC = "list_comp_charac"
    COLUMN_TYPE_KEYS = [COLUMN_TYPE_KEY_LABEL, COLUMN_TYPE_KEY_NAME, 
                        COLUMN_TYPE_KEY_SWITCH_DEFAULT_OFF, COLUMN_TYPE_KEY_SWITCH_DEFAULT_ON,
                        COLUMN_TYPE_KEY_LIST_COMP_CHARAC]
    
    # Construct a dictionary mapping each page-key to a list of unique keys representing columns.
    # This ordering describes how a framework template will be constructed.
    KEY_COMPARTMENT_LABEL = KEY_COMPARTMENT + COLUMN_TYPE_KEY_LABEL
    KEY_COMPARTMENT_NAME = KEY_COMPARTMENT + COLUMN_TYPE_KEY_NAME
    KEY_CHARACTERISTIC_LABEL = KEY_CHARACTERISTIC + COLUMN_TYPE_KEY_LABEL
    KEY_CHARACTERISTIC_NAME = KEY_CHARACTERISTIC + COLUMN_TYPE_KEY_NAME

    PAGE_COLUMN_KEYS = OrderedDict()
    for page_key in PAGE_KEYS: PAGE_COLUMN_KEYS[page_key] = []
    PAGE_COLUMN_KEYS["poptype"] = ["popattlabel", "popattname", "popoptlabel", "popoptname"]
    PAGE_COLUMN_KEYS[KEY_COMPARTMENT] = [KEY_COMPARTMENT_LABEL, KEY_COMPARTMENT_NAME, "sourcetag", "sinktag", "junctiontag"]
    PAGE_COLUMN_KEYS[KEY_CHARACTERISTIC] = [KEY_CHARACTERISTIC_LABEL, KEY_CHARACTERISTIC_NAME, "characincludes"]
    PAGE_COLUMN_KEYS["par"] = ["parlabel", "parname", "transid"]
    PAGE_COLUMN_KEYS["progtype"] = ["progtypelabel", "progtypename", "progattlabel", "progattname"]
    
    # Likewise construct a key dictionary mapping pages to abstract items that appear on these pages.
    # Like with columns, items need unique keys even if associated with different pages.
    # Note: The order of item keys is also important as importing files will start scans through columns associated with the first, i.e. core, item-key.
    PAGE_ITEM_KEYS = OrderedDict()
    for page_key in PAGE_KEYS: PAGE_ITEM_KEYS[page_key] = []
    PAGE_ITEM_KEYS["poptype"] = ["attitem","optitem"]
    PAGE_ITEM_KEYS[KEY_COMPARTMENT] = ["compitem"]
    PAGE_ITEM_KEYS[KEY_CHARACTERISTIC] = ["characitem"]
    PAGE_ITEM_KEYS["par"] = ["paritem"]
    PAGE_ITEM_KEYS["progtype"] = ["progitem","progattitem"]
    
    # Keys for float-valued variables related in some way to framework-file formatting.
    # They must have corresponding system-settings defaults.
    FORMAT_VARIABLE_KEYS = ["column_width","comment_xscale","comment_yscale"]
    
    # Construct a dictionary of specifications detailing how to construct pages and page columns.
    # Everything here is hard-coded and abstract, with semantics drawn from a configuration file later.
    PAGE_SPECS = OrderedDict()
    COLUMN_SPECS = OrderedDict()
    for page_key in PAGE_KEYS:
        PAGE_SPECS[page_key] = dict()  
        column_count = 0
        for column_key in PAGE_COLUMN_KEYS[page_key]:
            if column_key in COLUMN_SPECS: raise OptimaException("Key uniqueness failure. Framework settings specify the same key '{0}' for more than one column.".format(column_key))
            COLUMN_SPECS[column_key] = dict()
            # Associate each column with a position value for easy reference.
            # This is a default number for template creation; column positions may be different in loaded framework files.
            COLUMN_SPECS[column_key]["default_pos"] = column_count
            COLUMN_SPECS[column_key]["type"] = None
            column_count += 1
            # For convenience, do default typing based on column key here.
            for column_type_key in COLUMN_TYPE_KEYS:
                if column_key.endswith(column_type_key):
                     COLUMN_SPECS[column_key]["type"] = column_type_key
    # Non-default types should overwrite defaults here.
    COLUMN_SPECS["sourcetag"]["type"] = COLUMN_TYPE_KEY_SWITCH_DEFAULT_OFF
    COLUMN_SPECS["sinktag"]["type"] = COLUMN_TYPE_KEY_SWITCH_DEFAULT_OFF
    COLUMN_SPECS["junctiontag"]["type"] = COLUMN_TYPE_KEY_SWITCH_DEFAULT_OFF
    COLUMN_SPECS["characincludes"]["type"] = COLUMN_TYPE_KEY_LIST_COMP_CHARAC
    
    # A mapping from item descriptors to keys.
    ITEM_DESCRIPTOR_KEY = dict()
                     
    # Construct a dictionary of specifications detailing framework page-item IO.
    # Warning: Incorrect modifications are particularly dangerous here due to the possibility of broken Excel links and subitem recursions.
    ITEM_ATTRIBUTES = ["label","name"]
    ITEM_SPECS = OrderedDict()     # Order is important when running through subitems.
    for page_key in PAGE_ITEM_KEYS:
        for item_key in PAGE_ITEM_KEYS[page_key]:
            if item_key in ITEM_SPECS: raise OptimaException("Key uniqueness failure. Framework settings specify the same key '{0}' for more than one item type.".format(item_key))
            # Map item key back to page key and also provide a string-valued descriptor.
            # This is technically the user-interface label of an item 'type', but is called a descriptor to avoid confusion with labels of item 'instances'.
            ITEM_SPECS[item_key] = {"page_key":page_key, "descriptor":item_key,
            # Specify whether page-item IO should include or exclude specified columns.
            # Then specify a list of column keys to be included or excluded when reading or writing a page-item.
            # Many page-items involve all columns, so the default is to exclude no columns.
                                    "inc_not_exc":False, "column_keys":None,
            # Some page-items can be divided into columns and other page-items; the keys of the latter should be listed.
                                    "subitem_keys":None, 
            # In principle page-items have no restriction in producing other page-items.
            # But factory methods will only generate core page-items; all subitems should mark the key of its superitem.
                                    "superitem_key":None}
            for attribute in ITEM_ATTRIBUTES:
                ITEM_SPECS[item_key]["key_"+attribute] = None
            ITEM_DESCRIPTOR_KEY[ITEM_SPECS[item_key]["descriptor"]] = item_key   # Map default descriptors to keys.
    # Define a default population attribute item.
    ITEM_SPECS["attitem"]["inc_not_exc"] = True
    ITEM_SPECS["attitem"]["column_keys"] = ["popattlabel","popattname"]
    ITEM_SPECS["attitem"]["key_label"] = "popattlabel"
    ITEM_SPECS["attitem"]["key_name"] = "popattname"
    ITEM_SPECS["attitem"]["subitem_keys"] = ["optitem"]
    # Define a default population option item, which is a subitem of a population attribute.
    ITEM_SPECS["optitem"]["column_keys"] = ["popattlabel","popattname"]
    ITEM_SPECS["optitem"]["key_label"] = "popoptlabel"
    ITEM_SPECS["optitem"]["key_name"] = "popoptname"
    ITEM_SPECS["optitem"]["superitem_key"] = "attitem"
    # Define a default compartment item.
    ITEM_SPECS["compitem"]["key_label"] = KEY_COMPARTMENT_LABEL
    ITEM_SPECS["compitem"]["key_name"] = KEY_COMPARTMENT_NAME
    # Define a default characteristic item.
    ITEM_SPECS["characitem"]["key_label"] = KEY_CHARACTERISTIC_LABEL
    ITEM_SPECS["characitem"]["key_name"] = KEY_CHARACTERISTIC_NAME
    # Define a default parameter item.
    ITEM_SPECS["paritem"]["key_label"] = "parlabel"
    ITEM_SPECS["paritem"]["key_name"] = "parname"
    # Define a default program type item.
    ITEM_SPECS["progitem"]["inc_not_exc"] = True
    ITEM_SPECS["progitem"]["column_keys"] = ["progtypelabel","progtypename"]
    ITEM_SPECS["progitem"]["key_label"] = "progtypelabel"
    ITEM_SPECS["progitem"]["key_name"] = "progtypename"
    ITEM_SPECS["progitem"]["subitem_keys"] = ["progattitem"]
    # Define a default program type attribute item.
    ITEM_SPECS["progattitem"]["inc_not_exc"] = True
    ITEM_SPECS["progattitem"]["column_keys"] = ["progattlabel","progattname"]
    ITEM_SPECS["progattitem"]["key_label"] = "progattlabel"
    ITEM_SPECS["progattitem"]["key_name"] = "progattname"
    ITEM_SPECS["progattitem"]["superitem_key"] = "progitem"
    
                   
    @classmethod
    @logUsage
    def reloadConfigFile(cls):
        """
        Reads a framework configuration file and extends the settings to use the semantics and values provided.
        Method is titled with 'reload' as the process will have already been called once during initial import.
        Note: Currently references the default configuration file, but can be modified in the future.
        """
        config_path = getOptimaCorePath(subdir=SystemSettings.CODEBASE_DIRNAME) + SystemSettings.CONFIG_FRAMEWORK_FILENAME
        logger.info("Attempting to generate Optima Core framework settings from configuration file.")
        logger.info("Location... {0}".format(config_path))
        cp = configparser.ConfigParser()
        cp.read(config_path)
        
        # Flesh out page details.
        for page_key in cls.PAGE_KEYS:
            # Read in required page title.
            try: cls.PAGE_SPECS[page_key]["title"] = getConfigValue(config = cp, section = "page_"+page_key, option = "title")
            except:
                logger.exception("Framework configuration loading process failed. Every page in a framework file needs a title.")
                raise
            # Read in optional page format variables.
            for format_variable_key in cls.FORMAT_VARIABLE_KEYS:
                try: 
                    value_overwrite = float(getConfigValue(config = cp, section = "page_"+page_key, option = format_variable_key, mute_warnings = True))
                    cls.PAGE_SPECS[page_key][format_variable_key] = value_overwrite
                except ValueError: logger.warning("Framework configuration file for page-key '{0}' has an entry for '{1}' " 
                                                  "that cannot be converted to a float. Using a default value.".format(page_key, format_variable_key))
                except: pass
            
            # Flesh out page column details.
            for column_key in cls.PAGE_COLUMN_KEYS[page_key]:
                # Read in required column header.
                try: cls.COLUMN_SPECS[column_key]["header"] = getConfigValue(config = cp, section = "_".join(["column",column_key]), option = "header")
                except:
                    logger.exception("Framework configuration loading process failed. Every column in a framework page needs a header.")
                    raise
                # Read in optional column comment.
                try: cls.COLUMN_SPECS[column_key]["comment"] = getConfigValue(config = cp, section = "_".join(["column",column_key]), option = "comment")
                except: pass
                # Read in optional prefix that will prepend default text written into this column.
                try: cls.COLUMN_SPECS[column_key]["prefix"] = getConfigValue(config = cp, section = "_".join(["column",column_key]), option = "prefix", mute_warnings = True)
                except: pass
                # Read in optional column format variables.
                for format_variable_key in cls.FORMAT_VARIABLE_KEYS:
                    try: 
                        value_overwrite = float(getConfigValue(config = cp, section = "_".join(["column",column_key]), option = format_variable_key, mute_warnings = True))
                        cls.COLUMN_SPECS[column_key][format_variable_key] = value_overwrite
                    except ValueError: logger.warning("Framework configuration file for column-key '{0}' has an entry for '{1}' " 
                                                      "that cannot be converted to a float. Using a default value.".format(column_key, format_variable_key))
                    except: pass
            
        # Flesh out item details.
        for item_key in cls.ITEM_SPECS:
            try: descriptor = getConfigValue(config = cp, section = "item_"+item_key, option = "descriptor")
            except:
                logger.warning("Framework configuration file cannot find a descriptor for item-key '{0}', so the descriptor will be the key itself.".format(item_key))
                continue
            old_descriptor = cls.ITEM_SPECS[item_key]["descriptor"]
            del cls.ITEM_DESCRIPTOR_KEY[old_descriptor]
            cls.ITEM_SPECS[item_key]["descriptor"] = descriptor
            cls.ITEM_DESCRIPTOR_KEY[descriptor] = item_key
        
        logger.info("Optima Core framework settings successfully generated.") 
        return