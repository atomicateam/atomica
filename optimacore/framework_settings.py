# -*- coding: utf-8 -*-
"""
Optima Core project-framework settings file.
Contains metadata describing the construction of a model framework.
The definitions are hard-coded, while interface semantics are drawn from a configuration file.
"""

from optimacore.system import SystemSettings as SS

from optimacore.system import logUsage, accepts, OptimaException
from optimacore.system import logger, getOptimaCorePath, displayName
from optimacore.parser import loadConfigFile, getConfigValue, configparser
from optimacore.excel import ExcelSettings

from collections import OrderedDict

class KeyUniquenessException(OptimaException):
    def __init__(self, key, object_type, **kwargs):
        message = ("Key uniqueness failure. Settings specify the same key '{0}' for more than one '{1}'.".format(key, object_type))
        return super().__init__(message, **kwargs)

class DetailColumns(object):
    """ Lightweight structure to associate a workbook table of detail columns with a specific item type. """
    def __init__(self, item_type): self.item_type = item_type

class ContentType(object):
    """ Lightweight structure to associate the contents of an item attribute with rules for IO. """
    def __init__(self, is_list = False): self.is_list = is_list
class LabelType(ContentType):
    """ Lightweight structure to associate the contents of an item attribute with display label formats. """
    def __init__(self): super(LabelType,self).__init__()
class NameType(ContentType):
    """ Lightweight structure to associate the contents of an item attribute with code name formats. """
    def __init__(self): super(NameType,self).__init__()
class SwitchType(ContentType):
    """ Lightweight structure to associate the contents of an item attribute with boolean flags. """
    def __init__(self, default_on = False, **kwargs):
        super(SwitchType,self).__init__(**kwargs)
        self.default_on = default_on
class AttributeReference(ContentType):
    """ Lightweight structure to have the contents of an item type attribute reference those of another item type attribute. """
    def __init__(self, item_type_specs, other_item_type, other_attribute, **kwargs):
        super(AttributeReference,self).__init__(**kwargs)
        self.other_item_type = other_item_type
        self.other_attribute = other_attribute
        item_type_specs[other_item_type]["attributes"][other_attribute]["is_ref"] = True
class SuperReference(AttributeReference):
    """ Lightweight structure to have the contents of an item type attribute reference those of a superitem type attribute. """
    def __init__(self, **kwargs): super(SuperReference,self).__init__(**kwargs)
class ExtraSelfReference(AttributeReference):
    """
    Lightweight structure to have the contents of an item type attribute reference those of another item type attribute.
    It can also reference another attribute of the same item.
    """
    def __init__(self, item_type_specs, own_item_type, own_attribute, **kwargs):
        super(ExtraSelfReference,self).__init__(item_type_specs = item_type_specs, **kwargs)
        self.own_item_type = own_item_type
        self.own_attribute = own_attribute
        item_type_specs[own_item_type]["attributes"][own_attribute]["is_ref"] = True

