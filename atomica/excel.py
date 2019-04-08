# -*- coding: utf-8 -*-
"""
Miscellaneous utility functions for Excel files

This module implements utility functions for Excel functionality that is common
to different kinds of spreadsheets used in Atomica (e.g. Databooks and Program Books).
For example, Excel formatting, and time-varying data entry tables, are implemented here.

"""

from xlsxwriter.utility import xl_rowcol_to_cell as xlrc
import sciris as sc
import io
import openpyxl
from openpyxl.comments import Comment
import numpy as np
from .system import FrameworkSettings as FS
from .system import logger

def standard_formats(workbook):
    # Add standard formatting to a workbook and return the set of format objects
    # for use when writing within the workbook
    """ the formats used in the spreadsheet """
#    darkgray = '#413839'
#    optima_blue = '#18C1FF'
    atomica_blue = '#98E0FA'
    optional_orange = '#FFA500'
    BG_COLOR = atomica_blue
    OPT_COLOR = optional_orange
    BORDER_COLOR = 'white'

    formats = {}

    # Locked formats
    formats['bold'] = workbook.add_format({'bold': 1})
    formats['center'] = workbook.add_format({'align': 'center'})
    formats['center_bold'] = workbook.add_format({'bold': 1, 'align': 'center'})
    formats['rc_title'] = {}
    formats['rc_title']['right'] = {}
    formats['rc_title']['right']['T'] = workbook.add_format({'bold': 1, 'align': 'right', 'text_wrap': True})
    formats['rc_title']['right']['F'] = workbook.add_format({'bold': 1, 'align': 'right', 'text_wrap': False})
    formats['rc_title']['left'] = {}
    formats['rc_title']['left']['T'] = workbook.add_format({'bold': 1, 'align': 'left', 'text_wrap': True})
    formats['rc_title']['left']['F'] = workbook.add_format({'bold': 1, 'align': 'left', 'text_wrap': False})

    # Unlocked formats
    formats['unlocked'] = workbook.add_format({'locked': 0, 'bg_color': BG_COLOR, 'border': 1, 'border_color': BORDER_COLOR})
    formats['center_unlocked'] = workbook.add_format({'align': 'center', 'locked': 0, 'bg_color': BG_COLOR, 'border': 1, 'border_color': BORDER_COLOR})
    formats['general'] = workbook.add_format({'locked': 0, 'num_format': 0x00, 'bg_color': BG_COLOR, 'border': 1, 'border_color': BORDER_COLOR})

    # Conditional formats
    formats['unlocked_boolean_true'] = workbook.add_format({'bg_color': OPT_COLOR})
    formats['unlocked_boolean_false'] = workbook.add_format({'bg_color': BG_COLOR})
    formats['not_required'] = workbook.add_format({'bg_color': '#EEEEEE', 'border': 1, 'border_color': '#CCCCCC'})
    formats['white_bg'] = workbook.add_format({'bg_color': '#FFFFFF', 'border': 1, 'border_color': '#CCCCCC'})
    formats['ignored'] = workbook.add_format({'pattern': 14})  # Hatched with diagonal lines - this represents a cell whose value will not be used in the model run (e.g., an assumption that also has time-specific points)
    formats['warning'] = workbook.add_format({'bg_color': '#FF0000'})
    formats['ignored_warning'] = workbook.add_format({'pattern': 14, 'bg_color': '#FF0000'})  # hatched, with red background
    formats['ignored_not_required'] = workbook.add_format({'pattern': 14, 'bg_color': '#EEEEEE', 'border': 1, 'border_color': '#CCCCCC'})  # hatched, with grey background

    return formats


def apply_widths(worksheet, width_dict):
    for idx, width in width_dict.items():
        worksheet.set_column(idx, idx, width * 1.1 + 1)


def update_widths(width_dict: dict, column_index: int, contents: str) -> None:
    """
    Keep track of required width for a column

    ``width_dict`` is a dict that is keyed by column index e.g. 0,1,2
    and the value is the length of the longest contents seen for that column

    :param width_dict: Storage dictionary
    :param column_index: Index of the column value has been inserted in
    :param contents: Content, length of which is used to set width

    """

    if width_dict is None or contents is None or not sc.isstring(contents):
        return

    if len(contents) == 0:
        return

    if column_index not in width_dict:
        width_dict[column_index] = len(contents)
    else:
        width_dict[column_index] = max(width_dict[column_index], len(contents))


def transfer_comments(target:sc.Spreadsheet, comment_source:sc.Spreadsheet) -> None:
    """
    Copy comments between spreadsheets

    This function copies comments from one spreadsheet to another. Under the hood,
    a new spreadsheet is created with values from the ``target`` Spreadsheet
    and cell-wise formatting from the ``comment_source`` Spreadsheet. If a cell exists in
    this spreadsheet and not in the source, it will be retained as-is. If more cells exist in
    the ``comment_source`` than in this spreadsheet, those cells will be dropped. If a sheet exists in
    the ``comment_source`` and not in the current workbook, it will be added

    :param target: The target spreadsheet to write comments into
    :param comment_source: The source spreadsheet containing comments

    """

    assert isinstance(target, sc.Spreadsheet)
    assert isinstance(comment_source, sc.Spreadsheet)

    this_workbook = openpyxl.load_workbook(target.tofile(), data_only=False)  # This is the value source workbook
    old_workbook = openpyxl.load_workbook(comment_source.tofile(), data_only=False)  # A openpyxl workbook for the old content

    for sheet in this_workbook.worksheets:

        # If this sheet isn't in the old workbook, do nothing
        if sheet.title not in old_workbook.sheetnames:
            continue

        # Transfer comments
        for row in old_workbook[sheet.title].rows:
            for cell in row:
                if cell.comment:
                    sheet[cell.coordinate].comment = Comment(cell.comment.text, '')

    # Save the modified spreadsheet to a new buffer
    f = io.BytesIO()
    this_workbook.save(f)
    f.flush()
    f.seek(0)
    target.load(f)


