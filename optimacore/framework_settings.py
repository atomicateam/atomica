# -*- coding: utf-8 -*-
"""
Optima Core project-framework settings file.
Contains metadata describing the construction of a model framework.
The definitions are hard-coded, while interface semantics are drawn from a configuration file.
"""

from optimacore.system import logUsage, accepts
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
        if not mute_warnings: logger.warn("Framework configuration file has no section with label '{0}'.".format(section))
        raise configparser.NoSectionError(section)
    if not config.has_option(section, option):
        if not mute_warnings: logger.warn("Framework configuration file, section '{0}', has no option with label '{1}'.".format(section,option))
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
    Some of this is hard-coded and any changes risk disrupting framework operations.
    The rest is parsed from a framework configuration file during the module import phase.
    Note: As a codebase-specific settings class, there is no need to instantiate it as an object.
    """
    # Construct a dictionary with ordered keys representing pages.
    # Each page-key corresponds to a list of keys representing columns.
    # These orders describe how a framework template will be constructed.
    # There is no restriction in using the same column key for different page keys.
    PAGE_COLUMN_KEYS = OrderedDict()
    PAGE_COLUMN_KEYS["poptype"] = ["attlabel","attname","optlabel","optname"]
    PAGE_COLUMN_KEYS["comp"] = ["label","name","sourcetag","sinktag","junctiontag"]
    PAGE_COLUMN_KEYS["trans"] = []
    PAGE_COLUMN_KEYS["charac"] = ["label","name"]
    PAGE_COLUMN_KEYS["par"] = ["label","name","trans"]
    PAGE_COLUMN_KEYS["progtype"] = ["label","name","attlabel","attname"]
    
    # Likewise construct a key dictionary mapping pages to abstract page-items that appear on these pages.
    # Unlike with page columns, page items need unique keys even if associated with different pages.
    # Note: The order of item keys is also important as importing files will start scans through columns associated with the first, i.e. core, item-key.
    PAGE_ITEM_KEYS = OrderedDict()
    for page_key in PAGE_COLUMN_KEYS: PAGE_ITEM_KEYS[page_key] = []
    PAGE_ITEM_KEYS["poptype"] = ["attitem","optitem"]
    PAGE_ITEM_KEYS["comp"] = ["compitem"]
    PAGE_ITEM_KEYS["charac"] = ["characitem"]
    PAGE_ITEM_KEYS["par"] = ["paritem"]
    PAGE_ITEM_KEYS["progtype"] = ["progitem","progattitem"]
    
    # Reverse the page-item key dictionary.
    # Is called a 'map' to emphasise the 1-to-1 pairing, rather than referencing lists.
    ITEM_PAGE_KEY_MAP = dict()
    for page_key in PAGE_ITEM_KEYS:
        for item_key in PAGE_ITEM_KEYS[page_key]:
            ITEM_PAGE_KEY_MAP[item_key] = page_key
    
    # Create key semantics for types that columns can be.
    COLUMN_TYPE_KEY_LABEL = "label"
    COLUMN_TYPE_KEY_NAME = "name"
    COLUMN_TYPE_KEY_SWITCH = "switch"
    
    # Keys for float-valued variables related in some way to framework-file formatting.
    # They must have corresponding system-settings defaults.
    FORMAT_VARIABLE_KEYS = ["column_width","comment_xscale","comment_yscale"]
    
    # Construct a dictionary of specifications detailing how to construct pages and page columns.
    # Everything here is hard-coded and abstract, with semantics drawn from a configuration file later.
    PAGE_SPECS = OrderedDict()
    PAGE_COLUMN_SPECS = OrderedDict()
    for page_key in PAGE_COLUMN_KEYS:
        PAGE_SPECS[page_key] = dict()  
        PAGE_COLUMN_SPECS[page_key] = OrderedDict()
        column_count = 0
        for column_key in PAGE_COLUMN_KEYS[page_key]:
            PAGE_COLUMN_SPECS[page_key][column_key] = dict()
            # Associate each column with a position value for easy reference.
            # This is a default number for template creation; column positions may be different in loaded framework files.
            PAGE_COLUMN_SPECS[page_key][column_key]["default_pos"] = column_count
            PAGE_COLUMN_SPECS[page_key][column_key]["type"] = None
            column_count += 1
    PAGE_COLUMN_SPECS["poptype"]["attlabel"]["type"] = COLUMN_TYPE_KEY_LABEL
    PAGE_COLUMN_SPECS["poptype"]["attname"]["type"] = COLUMN_TYPE_KEY_NAME
    PAGE_COLUMN_SPECS["poptype"]["optlabel"]["type"] = COLUMN_TYPE_KEY_LABEL
    PAGE_COLUMN_SPECS["poptype"]["optname"]["type"] = COLUMN_TYPE_KEY_NAME
    PAGE_COLUMN_SPECS["comp"]["label"]["type"] = COLUMN_TYPE_KEY_LABEL
    PAGE_COLUMN_SPECS["comp"]["name"]["type"] = COLUMN_TYPE_KEY_NAME
    PAGE_COLUMN_SPECS["comp"]["sourcetag"]["type"] = COLUMN_TYPE_KEY_SWITCH
    PAGE_COLUMN_SPECS["comp"]["sinktag"]["type"] = COLUMN_TYPE_KEY_SWITCH
    PAGE_COLUMN_SPECS["comp"]["junctiontag"]["type"] = COLUMN_TYPE_KEY_SWITCH
    PAGE_COLUMN_SPECS["charac"]["label"]["type"] = COLUMN_TYPE_KEY_LABEL
    PAGE_COLUMN_SPECS["charac"]["name"]["type"] = COLUMN_TYPE_KEY_NAME
    PAGE_COLUMN_SPECS["par"]["label"]["type"] = COLUMN_TYPE_KEY_LABEL
    PAGE_COLUMN_SPECS["par"]["name"]["type"] = COLUMN_TYPE_KEY_NAME
    PAGE_COLUMN_SPECS["progtype"]["label"]["type"] = COLUMN_TYPE_KEY_LABEL
    PAGE_COLUMN_SPECS["progtype"]["name"]["type"] = COLUMN_TYPE_KEY_NAME
    PAGE_COLUMN_SPECS["progtype"]["attlabel"]["type"] = COLUMN_TYPE_KEY_LABEL
    PAGE_COLUMN_SPECS["progtype"]["attname"]["type"] = COLUMN_TYPE_KEY_NAME
    
    # A mapping from item descriptors to keys.
    ITEM_DESCRIPTOR_KEY_MAP = dict()
                     
    # Construct a dictionary of specifications detailing how to construct page-items.
    # Warning: Incorrect modifications are particularly dangerous here due to the possibility of broken Excel links and subitem recursions.
    PAGE_ITEM_ATTRIBUTES = ["label","name"]
    PAGE_ITEM_SPECS = OrderedDict()     # Order is important when running through subitems.
    for page_key in PAGE_ITEM_KEYS:
        PAGE_ITEM_SPECS[page_key] = dict()
        for item_key in PAGE_ITEM_KEYS[page_key]:
            # Mark the page-item with a string-valued descriptor.
            # This is technically the user-interface label of an item type, but is called a descriptor to avoid confusion with labels of item instances.
            PAGE_ITEM_SPECS[page_key][item_key] = {"descriptor":item_key,
            # Specify whether page-item construction should include or exclude filling out specified columns.
            # Then specify a list of column keys to be included or excluded when constructing a page-item.
            # Many page-items involve all columns, so the default is to exclude no columns.
                                                   "inc_not_exc":False, "column_keys":None,
            # Some page-items can be divided into columns and other page-items; the keys of the latter should be listed.
                                                   "subitem_keys":None, 
            # In principle page-items have no restriction in producing other page-items.
            # But factory methods will only generate core page-items; all subitems should mark the key of its superitem.
                                                   "superitem_key":None}
            for attribute in PAGE_ITEM_ATTRIBUTES:
                PAGE_ITEM_SPECS[page_key][item_key]["key_"+attribute] = None
            ITEM_DESCRIPTOR_KEY_MAP[PAGE_ITEM_SPECS[page_key][item_key]["descriptor"]] = item_key   # Map default descriptors to keys.
    # Define a default population attribute item.
    PAGE_ITEM_SPECS["poptype"]["attitem"]["inc_not_exc"] = True
    PAGE_ITEM_SPECS["poptype"]["attitem"]["column_keys"] = ["attlabel","attname"]
    PAGE_ITEM_SPECS["poptype"]["attitem"]["key_label"] = "attlabel"
    PAGE_ITEM_SPECS["poptype"]["attitem"]["key_name"] = "attname"
    PAGE_ITEM_SPECS["poptype"]["attitem"]["subitem_keys"] = ["optitem"]
    # Define a default population option item, which is a subitem of a population attribute.
    PAGE_ITEM_SPECS["poptype"]["optitem"]["column_keys"] = ["attlabel","attname"]
    PAGE_ITEM_SPECS["poptype"]["optitem"]["key_label"] = "optlabel"
    PAGE_ITEM_SPECS["poptype"]["optitem"]["key_name"] = "optname"
    PAGE_ITEM_SPECS["poptype"]["optitem"]["superitem_key"] = "attitem"
    # Define a default compartment item.
    PAGE_ITEM_SPECS["comp"]["compitem"]["key_label"] = "label"
    PAGE_ITEM_SPECS["comp"]["compitem"]["key_name"] = "name"
    # Define a default characteristic item.
    PAGE_ITEM_SPECS["charac"]["characitem"]["key_label"] = "label"
    PAGE_ITEM_SPECS["charac"]["characitem"]["key_name"] = "name"
    # Define a default parameter item.
    PAGE_ITEM_SPECS["par"]["paritem"]["key_label"] = "label"
    PAGE_ITEM_SPECS["par"]["paritem"]["key_name"] = "name"
    # Define a default program type item.
    PAGE_ITEM_SPECS["progtype"]["progitem"]["inc_not_exc"] = True
    PAGE_ITEM_SPECS["progtype"]["progitem"]["column_keys"] = ["label","name"]
    PAGE_ITEM_SPECS["progtype"]["progitem"]["key_label"] = "label"
    PAGE_ITEM_SPECS["progtype"]["progitem"]["key_name"] = "name"
    PAGE_ITEM_SPECS["progtype"]["progitem"]["subitem_keys"] = ["progattitem"]
    # Define a default program type attribute item.
    PAGE_ITEM_SPECS["progtype"]["progattitem"]["inc_not_exc"] = True
    PAGE_ITEM_SPECS["progtype"]["progattitem"]["column_keys"] = ["attlabel","attname"]
    PAGE_ITEM_SPECS["progtype"]["progattitem"]["key_label"] = "attlabel"
    PAGE_ITEM_SPECS["progtype"]["progattitem"]["key_name"] = "attname"
    PAGE_ITEM_SPECS["progtype"]["progattitem"]["superitem_key"] = "progitem"
    
                   
    @classmethod
    @logUsage
    def reloadConfigFile(cls):
        """
        Reads a framework configuration file and extends the settings to use the semantics and values provided.
        Method is titled with 'reload' as the process will have already been called once during initial import.
        Note: Currently references the default configuration file, but can be modified in the future.
        """
        config_path = getOptimaCorePath(subdir=SystemSettings.CODEBASE_DIRNAME)+SystemSettings.CONFIG_FRAMEWORK_FILENAME
        logger.info("Attempting to generate Optima Core framework settings from configuration file.")
        logger.info("Location... {0}".format(config_path))
        cp = configparser.ConfigParser()
        cp.read(config_path)
        
        # Flesh out page details.
        for page_key in cls.PAGE_COLUMN_KEYS:
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
                except ValueError: logger.warn("Framework configuration file for page-key '{0}' has an entry for '{1}' " 
                                               "that cannot be converted to a float. Using a default value.".format(page_key, format_variable_key))
                except: pass
            
            # Flesh out page column details.
            for column_key in cls.PAGE_COLUMN_KEYS[page_key]:
                # Read in required column header.
                try: cls.PAGE_COLUMN_SPECS[page_key][column_key]["header"] = getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = "header")
                except:
                    logger.exception("Framework configuration loading process failed. Every column in a framework page needs a header.")
                    raise
                # Read in optional column comment.
                try: cls.PAGE_COLUMN_SPECS[page_key][column_key]["comment"] = getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = "comment")
                except: pass
                # Read in optional prefix that will prepend default text written into this column.
                try: cls.PAGE_COLUMN_SPECS[page_key][column_key]["prefix"] = getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = "prefix", mute_warnings = True)
                except: pass
                # Read in optional column format variables.
                for format_variable_key in cls.FORMAT_VARIABLE_KEYS:
                    try: 
                        value_overwrite = float(getConfigValue(config = cp, section = "_".join(["column",page_key,column_key]), option = format_variable_key, mute_warnings = True))
                        cls.PAGE_COLUMN_SPECS[page_key][column_key][format_variable_key] = value_overwrite
                    except ValueError: logger.warn("Framework configuration file for page-key '{0}', column-key '{1}', has an entry for '{2}' " 
                                                   "that cannot be converted to a float. Using a default value.".format(page_key, column_key, format_variable_key))
                    except: pass
            
        # Flesh out item details.
        for item_key in cls.ITEM_PAGE_KEY_MAP:
            try: descriptor = getConfigValue(config = cp, section = "item_"+item_key, option = "descriptor")
            except:
                logger.warning("Framework configuration file cannot find a descriptor for item-key '{0}', so the descriptor will be the key itself.".format(item_key))
                continue
            page_key = cls.ITEM_PAGE_KEY_MAP[item_key]
            old_descriptor = cls.PAGE_ITEM_SPECS[page_key][item_key]["descriptor"]
            del cls.ITEM_DESCRIPTOR_KEY_MAP[old_descriptor]
            cls.PAGE_ITEM_SPECS[page_key][item_key]["descriptor"] = descriptor
            cls.ITEM_DESCRIPTOR_KEY_MAP[descriptor] = item_key
        
        logger.info("Optima Core framework settings successfully generated.") 
        return