class BaseStructuralSettings():
    NAME = "general_workbook"
    CONFIG_PATH = str()

    KEY_COMPARTMENT = "comp"
    KEY_CHARACTERISTIC = "charac"
    KEY_PARAMETER = "par"
    KEY_POPULATION = "pop"
    KEY_PROGRAM = "prog"
    KEY_DATAPAGE = "datapage"

    TERM_ITEM = "item"
    TERM_TYPE = "type"
    TERM_ATTRIBUTE = "att"
    TERM_OPTION = "opt"

    KEY_POPULATION_ATTRIBUTE = KEY_POPULATION + TERM_ATTRIBUTE
    KEY_POPULATION_OPTION = KEY_POPULATION + TERM_OPTION
    KEY_PROGRAM_TYPE = KEY_PROGRAM + TERM_TYPE
    KEY_PROGRAM_ATTRIBUTE = KEY_PROGRAM + TERM_ATTRIBUTE

    ITEM_TYPES = [KEY_POPULATION_ATTRIBUTE, KEY_POPULATION_OPTION, KEY_COMPARTMENT, KEY_CHARACTERISTIC, KEY_PARAMETER, KEY_PROGRAM_TYPE, KEY_PROGRAM_ATTRIBUTE]

    PAGE_KEYS = []                          # Derived settings should overwrite this.
    PAGE_SPECS = None                       # Class method makes this an ordered dictionary.

    ITEM_TYPE_SPECS = None                  # Class method makes this an ordered dictionary.
    ITEM_TYPE_DESCRIPTOR_KEY = dict()       # A mapping from item type descriptors to type-key.

    @classmethod
    @logUsage
    def createPageTable(cls, item_type, table):
        cls.PAGE_SPECS[item_type]["tables"].append(table)

    @classmethod
    @logUsage
    def createPageSpecs(cls):
        cls.PAGE_SPECS = OrderedDict()
        for page_key in cls.PAGE_KEYS:
            cls.PAGE_SPECS[page_key] = {"title":page_key.title()}
            cls.PAGE_SPECS[page_key]["tables"] = []

    @classmethod
    @logUsage
    def createItemTypeDescriptor(cls, item_type, descriptor):
        if "descriptor" in cls.ITEM_TYPE_SPECS[item_type]:
            old_descriptor = cls.ITEM_TYPE_SPECS[item_type]["descriptor"]
            del cls.ITEM_TYPE_DESCRIPTOR_KEY[old_descriptor]
        cls.ITEM_TYPE_SPECS[item_type]["descriptor"] = descriptor
        cls.ITEM_TYPE_DESCRIPTOR_KEY[descriptor] = item_type

    @classmethod
    @logUsage
    def createItemTypeAttribute(cls, item_type, attributes, content_type = None):
        for attribute in attributes:
            attribute_dict = {"header":SS.DEFAULT_SPACE_LABEL.join([item_type, attribute]).title(),
                              "comment":"This column defines a '{0}' attribute for a '{1}' item.".format(attribute, item_type),
                              "content_type":content_type}
            cls.ITEM_TYPE_SPECS[item_type]["attributes"][attribute] = attribute_dict
    
    @classmethod
    @logUsage
    def createItemTypeSubitemTypes(cls, item_type, subitem_types):
        for subitem_type in subitem_types:
            attribute_dict = {"ref_item_type":subitem_type}
            cls.ITEM_TYPE_SPECS[item_type]["attributes"][subitem_type + SS.DEFAULT_SUFFIX_PLURAL] = attribute_dict
            for attribute in ["name","label"]:
                cls.ITEM_TYPE_SPECS[subitem_type]["attributes"][attribute]["content_type"] = SuperReference(item_type_specs = cls.ITEM_TYPE_SPECS, other_item_type = item_type, other_attribute = attribute)
    
    @classmethod
    @logUsage
    def createItemTypeSpecs(cls):
        cls.ITEM_TYPE_SPECS = OrderedDict()
        for item_type in cls.ITEM_TYPES:
            cls.ITEM_TYPE_SPECS[item_type] = dict()
            cls.ITEM_TYPE_SPECS[item_type]["attributes"] = OrderedDict()
            cls.ITEM_TYPE_SPECS[item_type]["default_amount"] = int()
            cls.createItemTypeDescriptor(item_type = item_type, descriptor = item_type)
            cls.createItemTypeAttribute(item_type = item_type, attributes = ["name"], content_type = NameType())
            cls.createItemTypeAttribute(item_type = item_type, attributes = ["label"], content_type = LabelType())

    @classmethod
    @logUsage
    def reloadConfigFile(cls):
        """
        Reads a configuration file to flesh out user-interface semantics and formats for the hard-coded structures.
        Method is titled with 'reload' as the process will have already been called once during initial import.
        Note: Currently references the default configuration file, but can be modified in the future.
        """
        config_path = cls.CONFIG_PATH
        logger.info("Attempting to generate Optima Core {0} settings from configuration file.".format(displayName(cls.NAME)))
        logger.info("Location... {0}".format(config_path))
        cp = configparser.ConfigParser()
        cp.read(config_path)

        def transferFormatVariables(specs, config_section):
            """
            Read in optional format variables for writing default attribute content.
            This can be defined across a page or specifically for an attribute.
            """
            for format_variable_key in ExcelSettings.FORMAT_VARIABLE_KEYS:
                try: 
                    value_overwrite = float(getConfigValue(config = cp, section = config_section, option = format_variable_key, mute_warnings = True))
                    specs[format_variable_key] = value_overwrite
                except ValueError: logger.warning("Configuration file has an entry for '{0}' in section '{1}' that cannot be converted to a float. "
                                                  "Using a default value.".format(format_variable_key, config_section))
                except: pass
        
        # Flesh out page details.
        for page_key in cls.PAGE_KEYS:
            # Read in required page title.
            try: cls.PAGE_SPECS[page_key]["title"] = getConfigValue(config = cp, section = SS.DEFAULT_SPACE_NAME.join(["page",page_key]), option = "title")
            except:
                logger.error("Configuration loading process failed. Every page in a workbook needs a title.")
                raise
            transferFormatVariables(specs = cls.PAGE_SPECS[page_key], config_section = SS.DEFAULT_SPACE_NAME.join(["page",page_key]))
            
        # Flesh out item-type details.
        for item_type in cls.ITEM_TYPE_SPECS:
            try: cls.ITEM_TYPE_SPECS[item_type]["default_amount"] = int(getConfigValue(config = cp, section = SS.DEFAULT_SPACE_NAME.join(["itemtype",item_type]), option = "default_amount"))
            except: logger.warning("Configuration file cannot find a valid 'default_amount' for item type '{0}', so these items will not be constructed in templates by default.".format(item_type))
            try: descriptor = getConfigValue(config = cp, section = SS.DEFAULT_SPACE_NAME.join(["itemtype",item_type]), option = "descriptor")
            except:
                logger.warning("Configuration file cannot find a 'descriptor' for item type '{0}', so the descriptor will be the key itself.".format(item_type))
                continue
            cls.createItemTypeDescriptor(item_type = item_type, descriptor = descriptor)
        
            for attribute in cls.ITEM_TYPE_SPECS[item_type]["attributes"]:
                if not "ref_item_type" in cls.ITEM_TYPE_SPECS[item_type]["attributes"][attribute]:
                    # Read in attribute header.
                    try: cls.ITEM_TYPE_SPECS[item_type]["attributes"][attribute]["header"] = getConfigValue(config = cp, section = SS.DEFAULT_SPACE_NAME.join(["attribute",item_type,attribute]), option = "header")
                    except: pass
                    # Read in attribute comment.
                    try: cls.ITEM_TYPE_SPECS[item_type]["attributes"][attribute]["comment"] = getConfigValue(config = cp, section = SS.DEFAULT_SPACE_NAME.join(["attribute",item_type,attribute]), option = "comment")
                    except: pass
                    # Read in optional prefix for writing default attribute content.
                    try: cls.ITEM_TYPE_SPECS[item_type]["attributes"][attribute]["prefix"] = getConfigValue(config = cp, section = SS.DEFAULT_SPACE_NAME.join(["attribute",item_type,attribute]), option = "prefix", mute_warnings = True)
                    except: pass
                    transferFormatVariables(specs = cls.ITEM_TYPE_SPECS[item_type]["attributes"][attribute], config_section = SS.DEFAULT_SPACE_NAME.join(["attribute",item_type,attribute]))

        #import pprint
        #pprint.pprint(cls.PAGE_SPECS)
        #pprint.pprint(cls.ITEM_TYPE_SPECS)

        logger.info("Optima Core {0} settings successfully generated.".format(displayName(cls.NAME))) 
        return

    @classmethod
    @logUsage
    def elaborateStructure(cls):
        raise OptimaException("Base structural settings class was instructed to elaborate structure. "
                              "This should not happen and suggests that a derived settings class has not overloaded the class method. ")

