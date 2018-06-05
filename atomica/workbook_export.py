from atomica.system import SystemSettings as SS
from atomica.structure_settings import FrameworkSettings as FS
from atomica.structure_settings import DataSettings as DS
from atomica.excel import ExcelSettings as ES

from atomica.system import logger, AtomicaException, accepts, prepare_filepath, display_name
from atomica.excel import create_standard_excel_formats, create_default_format_variables, create_value_entry_block
from atomica.structure_settings import DetailColumns, TableTemplate, ConnectionMatrix, TimeDependentValuesEntry, \
    IDType, IDRefType, SwitchType, QuantityFormatType
from atomica.workbook_utils import WorkbookTypeException, get_workbook_page_keys, get_workbook_page_spec, \
    get_workbook_item_type_specs, get_workbook_item_specs
from atomica.structure import get_quantity_type_list

from sciris.core import odict, isnumber
from copy import deepcopy as dcp
import xlsxwriter as xw
from xlsxwriter.utility import xl_rowcol_to_cell as xlrc
import numpy as np


class KeyUniquenessException(AtomicaException):
    def __init__(self, key, dict_type, **kwargs):
        if key is None:
            message = ("Key uniqueness failure. A key is used more than once in '{0}'.".format(dict_type))
        else:
            message = ("Key uniqueness failure. Key '{0}' is used more than once in '{1}'.".format(key, dict_type))
        super(KeyUniquenessException, self).__init__(message, **kwargs)


class InvalidReferenceException(AtomicaException):
    def __init__(self, item_type, attribute, ref_item_type, ref_attribute, **kwargs):
        message = ("Workbook construction failed when item '{0}', attribute '{1}', attempted to reference nonexistent "
                   "values, specifically item '{2}', attribute '{3}'. It is possible the referenced attribute values "
                   "are erroneously scheduled to be created later.".format(item_type, attribute,
                                                                           ref_item_type, ref_attribute))
        super(InvalidReferenceException, self).__init__(message, **kwargs)


class WorkbookInstructions(object):
    """ An object that stores instructions for how many items should be created during workbook construction. """

    def __init__(self, workbook_type=None):
        """ Initialize instructions that detail how to construct a workbook. """
        # Every relevant item must be included in a dictionary that lists how many should be created.
        self.num_items = odict()
        if workbook_type == SS.STRUCTURE_KEY_FRAMEWORK:
            item_type_specs = FS.ITEM_TYPE_SPECS
        elif workbook_type == SS.STRUCTURE_KEY_DATA:
            item_type_specs = DS.ITEM_TYPE_SPECS
        else:
            raise WorkbookTypeException(workbook_type)
        for item_type in item_type_specs:
            if item_type_specs[item_type]["instruction_allowed"]:
                self.num_items[item_type] = item_type_specs[item_type]["default_amount"]
        self.data_start = 2000.0
        self.data_end = 2020.0
        self.data_dt = 1.0

    @property
    def tvec(self):
        """ A time vector associated with workbook instructions, typically only used when generating databooks. """
        return np.arange(self.data_start, self.data_end + self.data_dt / 2, self.data_dt)

    @accepts(str, int)
    def update_number_of_items(self, item_type, number):
        """ Overwrite the number of items that will be constructed for the template workbook. """
        try:
            self.num_items[item_type] = number
        except KeyError:
            raise AtomicaException("An attempted update of workbook instructions to produce '{0}' "
                                   "instances of item type '{1}' failed.".format(number, item_type))

    def update_time_vector(self, data_start=None, data_end=None, data_dt=None):
        """ Update the attributes that determine a time vector for workbook instructions. """
        if data_start is not None:
            self.data_start = data_start
        if data_end is not None:
            self.data_end = data_end
        if data_dt is not None:
            self.data_dt = data_dt


def make_instructions(framework=None, data=None, instructions=None, workbook_type=None):
    """
    Generates instructions that detail the number of items pertinent to workbook construction processes.
    If instructions are already provided, they will be used regardless of the presence of any structure.
    Otherwise, if a ProjectFramework or ProjectData structure is available, this will be used in filling out a workbook.
    If relevant structure is unavailable, a default set of instructions will be produced instead.
    This function returns a boolean tag indicating whether to use instructions or not according to the above logic.
    """
    use_instructions = False
    # Check if framework/data is missing for the relevant workbook. If so, use instructions.
    if workbook_type == SS.STRUCTURE_KEY_FRAMEWORK:
        if framework is None:
            use_instructions = True
    elif workbook_type == SS.STRUCTURE_KEY_DATA:
        if data is None:
            use_instructions = True
    else:
        raise WorkbookTypeException(workbook_type)
    # If no instructions are provided, generate a default, even if they will not be used.
    if instructions is None:
        instructions = WorkbookInstructions(workbook_type=workbook_type)
    else:
        use_instructions = True  # If instructions are provided, they must be used.
    return instructions, use_instructions


