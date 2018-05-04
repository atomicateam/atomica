# -*- coding: utf-8 -*-
"""
Atomica project-framework settings file.
Contains metadata describing the construction of a model framework.
The definitions are hard-coded, while interface semantics are drawn from a configuration file.
"""

from sciris.core import odict

from atomica.excel import ExcelSettings
from atomica.parser_config import load_config_file, get_config_value, configparser
from atomica.system import SystemSettings as SS, AtomicaException, logger, atomica_path, display_name


class KeyUniquenessException(AtomicaException):
    def __init__(self, key, object_type, **kwargs):
        message = ("Key uniqueness failure. "
                   "Settings specify the same key '{0}' for more than one '{1}'.".format(key, object_type))
        super(KeyUniquenessException, self).__init__(message, **kwargs)


class TableType(object):
    """ Structure to define a table for workbook IO. """

    def __init__(self): pass


class DetailColumns(TableType):
    """
    Structure to associate a workbook table of detail columns with a specific item type.
    Columns of the table exclude, or include, listed attributes.
    Attribute marked 'name' is an exception and will always appear in this table type as an item ID.
    """

    def __init__(self, item_type, attribute_list=None, exclude_not_include=True):
        super(DetailColumns, self).__init__()
        self.item_type = item_type
        self.exclude_not_include = exclude_not_include
        if attribute_list is None:
            attribute_list = []
        self.attribute_list = attribute_list


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

    def __init__(self, source_item_type, storage_attribute, target_item_type=None, storage_item_type=None):
        super(ConnectionMatrix, self).__init__()
        self.source_item_type = source_item_type
        if target_item_type is None:
            target_item_type = source_item_type
        self.target_item_type = target_item_type
        self.storage_item_type = storage_item_type
        self.storage_attribute = storage_attribute


class TableTemplate(TableType):
    """
    Structure indicating a table should be duplicated for each existing instance of an item type.
    In settings, item key should always be left as None, with template to be instantiated by other external functions.
    Because item instances only exist after framework file is read in, this table type should only appear in databook.
    """

    def __init__(self, item_type, item_key=None):
        super(TableTemplate, self).__init__()
        self.item_type = item_type
        self.item_key = item_key


class TimeDependentValuesEntry(TableTemplate):
    """
    Template table requesting time-dependent values, with each instantiation iterating over an item type.
    Argument 'value_attribute' specifies which attribute within item specs should contain values.
    """

    def __init__(self, iterated_type, value_attribute, **kwargs):
        super(TimeDependentValuesEntry, self).__init__(**kwargs)
        self.iterated_type = iterated_type
        self.value_attribute = value_attribute


class ContentType(object):
    """
    Structure to describe the contents of an item attribute, with optional default value.
    Attempts to enforce storage of contents as an optionally specified enforce type.
    An enforce type of 'None' is always ignored if no default provided.
    If contents are kept as a list, type enforcement and default valuing should be applied to each element.
    """

    def __init__(self, default_value=None, enforce_type=None, is_list=False):
        self.is_list = is_list
        self.default_value = default_value
        self.enforce_type = enforce_type


class IDType(ContentType):
    """
    Structure to associate the contents of an item attribute with code name or display label formats.
    Indicates to the associated attribute that repeat sections in a workbook should reference the initial section.
    Can store reference to 'superitem_type' so that ID is prepended by superitem ID during template-writing operations.
    """

    def __init__(self, name_not_label=True, superitem_type=None):
        super(IDType, self).__init__(enforce_type=str, is_list=False)
        self.name_not_label = name_not_label
        self.superitem_type = superitem_type


class IDRefType(ContentType):
    """
    Structure to associate contents of item attribute with an ID, or lists thereof, belonging to specified item types.
    Argument 'other_item_types' should be a list of other item types that the contents can reference.
    Argument 'attribute' should, assuming standard terminology, be 'name' or 'label'.
    If argument 'self_referencing' is True, the item type of the attribute is also included with other item types. 
    """

    def __init__(self, attribute, item_types=None, self_referencing=False, **kwargs):
        super(IDRefType, self).__init__(**kwargs)
        self.attribute = attribute
        self.other_item_types = item_types
        self.self_referencing = self_referencing


class SwitchType(ContentType):
    """
    Structure to associate the contents of an item attribute with boolean flags.
    Content with no value defaults to the value of argument 'default_on'.
    """

    def __init__(self, default_on=False):
        super(SwitchType, self).__init__(default_value=False, enforce_type=bool, is_list=False)
        self.default_on = default_on
        if default_on:
            self.default_value = True