def createSpecs(undecorated_class):
    """
    Decorator that instructs all structural settings subclasses to create all relevant specifications.
    This decorator is required so that derived methods are defined.
    This is done at the import stage; failure means the class starts off incorrect and an import error is thrown.
    """
    try:
        undecorated_class.createPageSpecs()
        undecorated_class.createItemTypeSpecs()
        undecorated_class.elaborateStructure()
        loadConfigFile(undecorated_class)
    except:
        logger.error("Class '{0}' is unable to access required base class methods for creating specifications. "
                     "Import failed.".format(undecorated_class.__name__))
        raise ImportError
    return undecorated_class

@createSpecs
class FrameworkSettings(BaseStructuralSettings):
    BSS = BaseStructuralSettings
    NAME = SS.WORKBOOK_KEY_FRAMEWORK
    CONFIG_PATH = getOptimaCorePath(subdir=SS.CODEBASE_DIRNAME) + SS.CONFIG_FRAMEWORK_FILENAME

    PAGE_KEYS = [BSS.KEY_POPULATION_ATTRIBUTE, BSS.KEY_COMPARTMENT, "trans", 
                 BSS.KEY_CHARACTERISTIC, BSS.KEY_PARAMETER, BSS.KEY_PROGRAM_TYPE]

    @classmethod
    @logUsage
    def elaborateStructure(cls):
        # Certain framework pages are bijectively associated with an item type, thus sharing a key.
        # Hence, for convenience, link these pages with appropriate detail-column tables.
        for item_type in cls.ITEM_TYPES:
            if item_type in cls.PAGE_SPECS:
                cls.PAGE_SPECS[item_type]["tables"].append(DetailColumns(item_type))

        cls.createItemTypeAttribute(cls.KEY_COMPARTMENT, ["is_source","is_sink","is_junction"], content_type = SwitchType())
        cls.createItemTypeAttribute(cls.KEY_CHARACTERISTIC, ["includes"], 
                                    content_type = ExtraSelfReference(cls.ITEM_TYPE_SPECS, other_item_type = cls.KEY_COMPARTMENT, other_attribute = "name", 
                                                                      own_item_type = cls.KEY_CHARACTERISTIC, own_attribute = "name", is_list = True))
        cls.createItemTypeAttribute(cls.KEY_PARAMETER, ["tag_link"])
        # Subitem type association must be done after all item types and attributes are defined, due to cross-reference formation.
        cls.createItemTypeSubitemTypes(cls.KEY_POPULATION_ATTRIBUTE, [cls.KEY_POPULATION_OPTION])
        cls.createItemTypeSubitemTypes(cls.KEY_PROGRAM_TYPE, [cls.KEY_PROGRAM_ATTRIBUTE])