def create_attribute_cell_content(worksheet, row, col, attribute, item_type, item_type_specs, item_number,
                                  alt_content=None, alt_condition=None,
                                  formats=None, format_key=None, temp_storage=None):
    """ Write default content into the cell of a worksheet corresponding to an attribute of an item. """

    # Determine attribute information and prepare for content production.
    attribute_spec = item_type_specs[item_type]["attributes"][attribute]
    if temp_storage is None:
        temp_storage = odict()
    if formats is None:
        raise AtomicaException("Excel formats have not been passed to workbook table construction.")
    if format_key is None:
        format_key = ES.FORMAT_KEY_CENTER
    cell_format = formats[format_key]

    # Set up default content type and reference information.
    content_type = None
    do_reference = False
    other_item_type = None
    other_attribute = None

    # Determine content type and prepare for referencing if appropriate.
    if "content_type" in attribute_spec:
        content_type = attribute_spec["content_type"]
    if isinstance(content_type, IDRefType):
        do_reference = True
        if content_type.other_item_types is not None:
            other_item_type = content_type.other_item_types[0]
            other_attribute = content_type.attribute

    # Default content is blank.
    content = ""
    sep = ""
    validation_source = None
    rc = xlrc(row, col, True, True)  # Make the reference absolute for user benefits, e.g. copying tables.

    # Content associated with standard content types is set up here.
    if isinstance(content_type, IDType):
        # Prepare for referencing if this attribute has a superitem type.
        if content_type.superitem_type is not None:
            do_reference = True
            other_item_type = content_type.superitem_type
            other_attribute = attribute
        # Name and label attributes, i.e. those of ID type, reference earlier constructions of themselves if possible.
        # This is excluded for subitems due to their complicated form of content construction.
        if not do_reference and item_type in temp_storage and attribute in temp_storage[item_type] \
                and len(temp_storage[item_type][attribute]["list_content"]) > item_number:
            do_reference = True  # Is not a reference type object but will allow one-to-one referencing to take place.
            other_item_type = item_type
            other_attribute = attribute
        # Otherwise construct content with a prefix if provided.
        else:
            content = str(item_number)  # The default content is the number of this item.
            if content_type.name_not_label:
                space = SS.DEFAULT_SPACE_NAME
                sep = SS.DEFAULT_SEPARATOR_NAME
            else:
                space = SS.DEFAULT_SPACE_LABEL
                sep = SS.DEFAULT_SEPARATOR_LABEL
            if "prefix" in attribute_spec:
                content = attribute_spec["prefix"] + space + content
    elif isinstance(content_type, SwitchType):
        validation_source = [SS.DEFAULT_SYMBOL_NO, SS.DEFAULT_SYMBOL_YES]
        if content_type.default_on:
            validation_source.reverse()
        content = validation_source[0]
    elif isinstance(content_type, QuantityFormatType):
        validation_source = [""] + get_quantity_type_list(include_absolute=True, include_relative=True,
                                                          include_special=True)
        content = validation_source[0]
    content_backup = content

    # References to other content are constructed here.
    if do_reference is True:
        list_id = item_number

        # Superitem-based references link subitem attributes to corresponding superitem attributes.
        # The superitem referenced is the last one stored.
        # This is because subitem displays are meant to be created instantly after superitems.
        if isinstance(content_type, IDType) and content_type.superitem_type is not None:
            list_id = -1

        # If there is another item type to reference, proceed with referencing its ID.
        if other_item_type is not None:
            try:
                stored_refs = temp_storage[other_item_type][other_attribute]
            except KeyError:
                raise InvalidReferenceException(item_type=item_type, attribute=attribute, ref_item_type=other_item_type,
                                                ref_attribute=other_attribute)

            # For one-to-one referencing, do not create table content that goes beyond length of the referenced table.
            if len(stored_refs["list_content"]) > list_id:
                content_page = ""
                if not stored_refs["page_title"] == worksheet.name:
                    content_page = "'{0}'!".format(stored_refs["page_title"])
                ref_content = "={0}{1}".format(content_page, stored_refs["list_cell"][list_id])
                ref_content_backup = stored_refs["list_content_backup"][list_id]

                if isinstance(content_type, IDType) and content_type.superitem_type is not None:
                    content = "=CONCATENATE({0},\"{1}\")".format(ref_content.lstrip("="), sep + content)
                    content_backup = ref_content_backup + sep + content_backup
                else:
                    content = ref_content
                    content_backup = ref_content_backup

        # If the content is marked to reference its own item type, append the ID to current content.
        # This reference should be to an ID of the same item a row ago.
        if isinstance(content_type, IDRefType) and content_type.self_referencing and item_number > 0:
            list_id = item_number - 1
            try:
                stored_refs = temp_storage[item_type][content_type.attribute]
            except KeyError:
                raise InvalidReferenceException(item_type=item_type, attribute=attribute, ref_item_type=item_type,
                                                ref_attribute=content_type.attribute)
            content_page = ""
            if not stored_refs["page_title"] == worksheet.name:
                content_page = "'{0}'!".format(stored_refs["page_title"])
            ref_content = "={0}{1}".format(content_page, stored_refs["list_cell"][list_id])
            ref_content_backup = stored_refs["list_content_backup"][list_id]
            if content == "":
                content = ref_content
                content_backup = ref_content_backup
            else:
                if content.startswith("="):
                    content = content.lstrip("=")
                else:
                    content = "\"" + content + "\""
                content = "=CONCATENATE({0},\"{1}\",{2})".format(content, ES.LIST_SEPARATOR, ref_content.lstrip("="))
                content_backup = content_backup + ES.LIST_SEPARATOR + ref_content_backup

    # If content is of ID type, store it for referencing by other relevant attributes later.
    if isinstance(content_type, IDType):
        if item_type not in temp_storage:
            temp_storage[item_type] = {}
        if attribute not in temp_storage[item_type]:
            temp_storage[item_type][attribute] = {"list_content": [], "list_content_backup": [], "list_cell": []}
        # Make sure the attribute does not already have stored values associated with it.
        if not len(temp_storage[item_type][attribute]["list_content"]) > item_number:
            temp_storage[item_type][attribute]["list_content"].append(content)
            temp_storage[item_type][attribute]["list_content_backup"].append(content_backup)
            temp_storage[item_type][attribute]["list_cell"].append(rc)
            temp_storage[item_type][attribute]["page_title"] = worksheet.name

    # Do a final check to see if the content is still blank, in which case apply a default value.
    if content == "" and content_type is not None and content_type.default_value is not None:
        default_value = content_type.default_value
        if default_value is True:
            default_value = SS.DEFAULT_SYMBOL_YES
        if default_value is False:
            default_value = SS.DEFAULT_SYMBOL_NO
        content = default_value

    # Modify content for optional conditions.
    if alt_condition is not None:
        content = "=IF({0},{1},{2})".format(alt_condition,alt_content,content.lstrip("="))

    # Actually write the content, using a backup value where the content is an equation and may not be calculated.
    # This lack of calculation occurs when Excel files are not opened before writing and reading phases.
    # Also validate that the cell only allows certain values.
    if isinstance(content, str) and content.startswith("="):
        worksheet.write_formula(rc, content, cell_format, content_backup)
    else:
        worksheet.write(rc, content, cell_format)
    if validation_source is not None:
        worksheet.data_validation(rc, {"validate": "list", "source": validation_source})

    return content, content_backup