# TODO: Determine if type is necessary and, if so, implement restrictions.
class TimeSeriesType(ContentType):
    """
    Structure to associate the contents of an item attribute with a TimeSeries object.
    """

    def __init__(self):
        super(TimeSeriesType, self).__init__(is_list=False)


class QuantityFormatType(ContentType):
    """
    Structure to associate the contents of an item attribute with quantity types.
    """

    def __init__(self):
        super(QuantityFormatType, self).__init__()


class BaseStructuralSettings(object):
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
    TERM_DATA = "data"
    TERM_FUNCTION = "func"

    QUANTITY_TYPE_PROBABILITY = "probability"
    QUANTITY_TYPE_DURATION = "duration"
    QUANTITY_TYPE_NUMBER = "number"
    QUANTITY_TYPE_FRACTION = "fraction"
    QUANTITY_TYPE_PROPORTION = "proportion"

    KEY_POPULATION_ATTRIBUTE = KEY_POPULATION + TERM_ATTRIBUTE
    KEY_POPULATION_OPTION = KEY_POPULATION + TERM_OPTION
    KEY_PROGRAM_TYPE = KEY_PROGRAM + TERM_TYPE
    KEY_PROGRAM_ATTRIBUTE = KEY_PROGRAM + TERM_ATTRIBUTE

    ITEM_TYPES = []

    PAGE_KEYS = []  # Derived settings should overwrite this.
    PAGE_SPECS = None  # Class method makes this an ordered dictionary.

    ITEM_TYPE_SPECS = None  # Class method makes this a dictionary.
    ITEM_TYPE_DESCRIPTOR_KEY = odict()  # A mapping from item type descriptors to type-key.

    @classmethod
    def create_page_specs(cls):
        cls.PAGE_SPECS = odict()
        for page_key in cls.PAGE_KEYS:
            cls.PAGE_SPECS[page_key] = {"label": page_key.title(), "can_skip": False, "read_order": 0}
            cls.PAGE_SPECS[page_key]["tables"] = []

    @classmethod
    def create_page_table(cls, item_type, table):
        cls.PAGE_SPECS[item_type]["tables"].append(table)

    @classmethod
    def create_item_type_descriptor(cls, item_type, descriptor):
        if "descriptor" in cls.ITEM_TYPE_SPECS[item_type]:
            old_descriptor = cls.ITEM_TYPE_SPECS[item_type]["descriptor"]
            del cls.ITEM_TYPE_DESCRIPTOR_KEY[old_descriptor]
        cls.ITEM_TYPE_SPECS[item_type]["descriptor"] = descriptor
        cls.ITEM_TYPE_DESCRIPTOR_KEY[descriptor] = item_type

    @classmethod
    def create_item_type_attributes(cls, item_types, attributes, content_type=None):
        for item_type in item_types:
            for attribute in attributes:
                attribute_dict = {"header": SS.DEFAULT_SPACE_LABEL.join([item_type, attribute]).title(),
                                  "comment": ("This column defines a '{0}' attribute "
                                              "for a '{1}' item.".format(attribute, item_type)),
                                  "content_type": content_type}
                cls.ITEM_TYPE_SPECS[item_type]["attributes"][attribute] = attribute_dict

    @classmethod
    def create_item_type_specs(cls):
        cls.ITEM_TYPE_SPECS = odict()
        for item_type in cls.ITEM_TYPES:
            cls.ITEM_TYPE_SPECS[item_type] = odict()
            cls.ITEM_TYPE_SPECS[item_type]["attributes"] = odict()
            cls.ITEM_TYPE_SPECS[item_type]["default_amount"] = int()
            # The following key notes whether the item type appears in workbook instructions.
            cls.ITEM_TYPE_SPECS[item_type]["instruction_allowed"] = False
            # If this item type is a subitem of another item type, the following key notes the superitem.
            cls.ITEM_TYPE_SPECS[item_type]["superitem_type"] = None
            cls.create_item_type_descriptor(item_type=item_type, descriptor=item_type)
            # All items have a code name and display label.
            cls.create_item_type_attributes(item_types=[item_type], attributes=["name"],
                                            content_type=IDType(name_not_label=True))
            cls.create_item_type_attributes(item_types=[item_type], attributes=["label"],
                                            content_type=IDType(name_not_label=False))

    @classmethod
    def create_item_type_subitem_types(cls, item_type, subitem_types):
        for subitem_type in subitem_types:
            attribute_dict = {"ref_item_type": subitem_type}
            cls.ITEM_TYPE_SPECS[item_type]["attributes"][subitem_type + SS.DEFAULT_SUFFIX_PLURAL] = attribute_dict
            cls.ITEM_TYPE_SPECS[subitem_type]["superitem_type"] = item_type
            # Item type specs and ID type contents should have been created and declared before this function.
            # The subitem ID attributes should only need to update references to a superitem.
            # TODO: Decide whether attributes should reference superitem type if item type already does.
            for attribute in ["name", "label"]:
                cls.ITEM_TYPE_SPECS[subitem_type]["attributes"][attribute]["content_type"].superitem_type = item_type

    @classmethod
    def reload_config_file(cls):
        """
        Reads a configuration file to flesh out user-interface semantics and formats for the hard-coded structures.
        Method is titled with 'reload' as the process will have already been called once during initial import.
        Note: Currently references the default configuration file, but can be modified in the future.
        """
        config_path = cls.CONFIG_PATH
        logger.info(
            "Attempting to generate Atomica {0} settings from configuration file.".format(display_name(cls.NAME)))
        logger.info("Location... {0}".format(config_path))
        cp = configparser.ConfigParser()
        cp.read(config_path)

        def transfer_format_variables(specs, config_section):
            """
            Read in optional format variables for writing default attribute content.
            This can be defined across a page or specifically for an attribute.
            """
            for format_variable_key in ExcelSettings.FORMAT_VARIABLE_KEYS:
                try:
                    value_overwrite = float(get_config_value(config=cp, section=config_section,
                                                             option=format_variable_key, mute_warnings=True))
                    specs[format_variable_key] = value_overwrite
                except ValueError:
                    logger.warning("Configuration file has an entry for '{0}' in section '{1}' that cannot be "
                                   "converted to a float. Using a default value.".format(format_variable_key,
                                                                                         config_section))
                except Exception:
                    pass

        # Flesh out page details.
        for page_key in cls.PAGE_KEYS:
            # Read in required page title.
            try:
                cls.PAGE_SPECS[page_key]["label"] = get_config_value(config=cp, section=SS.DEFAULT_SPACE_NAME.join(
                    ["page", page_key]), option="title")
            except Exception:
                logger.error("Configuration loading process failed. Every page in a workbook needs a title.")
                raise
            transfer_format_variables(specs=cls.PAGE_SPECS[page_key],
                                      config_section=SS.DEFAULT_SPACE_NAME.join(["page", page_key]))

        # Flesh out item-type details.
        for item_type in cls.ITEM_TYPE_SPECS:
            try:
                cls.ITEM_TYPE_SPECS[item_type]["default_amount"] = int(
                    get_config_value(config=cp, section=SS.DEFAULT_SPACE_NAME.join(["itemtype", item_type]),
                                     option="default_amount"))
            except Exception:
                logger.warning("Configuration file cannot find a valid 'default_amount' for item type '{0}', "
                               "so these items will not be constructed in templates by default.".format(item_type))
            try:
                descriptor = get_config_value(config=cp, section=SS.DEFAULT_SPACE_NAME.join(["itemtype", item_type]),
                                              option="descriptor")
                cls.create_item_type_descriptor(item_type=item_type, descriptor=descriptor)
            except Exception:
                logger.warning("Configuration file cannot find a valid 'descriptor' for item type '{0}', "
                               "so the descriptor will be the key itself.".format(item_type))

            for attribute in cls.ITEM_TYPE_SPECS[item_type]["attributes"]:
                if "ref_item_type" not in cls.ITEM_TYPE_SPECS[item_type]["attributes"][attribute]:
                    for option in ["header", "comment", "prefix"]:
                        try:
                            config_value = get_config_value(config=cp,
                                                            section=SS.DEFAULT_SPACE_NAME.join(["attribute",
                                                                                              item_type, attribute]),
                                                            option=option)
                            cls.ITEM_TYPE_SPECS[item_type]["attributes"][attribute][option] = config_value
                        except Exception:
                            pass
                    transfer_format_variables(specs=cls.ITEM_TYPE_SPECS[item_type]["attributes"][attribute],
                                              config_section=SS.DEFAULT_SPACE_NAME.join(["attribute",
                                                                                         item_type, attribute]))

        logger.info("Atomica {0} settings successfully generated.".format(display_name(cls.NAME)))
        return

    @classmethod
    def elaborate_structure(cls):
        raise AtomicaException("Base structural settings class was instructed to elaborate structure. "
                               "This should not happen and suggests that a derived settings class "
                               "has not overloaded the class method.")


