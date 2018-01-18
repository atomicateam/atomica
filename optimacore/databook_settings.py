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
from optimacore.excel import ExcelSettings

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
    # Define simple key semantics, copying from framework settings were required to maintain consistency.
    KEY_POPULATION = FrameworkSettings.KEY_POPULATION
    KEY_PROGRAM = FrameworkSettings.KEY_PROGRAM

    # Construct an ordered list of keys representing standard pages.
    PAGE_KEYS = [KEY_POPULATION, KEY_PROGRAM]

    # Each databook page consists of 'sections'.
    # These can be columns in the simplest case, but also include sets of complex data-entry units. 
    # Create key semantics for types that sections can be.
    SECTION_TYPE_COLUMN_LABEL = FrameworkSettings.COLUMN_TYPE_LABEL
    SECTION_TYPE_COLUMN_NAME = FrameworkSettings.COLUMN_TYPE_NAME
    SECTION_TYPES = [SECTION_TYPE_COLUMN_LABEL, SECTION_TYPE_COLUMN_NAME]

    # Construct an ordered list of keys representing items defined in a databook.
    # Unlike with frameworks, these tend to extend over multiple pages, leading to significant differences in input and output.
    ITEM_TYPES = [KEY_POPULATION, KEY_PROGRAM]
    
    # Construct a dictionary mapping each page-key to a list of unique keys representing sections.
    # This ordering describes how a databook will be constructed.
    KEY_POPULATION_LABEL = KEY_POPULATION + SECTION_TYPE_COLUMN_LABEL
    KEY_POPULATION_NAME = KEY_POPULATION + SECTION_TYPE_COLUMN_NAME

    PAGE_SECTION_KEYS = OrderedDict()
    for page_key in PAGE_KEYS: PAGE_SECTION_KEYS[page_key] = []
    PAGE_SECTION_KEYS[KEY_POPULATION] = [KEY_POPULATION_LABEL, KEY_POPULATION_NAME]

    # Construct a dictionary of specifications detailing how to construct pages and page sections.
    # Everything here is hard-coded and abstract, with semantics drawn from a configuration file later.
    # Note: For databooks, this dictionary does the heavy lifting; sections are iteratively created for all items.
    PAGE_SPECS = OrderedDict()
    SECTION_SPECS = OrderedDict()
    for page_key in PAGE_KEYS:
        PAGE_SPECS[page_key] = dict()
        section_count = 0
        for section_key in PAGE_SECTION_KEYS[page_key]:
            if section_key in SECTION_SPECS: raise OptimaException("Key uniqueness failure. Databook settings specify the same key '{0}' for more than one section.".format(section_key))
            SECTION_SPECS[section_key] = dict()

            ## Associate each section with a position value for easy reference.
            ## Note: Given that not all sections are columns, output-based interpretation of this number may vary.
            #SECTION_SPECS[section_key]["default_pos"] = section_count

            # Attach a reference to an item type that is associated with this section, for input-output purposes.
            SECTION_SPECS[section_key]["item_type"] = None
            # Also determine the type this section is, as listed earlier.
            SECTION_SPECS[section_key]["type"] = None
            section_count += 1
            # For convenience, do default referencing and typing based on section key here.
            for item_type in ITEM_TYPES:
                if page_key.startswith(item_type):
                    SECTION_SPECS[section_key]["item_type"] = item_type
            for section_type in SECTION_TYPES:
                if section_key.endswith(section_type):
                    SECTION_SPECS[section_key]["type"] = section_type
    # Non-default types should overwrite defaults here.
    pass

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
        Reads a databook configuration file and extends the settings to use the semantics and values provided.
        Method is titled with 'reload' as the process will have already been called once during initial import.
        Note: Currently references the default configuration file, but can be modified in the future.
        """
        config_path = getOptimaCorePath(subdir=SystemSettings.CODEBASE_DIRNAME) + SystemSettings.CONFIG_DATABOOK_FILENAME
        logger.info("Attempting to generate Optima Core databook settings from configuration file.")
        logger.info("Location... {0}".format(config_path))
        cp = configparser.ConfigParser()
        cp.read(config_path)

        # Flesh out page details.
        for page_key in cls.PAGE_KEYS:
            # Read in required page title.
            try: cls.PAGE_SPECS[page_key]["title"] = getConfigValue(config = cp, section = "page_"+page_key, option = "title")
            except:
                logger.exception("Databook configuration loading process failed. Every page in a databook needs a title.")
                raise
            # Read in optional page format variables.
            for format_variable_key in ExcelSettings.FORMAT_VARIABLE_KEYS:
                try: 
                    value_overwrite = float(getConfigValue(config = cp, section = "page_"+page_key, option = format_variable_key, mute_warnings = True))
                    cls.PAGE_SPECS[page_key][format_variable_key] = value_overwrite
                except ValueError: logger.warning("Databook configuration file for page-key '{0}' has an entry for '{1}' " 
                                                  "that cannot be converted to a float. Using a default value.".format(page_key, format_variable_key))
                except: pass

            # Flesh out page section details.
            # TODO: Generalise beyond columns.
            for section_key in cls.PAGE_SECTION_KEYS[page_key]:
                # Read in required column header.
                try: cls.SECTION_SPECS[section_key]["header"] = getConfigValue(config = cp, section = "_".join(["section",section_key]), option = "header")
                except:
                    logger.exception("Databook configuration loading process failed. Every section in a framework page needs a header.")
                    raise
                # Read in optional section comment.
                try: cls.SECTION_SPECS[section_key]["comment"] = getConfigValue(config = cp, section = "_".join(["section",section_key]), option = "comment")
                except: pass
                # Read in optional prefix that will prepend default text written into this section.
                try: cls.SECTION_SPECS[section_key]["prefix"] = getConfigValue(config = cp, section = "_".join(["section",section_key]), option = "prefix", mute_warnings = True)
                except: pass
                
                # Read in optional reference to another section that will be used to prepend default text written into this section.
                # This is typically used to have text reference other columns via Excel formula; it will override standard 'prefix' instructions.
                try: cls.SECTION_SPECS[section_key]["ref_section"] = getConfigValue(config = cp, section = "_".join(["section",section_key]), option = "ref_section", mute_warnings = True)
                except: pass
                if "ref_section" in cls.SECTION_SPECS[section_key]:
                    ref_section = cls.SECTION_SPECS[section_key]["ref_section"]
                    if not ref_section in cls.SECTION_SPECS:
                        raise OptimaException("Databook configuration file specifies non-existent section '{0}' as a 'referenced section' for "
                                              "section '{1}'.".format(ref_section, section_key))
                    else:
                        if not cls.SECTION_SPECS[section_key]["item_type"] == cls.SECTION_SPECS[ref_section]["item_type"]:
                            raise OptimaException("Databook configuration file states that section with key '{0}' and item type '{1}' references section with key '{2}' "
                                                 "and item type '{3}'. Different item types are not allowed, "
                                                 "in case there is no one-to-one mapping from item to item.".format(section_key, cls.SECTION_SPECS[section_key]["item_type"],
                                                                                                                    ref_section, cls.SECTION_SPECS[ref_section]["item_type"]))
                        # Note that the referenced section is a reference, i.e. its values must persist during the entire databook construction process.
                        cls.SECTION_SPECS[ref_section]["is_ref"] = True

                # Read in optional section format variables.
                for format_variable_key in ExcelSettings.FORMAT_VARIABLE_KEYS:
                    try: 
                        value_overwrite = float(getConfigValue(config = cp, section = "_".join(["section",section_key]), option = format_variable_key, mute_warnings = True))
                        cls.SECTION_SPECS[section_key][format_variable_key] = value_overwrite
                    except ValueError: logger.warning("Databook configuration file for section-key '{0}' has an entry for '{1}' " 
                                                      "that cannot be converted to a float. Using a default value.".format(section_key, format_variable_key))
                    except: pass
            
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

        import pprint
        pprint.pprint(cls.SECTION_SPECS)
        
        logger.info("Optima Core databook settings successfully generated.") 
        return