@createSpecs
class DatabookSettings(BaseStructuralSettings):
    BSS = BaseStructuralSettings
    NAME = SS.WORKBOOK_KEY_DATA
    CONFIG_PATH = getOptimaCorePath(subdir=SS.CODEBASE_DIRNAME) + SS.CONFIG_DATABOOK_FILENAME

    PAGE_KEYS = [BSS.KEY_POPULATION, BSS.KEY_PROGRAM, BSS.KEY_CHARACTERISTIC, BSS.KEY_PARAMETER]

    @classmethod
    @logUsage
    def elaborateStructure(cls):
        cls.PAGE_SPECS[cls.KEY_POPULATION]["tables"].append(DetailColumns(cls.KEY_POPULATION))

        #cls.createItemTypeAttribute(cls.KEY_COMPARTMENT, ["is_source","is_sink","is_junction"])
        #cls.createItemTypeAttribute(cls.KEY_CHARACTERISTIC, ["includes"], 
        #                            content_type = ExtraSelfReference(cls.ITEM_TYPE_SPECS, other_item_type = cls.KEY_COMPARTMENT, other_attribute = "name", 
        #                                                              own_item_type = cls.KEY_CHARACTERISTIC, own_attribute = "name", is_list = True))
        #cls.createItemTypeAttribute(cls.KEY_PARAMETER, ["tag_link"])
        ## Subitem type association must be done after all item types and attributes are defined, due to cross-reference formation.
        #cls.createItemTypeSubitemTypes(cls.KEY_POPULATION_ATTRIBUTE, [cls.KEY_POPULATION_OPTION])
        #cls.createItemTypeSubitemTypes(cls.KEY_PROGRAM_TYPE, [cls.KEY_PROGRAM_ATTRIBUTE])


##@loadConfigFile
#class FrameworkSettings():#BaseStructuralSettings):
#    """
#    Stores the definitions used in creating and reading framework files.
#    Structure is hard-coded and any changes risk disrupting framework operations.
#    UI semantics are parsed from a framework configuration file during the module import phase.
#    Note: As a codebase-specific settings class, there is no need to instantiate it as an object.
#    """
#    #BSS = BaseStructuralSettings    # Abbreviation for convenience.
#    # Define key semantics.
#    KEY_COMPARTMENT = "comp"
#    KEY_CHARACTERISTIC = "charac"
#    KEY_PARAMETER = "par"
#    KEY_POPULATION = "pop"
#    KEY_PROGRAM = "prog"
#    KEY_DATAPAGE = "datapage"

#    TERM_ITEM = "item"
#    TERM_TYPE = "type"
#    TERM_ATTRIBUTE = "att"
#    TERM_OPTION = "opt"

