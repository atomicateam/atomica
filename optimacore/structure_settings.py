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
    """ Structure to define a table for workbook IO. """
    def __init__(self): pass
class DetailColumns(TableType):
    """ Structure to associate a workbook table of detail columns with a specific item type. """
    def __init__(self, item_type):
        super(DetailColumns,self).__init__()
        self.item_type = item_type
class ConnectionMatrix(TableType):
    """
    Structure to define a matrix that connects two item types together.
    The connections are directional from row headers, e.g. the zeroth column, to column headers, e.g. the zeroth row.
    If no target item type is specified, the connections are between the same type of item.
    If no storage item type is specified, all values are stored in a dictionary within source item specs.
    In this case, the attribute containing the dict is 'storage_attribute' and it is keyed by target item.
    However, if storage item type is specified, the linking value is considered to be a 'name' of this type.
    A list of tuples containing source and target items is stored under 'storage_attribute'.
    """
    def __init__(self, source_item_type, storage_attribute, target_item_type = None, storage_item_type = None):
        super(ConnectionMatrix,self).__init__()
        self.source_item_type = source_item_type
        if target_item_type is None: target_item_type = source_item_type
        self.target_item_type = target_item_type
        self.storage_item_type = storage_item_type
        self.storage_attribute = storage_attribute
class TableTemplate(TableType):
    """
    Structure indicating a table should be duplicated for each existing instance of an item type.
    In settings, item key should always be left as None, with the template to be instantiated by other external functions.
    Because instances of an item only exist after a framework file is read in, this table type should only appear in a databook.
    """
    def __init__(self, item_type, item_key = None):
        super(TableTemplate,self).__init__()
        self.item_type = item_type
        self.item_key = item_key
class TimeDependentValuesEntry(TableTemplate):
    """
    Template table requesting time-dependent values, with each instantiation iterating over an item type.
    Argument 'value_attribute' specifies which attribute within item specs should contain values.
    """
    def __init__(self, iterated_type, value_attribute, **kwargs):
        super(TimeDependentValuesEntry,self).__init__(**kwargs)
        self.iterated_type = iterated_type
        self.value_attribute = value_attribute

class ContentType(object):
    """ Structure to describe the contents of an item attribute. """
    def __init__(self, is_list = False): self.is_list = is_list
class IDType(ContentType):
    """
    Structure to associate the contents of an item attribute with code name or display label formats.
    Indicates to the associated attribute that repeat sections in a workbook should reference the initial section.
    Can store a reference to a 'superitem_type' so that ID is prepended by the ID of the superitem during template-writing operations.
    """
    def __init__(self, name_not_label = True, superitem_type = None): 
        super(IDType,self).__init__(is_list = False)
        self.name_not_label = name_not_label
        self.superitem_type = superitem_type
class IDRefListType(ContentType):
    """
    Structure to associate the contents of an item attribute with lists of IDs belonging to items of specified types.
    Argument 'other_item_types' should be a list of other item types that the contents can reference.
    Argument 'attribute' should, assuming standard terminology, be 'name' or 'label'.
    If argument 'self_referencing' is True, the item type of the attribute is also included with other item types. 
    """
    def __init__(self, attribute, item_types = None, self_referencing = False):
        super(IDRefListType,self).__init__(is_list = True)
        self.attribute = attribute
        self.other_item_types = item_types
        self.self_referencing = self_referencing
class SwitchType(ContentType):
    """
    Structure to associate the contents of an item attribute with boolean flags.
    Content with no value defaults to the value of argument 'default_on'.
    """
    def __init__(self, default_on = False):
        super(SwitchType,self).__init__(is_list = False)
        self.default_on = default_on
# TODO: Determine if type is necessary and, if so, implement restrictions.
class TimeSeriesType(ContentType):
    """
    Structure to associate the contents of an item attribute with a TimeSeries object.
    """
    def __init__(self):
        super(TimeSeriesType,self).__init__(is_list = False)



