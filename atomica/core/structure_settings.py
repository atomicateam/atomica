# -*- coding: utf-8 -*-
"""
Atomica structure settings file, in charge of defining the structure of both Framework and Data objects.
The definitions are hard-coded, while interface semantics are drawn from a configuration file.

Architecture description:
Upon importing Atomica, 'static' variables used throughout the codebase are established.
These settings are encapsulated by classes SystemSettings, ExcelSettings, FrameworkSettings and DataSettings.
None of these classes are instantiated as objects (i.e. no init/attributes/etc.); they are treated as namespace classes.
In the cases of SystemSettings and ExcelSettings, the collections of variables are simple to import and understand.

FrameworkSettings/DataSettings is more complicated to understand because 'static' variable values are soft-coded.
Specifically, they are pulled from format_framework.ini/format_databook.ini, respectively, before becoming 'static'.
E.g.; the name of a parameter framework Excel page can freely be set as "Frog" externally in an .ini file...
...but Atomica will then statically expect, upon start-up, that framework Excel parameter pages are titled "Frog".

...

Every application (e.g. epidemiological) corresponds to one Project object.
Each Project needs to load in a Framework object that defines the system (i.e. compartment objects, etc.).
This is imported from a framework file filled out by a modeller.
Each Project needs to load in a corresponding Data object that fleshes out the system (i.e. compartment sizes, etc.).
This is imported from a databook file filled out by a user; the databook is created once Project framework is loaded.
Both are required for evolving a system and applying subsequent analyses.

ProjectFramework and ProjectData are both
"""

import sciris.core as sc
from .excel import ExcelSettings
from .parser_config import load_config_file, get_config_value, configparser
from .system import SystemSettings as SS, AtomicaException, logger, atomica_path, display_name
from xlsxwriter.utility import xl_rowcol_to_cell as xlrc
from xlsxwriter.utility import xl_cell_to_rowcol

import numpy as np

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


class TableTemplate(TableType):
    """
    Structure indicating a table should be duplicated for each existing instance of an item type.
    In settings, template item key should always be left as None.
    The template should be instantiated by other external functions, e.g. following framework file import.
    Because item instances only exist after framework file is read in, this table type should only appear in databook.

    Note that, if the template item type only exists in ProjectData and not ProjectFramework...
    The template will be iterated according to the number of items to be constructed according to workbook instructions.
    """

    def __init__(self, template_item_type, template_item_key=None):
        super(TableTemplate, self).__init__()
        self.template_item_type = template_item_type
        self.template_item_key = template_item_key

class Table():
    # TODO - Maybe delete this if it's not doing anything useful
    def __init__(self):
        pass

    def read(self,worksheet,start_row):
        # Reads contents from the start row, column 1, to the next blank row
        # And then attempts to parse
        return None

    def write(self,worksheet,start_row,formats,references=None):
        # Writes the contents of this table to the specified worksheet at the given start row
        # Returns the next row for writing
        return start_row