def read_tables(worksheet):
    # This function takes in a openpyxl worksheet, and returns tables
    # A table consists of a block of rows with any #ignore rows skipped
    # This function will start at the top of the worksheet, read rows into a buffer
    # until it gets to the first entirely empty row
    # And then returns the contents of that buffer as a table. So a table is a list of openpyxl rows
    # This function continues until it has exhausted all of the rows in the sheet

    buffer = []
    tables = []
    start_rows = []
    start = None

    for i, row in enumerate(worksheet.rows):

        # Skip any rows starting with '#ignore'
        if len(row)==0 or (row[0].value and sc.isstring(row[0].value) and row[0].value.startswith('#ignore')):
            continue  # Move on to the next row if row skipping is marked True
            
        # Find out whether we need to add the row to the buffer
        for cell in row:
            if cell.value:  # If the row has a non-empty cell, add the row to the buffer
                if not buffer:
                    start = i + 1  # Excel rows are indexed starting at 1
                buffer.append(row)
                break
        else:  # If the row was empty, then yield the buffer and flag that it should be cleared at the next iteration
            if buffer:
                tables.append(buffer)  # Only append the buffer if it is not empty
                start_rows.append(start)
            buffer = []

    # After the last row, if the buffer has some un-flushed contents, then yield it
    if buffer:
        tables.append(buffer)
        start_rows.append(start)

    return tables, start_rows