def create_specs(undecorated_class):
    """
    Decorator that instructs all structural settings subclasses to create all relevant specifications.
    This decorator is required so that derived methods are defined.
    This is done at the import stage; failure means the class starts off incorrect and an import error is thrown.
    """
    #    try:
    undecorated_class.create_page_specs()
    undecorated_class.create_item_type_specs()
    undecorated_class.elaborate_structure()
    load_config_file(undecorated_class)
    #    except:
    #        logger.error("Class '{0}' is unable to process required base class methods for creating specifications. "
    #                     "Import failed.".format(undecorated_class.__name__))
    #        raise ImportError
    return undecorated_class


@create_specs
class FrameworkSettings(BaseStructuralSettings):
    BSS = BaseStructuralSettings
    NAME = SS.STRUCTURE_KEY_FRAMEWORK
    CONFIG_PATH = atomica_path(subdir=SS.CODEBASE_DIRNAME) + SS.CONFIG_FRAMEWORK_FILENAME

    ITEM_TYPES = [BSS.KEY_POPULATION_ATTRIBUTE, BSS.KEY_POPULATION_OPTION,
                  BSS.KEY_COMPARTMENT, BSS.KEY_CHARACTERISTIC, BSS.KEY_PARAMETER,
                  BSS.KEY_PROGRAM_TYPE, BSS.KEY_PROGRAM_ATTRIBUTE, BSS.KEY_DATAPAGE]

    # TODO: Reintroduce BSS.KEY_POPULATION_ATTRIBUTE here when ready to develop population attribute functionality.
    PAGE_KEYS = [BSS.KEY_DATAPAGE, BSS.KEY_COMPARTMENT, BSS.KEY_TRANSITION,
                 BSS.KEY_CHARACTERISTIC, BSS.KEY_PARAMETER, BSS.KEY_PROGRAM_TYPE]

    @classmethod
    def elaborate_structure(cls):
        # Certain framework pages are bijectively associated with an item type, thus sharing a key.
        # Hence, for convenience, link these pages with appropriate detail-column tables.
        # Also make sure all item types appear in framework instructions.
        for item_type in cls.ITEM_TYPES:
            cls.ITEM_TYPE_SPECS[item_type]["instruction_allowed"] = True
            if item_type in cls.PAGE_SPECS:
                if item_type == cls.KEY_DATAPAGE:
                    table = DetailColumns(item_type, attribute_list=["label"],
                                          exclude_not_include=False)
                elif item_type == cls.KEY_PARAMETER:
                    table = DetailColumns(item_type, attribute_list=["links", "dependencies"],
                                          exclude_not_include=True)
                else:
                    table = DetailColumns(item_type)
                cls.PAGE_SPECS[item_type]["tables"].append(table)
        cls.PAGE_SPECS[cls.KEY_DATAPAGE]["can_skip"] = True
        cls.PAGE_SPECS[cls.KEY_TRANSITION][
            "read_order"] = 1  # Ensure that transition matrix is read after parameter page.
        cls.PAGE_SPECS[cls.KEY_TRANSITION]["tables"].append(ConnectionMatrix(source_item_type=cls.KEY_COMPARTMENT,
                                                                             storage_item_type=cls.KEY_PARAMETER,
                                                                             storage_attribute="links"))

        cls.create_item_type_attributes([cls.KEY_COMPARTMENT], ["is_source", "is_sink", "is_junction"],
                                        content_type=SwitchType())
        cls.create_item_type_attributes([cls.KEY_COMPARTMENT], ["setup_weight"],
                                        content_type=ContentType(enforce_type=float, default_value=1))
        cls.create_item_type_attributes([cls.KEY_CHARACTERISTIC], ["setup_weight"],
                                        content_type=ContentType(enforce_type=float, default_value=1))
        cls.create_item_type_attributes([cls.KEY_CHARACTERISTIC], ["includes"],
                                        content_type=IDRefType(attribute="name", item_types=[cls.KEY_COMPARTMENT],
                                                               self_referencing=True, is_list=True))
        cls.create_item_type_attributes([cls.KEY_CHARACTERISTIC], ["denominator"],
                                        content_type=IDRefType(attribute="name", self_referencing=True))
        cls.create_item_type_attributes([cls.KEY_CHARACTERISTIC], ["default_value"])
        cls.create_item_type_attributes([cls.KEY_PARAMETER], ["format"],
                                        content_type=QuantityFormatType())
        cls.create_item_type_attributes([cls.KEY_PARAMETER], ["default_value", cls.TERM_FUNCTION, "dependencies"])
        cls.create_item_type_attributes([cls.KEY_PARAMETER], ["links"], content_type=ContentType(is_list=True))
        cls.create_item_type_attributes([cls.KEY_DATAPAGE],
                                        ["read_order", "refer_to_settings"] + ExcelSettings.FORMAT_VARIABLE_KEYS)
        cls.create_item_type_attributes([cls.KEY_DATAPAGE], ["tables"], content_type=ContentType(is_list=True))
        cls.create_item_type_attributes([cls.KEY_DATAPAGE], ["can_skip"], content_type=SwitchType())
        # TODO: ELABORATE DATA PAGE.
        cls.create_item_type_attributes([cls.KEY_COMPARTMENT, cls.KEY_CHARACTERISTIC, cls.KEY_PARAMETER],
                                        [cls.KEY_DATAPAGE],
                                        content_type=IDRefType(attribute="name", item_types=[cls.KEY_DATAPAGE]))
        cls.create_item_type_attributes([cls.KEY_COMPARTMENT, cls.KEY_CHARACTERISTIC, cls.KEY_PARAMETER],
                                        ["datapage_order"],
                                        content_type=ContentType(enforce_type=int))
        # Subitem type association is done after item types and attributes are defined, due to cross-referencing.
        cls.create_item_type_subitem_types(cls.KEY_POPULATION_ATTRIBUTE, [cls.KEY_POPULATION_OPTION])
        cls.create_item_type_subitem_types(cls.KEY_PROGRAM_TYPE, [cls.KEY_PROGRAM_ATTRIBUTE])


