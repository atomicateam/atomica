from atomica.system import AtomicaException, display_name, SystemSettings as SS
from atomica.structure_settings import FrameworkSettings as FS, DataSettings as DS


class WorkbookTypeException(AtomicaException):
    def __init__(self, workbook_type, **kwargs):
        available_workbook_types = [SS.STRUCTURE_KEY_FRAMEWORK, SS.STRUCTURE_KEY_DATA]
        message = ("Unable to operate read and write processes for a workbook of type '{0}'. "
                   "Available options are: '{1}'".format(workbook_type, "' or '".join(available_workbook_types)))
        super(WorkbookTypeException, self).__init__(message, **kwargs)


class WorkbookRequirementException(AtomicaException):
    def __init__(self, workbook_type, requirement_type, **kwargs):
        message = ("Select {0} IO operations cannot proceed without a '{1}' being provided. "
                   "Abandoning workbook IO.".format(display_name(workbook_type), requirement_type))
        super(WorkbookRequirementException, self).__init__(message, **kwargs)


def get_workbook_references(framework=None, workbook_type=None, refer_to_settings=False):
    ref_dict = dict()
    if workbook_type == SS.STRUCTURE_KEY_FRAMEWORK:
        ref_dict["page_keys"] = FS.PAGE_KEYS
        ref_dict["page_specs"] = FS.PAGE_SPECS
        ref_dict["item_type_specs"] = FS.ITEM_TYPE_SPECS
        ref_dict["item_specs"] = dict()
    elif workbook_type == SS.STRUCTURE_KEY_DATA:
        if framework is None:
            raise WorkbookRequirementException(workbook_type=SS.STRUCTURE_KEY_DATA, requirement_type="ProjectFramework")
        if refer_to_settings is True:
            ref_dict["page_keys"] = DS.PAGE_KEYS
            ref_dict["page_specs"] = DS.PAGE_SPECS
        else:
            ref_dict["page_keys"] = framework.specs[FS.KEY_DATAPAGE].keys()
            ref_dict["page_specs"] = framework.specs[FS.KEY_DATAPAGE]
        ref_dict["item_type_specs"] = DS.ITEM_TYPE_SPECS
        ref_dict["item_specs"] = framework.specs
    else:
        raise WorkbookTypeException(workbook_type)
    return ref_dict


def get_workbook_page_keys(framework=None, workbook_type=None):
    ref_dict = get_workbook_references(framework=framework, workbook_type=workbook_type)
    return ref_dict["page_keys"]


def get_workbook_page_specs(framework=None, workbook_type=None):
    ref_dict = get_workbook_references(framework=framework, workbook_type=workbook_type)
    return ref_dict["page_specs"]


def get_workbook_page_spec(page_key, framework=None, workbook_type=None):
    ref_dict = get_workbook_references(framework=framework, workbook_type=workbook_type)
    if "refer_to_settings" in ref_dict["page_specs"][page_key] and \
            ref_dict["page_specs"][page_key]["refer_to_settings"] is True:
        ref_dict = get_workbook_references(framework=framework, workbook_type=workbook_type, refer_to_settings=True)
    return ref_dict["page_specs"][page_key]


def get_workbook_item_type_specs(framework=None, workbook_type=None):
    ref_dict = get_workbook_references(framework=framework, workbook_type=workbook_type)
    return ref_dict["item_type_specs"]


def get_workbook_item_specs(framework=None, workbook_type=None):
    """
    Get instantiated item specifications to aid in the construction of workbook.
    Note that none exist during framework construction.
    In contrast, databook construction has all item instances available in the framework.
    """
    ref_dict = get_workbook_references(framework=framework, workbook_type=workbook_type)
    return ref_dict["item_specs"]