def write_headers_dc(worksheet, table, start_row, start_col, item_type=None, framework=None, data=None,
                     workbook_type=None, formats=None, format_variables=None):
    if item_type is None:
        item_type = table.item_type
    item_type_specs = get_workbook_item_type_specs(framework=framework, workbook_type=workbook_type)
    item_type_spec = item_type_specs[item_type]

    if formats is None:
        raise AtomicaException("Excel formats have not been passed to workbook table construction.")
    if format_variables is None:
        format_variables = create_default_format_variables()
    orig_format_variables = dcp(format_variables)
    format_variables = dcp(orig_format_variables)
    revert_format_variables = False

    row, col, header_column_map = start_row, start_col, odict()
    for attribute in item_type_spec["attributes"]:
        # Ignore explicitly excluded attributes or implicitly not-included attributes for table construction.
        # Item name is always in the table though.
        if not attribute == "name":
            if table.exclude_not_include == (attribute in table.attribute_list):
                continue
        attribute_spec = item_type_spec["attributes"][attribute]
        if "ref_item_type" in attribute_spec:
            _, col, sub_map = write_headers_dc(worksheet=worksheet, table=table,
                                               item_type=attribute_spec["ref_item_type"],
                                               start_row=row, start_col=col,
                                               framework=framework, data=data, workbook_type=workbook_type,
                                               formats=formats, format_variables=format_variables)
            len_map = len(header_column_map)
            len_sub_map = len(sub_map)
            header_column_map.update(sub_map)
            if not len(header_column_map) == len_map + len_sub_map:
                raise KeyUniquenessException(None, "header-column map")
        else:
            for format_variable_key in format_variables:
                if format_variable_key in attribute_spec:
                    revert_format_variables = True
                    format_variables[format_variable_key] = attribute_spec[format_variable_key]
            header = attribute_spec["header"]
            if header in header_column_map:
                raise KeyUniquenessException(header, "header-column map")
            header_column_map[header] = col
            worksheet.write(row, col, header, formats[ES.FORMAT_KEY_CENTER_BOLD])
            if "comment" in attribute_spec:
                header_comment = attribute_spec["comment"]
                worksheet.write_comment(row, col, header_comment,
                                        {"x_scale": format_variables[ES.KEY_COMMENT_XSCALE],
                                         "y_scale": format_variables[ES.KEY_COMMENT_YSCALE]})
            worksheet.set_column(col, col, format_variables[ES.KEY_COLUMN_WIDTH])
            if revert_format_variables:
                format_variables = dcp(orig_format_variables)
                revert_format_variables = False
            col += 1
    row += 1
    next_row, next_col = row, col
    return next_row, next_col, header_column_map


def write_contents_dc(worksheet, table, start_row, header_column_map, item_type=None, framework=None, data=None,
                      instructions=None, workbook_type=None,
                      formats=None, temp_storage=None):
    if item_type is None:
        item_type = table.item_type
    item_type_specs = get_workbook_item_type_specs(framework=framework, workbook_type=workbook_type)
    item_type_spec = item_type_specs[item_type]
    instructions, use_instructions = make_instructions(framework=framework, data=data, instructions=instructions,
                                                       workbook_type=workbook_type)

    if temp_storage is None:
        temp_storage = odict()

    row, new_row = start_row, start_row
    if use_instructions:
        for item_number in range(instructions.num_items[item_type]):
            for attribute in item_type_spec["attributes"]:
                # Ignore explicitly excluded attributes or implicitly not-included attributes for table construction.
                # Item name is always in the table though.
                if not attribute == "name":
                    if table.exclude_not_include == (attribute in table.attribute_list):
                        continue
                attribute_spec = item_type_spec["attributes"][attribute]
                if "ref_item_type" in attribute_spec:
                    sub_row = write_contents_dc(worksheet=worksheet, table=table,
                                                item_type=attribute_spec["ref_item_type"],
                                                start_row=row, header_column_map=header_column_map,
                                                framework=framework, data=data, instructions=instructions,
                                                workbook_type=workbook_type,
                                                formats=formats, temp_storage=temp_storage)
                    new_row = max(new_row, sub_row)
                else:
                    col = header_column_map[attribute_spec["header"]]
                    create_attribute_cell_content(worksheet=worksheet, row=row, col=col,
                                                  attribute=attribute, item_type=item_type,
                                                  item_type_specs=item_type_specs,
                                                  item_number=item_number, formats=formats, temp_storage=temp_storage)
            row = max(new_row, row + 1)
    next_row = row + 1  # Delimit with a blank row.
    return next_row


def write_detail_columns(worksheet, table, start_row, start_col, framework=None, data=None, instructions=None,
                         workbook_type=None, formats=None, format_variables=None, temp_storage=None):
    if temp_storage is None:
        temp_storage = odict()

    row, col = start_row, start_col
    row, _, header_column_map = write_headers_dc(worksheet=worksheet, table=table, start_row=row, start_col=col,
                                                 framework=framework, data=data, workbook_type=workbook_type,
                                                 formats=formats, format_variables=format_variables)
    row = write_contents_dc(worksheet=worksheet, table=table, start_row=row, header_column_map=header_column_map,
                            framework=framework, data=data, instructions=instructions, workbook_type=workbook_type,
                            formats=formats, temp_storage=temp_storage)
    next_row, next_col = row, col
    return next_row, next_col


