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
from copy import deepcopy as dcp

class KeyUniquenessException(OptimaException):
    def __init__(self, key, object_type, **kwargs):
        message = ("Key uniqueness failure. Settings specify the same key '{0}' for more than one '{1}'.".format(key, object_type))
        return super().__init__(message, **kwargs)

class TableType(object):
    """ Lightweight structure to define a table for workbook IO. """
    def __init__(self): pass
class DetailColumns(TableType):
    """ Structure to associate a workbook table of detail columns with a specific item type. """
    def __init__(self, item_type):
        super(DetailColumns,self).__init__()
        self.item_type = item_type
class TableTemplate(TableType):
    """
    Structure indicating a table should be duplicated for each existing instance of an item type.
    In settings, item key should always be left as None, with the template to be instantiated by other external functions.
    Because instances of an item only exist after a framework file is read in, this table type only appears in a databook.
    """
    def __init__(self, item_type, item_key = None):
        super(TableTemplate,self).__init__()
        self.item_type = item_type
        self.item_key = item_key
class TimeDependentValuesEntry(TableTemplate):
    """ Template table requesting time-dependent values, with each instantiation iterating over an item type. """
    def __init__(self, iterated_type, **kwargs):
        super(TimeDependentValuesEntry,self).__init__(**kwargs)
        self.iterated_type = iterated_type

class ContentType(object):
    """ Lightweight structure to associate the contents of an item attribute with rules for IO. """
    def __init__(self, is_list = False): self.is_list = is_list
class LabelType(ContentType):
    """
    Structure to associate the contents of an item attribute with display label formats.
    Indicates to the associated attribute that repeat sections in a workbook should reference the initial section.
    Any attribute with this content type should be marked with a True value for "is_ref" to utilize referencing rules.
    """
    def __init__(self): super(LabelType,self).__init__()
class NameType(ContentType):
    """
    Structure to associate the contents of an item attribute with code name formats.
    Indicates to the associated attribute that repeat sections in a workbook should reference the initial section.
    Any attribute with this content type should be marked with a True value for "is_ref" to utilize referencing rules.
    """
    def __init__(self): super(NameType,self).__init__()
class SwitchType(ContentType):
    """ Structure to associate the contents of an item attribute with boolean flags. """
    def __init__(self, default_on = False, **kwargs):
        super(SwitchType,self).__init__(**kwargs)
        self.default_on = default_on
class AttributeReference(ContentType):
    """ Structure to have the contents of an item type attribute reference those of another item type attribute. """
    def __init__(self, item_type_specs, other_item_type, other_attribute, **kwargs):
        super(AttributeReference,self).__init__(**kwargs)
        self.other_item_type = other_item_type
        self.other_attribute = other_attribute
        item_type_specs[other_item_type]["attributes"][other_attribute]["is_ref"] = True
class SuperReference(AttributeReference):
    """
    Structure to have the contents of an item type attribute reference those of a superitem type attribute.
    Contents for the attribute will be produced as usual, but prepended by values of the superitem type attribute.
    """
    def __init__(self, **kwargs): super(SuperReference,self).__init__(**kwargs)
class ExtraSelfReference(AttributeReference):
    """
    Structure to have the contents of an item type attribute reference those of another item type attribute.
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

    ITEM_TYPE_SPECS = None                  # Class method makes this a dictionary.
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
    def createItemTypeAttribute(cls, item_type, attributes, content_type = None, is_ref = False):
        for attribute in attributes:
            attribute_dict = {"header":SS.DEFAULT_SPACE_LABEL.join([item_type, attribute]).title(),
                              "comment":"This column defines a '{0}' attribute for a '{1}' item.".format(attribute, item_type),
                              "content_type":content_type}
            if is_ref: attribute_dict["is_ref"] = True
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
        cls.ITEM_TYPE_SPECS = dict()
        for item_type in cls.ITEM_TYPES:
            cls.ITEM_TYPE_SPECS[item_type] = dict()
            cls.ITEM_TYPE_SPECS[item_type]["attributes"] = OrderedDict()
            cls.ITEM_TYPE_SPECS[item_type]["default_amount"] = int()
            cls.createItemTypeDescriptor(item_type = item_type, descriptor = item_type)
            # All items have a code name and display label.
            # As they are frequently used multiple times in workbooks as table keys, they must be marked as references so that initial content is linked to by cloned content.
            cls.createItemTypeAttribute(item_type = item_type, attributes = ["label"], content_type = LabelType(), is_ref = True)
            cls.createItemTypeAttribute(item_type = item_type, attributes = ["name"], content_type = NameType(), is_ref = True)

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
            try:
                descriptor = getConfigValue(config = cp, section = SS.DEFAULT_SPACE_NAME.join(["itemtype",item_type]), option = "descriptor")
                cls.createItemTypeDescriptor(item_type = item_type, descriptor = descriptor)
            except:
                logger.warning("Configuration file cannot find a valid 'descriptor' for item type '{0}', so the descriptor will be the key itself.".format(item_type))
        
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

    ITEM_TYPES = dcp(BSS.ITEM_TYPES)
    ITEM_TYPES.extend([BSS.KEY_POPULATION, BSS.KEY_PROGRAM])

    PAGE_KEYS = [BSS.KEY_POPULATION, BSS.KEY_PROGRAM, BSS.KEY_CHARACTERISTIC, BSS.KEY_PARAMETER]

    @classmethod
    @logUsage
    def elaborateStructure(cls):
        cls.createItemTypeAttribute(cls.KEY_CHARACTERISTIC, ["assumption"])
        cls.createItemTypeAttribute(cls.KEY_CHARACTERISTIC, ["t"])
        cls.createItemTypeAttribute(cls.KEY_CHARACTERISTIC, ["val"])

        cls.PAGE_SPECS[cls.KEY_POPULATION]["tables"].append(DetailColumns(item_type = cls.KEY_POPULATION))
        cls.PAGE_SPECS[cls.KEY_PROGRAM]["tables"].append(DetailColumns(item_type = cls.KEY_PROGRAM))
        cls.PAGE_SPECS[cls.KEY_CHARACTERISTIC]["tables"].append(TimeDependentValuesEntry(item_type = cls.KEY_CHARACTERISTIC,
                                                                                         iterated_type = cls.KEY_POPULATION))
        cls.PAGE_SPECS[cls.KEY_PARAMETER]["tables"].append(TimeDependentValuesEntry(item_type = cls.KEY_PARAMETER,
                                                                                    iterated_type = cls.KEY_POPULATION))