class TimeDependentConnections(Table):
    # A TimeDependentConnection structure is suitable when there are time dependent interactions between two quantities
    # This class is used for transfers and interactions
    # The content that it writes consists of
    # - A connection matrix table that has Y/N selection of which interactions are present between two things
    # - A set of pairwise connections specifying to, from, units, assumption, and time
    # Interactions can have a diagonal, whereas transfers cannot (e.g. a population can infect itself but cannot transfer to itself)

    def __init__(self, code_name, full_name, tvec, pops, type, ts=None):
        # INPUTS
        # - code_name -
        # - full_name - the name of this quantity e.g. 'Aging'
        # - tvec - time values for the time-dependent rows
        # - pops - list of strings to use as the rows and columns - these are typically lists of population code names
        # - ts - all of the non-empty TimeSeries objects used. An interaction can only be Y/N for clarity, if it is Y then
        #   a row is displayed for the TimeSeries. Actually, the Y/N can be decided in the first instance based on the provided TimeSeries i.e.
        #   if a TimeSeries is provided for an interaction, then the interaction must have been marked with Y
        # type - 'transfer' or 'interaction'. A transfer cannot have diagonal entries, and can have Number or Probability formats. An Interaction can have
        # diagonal entries and only has N.A. formats
        self.code_name = code_name
        self.full_name = full_name
        self.type = type
        self.pops = pops
        self.tvec = tvec
        self.ts = ts if ts is not None else sc.odict()

        if self.type == 'transfer':
            self.enable_diagonal = False
            self.allowed_units = [FrameworkSettings.QUANTITY_TYPE_NUMBER.title(), FrameworkSettings.QUANTITY_TYPE_PROBABILITY.title()]
        elif self.type == 'interaction':
            self.enable_diagonal = True
            self.allowed_units = [SS.DEFAULT_SYMBOL_INAPPLICABLE.title()]
        else:
            raise AtomicaException('Unknown TimeDependentConnections type - must be "transfer" or "interaction"')

    def __repr__(self):
        return '<TDC %s "%s">' % (self.type.title(),self.code_name)

    @staticmethod
    def from_tables(tables,interaction_type):
        # interaction_type is 'transfer' or 'interaction'
        from .structure import TimeSeries # Import here to avoid circular reference

        # Read the names
        code_name = tables[0][1][0].value
        full_name = tables[0][1][1].value
        interaction_type = interaction_type

        # Read the pops
        pops = [x.value for x in tables[1][0][1:] if x.value]
        # TODO - At the moment, the Y/N content of the table depends on what timeseries is provided
        # Therefore, we only need to read in the TimeSeries to tell whether or not a connection exists
        # The convention is that the connection will be read if the TO and FROM pop match something in the pop list
        tvec = np.array([x.value for x in tables[2][0][6:]],dtype=float) # The 6 matches the offset in write() below
        ts_entries = sc.odict()
        for row in tables[2][1:]:
            if row[0].value != '...':
                assert row[0].value in pops, 'Population "%s" not found - should be contained in %s' % (row[0].value, pops)
                assert row[2].value in pops, 'Population "%s" not found - should be contained in %s' % (row[2].value, pops)
                vals = [x.value for x in row]
                from_pop = vals[0]
                to_pop = vals[2]
                units = vals[3]
                assumption = vals[4] # This is the assumption cell
                assert vals[5] == 'OR' # Double check we are reading a time-dependent row with the expected shape
                ts = TimeSeries(format=units,units=units)
                if assumption:
                    ts.insert(None, float(assumption))
                for t, v in zip(tvec, vals[6:]):
                    if v is not None:
                        ts.insert(t, v)
                ts_entries[(from_pop,to_pop)] = ts

        return TimeDependentConnections(code_name, full_name, tvec, pops, interaction_type, ts=ts_entries)

    def write(self,worksheet,start_row,formats,references=None):

        if not references:
            references = {x:x for x in self.pops} # Default null mapping for populations

        ### First, write the titles
        current_row = start_row
        worksheet.write(current_row, 0, 'Abbreviation', formats["center_bold"])
        worksheet.write(current_row, 1, 'Full Name', formats["center_bold"])
        current_row += 1
        worksheet.write(current_row, 0, self.code_name)
        worksheet.write(current_row, 1, self.full_name)
        references[self.code_name] = "='%s'!%s" % (worksheet.name, xlrc(current_row, 0, True, True))
        references[self.full_name] = "='%s'!%s" % (worksheet.name, xlrc(current_row, 1, True, True))  # Reference to the full name

        ### Then, write the matrix
        current_row += 2 # Leave a blank row below the matrix

        # Note - table_references are local to this TimeDependentConnections instance
        # For example, there could be two transfers, and each of them could potentially transfer between 0-4 and 5-14
        # so the worksheet might contain two references from 0-4 to 5-14 but they would be for different transfers and thus
        # the time-dependent rows would depend on different boolean table cells
        current_row,table_references,values_written = write_matrix(worksheet,current_row,self.pops,self.ts,formats,references,enable_diagonal=self.enable_diagonal,boolean_choice=True)

        ### Finally, write the time dependent part
        headings = []
        headings.append('') # From
        headings.append('') # --->
        headings.append('') # To
        headings.append('Quantity Type')
        headings.append('Constant')
        headings.append('') # OR
        headings += [str(x) for x in self.tvec] # Times
        for i, entry in enumerate(headings):
            worksheet.write(current_row, i, entry, formats['center_bold'])

        # Now, we will write a wrapper that gates the content
        # If the gating cell is 'Y', then the content will be displayed, otherwise not
        def gate_content(content,gating_cell):
            if content.startswith('='): # If this is itself a reference
                return ('=IF(%s="Y",%s,"...")' % (gating_cell, content[1:]))
            else:
                return('=IF(%s="Y","%s","...")' % (gating_cell,content))

        for from_idx in range(0,len(self.pops)):
            for to_idx in range(0, len(self.pops)):
                current_row += 1
                from_pop = self.pops[from_idx]
                to_pop = self.pops[to_idx]
                entry_tuple = (from_pop,to_pop)
                entry_cell = table_references[entry_tuple]
                if entry_tuple in self.ts:
                    ts = self.ts[entry_tuple]
                else:
                    ts = None

                if ts:
                    worksheet.write_formula(current_row, 0, gate_content(references[from_pop], entry_cell), formats['center_bold'], value=from_pop)
                    worksheet.write_formula(current_row, 1, gate_content('--->', entry_cell), formats['center_bold'], value='--->')
                    worksheet.write_formula(current_row, 2, gate_content(references[to_pop], entry_cell), formats['center_bold'], value=to_pop)
                    worksheet.write(current_row, 3, ts.format)
                    worksheet.data_validation(xlrc(current_row, 3), {"validate": "list", "source": self.allowed_units})
                    worksheet.write(current_row, 4, ts.assumption, formats['unlocked'])
                    worksheet.write_formula(current_row, 5, gate_content('OR', entry_cell), formats['center_bold'], value='OR')
                else:
                    worksheet.write_formula(current_row, 0, gate_content(references[from_pop], entry_cell), formats['center_bold'], value='...')
                    worksheet.write_formula(current_row, 1, gate_content('--->', entry_cell), formats['center_bold'], value='...')
                    worksheet.write_formula(current_row, 2, gate_content(references[to_pop], entry_cell), formats['center_bold'], value='...')
                    worksheet.write_blank(current_row, 3, '')
                    worksheet.data_validation(xlrc(current_row, 3), {"validate": "list", "source": self.allowed_units})
                    worksheet.write_blank(current_row, 4, '', formats['unlocked'])
                    worksheet.write_formula(current_row, 5, gate_content('OR', entry_cell), formats['center_bold'], value='...')

                # Write hyperlink - it's a bit convoluted because we can't read back the contents of the original cell to know
                # whether it was originally Y or N
                if values_written[entry_cell] != SS.DEFAULT_SYMBOL_INAPPLICABLE:
                    worksheet.write_url(entry_cell, 'internal:%s!%s' % (worksheet.name, xlrc(current_row, 2)),cell_format=formats['center_unlocked'],string=values_written[entry_cell])

                offset = 6  # The time values start in this column (zero based index)
                content = np.full(self.tvec.shape, None)

                if ts:
                    for t, v in zip(ts.t, ts.vals):
                        idx = np.where(self.tvec == t)[0][0]
                        content[idx] = v

                for idx, v in enumerate(content):
                    if v is None:
                        worksheet.write_blank(current_row, offset + idx, v, formats['unlocked'])
                    else:
                        worksheet.write(current_row, offset + idx, v, formats['unlocked'])

        current_row += 2

        return current_row