def write_connection_matrix(worksheet, table, iteration, start_row, start_col,
                            framework=None, data=None, instructions=None,
                            workbook_type=None, formats=None, temp_storage=None):
    item_specs = get_workbook_item_specs(framework=framework, workbook_type=workbook_type)
    item_type_specs = get_workbook_item_type_specs(framework=framework, workbook_type=workbook_type)
    instructions, use_instructions = make_instructions(framework=framework, data=data, instructions=instructions,
                                                       workbook_type=workbook_type)

    if temp_storage is None:
        temp_storage = odict()
    if formats is None:
        raise AtomicaException("Excel formats have not been passed to workbook table construction.")

    source_item_type = table.source_item_type
    target_item_type = table.target_item_type
    # Set up identifier for the item that this connection matrix is constructed for.
    # If the table is not a template, this term will remain none.
    term = None

    row, col = start_row, start_col
    # TODO: Handle the case where construction is based on framework/data contents rather than instructions.
    if use_instructions:
        source_amount = instructions.num_items[source_item_type]
        target_amount = instructions.num_items[target_item_type]
        # In the template case, create 'corner' headers to identify table.
        # TODO: In the non-template case, maybe implement 'corner' headers.
        if table.template_item_type is not None:
            # If instantiated for an item, use that label as the header.
            if table.template_item_key is not None:
                try:
                    term = item_specs[table.template_item_type][table.template_item_key]["label"]
                except KeyError:
                    raise AtomicaException("No instantiation of item type '{0}' exists with the key of "
                                           "'{1}'.".format(table.template_item_type, table.template_item_key))
                worksheet.write(start_row, start_col, term, formats[ES.FORMAT_KEY_CENTER_BOLD])
            # If the instantiation was deferred to this workbook, create content according to iteration number.
            else:
                # Grab the content that is created; the 'backup' content is better as it is a value without equations.
                _, term = create_attribute_cell_content(worksheet=worksheet, row=start_row, col=start_col, attribute="label",
                                                        item_type=table.template_item_type, item_type_specs=item_type_specs,
                                                        item_number=iteration, formats=formats,
                                                        format_key=ES.FORMAT_KEY_CENTER_BOLD, temp_storage=temp_storage)
        target_col = start_col + 1
        # target_keys = list()    # Convenient list to store keys of all target iterated items.
        for item_number in range(target_amount):
            _, target_key = create_attribute_cell_content(worksheet=worksheet, row=start_row, col=target_col,
                                                          attribute="name", item_type=target_item_type,
                                                          item_type_specs=item_type_specs, item_number=item_number, formats=formats,
                                                          format_key=ES.FORMAT_KEY_CENTER_BOLD, temp_storage=temp_storage)
            # target_keys.append(target_key)
            target_col += 1
        source_row = start_row + 1
        for item_number in range(source_amount):
            _, source_key = create_attribute_cell_content(worksheet=worksheet, row=source_row, col=start_col,
                                                          attribute="name", item_type=source_item_type,
                                                          item_type_specs=item_type_specs, item_number=item_number, formats=formats,
                                                          format_key=ES.FORMAT_KEY_CENTER_BOLD, temp_storage=temp_storage)
            # Template connection matrices do not mark connections with an item name and leave the rest blank.
            # Because the matrix is defined for one item, the name of which relates to the header in the corner...
            # The existence of a connection is typically marked by a 'y' with any other value marking an absence.
            if table.template_item_type is not None:
                for other_number in range(target_amount):
                    rc = xlrc(source_row, start_col + other_number + 1)
                    # Disable self-connections.
                    if item_number == other_number and source_item_type == target_item_type:
                        worksheet.write(rc, SS.DEFAULT_SYMBOL_INAPPLICABLE, formats[ES.FORMAT_KEY_CENTER])
                        worksheet.data_validation(rc, {"validate": "list",
                                                       "source": [SS.DEFAULT_SYMBOL_INAPPLICABLE]})
                    else:
                        # Whether connections are marked to exist likely affect whether they appear in other tables.
                        # Store information for referencing elsewhere; this is used for items like transfers.
                        item_type = table.template_item_type
                        source_type = table.source_item_type
                        target_type = table.target_item_type
                        # target_key = target_keys[other_number]
                        if term not in temp_storage[item_type]:
                            temp_storage[item_type][term] = dict()
                        if (source_type,target_type) not in temp_storage[item_type][term]:
                            temp_storage[item_type][term][(source_type,target_type)] = dict()
                        if (item_number, other_number) not in temp_storage[item_type][term][(source_type,target_type)]:
                            temp_storage[item_type][term][(source_type,target_type)][(item_number, other_number)] = dict()
                        temp_storage[item_type][term][(source_type,target_type)][(item_number, other_number)]["cell"] = rc
                        temp_storage[item_type][term][(source_type,target_type)][(item_number, other_number)]["page_title"] = worksheet.name

                        # Actually fill the cell in with a 'yes or no' choice.
                        worksheet.write(rc, SS.DEFAULT_SYMBOL_NO, formats[ES.FORMAT_KEY_CENTER])
                        worksheet.data_validation(rc, {"validate": "list",
                                                       "source": [SS.DEFAULT_SYMBOL_NO, SS.DEFAULT_SYMBOL_YES]})
            source_row += 1
        row = source_row + 1  # Extra row to space out following tables.
        start_row = row  # Update start row down the page for iterated tables.

    next_row, next_col = row, col
    return next_row, next_col