class TimeDependentConnections(object):
    """
    Structure for reading/writing interactions

    A :class:`TimeDependentConnections` object is suitable when there are time dependent interactions between two quantities
    This class is used for both transfers and interactions. The content that it writes consists of

    - A connection matrix table that has Y/N selection of which interactions are present between two things
    - A set of pairwise connections specifying to, from, units, assumption, and time

    Interactions can have a diagonal, whereas transfers cannot (e.g. a population can infect itself but cannot transfer to itself).

    In Excel, a :class:`TimeDependentConnections` maps to three tables

    1. A table to enter the code name and full name
    2. An interactions matrix with Y/N indicating whether an interaction between two populations exists
    3. A set of rows for entering time varying data for each pair of populations

    :param code_name: the code name of this quantity e.g. 'aging'
    :param full_name: the full name of this quantity e.g. 'Aging'
    :param tvec: time values for the time-dependent rows
    :param pops: list of strings to use as the rows and columns - these are typically lists of population code names
    :param type: 'transfer' or 'interaction'. A transfer cannot have diagonal entries, and can have Number or Probability formats. An Interaction can have
                 diagonal entries and only has N.A. formats
    :param ts: Optionally specify a dict containing all of the non-empty TimeSeries objects used. The format is ``{(from_pop, to_pop):TimeSeries}``.
               An interaction can only be Y/N for clarity, if it is Y then a row is displayed for the TimeSeries. Actually, the Y/N can be
               decided in the first instance based on the provided TimeSeries i.e. if a TimeSeries is provided for an interaction, then the
               interaction must have been marked with Y
    :param pop_type: Specify pop_type, which is used by :meth:`ProjectData.add_pop` to determine which TDCs to add new populations to

    """

    def __init__(self, code_name:str, full_name:str, tvec, from_pops:list, to_pops:list, interpop_type:str, ts:dict=None, from_pop_type:str=None, to_pop_type:str=None):
        self.code_name = code_name
        self.full_name = full_name
        self.type = interpop_type
        self.from_pop_type = from_pop_type
        self.from_pops = from_pops
        self.to_pop_type = to_pop_type
        self.to_pops = to_pops
        self.tvec = tvec
        self.ts = ts if ts is not None else sc.odict()

        if self.type == 'transfer':
            self.enable_diagonal = False
            self.allowed_units = [FS.QUANTITY_TYPE_NUMBER + ' (per year)', FS.QUANTITY_TYPE_PROBABILITY + ' (per year)']
        elif self.type == 'interaction':
            self.enable_diagonal = True
            self.allowed_units = [FS.DEFAULT_SYMBOL_INAPPLICABLE]
        else:
            raise Exception('Unknown TimeDependentConnections type - must be "transfer" or "interaction"')

    def __repr__(self):
        return '<TDC %s "%s">' % (self.type.title(), self.code_name)

    @staticmethod
    def from_tables(tables:list, interaction_type):
        """
        Instantiate based on list of tables

        This method instantiates and initializes a new :class:`TimeDependentConnections` object from
        tables that have been read in using :func:`read_tables`. Note that the parent object
        such as :class:`ProjectData` is responsible for extracting the tables and passing them
        to this function. For instance, the transfers sheet might contain more than one set of
        tables, so it is the calling function's responsibility to split those tables up into
        the groups of three expected by this method.

        :param tables: A list of tables. A table here is a list of rows, and a row is a list of cells.
        :param interaction_type: A string identifying the interaction type - either 'transfer' or 'interaction'
        :return: A new :class:`TimeDependentConnections` instance

        """

        from .utils import TimeSeries  # Import here to avoid circular reference

        assert interaction_type in {'transfer','interaction'}, 'Unknown interaction type'

        # Read the name table
        code_name = tables[0][1][0].value
        full_name = tables[0][1][1].value
        if len(tables[0][0]) > 2 and sc.isstring(tables[0][0][2].value) and tables[0][0][2].value.strip().lower() == 'from population type' and tables[0][1][2].value is not None:
            cell_require_string(tables[0][1][2])
            from_pop_type = tables[0][1][2].value.strip()
        else:
            from_pop_type = None

        if len(tables[0][0]) > 3 and sc.isstring(tables[0][0][3].value) and tables[0][0][3].value.strip().lower() == 'to population type' and tables[0][1][3].value is not None:
            cell_require_string(tables[0][1][3])
            to_pop_type = tables[0][1][3].value.strip()
        else:
            to_pop_type = None

        if interaction_type == 'transfer':
            assert from_pop_type == to_pop_type, 'Transfers can only occur between populations of the same type'

        # Read the pops from the Y/N table. The Y/N content of the table depends on the timeseries objects that
        # are present. That is, if the Y/N matrix contains a Y then a TimeSeries must be read in, and vice versa.
        # Therefore, we don't actually parse the matrix, and instead just read in all the TimeSeries instances
        # that are defined and infer the matrix that way.
        to_pops = [x.value for x in tables[1][0][1:] if x.value]
        from_pops = []
        for row in tables[1][1:]:
            from_pops.append(row[0].value)

        # Now read any TimeSeries entries that are present. First we need to work out which columns are which, and
        # what times are present
        vals = [x.value for x in tables[2][0]]
        lowered_headings = [x.lower().strip() if sc.isstring(x) else x for x in vals]
        offset = 3 # The column where time values normally start

        if 'units' in lowered_headings:
            units_index = lowered_headings.index('units')
            offset += 1
        else:
            units_index = None

        if 'uncertainty' in lowered_headings:
            uncertainty_index = lowered_headings.index('uncertainty')
            offset += 1
        else:
            uncertainty_index = None

        if 'constant' in lowered_headings:
            constant_index = lowered_headings.index('constant')
            offset += 2
        elif 'assumption' in lowered_headings:
            constant_index = lowered_headings.index('assumption')
            offset += 2
        else:
            constant_index = None

        if None in vals[offset:]: # This handles the case where an empty column is followed by comments
            t_end = offset + vals[offset:].index(None)
        else:
            t_end = len(vals)
        tvec = np.array(vals[offset:t_end], dtype=float)
        ts_entries = sc.odict()

        for row in tables[2][1:]:
            if row[0].value != '...':
                assert row[0].value in from_pops, 'Population "%s" not found - should be contained in %s' % (row[0].value, from_pops)
                assert row[2].value in to_pops, 'Population "%s" not found - should be contained in %s' % (row[2].value, to_pops)
                vals = [x.value for x in row]
                from_pop = vals[0]
                to_pop = vals[2]

                if units_index is not None and vals[units_index]:
                    assert sc.isstring(vals[units_index]), "The 'units' quantity needs to be specified as text e.g. 'probability'"
                    units = vals[units_index]
                    if units.lower().strip() in FS.STANDARD_UNITS:
                        units = units.lower().strip()  # Only lower and strip units if they are standard units
                else:
                    units = None

                ts = TimeSeries(units=units)

                if uncertainty_index is not None:
                    ts.sigma = cell_get_number(row[uncertainty_index])
                else:
                    ts.sigma = None

                if constant_index is not None:
                    ts.assumption = cell_get_number(row[constant_index])
                else:
                    ts.assumption = None

                if constant_index is not None:
                    assert sc.isstring(vals[offset - 1]) and vals[offset - 1].strip().lower() == 'or', 'Error with validating row in TDC table "%s" (did not find the text "OR" in the expected place)' % (code_name)  # Check row is as expected

                data_cells = row[offset:t_end]

                for t, cell in zip(tvec, data_cells):
                    if np.isfinite(t):  # Ignore any times that are NaN - this happens if the cell was empty and casted to a float
                        ts.insert(t, cell_get_number(cell))  # If cell_get_number returns None, this gets handled accordingly by ts.insert()
                ts_entries[(from_pop, to_pop)] = ts

        return TimeDependentConnections(code_name, full_name, tvec, from_pops=from_pops, to_pops=to_pops, interpop_type=interaction_type, ts=ts_entries, from_pop_type=from_pop_type, to_pop_type=to_pop_type)

    def write(self, worksheet, start_row, formats, references:dict=None, widths:dict=None, assumption_heading='Constant', write_units:bool=None, write_uncertainty:bool=None, write_assumption:bool=None) -> int:
        """
        Write to cells in a worksheet

        :param worksheet: An xlsxwriter worksheet instance
        :param start_row: The first row in which to write values
        :param formats: Format dict for the opened workbook - typically the return value of :func:`standard_formats` when the workbook was opened
        :param references: References dict containing cell references for strings in the current workbook
        :param widths: ``dict`` storing column widths
        :param assumption_heading: String to use for assumption/constant column heading - either 'Constant' or 'Assumption' (they are functionally identical and
                                   both map to the ``assumption`` attribute of the underlying :class:`TimeSeries` object)
        :param write_units: If True, write the units column to the spreadsheet
        :param write_uncertainty: If True, write the uncertainty column to the spreadsheet
        :param write_assumption: If True, write the constant/assumption column to the spreadsheet
        :return: The row index for the next available row for writing in the spreadsheet

        """

        assert assumption_heading in {'Constant','Assumption'}, 'Unsupported assumption heading'
        if write_units is None:
            write_units = any((ts.units is not None for ts in self.ts.values()))
        if write_uncertainty is None:
            write_uncertainty = any((ts.sigma is not None for ts in self.ts.values()))
        if write_assumption is None:
            write_assumption = any((ts.assumption is not None for ts in self.ts.values()))

        if not references:
            references = {x: x for x in self.from_pops+self.to_pops}  # Default null mapping for populations

        # First, write the name entry table
        current_row = start_row
        worksheet.write(current_row, 0, 'Abbreviation', formats["center_bold"])
        update_widths(widths, 0, 'Abbreviation')
        worksheet.write(current_row, 1, 'Full Name', formats["center_bold"])
        update_widths(widths, 1, 'Full Name')
        worksheet.write(current_row, 2, 'From population type', formats["center_bold"])
        update_widths(widths, 2, 'From population type')
        worksheet.write(current_row, 3, 'To population type', formats["center_bold"])
        update_widths(widths, 3, 'To population type')

        current_row += 1
        worksheet.write(current_row, 0, self.code_name)
        update_widths(widths, 0, self.code_name)
        worksheet.write(current_row, 1, self.full_name)
        update_widths(widths, 1, self.full_name)
        worksheet.write(current_row, 2, self.from_pop_type)
        update_widths(widths, 2, self.from_pop_type)
        worksheet.write(current_row, 3, self.to_pop_type)
        update_widths(widths, 3, self.to_pop_type)

        references[self.code_name] = "='%s'!%s" % (worksheet.name, xlrc(current_row, 0, True, True))
        references[self.full_name] = "='%s'!%s" % (worksheet.name, xlrc(current_row, 1, True, True))  # Reference to the full name

        # Then, write the Y/N matrix
        current_row += 2  # Leave a blank row below the matrix
        # Note - table_references are local to this TimeDependentConnections instance
        # For example, there could be two transfers, and each of them could potentially transfer between 0-4 and 5-14
        # so the worksheet might contain two references from 0-4 to 5-14 but they would be for different transfers and thus
        # the time-dependent rows would depend on different boolean table cells
        current_row, table_references, values_written = self._write_pop_matrix(worksheet, current_row, formats, references, boolean_choice=True, widths=widths)

        # Finally, write the time dependent part
        headings = []
        headings.append('')  # From
        headings.append('')  # --->
        headings.append('')  # To
        offset = len(headings)

        if write_units:
            headings.append('Units')
            units_index = offset  # Column to write the units in
            offset += 1

        if write_uncertainty:
            headings.append('Uncertainty')
            uncertainty_index = offset  # Column to write the units in
            offset += 1

        if write_assumption:
            headings.append(assumption_heading)
            headings.append('')
            constant_index = offset
            offset += 2

        headings += [float(x) for x in self.tvec]
        for i, entry in enumerate(headings):
            worksheet.write(current_row, i, entry, formats['center_bold'])
            update_widths(widths, i, entry)

        # Now, we will write a wrapper that gates the content
        # If the gating cell is 'Y', then the content will be displayed, otherwise not
        def gate_content(content, gating_cell):
            if content.startswith('='):  # If this is itself a reference
                return ('=IF(%s="Y",%s,"...")' % (gating_cell, content[1:]))
            else:
                return('=IF(%s="Y","%s","...")' % (gating_cell, content))

        for from_idx in range(0, len(self.from_pops)):
            for to_idx in range(0, len(self.to_pops)):
                current_row += 1
                from_pop = self.from_pops[from_idx]
                to_pop = self.to_pops[to_idx]
                entry_tuple = (from_pop, to_pop)
                entry_cell = table_references[entry_tuple]

                if entry_tuple in self.ts:
                    ts = self.ts[entry_tuple]
                    format = formats['not_required']
                else:
                    ts = None
                    format = formats['unlocked']

                if ts:
                    worksheet.write_formula(current_row, 0, gate_content(references[from_pop], entry_cell), formats['center_bold'], value=from_pop)
                    update_widths(widths, 0, from_pop)
                    worksheet.write_formula(current_row, 1, gate_content('--->', entry_cell), formats['center'], value='--->')
                    worksheet.write_formula(current_row, 2, gate_content(references[to_pop], entry_cell), formats['center_bold'], value=to_pop)
                    update_widths(widths, 2, to_pop)

                    if write_units:
                        worksheet.write(current_row, units_index, ts.units.title(), format)
                        update_widths(widths, units_index, ts.units.title())
                        if self.allowed_units:
                            worksheet.data_validation(xlrc(current_row, units_index), {"validate": "list", "source": [x.title() for x in self.allowed_units]})

                    if write_uncertainty:
                        worksheet.write(current_row, uncertainty_index, ts.sigma, formats['not_required'])
                        update_widths(widths, uncertainty_index, ts.units.title())

                    if write_assumption:
                        worksheet.write(current_row, constant_index, ts.assumption, format)
                        worksheet.write_formula(current_row, constant_index+1, gate_content('OR', entry_cell), formats['center'], value='OR')
                        update_widths(widths, constant_index+1, 'OR')

                else:
                    worksheet.write_formula(current_row, 0, gate_content(references[from_pop], entry_cell), formats['center_bold'], value='...')
                    worksheet.write_formula(current_row, 1, gate_content('--->', entry_cell), formats['center'], value='...')
                    worksheet.write_formula(current_row, 2, gate_content(references[to_pop], entry_cell), formats['center_bold'], value='...')

                    if write_units:
                        worksheet.write_blank(current_row, units_index, '', format)
                        if self.allowed_units:
                            worksheet.data_validation(xlrc(current_row, units_index), {"validate": "list", "source": [x.title() for x in self.allowed_units]})

                    if write_uncertainty:
                        worksheet.write_blank(current_row, uncertainty_index, '', formats['not_required'])

                    if write_assumption:
                        worksheet.write_blank(current_row, constant_index, '', format)
                        worksheet.write_formula(current_row, constant_index+1, gate_content('OR', entry_cell), formats['center'], value='...')
                        update_widths(widths, constant_index+1,  '...')

                # Write hyperlink - it's a bit convoluted because we can't read back the contents of the original cell to know
                # whether it was originally Y or N
                if values_written[entry_cell] != FS.DEFAULT_SYMBOL_INAPPLICABLE:
                    worksheet.write_url(entry_cell, 'internal:%s!%s' % (worksheet.name, xlrc(current_row, 2)), cell_format=formats['center_unlocked'], string=values_written[entry_cell])

                content = [None] * len(self.tvec)

                if ts:
                    for t, v in zip(ts.t, ts.vals):
                        idx = np.where(self.tvec == t)[0][0]
                        content[idx] = v

                for idx, v in enumerate(content):
                    if v is None:
                        worksheet.write_blank(current_row, offset + idx, v, format)
                    else:
                        worksheet.write(current_row, offset + idx, v, format)
                    widths[offset+idx] = max(widths[offset+idx],7) if offset+idx in widths else 7

                if write_assumption:
                    # Conditional formatting for the assumption, depending on whether time-values were entered
                    fcn_empty_times = 'COUNTIF(%s:%s,"<>" & "")>0' % (xlrc(current_row, offset), xlrc(current_row, offset + idx))
                    worksheet.conditional_format(xlrc(current_row, constant_index), {'type': 'formula', 'criteria': '=' + fcn_empty_times, 'format': formats['ignored']})
                    worksheet.conditional_format(xlrc(current_row, constant_index), {'type': 'formula', 'criteria': '=AND(%s,NOT(ISBLANK(%s)))' % (fcn_empty_times, xlrc(current_row, constant_index)), 'format': formats['ignored_warning']})

                # Conditional formatting for the row - it has a white background if the gating cell is 'N'
                # worksheet.conditional_format('%s:%s' % (xlrc(current_row, 3), xlrc(current_row, 4)), {'type': 'formula', 'criteria': '=%s<>"Y"' % (entry_cell), 'format': formats['white_bg']})
                worksheet.conditional_format('%s:%s' % (xlrc(current_row, 3), xlrc(current_row, offset + idx)), {'type': 'formula', 'criteria': '=%s<>"Y"' % (entry_cell), 'format': formats['white_bg']})

        current_row += 2

        return current_row

    def _write_pop_matrix(self, worksheet, start_row, formats, references:dict=None, boolean_choice=False, widths:dict=None):
        """
        Write a square matrix to Excel

        This function writes the Y/N matrix

        - Transfer matrix
        - Interactions matrix

        If ``self.enable_diagonal`` is ``False`` then the diagonal will be forced to be ``'N.A.'``. If an entry
        is specified for an entry on the diagonal and ``enable_diagonal=False``, an error will be thrown

        :param worksheet: An xlsxwriter worksheet instance
        :param start_row: The first row in which to write values
        :param formats: Format dict for the opened workbook - typically the return value of :func:`standard_formats` when the workbook was opened
        :param references: Optionally supply dict with references, used to link population names in Excel
        :param boolean_choice: If True, values will be coerced to Y/N and an Excel validation will be added
        :param widths: ``dict`` storing column widths
        :return: Tuple with ``(next_row, table_references, values_written)``. The references are used for hyperlinking to the Excel matrix

        """

        entries = self.ts

        if not references:
            references = {x: x for x in self.from_pops+self.to_pops}  # This is a null-mapping that takes say 'adults'->'adults' thus simplifying the workflow. Otherwise, it's assumed a reference exists for every node

        table_references = {}
        values_written = {}

        # Write the headers
        for i, node in enumerate(self.to_pops):
            worksheet.write_formula(start_row, i + 1, references[node], formats['center_bold'], value=node)
            update_widths(widths, i + 1, node)
        for i, node in enumerate(self.from_pops):
            worksheet.write_formula(start_row + i + 1, 0, references[node], formats['center_bold'], value=node)
            update_widths(widths, 0, node)

        # Prepare the content - first replace the dict with one keyed by index. This is because we cannot apply formatting
        # after writing content, so have to do the writing in a single pass over the entire matrix
        if boolean_choice:
            content = np.full((len(self.from_pops), len(self.to_pops)), 'N', dtype=object)  # This will also coerce the value to string in preparation for writing
        else:
            content = np.full((len(self.from_pops), len(self.to_pops)), '', dtype=object)  # This will also coerce the value to string in preparation for writing

        for interaction, value in entries.items():
            from_pop, to_pop = interaction
            if not self.enable_diagonal and from_pop == to_pop:
                raise Exception('Trying to write a diagonal entry to a table that is not allowed to contain diagonal terms')  # This is because data loss will occur if the user adds entries on the diagonal, then writes the table, and then reads it back in
            from_idx = self.from_pops.index(from_pop)
            to_idx = self.to_pops.index(to_pop)
            if boolean_choice:
                value = 'Y' if value else 'N'
            content[from_idx, to_idx] = value

        # Write the content
        for from_idx in range(0, len(self.from_pops)):
            for to_idx in range(0, len(self.to_pops)):
                row = start_row + 1 + from_idx
                col = to_idx + 1
                if not self.enable_diagonal and self.to_pops[to_idx] == self.from_pops[from_idx]:  # Disable the diagonal if it's linking the same two quantities and that's desired
                    val = FS.DEFAULT_SYMBOL_INAPPLICABLE
                    worksheet.write(row, col, val, formats["center"])
                    worksheet.data_validation(xlrc(row, col), {"validate": "list", "source": ["N.A."]})
                else:
                    val = content[from_idx, to_idx]
                    worksheet.write(row, col, content[from_idx, to_idx], formats["center_unlocked"])
                    if boolean_choice:
                        worksheet.data_validation(xlrc(row, col), {"validate": "list", "source": ["Y", "N"]})
                        worksheet.conditional_format(xlrc(row, col), {'type': 'cell', 'criteria': 'equal to', 'value': '"Y"', 'format': formats['unlocked_boolean_true']})
                        worksheet.conditional_format(xlrc(row, col), {'type': 'cell', 'criteria': 'equal to', 'value': '"N"', 'format': formats['unlocked_boolean_false']})
                table_references[(self.from_pops[from_idx], self.to_pops[to_idx])] = xlrc(row, col, True, True)  # Store reference to this interaction
                values_written[table_references[(self.from_pops[from_idx], self.to_pops[to_idx])]] = val

        next_row = start_row + 1 + len(self.from_pops) + 1
        return next_row, table_references, values_written