def write_matrix(worksheet,start_row,nodes,entries,formats,references=None, enable_diagonal=True, boolean_choice=False):
    # This function writes a matrix
    # It gets used for
    # - Transfer matrix
    # - Interactions matrix
    # - Framework transition/link matrix
    #
    # - nodes is a list of strings used to label the rows and columns
    # - entries is a dict where where key is a tuple specifying (from,to) = (row,col) and
    # the value is the string to write to the matrix
    # - If 'enable_diagonal' is False, then the diagonal will be forced to be 'N.A.'. If an entry
    #   is specified for an entry on the diagonal and enable_diagonal=False, an error will be thrown
    # - boolean_choice is like namer/marker mode. If True, entries can only be Y/N based on the truthiness of the value in the entries dict
    #
    # table_references is a dict that contains a mapping between the tuple (to,from) and a cell. This can be
    # subsequently used to programatically block out time-dependent rows

    if not references:
        references = {x:x for x in nodes} # This is a null-mapping that takes say 'adults'->'adults' thus simplifying the workflow. Otherwise, it's assumed a reference exists for every node

    table_references = {}
    values_written = {}

    # Write the headers
    for i,node in enumerate(nodes):
        worksheet.write_formula(start_row+i+1, 0  , references[node], formats['center_bold'],value=node)
        worksheet.write_formula(start_row  , i+1, references[node], formats['center_bold'],value=node)

    # Prepare the content - first replace the dict with one keyed by index. This is because we cannot apply formatting
    # after writing content, so have to do the writing in a single pass over the entire matrix
    if boolean_choice:
        content = np.full((len(nodes),len(nodes)),'N',dtype=object) # This will also coerce the value to string in preparation for writing
    else:
        content = np.full((len(nodes),len(nodes)),'',dtype=object) # This will also coerce the value to string in preparation for writing

    for interaction, value in entries.items():
        from_node,to_node = interaction
        if not enable_diagonal and from_node == to_node:
            raise AtomicaException('Trying to write a diagonal entry to a table that is not allowed to contain diagonal terms') # This is because data loss will occur if the user adds entries on the diagonal, then writes the table, and then reads it back in
        from_idx = nodes.index(from_node)
        to_idx = nodes.index(to_node)
        if boolean_choice:
            value = 'Y' if value else 'N'
        content[from_idx,to_idx] = value

    # Write the content
    for from_idx in range(0,len(nodes)):
        for to_idx in range(0,len(nodes)):
            row = start_row+1+from_idx
            col = to_idx+1
            if not enable_diagonal and to_idx == from_idx: # Disable the diagonal if that's what's desired
                val = SS.DEFAULT_SYMBOL_INAPPLICABLE
                worksheet.write(row,col,val, formats["center"])
                worksheet.data_validation(xlrc(row,col), {"validate": "list", "source": ["N.A."]})
            else:
                val = content[from_idx,to_idx]
                worksheet.write(row,col, content[from_idx,to_idx], formats["center_unlocked"])
                if boolean_choice:
                    worksheet.data_validation(xlrc(row,col), {"validate": "list", "source": ["Y","N"]})
            table_references[(nodes[from_idx],nodes[to_idx])] = xlrc(row,col,True,True) # Store reference to this interaction
            values_written[table_references[(nodes[from_idx],nodes[to_idx])]] = val
    next_row = start_row + 1 + len(nodes) + 1

    return next_row,table_references,values_written