def write_time_dependent_values_entry(worksheet, table, iteration, start_row, start_col,
                                      framework=None, data=None, instructions=None, workbook_type=None,
                                      formats=None, format_variables=None, temp_storage=None):
    item_specs = get_workbook_item_specs(framework=framework, workbook_type=workbook_type)
    item_type_specs = get_workbook_item_type_specs(framework=framework, workbook_type=workbook_type)
    instructions, use_instructions = make_instructions(framework=framework, data=data, instructions=instructions,
                                                       workbook_type=workbook_type)
    if temp_storage is None:
        temp_storage = odict()

    item_type = table.template_item_type
    item_key = table.template_item_key
    iterated_type = table.iterated_type

    if formats is None:
        raise AtomicaException("Excel formats have not been passed to workbook table construction.")
    if format_variables is None:
        format_variables = create_default_format_variables()
    orig_format_variables = dcp(format_variables)
    format_variables = dcp(orig_format_variables)

    row, col = start_row, start_col
    block_col = 1  # Column increment at which data entry block begins.
    # Set up identifier for the item that this TDVE table is constructed for.
    term = None

    # Set up a header for the table relating to the object for which the databook is requesting values.
    attribute = "label"
    attribute_spec = item_type_specs[item_type]["attributes"][attribute]
    for format_variable_key in format_variables:
        if format_variable_key in attribute_spec:
            format_variables[format_variable_key] = attribute_spec[format_variable_key]
    # If instantiated for an item, use that label as the header.
    if item_key is not None:
        try:
            term = item_specs[item_type][item_key]["label"]
        except KeyError:
            raise AtomicaException("No instantiation of item type '{0}' exists with the key of "
                                   "'{1}'.".format(item_type, item_key))
        worksheet.write(start_row, start_col, term, formats[ES.FORMAT_KEY_CENTER_BOLD])
    # If the instantiation was deferred to this workbook, create content according to iteration number.
    else:
        _, term = create_attribute_cell_content(worksheet=worksheet, row=start_row, col=start_col, attribute="label",
                                      item_type=item_type, item_type_specs=item_type_specs,
                                      item_number=iteration, formats=formats,
                                      format_key=ES.FORMAT_KEY_CENTER_BOLD, temp_storage=temp_storage)
    if "comment" in attribute_spec:
        header_comment = attribute_spec["comment"]
        worksheet.write_comment(row, col, header_comment,
                                {"x_scale": format_variables[ES.KEY_COMMENT_XSCALE],
                                 "y_scale": format_variables[ES.KEY_COMMENT_YSCALE]})
    worksheet.set_column(col, col, format_variables[ES.KEY_COLUMN_WIDTH])

    # Create the standard value entry block, extracting the number of items from instructions.
    # TODO: Adjust this for when writing existing values to workbook.
    num_items = 0
    if use_instructions:
        num_items = instructions.num_items[iterated_type]
    # If the table actually iterates over connections between items rather than items themselves...
    # Push the data entry block back and make space for more 'item to item' headers, self-connections excluded.
    if table.iterate_over_links:
        block_col = 3
        num_items = num_items * (num_items - 1)
    default_values = [0.0] * num_items
    # Decide what quantity types, a.k.a. value formats, are allowed for the item.
    if item_type in [FS.KEY_COMPARTMENT,
                     FS.KEY_CHARACTERISTIC]:  # State variables are in number amounts unless normalized.
        if "denominator" in item_specs[item_type][item_key] and \
                item_specs[item_type][item_key]["denominator"] is not None:
            quantity_types = [FS.QUANTITY_TYPE_FRACTION.title()]
        else:
            quantity_types = [FS.QUANTITY_TYPE_NUMBER.title()]
    # Modeller's choice for parameters.
    elif item_type in [FS.KEY_PARAMETER] and \
            "format" in item_specs[item_type][item_key] and not item_specs[item_type][item_key]["format"] is None:
        quantity_types = [item_specs[item_type][item_key]["format"].title()]
        # Make sure proportions do not default to a value of zero.
        if item_specs[item_type][item_key]["format"] == FS.QUANTITY_TYPE_PROPORTION:
            default_values = [1.0] * num_items
    else:
        # User choice if a transfer or a transition parameter.
        if item_type in [FS.KEY_TRANSFER] or (FS.KEY_TRANSITIONS in item_specs[item_type][item_key] and
                                              len(item_specs[item_type][item_key][FS.KEY_TRANSITIONS]) > 0):
            quantity_types = [FS.QUANTITY_TYPE_NUMBER.title(), FS.QUANTITY_TYPE_PROBABILITY.title()]
        # If not a transition, the format of this parameter is meaningless.
        else:
            quantity_types = [SS.DEFAULT_SYMBOL_INAPPLICABLE.title()]
    if item_key is not None and "default_value" in item_specs[item_type][item_key] and \
            item_specs[item_type][item_key]["default_value"] is not None:
        default_values = [item_specs[item_type][item_key]["default_value"]] * num_items
    # TODO: Make sure this is robust when writing from framework/data rather than instructions.
    time_vector = instructions.tvec
    create_value_entry_block(excel_page=worksheet, start_row=start_row, start_col=start_col + block_col,
                             num_items=num_items, time_vector=time_vector,
                             default_values=default_values, formats=formats,
                             quantity_types=quantity_types)

    # Fill in the appropriate 'keys' for the table.
    row += 1
    if use_instructions:
        # Construct row headers for tuples of iterated item type, if appropriate.
        if table.iterate_over_links:
            for source_number in range(instructions.num_items[iterated_type]):
                for target_number in range(instructions.num_items[iterated_type]):
                    if source_number == target_number:
                        continue
                    item_type = table.template_item_type
                    iterated_type = table.iterated_type
                    try:
                        rc = temp_storage[item_type][term][(iterated_type,iterated_type)][(source_number, target_number)]["cell"]
                        page_title = temp_storage[item_type][term][(iterated_type,iterated_type)][(source_number, target_number)]["page_title"]
                        condition_string = "'{0}'!{1}<>\"{2}\"".format(page_title, rc, SS.DEFAULT_SYMBOL_YES)
                    except KeyError:
                        condition_string = None
                    create_attribute_cell_content(worksheet=worksheet, row=row, col=col, attribute="label",
                                                  item_type=iterated_type, item_type_specs=item_type_specs,
                                                  alt_content="\""+SS.DEFAULT_SYMBOL_IGNORE+"\"", alt_condition=condition_string,
                                                  item_number=source_number, formats=formats, temp_storage=temp_storage)
                    rc_check = xlrc(row, col + 2)
                    worksheet.write(row, col + 1, "=IF({0}=\"{1}\",\"{2}\",\"{3}\")".format(rc_check, str(), str(),
                                                                                            SS.DEFAULT_SYMBOL_TO),
                                    formats[ES.FORMAT_KEY_CENTER_BOLD], "")
                    create_attribute_cell_content(worksheet=worksheet, row=row, col=col + 2, attribute="label",
                                                  item_type=iterated_type, item_type_specs=item_type_specs,
                                                  alt_content="\"\"", alt_condition=condition_string,
                                                  item_number=target_number, formats=formats, temp_storage=temp_storage)
                    row += 1
        # Construct row headers for iterated item type.
        else:
            for item_number in range(instructions.num_items[iterated_type]):
                create_attribute_cell_content(worksheet=worksheet, row=row, col=col,
                                              attribute="label", item_type=iterated_type,
                                              item_type_specs=item_type_specs,
                                              item_number=item_number, formats=formats, temp_storage=temp_storage)
                row += 1
    row += 1  # Extra row to space out following tables.

    next_row, next_col = row, col
    return next_row, next_col


def write_table(worksheet, table, start_row, start_col, framework=None, data=None, instructions=None,
                workbook_type=None, formats=None, format_variables=None, temp_storage=None):
    # Check workbook type.
    if workbook_type not in [SS.STRUCTURE_KEY_FRAMEWORK, SS.STRUCTURE_KEY_DATA]:
        raise WorkbookTypeException(workbook_type)
    item_specs = get_workbook_item_specs(framework=framework, workbook_type=workbook_type)

    instructions, use_instructions = make_instructions(framework=framework, data=data, instructions=instructions,
                                                       workbook_type=workbook_type)

    if temp_storage is None:
        temp_storage = odict()

    row, col = start_row, start_col
    if isinstance(table, DetailColumns):
        row, col = write_detail_columns(worksheet=worksheet, table=table, start_row=row, start_col=col,
                                        framework=framework, data=data, instructions=instructions,
                                        workbook_type=workbook_type,
                                        formats=formats, format_variables=format_variables, temp_storage=temp_storage)
    if isinstance(table, TableTemplate):
        iteration_amount = 1
        # If the connection matrix is templated...
        if table.template_item_type is not None:
            # Check if instantiation is deferred.
            # If it is, iterate for the number of template-related items specified by instructions.
            if table.template_item_key is None:
                iteration_amount = instructions.num_items[table.template_item_type]
        if isinstance(table, ConnectionMatrix):
            for iteration in range(iteration_amount):
                row, col = write_connection_matrix(worksheet=worksheet, table=table, iteration=iteration,
                                                   start_row=row, start_col=col,
                                                   framework=framework, data=data, instructions=instructions,
                                                   workbook_type=workbook_type, formats=formats,
                                                   temp_storage=temp_storage)
        if isinstance(table, TimeDependentValuesEntry):
            for iteration in range(iteration_amount):
                row, col = write_time_dependent_values_entry(worksheet=worksheet, table=table, iteration=iteration,
                                                             start_row=row, start_col=col,
                                                             framework=framework, data=data, instructions=instructions,
                                                             workbook_type=workbook_type,
                                                             formats=formats, format_variables=format_variables,
                                                             temp_storage=temp_storage)

    next_row, next_col = row, col
    return next_row, next_col