#    # Define compound key semantics.
#    KEY_POPULATION_ATTRIBUTE = KEY_POPULATION + TERM_ATTRIBUTE
#    KEY_POPULATION_OPTION = KEY_POPULATION + TERM_OPTION
#    KEY_PROGRAM_TYPE = KEY_PROGRAM + TERM_TYPE
#    KEY_PROGRAM_ATTRIBUTE = KEY_PROGRAM + TERM_ATTRIBUTE

#    # Construct an ordered list of keys representing pages.
#    PAGE_KEYS = [KEY_POPULATION_ATTRIBUTE, KEY_COMPARTMENT, "trans", KEY_CHARACTERISTIC, KEY_PARAMETER, KEY_PROGRAM_TYPE]

#    # Create key semantics for types that columns can be.
#    COLUMN_TYPE_LABEL = "label"
#    COLUMN_TYPE_NAME = "name"
#    COLUMN_TYPE_SWITCH_DEFAULT_OFF = "switch_off"
#    COLUMN_TYPE_SWITCH_DEFAULT_ON = "switch_on"
#    COLUMN_TYPE_LIST_COMP_CHARAC = "list_comp_charac"
#    COLUMN_TYPES = [COLUMN_TYPE_LABEL, COLUMN_TYPE_NAME, 
#                    COLUMN_TYPE_SWITCH_DEFAULT_OFF, COLUMN_TYPE_SWITCH_DEFAULT_ON,
#                    COLUMN_TYPE_LIST_COMP_CHARAC]
    
#    # Construct a dictionary mapping each page-key to a list of unique keys representing columns.
#    # This ordering describes how a framework template will be constructed.
#    KEY_POPULATION_ATTRIBUTE_LABEL = KEY_POPULATION_ATTRIBUTE + COLUMN_TYPE_LABEL
#    KEY_POPULATION_ATTRIBUTE_NAME = KEY_POPULATION_ATTRIBUTE + COLUMN_TYPE_NAME
#    KEY_POPULATION_OPTION_LABEL = KEY_POPULATION_OPTION + COLUMN_TYPE_LABEL
#    KEY_POPULATION_OPTION_NAME = KEY_POPULATION_OPTION + COLUMN_TYPE_NAME
#    KEY_COMPARTMENT_LABEL = KEY_COMPARTMENT + COLUMN_TYPE_LABEL
#    KEY_COMPARTMENT_NAME = KEY_COMPARTMENT + COLUMN_TYPE_NAME
#    KEY_CHARACTERISTIC_LABEL = KEY_CHARACTERISTIC + COLUMN_TYPE_LABEL
#    KEY_CHARACTERISTIC_NAME = KEY_CHARACTERISTIC + COLUMN_TYPE_NAME
#    KEY_PARAMETER_LABEL = KEY_PARAMETER + COLUMN_TYPE_LABEL
#    KEY_PARAMETER_NAME = KEY_PARAMETER + COLUMN_TYPE_NAME
#    KEY_POPULATION_ATTRIBUTE_LABEL = KEY_POPULATION_ATTRIBUTE + COLUMN_TYPE_LABEL
#    KEY_POPULATION_ATTRIBUTE_NAME = KEY_POPULATION_ATTRIBUTE + COLUMN_TYPE_NAME
#    KEY_PROGRAM_TYPE_LABEL = KEY_PROGRAM_TYPE + COLUMN_TYPE_LABEL
#    KEY_PROGRAM_TYPE_NAME = KEY_PROGRAM_TYPE + COLUMN_TYPE_NAME
#    KEY_PROGRAM_ATTRIBUTE_LABEL = KEY_PROGRAM_ATTRIBUTE + COLUMN_TYPE_LABEL
#    KEY_PROGRAM_ATTRIBUTE_NAME = KEY_PROGRAM_ATTRIBUTE + COLUMN_TYPE_NAME