@create_specs
class DataSettings(BaseStructuralSettings):
    BSS = BaseStructuralSettings
    NAME = SS.STRUCTURE_KEY_DATA
    CONFIG_PATH = atomica_path(subdir=SS.CODEBASE_DIRNAME) + SS.CONFIG_DATABOOK_FILENAME

    ITEM_TYPES = [BSS.KEY_COMPARTMENT, BSS.KEY_CHARACTERISTIC, BSS.KEY_PARAMETER, BSS.KEY_POPULATION, BSS.KEY_PROGRAM]

    PAGE_KEYS = [BSS.KEY_POPULATION, BSS.KEY_PROGRAM, BSS.KEY_CHARACTERISTIC, BSS.KEY_PARAMETER]

    @classmethod
    def elaborate_structure(cls):
        cls.ITEM_TYPE_SPECS[cls.KEY_POPULATION]["instruction_allowed"] = True
        cls.ITEM_TYPE_SPECS[cls.KEY_PROGRAM]["instruction_allowed"] = True

        # TODO: Determine how programs in the databook work.
        # cls.create_item_type_attributes(cls.KEY_PROGRAM, ["target_pops"],
        #                                 IDRefType(attribute = "name", item_types = [cls.KEY_POPULATION]))
        cls.create_item_type_attributes([cls.KEY_COMPARTMENT], [cls.TERM_DATA], TimeSeriesType())
        cls.create_item_type_attributes([cls.KEY_CHARACTERISTIC], [cls.TERM_DATA], TimeSeriesType())
        cls.create_item_type_attributes([cls.KEY_PARAMETER], [cls.TERM_DATA], TimeSeriesType())

        cls.PAGE_SPECS[cls.KEY_POPULATION]["tables"].append(DetailColumns(item_type=cls.KEY_POPULATION))
        cls.PAGE_SPECS[cls.KEY_PROGRAM]["tables"].append(DetailColumns(item_type=cls.KEY_PROGRAM))
        # TODO: Enable other connection matrices.
        # cls.PAGE_SPECS[cls.KEY_PROGRAM]["tables"].append(ConnectionMatrix(source_item_type = cls.KEY_PROGRAM,
        #                                                                  target_item_type = cls.KEY_POPULATION,
        #                                                                  storage_attribute = "target_pops"))
        cls.PAGE_SPECS[cls.KEY_PARAMETER]["tables"].append(TimeDependentValuesEntry(item_type=cls.KEY_PARAMETER,
                                                                                    iterated_type=cls.KEY_POPULATION,
                                                                                    value_attribute=cls.TERM_DATA))
        charac_tables = cls.PAGE_SPECS[cls.KEY_CHARACTERISTIC]["tables"]
        charac_tables.append(TimeDependentValuesEntry(item_type=cls.KEY_COMPARTMENT,
                                                      iterated_type=cls.KEY_POPULATION,
                                                      value_attribute=cls.TERM_DATA))
        cls.PAGE_SPECS[cls.KEY_CHARACTERISTIC]["tables"].append(
            TimeDependentValuesEntry(item_type=cls.KEY_CHARACTERISTIC,
                                     iterated_type=cls.KEY_POPULATION,
                                     value_attribute=cls.TERM_DATA))