def write_worksheet(workbook, page_key, framework=None, data=None, instructions=None, workbook_type=None,
                    formats=None, format_variables=None, temp_storage=None):
    page_spec = get_workbook_page_spec(page_key=page_key, framework=framework, workbook_type=workbook_type)
    if len(page_spec["tables"]) == 0:
        return

    # Construct worksheet.
    page_title = page_spec["label"]
    logger.info("Creating page: {0}".format(page_title))
    worksheet = workbook.add_worksheet(page_title)

    # Propagate file-wide format variable values to page-wide format variable values.
    # Create the format variables if they were not passed in from a file-wide context.
    # Overwrite the file-wide defaults if page-based specifics are available in framework settings.
    if format_variables is None:
        format_variables = create_default_format_variables()
    else:
        format_variables = dcp(format_variables)
    for format_variable_key in format_variables:
        if format_variable_key in page_spec:
            format_variables[format_variable_key] = page_spec[format_variable_key]

    # Generate standard formats if they do not exist and construct headers for the page.
    if formats is None:
        formats = create_standard_excel_formats(workbook)

    if temp_storage is None:
        temp_storage = odict()

    # Iteratively construct tables.
    row, col = 0, 0
    for table in page_spec["tables"]:
        row, col = write_table(worksheet=worksheet, table=table, start_row=row, start_col=col,
                               framework=framework, data=data, instructions=instructions, workbook_type=workbook_type,
                               formats=formats, format_variables=format_variables, temp_storage=temp_storage)


# TODO: Decide on what metadata sheet should actually contain and review if data time ranges are still necessary.
def write_reference_worksheet(workbook, framework=None, data=None, instructions=None, workbook_type=None):
    """
    Creates a hidden worksheet for metadata and other values.
    These are useful to store but are not directly part of framework/data.
    """

    if workbook_type == SS.STRUCTURE_KEY_FRAMEWORK:
        return
    instructions, _ = make_instructions(framework=framework, data=data, instructions=instructions,
                                        workbook_type=workbook_type)

    # Construct worksheet.
    page_title = "metadata".title()
    logger.info("Creating page: {0}".format(page_title))
    worksheet = workbook.add_worksheet(page_title)

    # Hard code variables and values.
    worksheet.write(0, 0, "data_start")
    worksheet.write(1, 0, "data_end")
    worksheet.write(2, 0, "data_dt")
    worksheet.write(0, 1, instructions.data_start)
    worksheet.write(1, 1, instructions.data_end)
    worksheet.write(2, 1, instructions.data_dt)

    worksheet.hide()


@accepts(str)
def write_workbook(workbook_path, framework=None, data=None, instructions=None, workbook_type=None):
    page_keys = get_workbook_page_keys(framework=framework, workbook_type=workbook_type)

    logger.info("Constructing a {0}: {1}".format(display_name(workbook_type), workbook_path))

    # Construct workbook and related formats.
    prepare_filepath(workbook_path)
    workbook = xw.Workbook(workbook_path)
    formats = create_standard_excel_formats(workbook)
    format_variables = create_default_format_variables()

    # Create a storage dictionary for values and formulae that may persist between sections.
    temp_storage = odict()

    # Iteratively construct worksheets.
    for page_key in page_keys:
        write_worksheet(workbook=workbook, page_key=page_key,
                        framework=framework, data=data, instructions=instructions, workbook_type=workbook_type,
                        formats=formats, format_variables=format_variables, temp_storage=temp_storage)
    write_reference_worksheet(workbook=workbook, framework=framework, data=data,
                              instructions=instructions, workbook_type=workbook_type)
    workbook.close()

    logger.info("{0} construction complete.".format(display_name(workbook_type, as_title=True)))


# %% COMPLETELY INDEPENDENT CODE TO MAKE A SPREADSHEET FOR PROGRAMS.
# TODO: reconcile these!!!


def makeprogramspreadsheet(filename, pops, progs, datastart=None, dataend=None, verbose=2):
    """ Generate the Atomica programs spreadsheet """

    # An integer argument is given: just create a pops dict using empty entries
    if isnumber(pops):
        npops = pops
        pops = []  # Create real pops list
        for p in range(npops):
            pops.append('Pop %i' % (p + 1))

    if isnumber(progs):
        nprogs = progs
        progs = []  # Create real pops list
        for p in range(nprogs):
            progs.append({'short': 'Prog %i' % (p + 1), 'name': 'Program %i' % (p + 1)})

            # Ensure years are integers
    if datastart is None: datastart = 2015.  # TEMP
    if dataend is None:   dataend = 2018.  # TEMP
    datastart, dataend = int(datastart), int(dataend)

    book = ProgramSpreadsheet(filename, pops, progs, datastart, dataend)
    book.create(filename)

    return filename