#    PAGE_COLUMN_KEYS = OrderedDict()
#    for page_key in PAGE_KEYS: PAGE_COLUMN_KEYS[page_key] = []
#    PAGE_COLUMN_KEYS[KEY_POPULATION_ATTRIBUTE] = [KEY_POPULATION_ATTRIBUTE_LABEL, KEY_POPULATION_ATTRIBUTE_NAME, 
#                                                  KEY_POPULATION_OPTION_LABEL, KEY_POPULATION_OPTION_NAME]
#    PAGE_COLUMN_KEYS[KEY_COMPARTMENT] = [KEY_COMPARTMENT_LABEL, KEY_COMPARTMENT_NAME, "sourcetag", "sinktag", "junctiontag"]
#    PAGE_COLUMN_KEYS[KEY_CHARACTERISTIC] = [KEY_CHARACTERISTIC_LABEL, KEY_CHARACTERISTIC_NAME, "characincludes"]
#    PAGE_COLUMN_KEYS[KEY_PARAMETER] = [KEY_PARAMETER_LABEL, KEY_PARAMETER_NAME, "transid"]
#    PAGE_COLUMN_KEYS[KEY_PROGRAM_TYPE] = [KEY_PROGRAM_TYPE_LABEL, KEY_PROGRAM_TYPE_NAME,
#                                          KEY_PROGRAM_ATTRIBUTE_LABEL, KEY_PROGRAM_ATTRIBUTE_NAME]
    
#    # Likewise construct a key dictionary mapping pages to types of items that appear on these pages.
#    # As with columns, item types need unique keys even if associated with different pages.
#    # Note: The order of item-type keys is also important as importing files will start scans through columns associated with the first, i.e. core, item-type key.
#    PAGE_ITEM_TYPES = OrderedDict()
#    for page_key in PAGE_KEYS: PAGE_ITEM_TYPES[page_key] = []
#    PAGE_ITEM_TYPES[KEY_POPULATION_ATTRIBUTE] = ["attitem","optitem"]
#    PAGE_ITEM_TYPES[KEY_COMPARTMENT] = ["compitem"]
#    PAGE_ITEM_TYPES[KEY_CHARACTERISTIC] = ["characitem"]
#    PAGE_ITEM_TYPES[KEY_PARAMETER] = ["paritem"]
#    PAGE_ITEM_TYPES[KEY_PROGRAM_TYPE] = ["progitem","progattitem"]
    
#    # Construct a dictionary of specifications detailing how to construct pages and page columns.
#    # Everything here is hard-coded and abstract, with semantics drawn from a configuration file later.
#    PAGE_SPECS = OrderedDict()
#    COLUMN_SPECS = OrderedDict()
#    for page_key in PAGE_KEYS:
#        PAGE_SPECS[page_key] = dict()  
#        column_count = 0
#        for column_key in PAGE_COLUMN_KEYS[page_key]:
#            if column_key in COLUMN_SPECS: raise OptimaException("Key uniqueness failure. Framework settings specify the same key '{0}' for more than one column.".format(column_key))
#            COLUMN_SPECS[column_key] = dict()
#            # Associate each column with a position value for easy reference.
#            # This is a default number for template creation; column positions may be different in loaded framework files.
#            COLUMN_SPECS[column_key]["default_pos"] = column_count
#            COLUMN_SPECS[column_key]["type"] = None
#            column_count += 1
#            # For convenience, do default typing based on column key here.
#            for column_type in COLUMN_TYPES:
#                if column_key.endswith(column_type):
#                     COLUMN_SPECS[column_key]["type"] = column_type
#    # Non-default types should overwrite defaults here.
#    COLUMN_SPECS["sourcetag"]["type"] = COLUMN_TYPE_SWITCH_DEFAULT_OFF
#    COLUMN_SPECS["sinktag"]["type"] = COLUMN_TYPE_SWITCH_DEFAULT_OFF
#    COLUMN_SPECS["junctiontag"]["type"] = COLUMN_TYPE_SWITCH_DEFAULT_OFF
#    COLUMN_SPECS["characincludes"]["type"] = COLUMN_TYPE_LIST_COMP_CHARAC
    
#    # A mapping from item type descriptors to type-key.
#    ITEM_TYPE_DESCRIPTOR_KEY = dict()
                     