class BaseStructuralSettings():
    NAME = "general_workbook"
    CONFIG_PATH = str()

    KEY_COMPARTMENT = "comp"
    KEY_CHARACTERISTIC = "charac"
    KEY_TRANSITION = "trans"
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
    def createPageSpecs(cls):
        cls.PAGE_SPECS = OrderedDict()
        for page_key in cls.PAGE_KEYS:
            cls.PAGE_SPECS[page_key] = {"title":page_key.title()}
            cls.PAGE_SPECS[page_key]["tables"] = []

    @classmethod
    @logUsage
    def createPageTable(cls, item_type, table):
        cls.PAGE_SPECS[item_type]["tables"].append(table)

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
    def createItemTypeAttributes(cls, item_type, attributes, content_type = None):
        for attribute in attributes:
            attribute_dict = {"header":SS.DEFAULT_SPACE_LABEL.join([item_type, attribute]).title(),
                              "comment":"This column defines a '{0}' attribute for a '{1}' item.".format(attribute, item_type),
                              "content_type":content_type}
            cls.ITEM_TYPE_SPECS[item_type]["attributes"][attribute] = attribute_dict
    
    @classmethod
    @logUsage
    def createItemTypeSpecs(cls):
        cls.ITEM_TYPE_SPECS = dict()
        for item_type in cls.ITEM_TYPES:
            cls.ITEM_TYPE_SPECS[item_type] = dict()
            cls.ITEM_TYPE_SPECS[item_type]["attributes"] = OrderedDict()
            cls.ITEM_TYPE_SPECS[item_type]["default_amount"] = int()
            cls.ITEM_TYPE_SPECS[item_type]["instruction_allowed"] = False   # This key notes whether the item type appears in workbook instructions.
            cls.ITEM_TYPE_SPECS[item_type]["superitem_type"] = None         # If this item type is a subitem of another item type, this key notes the superitem.
            cls.createItemTypeDescriptor(item_type = item_type, descriptor = item_type)
            # All items have a code name and display label.
            cls.createItemTypeAttributes(item_type = item_type, attributes = ["name"], content_type = IDType(name_not_label = True))
            cls.createItemTypeAttributes(item_type = item_type, attributes = ["label"], content_type = IDType(name_not_label = False))

    @classmethod
    @logUsage
    def createItemTypeSubitemTypes(cls, item_type, subitem_types):
        for subitem_type in subitem_types:
            attribute_dict = {"ref_item_type":subitem_type}
            cls.ITEM_TYPE_SPECS[item_type]["attributes"][subitem_type + SS.DEFAULT_SUFFIX_PLURAL] = attribute_dict
            cls.ITEM_TYPE_SPECS[subitem_type]["superitem_type"] = item_type
            # Item type specs and ID type contents should have been created and declared before this function.
            # The subitem ID attributes should only need to update references to a superitem.
            # TODO: Decide whether attributes should reference superitem type if item type already does.
            for attribute in ["name","label"]:
                cls.ITEM_TYPE_SPECS[subitem_type]["attributes"][attribute]["content_type"].superitem_type = item_type

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
        logger.error("Class '{0}' is unable to process required base class methods for creating specifications. "
                     "Import failed.".format(undecorated_class.__name__))
        raise ImportError
    return undecorated_class


@createSpecs
class FrameworkSettings(BaseStructuralSettings):
    BSS = BaseStructuralSettings
    NAME = SS.WORKBOOK_KEY_FRAMEWORK
    CONFIG_PATH = getOptimaCorePath(subdir=SS.CODEBASE_DIRNAME) + SS.CONFIG_FRAMEWORK_FILENAME

    # TODO: Reintroduce BSS.KEY_POPULATION_ATTRIBUTE here when ready to develop population attribute functionality.
    PAGE_KEYS = [BSS.KEY_COMPARTMENT, BSS.KEY_TRANSITION, 
                 BSS.KEY_CHARACTERISTIC, BSS.KEY_PARAMETER, BSS.KEY_PROGRAM_TYPE]

    @classmethod
    @logUsage
    def elaborateStructure(cls):
        # Certain framework pages are bijectively associated with an item type, thus sharing a key.
        # Hence, for convenience, link these pages with appropriate detail-column tables.
        # Also make sure all item types appear in framework instructions.
        for item_type in cls.ITEM_TYPES:
            cls.ITEM_TYPE_SPECS[item_type]["instruction_allowed"] = True
            if item_type in cls.PAGE_SPECS:
                cls.PAGE_SPECS[item_type]["tables"].append(DetailColumns(item_type))
        cls.PAGE_SPECS[cls.KEY_TRANSITION]["tables"].append(ConnectionMatrix(source_item_type = cls.KEY_COMPARTMENT,
                                                                             storage_item_type = cls.KEY_PARAMETER,
                                                                             storage_attribute = "links"))

        cls.createItemTypeAttributes(cls.KEY_COMPARTMENT, ["is_source","is_sink","is_junction"], content_type = SwitchType())
        cls.createItemTypeAttributes(cls.KEY_CHARACTERISTIC, ["includes"], 
                                     content_type = IDRefListType(attribute = "name", item_types = [cls.KEY_COMPARTMENT], self_referencing = True))
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
        cls.ITEM_TYPE_SPECS[cls.KEY_POPULATION]["instruction_allowed"] = True
        cls.ITEM_TYPE_SPECS[cls.KEY_PROGRAM]["instruction_allowed"] = True

        #cls.createItemTypeAttributes(cls.KEY_PROGRAM, ["target_pops"], IDRefListType(attribute = "name", item_types = [cls.KEY_POPULATION]))
        cls.createItemTypeAttributes(cls.KEY_CHARACTERISTIC, ["values"], TimeSeriesType())
        cls.createItemTypeAttributes(cls.KEY_PARAMETER, ["values"], TimeSeriesType())

        cls.PAGE_SPECS[cls.KEY_POPULATION]["tables"].append(DetailColumns(item_type = cls.KEY_POPULATION))
        cls.PAGE_SPECS[cls.KEY_PROGRAM]["tables"].append(DetailColumns(item_type = cls.KEY_PROGRAM))
        # TODO: Enable other connection matrices.
        #cls.PAGE_SPECS[cls.KEY_PROGRAM]["tables"].append(ConnectionMatrix(source_item_type = cls.KEY_PROGRAM, 
        #                                                                  target_item_type = cls.KEY_POPULATION,
        #                                                                  storage_attribute = "target_pops"))
        cls.PAGE_SPECS[cls.KEY_CHARACTERISTIC]["tables"].append(TimeDependentValuesEntry(item_type = cls.KEY_CHARACTERISTIC,
                                                                                         iterated_type = cls.KEY_POPULATION,
                                                                                         value_attribute = "values"))
        cls.PAGE_SPECS[cls.KEY_PARAMETER]["tables"].append(TimeDependentValuesEntry(item_type = cls.KEY_PARAMETER,
                                                                                    iterated_type = cls.KEY_POPULATION,
                                                                                    value_attribute = "values"))