class AtomicaFormats:
    """ the formats used in the spreadsheet """
    darkgray = '#413839'
    originalblue = '#18C1FF'
    optionalorange = '#FFA500'
    BG_COLOR = originalblue
    OPT_COLOR = optionalorange
    BORDER_COLOR = 'white'

    PERCENTAGE = 'percentage'
    RATE = 'rate'
    DECIMAL = 'decimal'
    SCIENTIFIC = 'scientific'
    NUMBER = 'number'
    GENERAL = 'general'
    OPTIONAL = 'optional'

    def __init__(self, book):
        self.formats = {}
        self.book = book
        # locked formats
        self.formats['bold'] = self.book.add_format({'bold': 1})
        self.formats['center_bold'] = self.book.add_format({'bold': 1, 'align': 'center'})
        self.formats['rc_title'] = {}
        self.formats['rc_title']['right'] = self.book.add_format({'bold': 1, 'align': 'right'})
        self.formats['rc_title']['left'] = self.book.add_format({'bold': 1, 'align': 'left'})
        # unlocked formats
        self.formats['unlocked'] = self.book.add_format({'locked': 0, 'bg_color': AtomicaFormats.BG_COLOR, 'border': 1,
                                                         'border_color': AtomicaFormats.BORDER_COLOR})
        self.formats['percentage'] = self.book.add_format(
            {'locked': 0, 'num_format': 0x09, 'bg_color': AtomicaFormats.BG_COLOR, 'border': 1,
             'border_color': AtomicaFormats.BORDER_COLOR})
        self.formats['rate'] = self.book.add_format(
            {'locked': 0, 'num_format': 0x09, 'bg_color': AtomicaFormats.BG_COLOR, 'border': 1,
             'border_color': AtomicaFormats.BORDER_COLOR})
        self.formats['decimal'] = self.book.add_format(
            {'locked': 0, 'num_format': 0x0a, 'bg_color': AtomicaFormats.BG_COLOR, 'border': 1,
             'border_color': AtomicaFormats.BORDER_COLOR})
        self.formats['scientific'] = self.book.add_format(
            {'locked': 0, 'num_format': 0x0b, 'bg_color': AtomicaFormats.BG_COLOR, 'border': 1,
             'border_color': AtomicaFormats.BORDER_COLOR})
        self.formats['number'] = self.book.add_format(
            {'locked': 0, 'num_format': 0x04, 'bg_color': AtomicaFormats.BG_COLOR, 'border': 1,
             'border_color': AtomicaFormats.BORDER_COLOR})
        self.formats['general'] = self.book.add_format(
            {'locked': 0, 'num_format': 0x00, 'bg_color': AtomicaFormats.BG_COLOR, 'border': 1,
             'border_color': AtomicaFormats.BORDER_COLOR})
        self.formats['optional'] = self.book.add_format(
            {'locked': 0, 'num_format': 0x00, 'bg_color': AtomicaFormats.OPT_COLOR, 'border': 1,
             'border_color': AtomicaFormats.BORDER_COLOR})
        self.formats['info_header'] = self.book.add_format(
            {'align': 'center', 'valign': 'vcenter', 'color': '#D5AA1D', 'fg_color': '#0E0655', 'font_size': 20})
        self.formats['grey'] = self.book.add_format({'fg_color': '#EEEEEE', 'text_wrap': True})
        self.formats['orange'] = self.book.add_format({'fg_color': '#FFC65E', 'text_wrap': True})
        self.formats['info_url'] = self.book.add_format(
            {'fg_color': '#EEEEEE', 'text_wrap': True, 'color': 'blue', 'align': 'center'})
        self.formats['grey_bold'] = self.book.add_format({'fg_color': '#EEEEEE', 'bold': True})
        self.formats['merge_format'] = self.book.add_format({'bold': 1, 'align': 'center', 'text_wrap': True})

    def write_block_name(self, sheet, name, row):
        sheet.write(row, 0, name, self.formats['bold'])

    def write_rowcol_name(self, sheet, row, col, name, align='right'):
        sheet.write(row, col, name, self.formats['rc_title'][align])

    def write_option(self, sheet, row, col, name='OR'):
        sheet.write(row, col, name, self.formats['center_bold'])

    # special processing for bool values (to keep the content separate from representation)
    def write_unlocked(self, sheet, row, col, data, row_format='unlocked'):
        if type(data) == bool:
            bool_data = 'TRUE' if data else 'FALSE'
            sheet.write(row, col, bool_data, self.formats[row_format])
        else:
            sheet.write(row, col, data, self.formats[row_format])

    def write_empty_unlocked(self, sheet, row, col, row_format='unlocked'):
        sheet.write_blank(row, col, None, self.formats[row_format])

    def writeline(self, sheet, row, row_format='grey'):
        sheet.write_blank(row, 0, None, self.formats[row_format])
        return row + 1

    def writeblock(self, sheet, row, text, row_format='grey', row_height=None, add_line=True):
        if row_height:
            sheet.set_row(row, row_height)
        sheet.write(row, 0, text, self.formats[row_format])
        if add_line:
            return self.writeline(sheet, row + 1)
        else:
            return row + 1


class SheetRange:
    def __init__(self, first_row, first_col, num_rows, num_cols):
        self.first_row = first_row
        self.first_col = first_col

        self.num_rows = num_rows
        self.num_cols = num_cols

        self.last_row = self.first_row + self.num_rows - 1
        self.last_col = self.first_col + self.num_cols - 1

        self.start = self.get_cell_address(self.first_row, self.first_col)
        self.end = self.get_cell_address(self.last_row, self.last_col)

    def get_address(self):
        return '%s:%s' % (self.start, self.end)

    def get_cell_address(self, row, col):
        return xw.utility.xl_rowcol_to_cell(row, col, row_abs=True, col_abs=True)

    """ gives the list of references to the entries in the row names (which are parameters) """

    def param_refs(self, sheet_name, column_number=1):
        par_range = range(self.first_row, self.last_row + 1)
        return ["='%s'!%s" % (sheet_name, self.get_cell_address(row, self.first_col + column_number)) for row in
                par_range]


def make_programs_range(name=None, popnames=None, items=None):
    """ 
    every programs item is a dictionary is expected to have the following fields:
    short, name, targetpops
    (2x str, 1x list of booleans)
    """
    column_names = ['Short name', 'Long name'] + popnames
    row_names = range(1, len(items) + 1)
    coded_params = []
    for item in items:
        if type(item) is dict:
            name = item['name']
            short = item['short']
            targetpops = [0 for popname in popnames]
        coded_params.append([short, name] + targetpops)
    return AtomicaContent(name=name, row_names=row_names, column_names=column_names, data=coded_params,
                          assumption=False)


def make_years_range(name=None, row_names=None, ref_range=None, data_start=None, data_end=None, data=None):
    if ref_range is not None:
        row_names = ref_range.param_refs()
    output = AtomicaContent(name=name, row_names=row_names, column_names=range(int(data_start), int(data_end + 1)),
                            data=data)
    return output