class TimeDependentValuesEntry(object):
    """ Table for time-dependent data entry

    This class is Databooks and Program books to enter potentially time-varying data.
    Conceptually, it maps a set of TimeSeries object to a single name and table in the
    spreadsheet. For example, a Characteristic might contain a TimeSeries for each population,
    and the resulting TimeDependentValuesEntry (TDVE) table would have a `name` matching the
    population, and TimeSeries for each population.

    The TDVE class optionally allows the specification of units, assumptions, and uncertainty,
    which each map to properties on the underlying TimeSeries objects. It also contains a
    time vector corresponding to the time values that appear or will appear in the spreadsheet.

    Note that the units are stored within the TimeSeries objects, which means that they can
    are able to differ across rows.

    :param name: The name/title for this table
    :param tvec: Specify the time values for this table. All TimeSeries in the ts dict should have corresponding time values
    :param ts: Optionally specify an odict() of TimeSeries objects populating the rows. Could be populated after
    :param allowed_units: Optionally specify a list of allowed units that will appear as a dropdown
    :param comment: Optionally specify descriptive text that will be added as a comment to the name cell

    """

    def __init__(self, name, tvec, ts=None, allowed_units=None, comment=None):

        if ts is None:
            ts = sc.odict()

        self.name = name #: Name for th quantity printed in Excel
        self.comment = comment #: A comment that will be added in Excel
        self.tvec = tvec #: time axis (e.g. np.arange(2000,2019)) - all TimeSeries time values must exactly match one of the values here
        self.ts = ts #: dict of :class:`TimeSeries` objects
        self.allowed_units = [x.title() if x in FS.STANDARD_UNITS else x for x in allowed_units] if allowed_units is not None else None  # Otherwise, can be an odict with keys corresponding to ts - leave as None for no restriction

    def __repr__(self):
        output = sc.prepr(self)
        return output

    @property
    def has_data(self) -> bool:
        """
        Check whether all time series have data entered

        :return: True if all of the TimeSeries objects stored in the TDVE have data
        """

        return all([x.has_data for x in self.ts.values()])

    @staticmethod
    def from_rows(rows: list):
        """
        Create new instance from Excel rows

        Given a set of openpyxl rows, instantiate a :class:`TimeDependentValuesEntry` object
        That is, the parent object e.g. :class:`ProjectData` is responsible for finding where the TDVE table is,
        and reading all of the rows associated with it (skipping ``#ignored`` rows) and then passing those rows,
        unparsed, to this function

        Headings for 'units', 'uncertainty', and 'assumption'/'constant' are optional and will be read in
        if they are present in the spreadsheet.

        :param rows: A list of rows
        :return: A new :class:`TimeDependentValuesEntry` instance

        """

        from .utils import TimeSeries  # Import here to avoid circular reference

        # First, read the headings
        vals = [x.value for x in rows[0]]

        if vals[0] is None:
            raise Exception('The name of the table is missing. This can also happen if extra rows have been added without a "#ignore" entry in the first column')
        elif not sc.isstring(vals[0]):
            raise Exception('In cell %s of the spreadsheet, the name of the quantity assigned to this table needs to be a string' % rows[0][0].coordinate)
        name = vals[0].strip()

        lowered_headings = [x.lower().strip() if sc.isstring(x) else x for x in vals]

        # We can optionally have units, uncertainty, and constant
        # nb. finding the index means this is robust to extra empty
        # columns, a user adding one of the these fields to a single table on a page
        # might introduce a blank column to all of the other TDVE elements on the page too
        # so the code below should be able to deal with this
        offset = 1  # This is the column where the time values start

        if 'units' in lowered_headings:
            units_index = lowered_headings.index('units')
            offset += 1
        else:
            units_index = None

        if 'uncertainty' in lowered_headings:
            uncertainty_index = lowered_headings.index('uncertainty')
            offset += 1
        else:
            uncertainty_index = None

        if 'constant' in lowered_headings:
            constant_index = lowered_headings.index('constant')
            offset += 2
        elif 'assumption' in lowered_headings:
            constant_index = lowered_headings.index('assumption')
            offset += 2
        else:
            constant_index = None

        if None in vals[offset:]:
            t_end = offset + vals[offset:].index(None)
        else:
            t_end = len(vals)
        tvec = np.array(vals[offset:t_end], dtype=float)
        ts_entries = sc.odict()

        # For each TimeSeries that we will instantiate
        for row in rows[1:]:
            vals = [x.value for x in row]
            if not sc.isstring(vals[0]):
                raise Exception('In cell %s of the spreadsheet, the name of the entry was expected to be a string, but it was not. The left-most column is expected to be a name. If you are certain the value is correct, add an single quote character at the start of the cell to ensure it remains as text' % row[0].coordinate)
            series_name = vals[0].strip()

            if units_index is not None and vals[units_index]:
                assert sc.isstring(vals[units_index]), "The 'units' quantity needs to be specified as text e.g. 'probability'"
                units = vals[units_index]
                if units.lower().strip() in FS.STANDARD_UNITS:
                    units = units.lower().strip()  # Only lower and strip units if they are standard units
            else:
                units = None

            ts = TimeSeries(units=units)

            if uncertainty_index is not None:
                ts.sigma = cell_get_number(row[uncertainty_index])
            else:
                ts.sigma = None

            if constant_index is not None:
                ts.assumption = cell_get_number(row[constant_index])
            else:
                ts.assumption = None

            if constant_index is not None:
                assert sc.isstring(vals[offset - 1]) and vals[offset - 1].strip().lower() == 'or', 'Error with validating row in TDVE table "%s" (did not find the text "OR" in the expected place)' % (name)  # Check row is as expected

            data_cells = row[offset:t_end]

            for t, cell in zip(tvec, data_cells):
                if np.isfinite(t):  # Ignore any times that are NaN - this happens if the cell was empty and casted to a float
                    ts.insert(t, cell_get_number(cell))  # If cell_get_number returns None, this gets handled accordingly by ts.insert()
            ts_entries[series_name] = ts

        tvec = tvec[np.isfinite(tvec)]  # Remove empty entries from the array
        return TimeDependentValuesEntry(name, tvec, ts_entries)

    def write(self, worksheet, start_row, formats, references: dict=None, widths:dict=None, assumption_heading='Constant', write_units:bool=None, write_uncertainty:bool=None, write_assumption:bool=None) -> int:
        """
        Write to cells in a worksheet

        :param worksheet: An xlsxwriter worksheet instance
        :param start_row: The first row in which to write values
        :param formats: Format dict for the opened workbook - typically the return value of :func:`standard_formats` when the workbook was opened
        :param references: References dict containing cell references for strings in the current workbook
        :param widths: ``dict`` storing column widths
        :param assumption_heading: String to use for assumption/constant column heading - either 'Constant' or 'Assumption' (they are functionally identical and
                                   both map to the ``assumption`` attribute of the underlying :class:`TimeSeries` object)
        :param write_units: If True, write the units column to the spreadsheet. By default, will only write if any of the TimeSeries objects have units
        :param write_uncertainty: If True, write the uncertainty column to the spreadsheet. By default, will only write if any of the TimeSeries objects have units
        :param write_assumption: If True, write the constant/assumption column to the spreadsheet. By default, will only write if any of the TimeSeries objects have units
        :return: The row index for the next available row for writing in the spreadsheet

        """

        assert assumption_heading in {'Constant','Assumption'}, 'Unsupported assumption heading'

        if write_units is None:
            write_units = any((ts.units is not None for ts in self.ts.values()))
        if write_uncertainty is None:
            write_uncertainty = any((ts.sigma is not None for ts in self.ts.values()))
        if write_assumption is None:
            write_assumption = any((ts.assumption is not None for ts in self.ts.values()))

        if not references:
            references = dict()

        current_row = start_row

        # First, assemble and write the headings
        headings = []
        headings.append(self.name)
        offset = 1  # This is the column where the time values start (after the 'or')

        if write_units:
            headings.append('Units')
            units_index = offset  # Column to write the units in
            offset += 1

        if write_uncertainty:
            headings.append('Uncertainty')
            uncertainty_index = offset  # Column to write the units in
            offset += 1

        if write_assumption:
            headings.append(assumption_heading)
            headings.append('')
            constant_index = offset
            offset += 2

        headings += [float(x) for x in self.tvec]
        for i, entry in enumerate(headings):
            if entry in references:
                worksheet.write_formula(current_row, 0, references[entry], formats['center_bold'], value=entry)
            else:
                worksheet.write(current_row, i, entry, formats['center_bold'])
            update_widths(widths, i, entry)

            if i == 0 and self.comment:
                worksheet.write_comment(xlrc(current_row, i), self.comment)

        # Now, write the TimeSeries objects - self.ts is an odict and whatever pops are present will be written in whatever order they are in
        for row_name, row_ts in self.ts.items():
            current_row += 1

            # Write the name
            if row_name in references:
                worksheet.write_formula(current_row, 0, references[row_name], formats['center_bold'], value=row_name)
                update_widths(widths, 0, row_name)
            else:
                worksheet.write_string(current_row, 0, row_name, formats['center_bold'])
                update_widths(widths, 0, row_name)

            # Write the units
            if write_units:

                if row_ts.units:
                    if row_ts.units.lower().strip() in FS.STANDARD_UNITS:  # Preserve case if nonstandard unit
                        unit = row_ts.units.title().strip()
                    else:
                        unit = row_ts.units.strip()
                    worksheet.write(current_row, units_index, unit)
                    update_widths(widths, units_index, unit)
                else:
                    worksheet.write(current_row, units_index, FS.DEFAULT_SYMBOL_INAPPLICABLE)

                if self.allowed_units and isinstance(self.allowed_units, dict) and row_name in self.allowed_units:  # Add dropdown selection if there is more than one valid choice for the units
                    allowed = self.allowed_units[row_name]
                elif self.allowed_units and not isinstance(self.allowed_units, dict):
                    allowed = self.allowed_units
                else:
                    allowed = None

                if allowed:
                    worksheet.data_validation(xlrc(current_row, units_index), {"validate": "list", "source": allowed})

            if write_uncertainty:
                if row_ts.sigma is None:
                    worksheet.write(current_row, uncertainty_index, row_ts.sigma, formats['not_required']) # NB. For now, uncertainty is always optional
                else:
                    worksheet.write(current_row, uncertainty_index, row_ts.sigma, formats['not_required'])

            if row_ts.has_data:
                format = formats['not_required']
            else:
                format = formats['unlocked']

            if write_assumption:
                worksheet.write(current_row, constant_index, row_ts.assumption, format)
                worksheet.write(current_row, constant_index+1, 'OR', formats['center'])
                update_widths(widths, constant_index+1, 'OR')

            # Write the time values
            content = [None] * len(self.tvec)  # Initialize an empty entry for every time in the TDVE's tvec

            for t, v in zip(row_ts.t, row_ts.vals):
                # If the TimeSeries contains data for that time point, then insert it now
                idx = np.where(self.tvec == t)[0]
                if len(idx):
                    content[idx[0]] = v

            for idx, v in enumerate(content):
                if v is None:
                    worksheet.write_blank(current_row, offset+idx, v, format)
                else:
                    worksheet.write(current_row, offset+idx, v, format)
                widths[offset+idx] = max(widths[offset+idx],7) if offset+idx in widths else 7

            if write_assumption:
                # Conditional formatting for the assumption
                # Do this here, because after the loop above, we have easy and clear access to the range of cells to include in the formula
                fcn_empty_times = 'COUNTIF(%s:%s,"<>" & "")>0' % (xlrc(current_row, offset), xlrc(current_row, offset + idx))
                # Hatched out if the cell will be ignored
                worksheet.conditional_format(xlrc(current_row, constant_index), {'type': 'formula', 'criteria': '=' + fcn_empty_times, 'format': formats['ignored']})
                worksheet.conditional_format(xlrc(current_row, constant_index), {'type': 'formula', 'criteria': '=AND(%s,NOT(ISBLANK(%s)))' % (fcn_empty_times, xlrc(current_row, constant_index)), 'format': formats['ignored_warning']})

        return current_row + 2  # Add two so there is a blank line after this table