#    # Construct a dictionary of specifications detailing framework-page item types.
#    # Note: For framework files, this dictionary does the heavy lifting; items are iteratively created across columns.
#    # Warning: Incorrect modifications are particularly dangerous here due to the possibility of broken Excel links and subitem recursions.
#    ITEM_TYPE_ATTRIBUTES = ["label","name"]
#    ITEM_TYPE_SPECS = OrderedDict()     # Order is important when running through subitems.
#    for page_key in PAGE_ITEM_TYPES:
#        for item_type in PAGE_ITEM_TYPES[page_key]:
#            if item_type in ITEM_TYPE_SPECS: raise OptimaException("Key uniqueness failure. Framework settings specify the same key '{0}' for more than one item type.".format(item_type))
#            # Map item type back to page key and also provide a string-valued descriptor, i.e. a user-interface label for the type.
#            ITEM_TYPE_SPECS[item_type] = {"page_key":page_key, "descriptor":item_type,
#            # Specify whether item type should include or exclude specified columns.
#            # Then specify a list of column keys to be included or excluded when reading or writing an item of this type.
#            # Many item types involve all columns, so the default is to exclude no columns.
#                                    "inc_not_exc":False, "column_keys":None,
#            # Some item types can be divided into columns and other subitem types; the keys of the latter should be listed.
#                                    "subitem_types":None, 
#            # Factory methods will only generate core page-items; all subitem types to be produced should mark the key of their superitem type.
#            # This chain of references should lead back to a core page item type.
#                                    "superitem_type":None}
#            for attribute in ITEM_TYPE_ATTRIBUTES:
#                ITEM_TYPE_SPECS[item_type]["key_"+attribute] = None
#            ITEM_TYPE_DESCRIPTOR_KEY[ITEM_TYPE_SPECS[item_type]["descriptor"]] = item_type   # Map default descriptors to keys.
#    # Define a default population attribute item type.
#    ITEM_TYPE_SPECS["attitem"]["inc_not_exc"] = True
#    ITEM_TYPE_SPECS["attitem"]["column_keys"] = [KEY_POPULATION_ATTRIBUTE_LABEL, KEY_POPULATION_ATTRIBUTE_NAME]
#    ITEM_TYPE_SPECS["attitem"]["key_label"] = KEY_POPULATION_ATTRIBUTE_LABEL
#    ITEM_TYPE_SPECS["attitem"]["key_name"] = KEY_POPULATION_ATTRIBUTE_NAME
#    ITEM_TYPE_SPECS["attitem"]["subitem_types"] = ["optitem"]
#    # Define a default population option item type.
#    ITEM_TYPE_SPECS["optitem"]["column_keys"] = [KEY_POPULATION_ATTRIBUTE_LABEL, KEY_POPULATION_ATTRIBUTE_NAME]
#    ITEM_TYPE_SPECS["optitem"]["key_label"] = KEY_POPULATION_OPTION_LABEL
#    ITEM_TYPE_SPECS["optitem"]["key_name"] = KEY_POPULATION_OPTION_NAME
#    ITEM_TYPE_SPECS["optitem"]["superitem_type"] = "attitem"
#    # Define a default compartment item type.
#    ITEM_TYPE_SPECS["compitem"]["key_label"] = KEY_COMPARTMENT_LABEL
#    ITEM_TYPE_SPECS["compitem"]["key_name"] = KEY_COMPARTMENT_NAME
#    # Define a default characteristic item type.
#    ITEM_TYPE_SPECS["characitem"]["key_label"] = KEY_CHARACTERISTIC_LABEL
#    ITEM_TYPE_SPECS["characitem"]["key_name"] = KEY_CHARACTERISTIC_NAME
#    # Define a default parameter item type.
#    ITEM_TYPE_SPECS["paritem"]["key_label"] = KEY_PARAMETER_LABEL
#    ITEM_TYPE_SPECS["paritem"]["key_name"] = KEY_PARAMETER_NAME
#    # Define a default program type item type.
#    ITEM_TYPE_SPECS["progitem"]["inc_not_exc"] = True
#    ITEM_TYPE_SPECS["progitem"]["column_keys"] = [KEY_PROGRAM_TYPE_LABEL, KEY_PROGRAM_TYPE_NAME]
#    ITEM_TYPE_SPECS["progitem"]["key_label"] = KEY_PROGRAM_TYPE_LABEL
#    ITEM_TYPE_SPECS["progitem"]["key_name"] = KEY_PROGRAM_TYPE_NAME
#    ITEM_TYPE_SPECS["progitem"]["subitem_types"] = ["progattitem"]
#    # Define a default program type attribute item type.
#    ITEM_TYPE_SPECS["progattitem"]["inc_not_exc"] = True
#    ITEM_TYPE_SPECS["progattitem"]["column_keys"] = [KEY_PROGRAM_ATTRIBUTE_LABEL, KEY_PROGRAM_ATTRIBUTE_NAME]
#    ITEM_TYPE_SPECS["progattitem"]["key_label"] = KEY_PROGRAM_ATTRIBUTE_LABEL
#    ITEM_TYPE_SPECS["progattitem"]["key_name"] = KEY_PROGRAM_ATTRIBUTE_NAME
#    ITEM_TYPE_SPECS["progattitem"]["superitem_type"] = "progitem"
    
                   
#    @classmethod
#    @logUsage
#    def reloadConfigFile(cls):
#        """
#        Reads a framework configuration file and extends the settings to use the semantics and values provided.
#        Method is titled with 'reload' as the process will have already been called once during initial import.
#        Note: Currently references the default configuration file, but can be modified in the future.
#        """
#        config_path = getOptimaCorePath(subdir=SystemSettings.CODEBASE_DIRNAME) + SystemSettings.CONFIG_FRAMEWORK_FILENAME
#        logger.info("Attempting to generate Optima Core framework settings from configuration file.")
#        logger.info("Location... {0}".format(config_path))
#        cp = configparser.ConfigParser()
#        cp.read(config_path)
        