class TitledRange(object):
    FIRST_COL = 2
    ROW_INTERVAL = 3

    def __init__(self, sheet=None, first_row=None, content=None):
        self.sheet = sheet
        self.content = content
        first_data_col = TitledRange.FIRST_COL
        num_data_rows = len(self.content.row_names)

        if self.content.row_levels is not None:
            first_data_col += 1
            num_data_rows *= len(self.content.row_levels)
            num_data_rows += len(self.content.row_names) - 1
        self.data_range = SheetRange(first_row + 2, first_data_col, num_data_rows, len(self.content.column_names))
        self.first_row = first_row

    def num_rows(self):
        return self.data_range.num_rows + 2

    """ emits the range and returns the new current row in the given sheet """

    def emit(self, formats, rc_row_align='right', rc_title_align='right'):  # only important for row/col titles
        # top-top headers
        formats.write_block_name(self.sheet, self.content.name, self.first_row)

        if self.content.assumption and self.first_row == 0 and self.content.assumption_properties['title'] is not None:
            formats.write_rowcol_name(self.sheet, self.first_row, self.data_range.last_col + 2,
                                      self.content.assumption_properties['title'])

        # headers
        for i, name in enumerate(self.content.column_names):
            formats.write_rowcol_name(self.sheet, self.first_row + 1, self.data_range.first_col + i, name,
                                      rc_title_align)

        if self.content.assumption:
            for index, col_name in enumerate(self.content.assumption_properties['columns']):
                formats.write_rowcol_name(self.sheet, self.first_row + 1, self.data_range.last_col + 2 + index,
                                          col_name)

        current_row = self.data_range.first_row
        num_levels = len(self.content.row_levels) if self.content.row_levels is not None else 1

        # iterate over rows, incrementing current_row as we go
        for i, names_format in enumerate(zip(self.content.get_row_names(), self.content.get_row_formats())):
            names, row_format = names_format
            start_col = self.data_range.first_col - len(names)
            # emit row name(s)
            for n, name in enumerate(names):
                formats.write_rowcol_name(self.sheet, current_row, start_col + n, name, rc_row_align)
            # emit data if present
            savedata = False
            if self.content.data is not None:
                try:
                    for j, item in enumerate(self.content.data[i]):
                        formats.write_unlocked(self.sheet, current_row, self.data_range.first_col + j, item, row_format)
                    savedata = True  # It saved successfully
                except:
                    errormsg = 'WARNING, failed to save "%s" with data:\n%s' % (self.content.name, self.content.data)
                    print(errormsg)
                    savedata = False
            if not savedata:
                for j in range(self.data_range.num_cols):
                    formats.write_empty_unlocked(self.sheet, current_row, self.data_range.first_col + j, row_format)
            # emit assumption
            if self.content.assumption:
                formats.write_option(self.sheet, current_row, self.data_range.last_col + 1,
                                     name=self.content.assumption_properties['connector'])
                for index, col_name in enumerate(self.content.assumption_properties['columns']):
                    saveassumptiondata = False
                    if self.content.assumption_data is not None:
                        try:
                            assumptiondata = self.content.assumption_data[i]
                            if isinstance(assumptiondata, list):  # Check to see if it's a list
                                if len(assumptiondata) != 1:  # Check to see if it has the right length
                                    errormsg = 'WARNING, assumption "%s" appears to have the wrong length:\n%s' % (
                                        self.content.name, assumptiondata)
                                    print(errormsg)
                                    saveassumptiondata = False
                                else:  # It has length 1, it's good to go
                                    assumptiondata = assumptiondata[0]  # Just pull out the only element
                            formats.write_unlocked(self.sheet, current_row, self.data_range.last_col + 2 + index,
                                                   assumptiondata, row_format)
                            saveassumptiondata = True
                        except Exception as E:
                            errormsg = 'WARNING, failed to save assumption "%s" with data:\n%s\nError message:\n (%s)' % (
                                self.content.name, self.content.assumption_data, repr(E))
                            print(errormsg)
                            saveassumptiondata = False
                            raise E
                    if not saveassumptiondata:
                        formats.write_empty_unlocked(self.sheet, current_row, self.data_range.last_col + 2 + index,
                                                     row_format)
            current_row += 1
            if num_levels > 1 and ((i + 1) % num_levels) == 0:  # shift between the blocks
                current_row += 1
        # done! return the new current_row plus spacing
        return current_row + TitledRange.ROW_INTERVAL  # for spacing

    def param_refs(self, column_number=0):
        return self.data_range.param_refs(self.sheet.get_name(), column_number)


class AtomicaContent(object):
    """ the content of the data ranges (row names, column names, optional data and assumptions) """

    def __init__(self, name=None, row_names=None, column_names=None, data=None, assumption_data=None, assumption=True):
        self.name = name
        self.row_names = row_names
        self.column_names = column_names
        self.data = data
        self.assumption = assumption
        self.row_levels = None
        self.row_format = AtomicaFormats.GENERAL
        self.row_formats = None
        self.assumption_properties = {'title': None, 'connector': 'OR', 'columns': ['Assumption']}
        self.assumption_data = assumption_data

    def get_row_names(self):
        if not self.row_levels is not None:
            return [[name] for name in self.row_names]
        else:
            return [[name, level] for name in self.row_names for level in self.row_levels]

    def get_row_formats(self):  # assume that the number of row_formats is same as the number of row_levels
        if not self.row_levels is not None:
            return [self.row_format for name in self.row_names]
        else:
            if self.row_formats is not None:
                return [row_format for name in self.row_names for row_format in self.row_formats]
            else:
                return [self.row_format for name in self.row_names for level in self.row_levels]


class ProgramSpreadsheet:
    def __init__(self, name, pops, progs, data_start=None, data_end=None, verbose=0):
        self.sheet_names = odict([
            ('targeting', 'Populations & programs'),
            ('costcovdata', 'Program data'),
        ])
        self.name = name
        self.pops = pops
        self.progs = progs
        self.data_start = data_start
        self.data_end = data_end
        self.verbose = verbose
        self.book = None
        self.sheets = None
        self.formats = None
        self.current_sheet = None
        self.prog_range = None
        self.ref_pop_range = None
        self.years_range = range(int(self.data_start), int(self.data_end + 1))

        self.npops = len(pops)
        self.nprogs = len(progs)

    def generate_targeting(self):
        self.current_sheet.set_column(2, 2, 15)
        self.current_sheet.set_column(3, 3, 40)
        self.current_sheet.set_column(6, 6, 12)
        self.current_sheet.set_column(7, 7, 16)
        self.current_sheet.set_column(8, 8, 16)
        self.current_sheet.set_column(9, 9, 12)
        current_row = 0

        targeting_content = make_programs_range('Populations & programs', self.pops, self.progs)
        self.prog_range = TitledRange(sheet=self.current_sheet, first_row=current_row, content=targeting_content)
        current_row = self.prog_range.emit(self.formats, rc_title_align='left')

        self.ref_prog_range = self.prog_range

    def emit_years_block(self, name, current_row, row_names, row_format=AtomicaFormats.GENERAL,
                         assumption=False, row_levels=None, row_formats=None):
        content = make_years_range(name=name, row_names=row_names, data_start=self.data_start, data_end=self.data_end)
        content.row_format = row_format
        content.assumption = assumption
        if row_levels is not None:
            content.row_levels = row_levels
        if row_formats is not None:
            content.row_formats = row_formats
        the_range = TitledRange(self.current_sheet, current_row, content)
        current_row = the_range.emit(self.formats)
        return current_row

    def generate_costcovdata(self):
        row_levels = ['Total spend', 'Unit cost', 'Coverage', 'Capacity constraint']
        self.current_sheet.set_column('C:C', 20)
        current_row = 0
        current_row = self.emit_years_block(name='Cost & coverage', current_row=current_row,
                                            row_names=self.ref_prog_range.param_refs(),
                                            row_formats=[AtomicaFormats.SCIENTIFIC, AtomicaFormats.GENERAL,
                                                         AtomicaFormats.GENERAL, AtomicaFormats.GENERAL],
                                            assumption=True, row_levels=row_levels)

    def create(self, path):
        if self.verbose >= 1:
            print("""Creating program spreadsheet %s with parameters:
            npops = %s, nprogs = %s, data_start = %s, data_end = %s""" % \
                  (path, self.npops, self.nprogs, self.data_start, self.data_end))
        self.book = xw.Workbook(path)
        self.formats = AtomicaFormats(self.book)
        self.sheets = {}
        for name in self.sheet_names:
            self.sheets[name] = self.book.add_worksheet(self.sheet_names[name])
            self.current_sheet = self.sheets[name]
            getattr(self, "generate_%s" % name)()  # this calls the corresponding generate function
        self.book.close()