def cell_require_string(cell) -> None:
    """
    Check that a cell contains a string

    :param cell: An openpyxl cell
    :raises: :class:`Exception` with informative message if the cell value is not a string

    """

    if not sc.isstring(cell.value):
        raise Exception('Cell %s needs to contain a string (i.e. not a number, date, or other cell type)' % cell.coordinate)


def cell_get_number(cell, dtype=float):
    """
    Return numeric value from cell

    This function is to guard against accidentally having the Excel cell contain a string
    instead of a number. If a string has been entered, an error will be raised. The added value
    from this function is that if the Excel cell type is empty but the value is
    empty or ``N.A.`` then the value will be treated as though the cell was correctly set to a
    numeric type but had been left empty.

    The output is cast to ``dtype`` which means that code that requires numeric input from Excel
    can use this input to guarantee that the resulting number is of the correct type, or ``None``.

    :param cell: An openpyxl cell
    :param dtype: If the cell is numeric, cast to this type (default is `float` but could be `int` for example)
    :return: A scalar instance of ``dtype`` (e.g. ``float``) or ``None`` if cell is empty or being treated as empty
    :raises: :class:`Exception` if the cell contains a string

    """

    if cell.value is None:
        return None
    elif cell.data_type == 'n':  # Numeric type
        return dtype(cell.value)
    elif cell.data_type == 's':  # Only do relatively expensive string processing if it's actually a string type
        s = cell.value.lower().strip()
        if s == FS.DEFAULT_SYMBOL_INAPPLICABLE:
            return None
        elif not s.replace('-', ''):
            return None

    raise Exception('Cell %s needs to contain a number' % cell.coordinate)


def validate_category(workbook, expected_category) -> None:
    """
    Check Atomica workbook type

    This function makes sure that a workbook has a particular category property
    stored within it, and displays an appropriate error message if not. If the
    category isn't present or doesn't start with 'atomica', just ignore it for
    robustness (instead, a parsing error will likely be raised)

    :param workbook: An openpyxl workbook
    :param category: The expected string category
    :raises: :class:`Exception` if the workbook category is not valid

    """

    category = workbook.properties.category
    if category and sc.isstring(category) and category.startswith('atomica:'):
        if category.strip() != expected_category.strip():
            expected_type = expected_category.split(':')[1].title()
            actual_type = category.split(':')[1].title()
            message = 'Error loading %s - the provided file was a %s file' % (expected_type, actual_type)
            raise Exception(message)