class TimeDependentValuesEntry(TableTemplate):
    """
    Template table requesting time-dependent values, with each instantiation iterating over an item type.
    Argument 'value_attribute' specifies which attribute within item specs should contain the parsed values.
    If argument 'iterate_over_links' is True, table rows are actually for links between items of the iterated type.
    Self connections are not included by default, but can be turned on by an optional argument.
    """

    # A TDVE table is used for representing Characteristics and Parameters that appear in the Parset, a quantity
    # that has one sparse time array for each population. A TDVE table contains
    # - An ordered list of TimeSeries objects
    # - A name for the quantity (as this is what gets printed and read, it's usually a full name rather than a code name)
    # - Optionally a list of allowed units - All TimeSeries objects must have units contained in this list
    # - A time axis (e.g. np.arange(2000,2019)) - all TimeSeries time values must exactly match one of the values here
    #   i.e. you cannot try to write a TimeSeries that has a time value that doesn't appear as a table heading

    def __init__(self, name=None, tvec=None, ts = None, allowed_units = None, self_connections=True, template_item_type=None,iterated_type=None,iterate_over_links=None,value_attribute=None):
        # ts - An odict where the key is a population name and the value is a TimeSeries
        # name - This is the name of the quantity i.e. the full name of the characteristic or parameter
        # tvec - The time values that will be written in the headings
        # allowed_units - Possible values for the unit selection dropdown

        super(TimeDependentValuesEntry, self).__init__(template_item_type=template_item_type)

        if ts is None:
            ts = sc.odict()

        # TODO - name and tvec should be compulsory positional arguments, they can be none to support legacy code for the moment
        self.name = name
        self.tvec = tvec
        self.ts = ts
        self.allowed_units = allowed_units

        # Todo - get rid of these once reading is updated?
        self.template_item_type = template_item_type # This is whether the table is for a compartment, characteristic, or parameter
        self.iterated_type = iterated_type # Most TDVE tables contain multiple TimeSeries, this states what they are e.g. 'pop'
        self.iterate_over_links = iterate_over_links
        self.value_attribute = value_attribute # This says something like 'data'
        self.self_connections = self_connections # This is probably only relevant for link tables

    @staticmethod
    def from_rows(rows):
        # Given a set of openpyxl rows, instantiate a TimeDependentValuesEntry object
        # That is, the parent object e.g. Databook() is responsible for finding where the TDVE table is,
        # and reading all of the rows associated with it (skipping #ignored rows) and then passing those rows,
        # unparsed, to this function
        from .structure import TimeSeries # Import here to avoid circular reference

        # First, read the headings
        vals = [x.value for x in rows[0]]
        name = vals[0]
        tvec = np.array(vals[4:],dtype=float)
        ts_entries = sc.odict()

        # For each TimeSeries that we will instantiate
        for row in rows[1:]:
            vals = [x.value for x in row]
            series_name = vals[0]
            format = vals[1].lower() if vals[1] else None
            units = vals[1].lower() if vals[1] else None
            assumption = vals[2]
            assert vals[3] == 'OR' # Check row is as expected
            data = vals[4:]
            ts = TimeSeries(format=format,units=units)
            if assumption is not None and assumption != SS.DEFAULT_SYMBOL_INAPPLICABLE.title():
                ts.insert(None,float(assumption))
            for t,v in zip(tvec,data):
                if np.isfinite(t) and v is not None: # Ignore any times that are NaN
                    ts.insert(t,v)
            ts_entries[series_name] = ts

        tvec = tvec[np.isfinite(tvec)] # Remove empty entries from the array
        return TimeDependentValuesEntry(name,tvec,ts_entries)

    def write(self,worksheet,start_row,formats,references=None):
        # references is a dict where the key is a string value and the content is a cell
        # Any populations that appear in this dict will have their value replaced by a reference
        # formats should be the dict returned by `excel.standard_formats` when it was called to add
        # formatting to the Workbook containing the worksheet passed in here.

        if not references:
            references = dict()

        current_row = start_row

        # First, assemble and write the headings
        headings = []
        headings.append(self.name)
        headings.append('Quantity Type')
        headings.append('Constant')
        headings.append('')
        headings += [float(x) for x in self.tvec]
        for i,entry in enumerate(headings):
            worksheet.write(current_row, i, entry, formats['center_bold'])

        # Now, write the TimeSeries objects - self.ts is an odict and whatever pops are present will be written in whatever order they are in
        for pop_name, pop_ts in self.ts.items():
            current_row += 1

            # Write the name
            if pop_name in references:
                worksheet.write_formula(current_row, 0, references[pop_name], formats['center_bold'],value=pop_name)
            else:
                worksheet.write_string(current_row, 0, pop_name, formats['center_bold'])

            # Write the units
            # TODO - change ts.format to ts.units??
            worksheet.write(current_row,1,pop_ts.format.title() if pop_ts.format else None)
            if self.allowed_units: # Add validation if a list of options is specified
                worksheet.data_validation(xlrc(current_row, 1),{"validate": "list", "source": self.allowed_units})

            # Write the assumption
            worksheet.write(current_row,2,pop_ts.assumption, formats['unlocked'])

            # Write the separator between the assumptions and the time values
            worksheet.write(current_row,3,'OR')

            # Write the time values
            offset = 4 # The time values start in this column (zero based index)
            content = np.full(self.tvec.shape,None)

            for t,v in zip(pop_ts.t,pop_ts.vals):
                idx = np.where(self.tvec == t)[0][0] # If this fails there must be a (forbidden) mismatch between the TimeSeries and the Databook tvec
                content[idx] = v

            for idx,v in enumerate(content):
                if v is None:
                    worksheet.write_blank(current_row, offset+idx, v, formats['unlocked'])
                else:
                    worksheet.write(current_row, offset+idx, v, formats['unlocked'])

        return current_row+2 # Add two so there is a blank line after this table