#        # Flesh out page details.
#        for page_key in cls.PAGE_KEYS:
#            # Read in required page title.
#            try: cls.PAGE_SPECS[page_key]["title"] = getConfigValue(config = cp, section = "page_"+page_key, option = "title")
#            except:
#                logger.exception("Framework configuration loading process failed. Every page in a framework file needs a title.")
#                raise
#            # Read in optional page format variables.
#            for format_variable_key in ExcelSettings.FORMAT_VARIABLE_KEYS:
#                try: 
#                    value_overwrite = float(getConfigValue(config = cp, section = "page_"+page_key, option = format_variable_key, mute_warnings = True))
#                    cls.PAGE_SPECS[page_key][format_variable_key] = value_overwrite
#                except ValueError: logger.warning("Framework configuration file for page-key '{0}' has an entry for '{1}' " 
#                                                  "that cannot be converted to a float. Using a default value.".format(page_key, format_variable_key))
#                except: pass
            
#            # Flesh out page column details.
#            for column_key in cls.PAGE_COLUMN_KEYS[page_key]:
#                # Read in required column header.
#                try: cls.COLUMN_SPECS[column_key]["header"] = getConfigValue(config = cp, section = "_".join(["column",column_key]), option = "header")
#                except:
#                    logger.exception("Framework configuration loading process failed. Every column in a framework page needs a header.")
#                    raise
#                # Read in optional column comment.
#                try: cls.COLUMN_SPECS[column_key]["comment"] = getConfigValue(config = cp, section = "_".join(["column",column_key]), option = "comment")
#                except: pass
#                # Read in optional prefix that will prepend default text written into this column.
#                try: cls.COLUMN_SPECS[column_key]["prefix"] = getConfigValue(config = cp, section = "_".join(["column",column_key]), option = "prefix", mute_warnings = True)
#                except: pass
#                # Read in optional column format variables.
#                for format_variable_key in ExcelSettings.FORMAT_VARIABLE_KEYS:
#                    try: 
#                        value_overwrite = float(getConfigValue(config = cp, section = "_".join(["column",column_key]), option = format_variable_key, mute_warnings = True))
#                        cls.COLUMN_SPECS[column_key][format_variable_key] = value_overwrite
#                    except ValueError: logger.warning("Framework configuration file for column-key '{0}' has an entry for '{1}' " 
#                                                      "that cannot be converted to a float. Using a default value.".format(column_key, format_variable_key))
#                    except: pass
            
#        # Flesh out item-type details.
#        for item_type in cls.ITEM_TYPE_SPECS:
#            try: descriptor = getConfigValue(config = cp, section = "itemtype_"+item_type, option = "descriptor")
#            except:
#                logger.warning("Framework configuration file cannot find a descriptor for item type '{0}', so the descriptor will be the key itself.".format(item_type))
#                continue
#            old_descriptor = cls.ITEM_TYPE_SPECS[item_type]["descriptor"]
#            del cls.ITEM_TYPE_DESCRIPTOR_KEY[old_descriptor]
#            cls.ITEM_TYPE_SPECS[item_type]["descriptor"] = descriptor
#            cls.ITEM_TYPE_DESCRIPTOR_KEY[descriptor] = item_type
        
#        logger.info("Optima Core framework settings successfully generated.") 
#        return