class ConnectionMatrix(TableTemplate):
    """
    Structure to define a matrix that connects two item types together.
    If no target item type is specified, the connections are between the same type of item.
    Connections are directional from row headers, e.g. zeroth column, to column headers, e.g. zeroth row.
    Connections are always depicted as a paired tuple of two strings, i.e. source item name and target item name.
    Self-connections are disabled by default but can be turned on by an optional argument.

    If the table is not specified as a template, i.e. template_item_type is passed in explicitly or implicity as None...
    The cell value denoting a connection becomes the 'connection)name' of the item this connection is attached to.
    Connections are listed under: specs[storage_item_type][connection_name][storage_attribute]
    If the table is specified as a template, i.e. template_item_type is not None...
    The template key becomes the 'name' of the item this connection is attached to.
    Accordingly, cell values marking the connection must be the system settings symbol for yes, e.g. 'y'.
    Connections are listed under: specs[template_item_type][template_item_key][storage_attribute]

    Note that only source_item_type and target_item_type are used when writing the matrix.
    Only storage_item_type and storage_attribute are used when reading the matrix.
    In the non-template case, errors will arise if the item has not yet been defined as part of the storage item type.

    An example for writing matrices:
        ConnectionMatrix(source_item_type="whatever1", target_item_type="whatever2",
                         storage_item_type="par", storage_attribute="links")
        AND Framework.specs["whatever1"].keys() = ["source1", "source2"]
        =>      target1 target2
        source1 _______ _______
        source2 _______ _______

    An example for reading matrices:
        ConnectionMatrix(source_item_type="whatever1", target_item_type="whatever2",
                         storage_item_type="par", storage_attribute="links")
        AND     target1 target2
        source1 par1    _______
        source2 _______ par1
        => specs["par"]["par1"]["links"][("source1","target1"),("source2","target2")]

    An example for reading template matrices:
        ConnectionMatrix(source_item_type="whatever1", target_item_type="whatever2",
                         storage_item_type=None, storage_attribute="links",
                         template_item_type="transfer", template_item_key="aging")
        AND     target1 target2
        source1 y       n
        source2 n       y
        => specs["transfer"]["aging"]["links"][("source1","target1"),("source2","target2")]
    """

    def __init__(self, source_item_type, storage_item_type, storage_attribute, target_item_type=None,
                 template_item_type=None, self_connections=False):
        super(ConnectionMatrix, self).__init__(template_item_type=template_item_type)
        self.source_item_type = source_item_type
        if target_item_type is None:
            target_item_type = source_item_type
        self.target_item_type = target_item_type
        if template_item_type is not None:
            self.storage_item_type = template_item_type
        self.storage_attribute = storage_attribute
        self.self_connections = self_connections


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
    KEY_TRANSITION = "link"
    KEY_PARAMETER = "par"
    KEY_POPULATION = "pop"
    KEY_TRANSFER = "transfer"
    KEY_INTERACTION = "interpop"
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

    KEY_TRANSITIONS = KEY_TRANSITION + SS.DEFAULT_SUFFIX_PLURAL
    KEY_POPULATION_LINKS = KEY_POPULATION + KEY_TRANSITION + SS.DEFAULT_SUFFIX_PLURAL
    KEY_TRANSFER_DATA = KEY_TRANSFER + TERM_DATA

    ITEM_TYPES = []

    PAGE_KEYS = []  # Derived settings should overwrite this.
    PAGE_SPECS = None  # Class method makes this an ordered dictionary.

    ITEM_TYPE_SPECS = None  # Class method makes this a dictionary.
    ITEM_TYPE_DESCRIPTOR_KEY = sc.odict()  # A mapping from item type descriptors to type-key.

    @classmethod
    def create_page_specs(cls):
        cls.PAGE_SPECS = sc.odict()
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
        cls.ITEM_TYPE_SPECS = sc.odict()
        for item_type in cls.ITEM_TYPES:
            cls.ITEM_TYPE_SPECS[item_type] = sc.odict()
            cls.ITEM_TYPE_SPECS[item_type]["attributes"] = sc.odict()
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
                    logger.debug("Configuration file has an entry for '{0}' in section '{1}' that cannot be "
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
                logger.debug("Configuration file cannot find a valid 'default_amount' for item type '{0}', "
                             "so these items will not be constructed in templates by default.".format(item_type))

            try:
                descriptor = get_config_value(config=cp, section=SS.DEFAULT_SPACE_NAME.join(["itemtype", item_type]),
                                              option="descriptor")
                cls.create_item_type_descriptor(item_type=item_type, descriptor=descriptor)
            except Exception:
                logger.debug("Configuration file cannot find a valid 'descriptor' for item type '{0}', "
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

    # TODO: Decide whether to reintroduce program types as a page and an item, with subitem program attributes.
    ITEM_TYPES = [BSS.KEY_POPULATION_ATTRIBUTE, BSS.KEY_POPULATION_OPTION, BSS.KEY_COMPARTMENT, BSS.KEY_CHARACTERISTIC,
                  BSS.KEY_PARAMETER, BSS.KEY_INTERACTION, BSS.KEY_DATAPAGE]

    # TODO: Reintroduce BSS.KEY_POPULATION_ATTRIBUTE here when ready to develop population attribute functionality.
    PAGE_KEYS = [BSS.KEY_DATAPAGE, BSS.KEY_COMPARTMENT, BSS.KEY_TRANSITION,
                 BSS.KEY_CHARACTERISTIC, BSS.KEY_INTERACTION, BSS.KEY_PARAMETER]

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
                    table = DetailColumns(item_type, attribute_list=[cls.KEY_TRANSITIONS, "dependencies"],
                                          exclude_not_include=True)
                else:
                    table = DetailColumns(item_type)
                cls.PAGE_SPECS[item_type]["tables"].append(table)
        cls.PAGE_SPECS[cls.KEY_DATAPAGE]["can_skip"] = True
        cls.PAGE_SPECS[cls.KEY_INTERACTION]["can_skip"] = True
        # Ensure that transition matrix page is read after parameter page so that link names are already defined.
        cls.PAGE_SPECS[cls.KEY_TRANSITION]["read_order"] = 1  # All other pages prioritised with read order value 0.
        cls.PAGE_SPECS[cls.KEY_TRANSITION]["tables"].append(ConnectionMatrix(source_item_type=cls.KEY_COMPARTMENT,
                                                                             storage_item_type=cls.KEY_PARAMETER,
                                                                             storage_attribute=cls.KEY_TRANSITIONS))

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

        cls.create_item_type_attributes([cls.KEY_PARAMETER, cls.KEY_INTERACTION], ["default_value"],
                                        content_type=ContentType(enforce_type=float))
        cls.create_item_type_attributes([cls.KEY_PARAMETER], ["min", "max"],
                                        content_type=ContentType(enforce_type=float))
        cls.create_item_type_attributes([cls.KEY_PARAMETER], [cls.TERM_FUNCTION, "dependencies"])
        cls.create_item_type_attributes([cls.KEY_PARAMETER], ["is_impact"],
                                        content_type=SwitchType(default_on=True))
        cls.create_item_type_attributes([cls.KEY_PARAMETER], [cls.KEY_TRANSITIONS],
                                        content_type=ContentType(is_list=True))

        cls.create_item_type_attributes([cls.KEY_DATAPAGE],
                                        ["read_order", "refer_to_settings"] + ExcelSettings.FORMAT_VARIABLE_KEYS)
        cls.create_item_type_attributes([cls.KEY_DATAPAGE], ["tables"], content_type=ContentType(is_list=True))
        cls.create_item_type_attributes([cls.KEY_DATAPAGE], ["can_skip"], content_type=SwitchType())
        cls.create_item_type_attributes([cls.KEY_COMPARTMENT, cls.KEY_CHARACTERISTIC, cls.KEY_PARAMETER],
                                        ["can_calibrate"],
                                        content_type=SwitchType(default_on=True))
        cls.create_item_type_attributes([cls.KEY_COMPARTMENT, cls.KEY_CHARACTERISTIC, cls.KEY_PARAMETER],
                                        [cls.KEY_DATAPAGE],
                                        content_type=IDRefType(attribute="name", item_types=[cls.KEY_DATAPAGE]))
        cls.create_item_type_attributes([cls.KEY_COMPARTMENT, cls.KEY_CHARACTERISTIC, cls.KEY_PARAMETER],
                                        ["datapage_order"],
                                        content_type=ContentType(enforce_type=int))
        cls.create_item_type_attributes([cls.KEY_COMPARTMENT, cls.KEY_CHARACTERISTIC],
                                        ["cascade_stage"],
                                        content_type=ContentType(enforce_type=int))
        # Subitem type association is done after item types and attributes are defined, due to cross-referencing.
        cls.create_item_type_subitem_types(cls.KEY_POPULATION_ATTRIBUTE, [cls.KEY_POPULATION_OPTION])


@create_specs
class DataSettings(BaseStructuralSettings):
    BSS = BaseStructuralSettings
    NAME = SS.STRUCTURE_KEY_DATA
    CONFIG_PATH = atomica_path(subdir=SS.CODEBASE_DIRNAME) + SS.CONFIG_DATABOOK_FILENAME

    ITEM_TYPES = [BSS.KEY_COMPARTMENT, BSS.KEY_CHARACTERISTIC, BSS.KEY_PARAMETER,
                  BSS.KEY_POPULATION, BSS.KEY_TRANSFER, BSS.KEY_INTERACTION]

    PAGE_KEYS = [BSS.KEY_POPULATION, BSS.KEY_TRANSFER, BSS.KEY_TRANSFER_DATA, BSS.KEY_INTERACTION,
                 BSS.KEY_CHARACTERISTIC, BSS.KEY_PARAMETER]

    @classmethod
    def elaborate_structure(cls):
        cls.ITEM_TYPE_SPECS[cls.KEY_POPULATION]["instruction_allowed"] = True
        cls.ITEM_TYPE_SPECS[cls.KEY_TRANSFER]["instruction_allowed"] = True
        # TODO: As above, delete the following comments if progbook is locked in.
        # cls.ITEM_TYPE_SPECS[cls.KEY_PROGRAM]["instruction_allowed"] = True

        # cls.create_item_type_attributes(cls.KEY_PROGRAM, ["target_pops"],
        #                                 IDRefType(attribute = "name", item_types = [cls.KEY_POPULATION]))
        cls.create_item_type_attributes([cls.KEY_COMPARTMENT], [cls.TERM_DATA], TimeSeriesType())
        cls.create_item_type_attributes([cls.KEY_CHARACTERISTIC], [cls.TERM_DATA], TimeSeriesType())
        cls.create_item_type_attributes([cls.KEY_PARAMETER], [cls.TERM_DATA], TimeSeriesType())
        cls.create_item_type_attributes([cls.KEY_TRANSFER, cls.KEY_INTERACTION], [cls.TERM_DATA], TimeSeriesType())
        cls.create_item_type_attributes([cls.KEY_TRANSFER, cls.KEY_INTERACTION], [cls.KEY_POPULATION_LINKS],
                                        ContentType(is_list=True))

        cls.PAGE_SPECS[cls.KEY_POPULATION]["tables"].append(DetailColumns(item_type=cls.KEY_POPULATION))

        # TODO: As above, delete the following comment if progbook is locked in.
        # cls.PAGE_SPECS[cls.KEY_PROGRAM]["tables"].append(DetailColumns(item_type=cls.KEY_PROGRAM))
        cls.PAGE_SPECS[cls.KEY_TRANSFER]["tables"].append(DetailColumns(item_type=cls.KEY_TRANSFER,
                                                                        attribute_list=["label"],
                                                                        exclude_not_include=False))
        cls.PAGE_SPECS[cls.KEY_TRANSFER]["tables"].append(ConnectionMatrix(template_item_type=cls.KEY_TRANSFER,
                                                                           source_item_type=cls.KEY_POPULATION,
                                                                           storage_item_type=None,
                                                                           storage_attribute=cls.KEY_POPULATION_LINKS))
        transfer_tables = cls.PAGE_SPECS[cls.KEY_TRANSFER_DATA]["tables"]
        transfer_tables.append(TimeDependentValuesEntry(template_item_type=cls.KEY_TRANSFER,
                                                        iterated_type=cls.KEY_POPULATION,
                                                        iterate_over_links=True,
                                                        value_attribute=cls.TERM_DATA))

        interaction_tables = cls.PAGE_SPECS[cls.KEY_INTERACTION]["tables"]
        interaction_tables.append(ConnectionMatrix(template_item_type=cls.KEY_INTERACTION,
                                                   source_item_type=cls.KEY_POPULATION,
                                                   storage_item_type=None,
                                                   storage_attribute=cls.KEY_POPULATION_LINKS,
                                                   self_connections=True))
        interaction_tables.append(TimeDependentValuesEntry(template_item_type=cls.KEY_INTERACTION,
                                                           iterated_type=cls.KEY_POPULATION,
                                                           iterate_over_links=True,
                                                           value_attribute=cls.TERM_DATA,
                                                           self_connections=True))

        cls.PAGE_SPECS[cls.KEY_TRANSFER]["can_skip"] = True
        cls.PAGE_SPECS[cls.KEY_TRANSFER_DATA]["can_skip"] = True
        # cls.PAGE_SPECS[cls.KEY_INTERACTION]["can_skip"] = True

        # TODO: As above, delete the following comment if progbook is locked in.
        # cls.PAGE_SPECS[cls.KEY_PROGRAM]["tables"].append(ConnectionMatrix(source_item_type = cls.KEY_PROGRAM,
        #                                                                  target_item_type = cls.KEY_POPULATION,
        #                                                                  storage_attribute = "target_pops"))
        table = TimeDependentValuesEntry(template_item_type=cls.KEY_PARAMETER, iterated_type=cls.KEY_POPULATION,
                                         value_attribute=cls.TERM_DATA)
        cls.PAGE_SPECS[cls.KEY_PARAMETER]["tables"].append(table)
        charac_tables = cls.PAGE_SPECS[cls.KEY_CHARACTERISTIC]["tables"]
        charac_tables.append(TimeDependentValuesEntry(template_item_type=cls.KEY_COMPARTMENT,
                                                      iterated_type=cls.KEY_POPULATION,
                                                      value_attribute=cls.TERM_DATA))
        cls.PAGE_SPECS[cls.KEY_CHARACTERISTIC]["tables"].append(
            TimeDependentValuesEntry(template_item_type=cls.KEY_CHARACTERISTIC,
                                     iterated_type=cls.KEY_POPULATION,
                                     value_attribute=cls.TERM_DATA))
