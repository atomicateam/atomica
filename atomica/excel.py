# -*- coding: utf-8 -*-
"""
Atomica Excel utilities file.
Contains functionality specific to Excel input and output.
"""

from .system import AtomicaException

from xlsxwriter.utility import xl_rowcol_to_cell as xlrc
import sciris as sc
import io
import openpyxl
from openpyxl.comments import Comment
import numpy as np
from .structure import FrameworkSettings as FS
from .system import logger, reraise_modify

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
    formats['unlocked'] = workbook.add_format({'locked': 0, 'bg_color': BG_COLOR, 'border': 1,'border_color': BORDER_COLOR})
    formats['center_unlocked'] = workbook.add_format({'align': 'center','locked': 0, 'bg_color': BG_COLOR, 'border': 1,'border_color': BORDER_COLOR})
    formats['general'] = workbook.add_format({'locked': 0, 'num_format': 0x00, 'bg_color': BG_COLOR, 'border': 1,'border_color': BORDER_COLOR})

    # Conditional formats
    formats['unlocked_boolean_true'] = workbook.add_format({'bg_color': OPT_COLOR})
    formats['unlocked_boolean_false'] = workbook.add_format({'bg_color': BG_COLOR})
    formats['not_required'] = workbook.add_format({'bg_color': '#EEEEEE','border': 1,'border_color': '#CCCCCC'})
    formats['white_bg'] = workbook.add_format({'bg_color': '#FFFFFF','border': 1,'border_color': '#CCCCCC'})
    formats['ignored'] = workbook.add_format({'pattern': 14}) # Hatched with diagonal lines - this represents a cell whose value will not be used in the model run (e.g., an assumption that also has time-specific points)
    formats['warning'] = workbook.add_format({'bg_color': '#FF0000'})
    formats['ignored_warning'] = workbook.add_format({'pattern': 14,'bg_color': '#FF0000'}) # hatched, with red background
    formats['ignored_not_required'] = workbook.add_format({'pattern': 14,'bg_color': '#EEEEEE','border': 1,'border_color': '#CCCCCC'}) # hatched, with grey background

    return formats


def apply_widths(worksheet,width_dict):
    for idx,width in width_dict.items():
        worksheet.set_column(idx, idx, width*1.1 + 1)


def update_widths(width_dict,column_index,contents):
    # Keep track of the maximum length of the contents in a column
    # width_dict is a dict that is keyed by column index e.g. 0,1,2
    # and the value is the length of the longest contents seen for that column
    if width_dict is None or contents is None or not sc.isstring(contents):
        return

    if len(contents) == 0:
        return

    if column_index not in width_dict:
        width_dict[column_index] = len(contents)
    else:
        width_dict[column_index] = max(width_dict[column_index],len(contents))


class AtomicaSpreadsheet(object):
    ''' A class for reading and writing data in binary format, so a project contains the spreadsheet loaded '''
    # This object provides an interface for managing the contents of files (particularly spreadsheets) as Python objects
    # that can be stored in the FE database. Basic usage is as follows:
    #
    # READING:
    #
    # ss = AtomicaSpreadsheet('input.xlsx') # Load a file into this object
    # f = ss.get_file() # Retrieve an in-memory file-like IO stream from the data
    # book = openpyxl.load_workbook(f) # This stream can be passed straight to openpyxl
    #
    # WRITING:
    #
    # f = io.BytesIO()
    # book = xlsxwriter.Workbook(f)
    # book.close()
    # spreadsheet = AtomicaSpreadsheet(f) # note that `f.flush()` will automatically be called
    # f.close()
    #
    # As shown above, no disk IO is required to manipulate the spreadsheets with openpyxl (or xlrd/xlsxwriter)

    def __init__(self, source):
        # Construct a new AtomicaSpreadsheet given the contents of the spreadsheet
        #
        # INPUTS
        # - source : This contains the contents of the file. It can be
        #   - A string, which is interpreted as a filename
        #   - A file-like object like a BytesIO, the entire contents of which will be read

        self.filename = None

        if isinstance(source,io.BytesIO):
            source.flush()
            source.seek(0)
            self.data = source.read()
        else:
            filepath = sc.makefilepath(filename=source)
            self.filename = filepath
            self.load_date = sc.now()
            with open(filepath, mode='rb') as f:
                self.data = f.read()

        self.load_date = sc.now()

    def __repr__(self):
        output = sc.prepr(self)
        return output

    def save(self, filename=None):
        # This function writes the contents of self.data to a file on disk
        if filename is None:
            if self.filename is not None:
                filename = self.filename
            else:
                raise Exception('Cannot determine filename')

        filepath = sc.makefilepath(filename=filename)
        with open(filepath, mode='wb') as f:
            f.write(self.data)
        print('Spreadsheet saved to %s.' % filepath)

        return filepath

    def get_file(self):
        # Return a file-like object with the contents of the file
        # This can then be used to open the workbook from memory without writing anything to disk e.g.
        # - book = openpyxl.load_workbook(self.get_file())
        # - book = xlrd.open_workbook(file_contents=self.get_file().read())
        return io.BytesIO(self.data)

def transfer_comments(target,comment_source):
    # Format this AtomicaSpreadsheet based on the extra meta-content in comment_source
    #
    # In reality, a new spreadsheet is created with values from this AtomicaSpreadsheet
    # and cell-wise formatting from the comment_source AtomicaSpreadsheet. If a cell exists in
    # this spreadsheet and not in the source, it will be retained as-is. If more cells exist in
    # the comment_source than in this spreadsheet, those cells will be dropped. If a sheet exists in
    # the comment_source and not in the current workbook, it will be added

    assert isinstance(comment_source, AtomicaSpreadsheet)

    this_workbook = openpyxl.load_workbook(target.get_file(),data_only=False) # This is the value source workbook
    old_workbook = openpyxl.load_workbook(comment_source.get_file(),data_only=False) # A openpyxl workbook for the old content

    for sheet in this_workbook.worksheets:

        # If this sheet isn't in the old workbook, do nothing
        if sheet.title not in old_workbook.sheetnames:
            continue

        # Transfer comments
        for row in old_workbook[sheet.title].rows:
            for cell in row:
                if cell.comment:
                    sheet[cell.coordinate].comment = Comment(cell.comment.text, '')

    f = io.BytesIO()
    this_workbook.save(f)
    f.flush()
    f.seek(0)
    target.data = f.read()

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

    for i,row in enumerate(worksheet.rows):

        # Skip any rows starting with '#ignore'
        if row[0].value and sc.isstring(row[0].value) and row[0].value.startswith('#ignore'):
            continue  # Move on to the next row if row skipping is marked True

        # Find out whether we need to add the row to the buffer
        for cell in row:
            if cell.value:  # If the row has a non-empty cell, add the row to the buffer
                if not buffer:
                    start = i+1 # Excel rows are indexed starting at 1
                buffer.append(row)
                break
        else: # If the row was empty, then yield the buffer and flag that it should be cleared at the next iteration
            if buffer:
                tables.append(buffer) # Only append the buffer if it is not empty
                start_rows.append(start)
            buffer = []

    # After the last row, if the buffer has some un-flushed contents, then yield it
    if buffer:
        tables.append(buffer)
        start_rows.append(start)

    return tables, start_rows


def write_matrix(worksheet,start_row,nodes,entries,formats,references=None, enable_diagonal=True, boolean_choice=False,widths=None):
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
        update_widths(widths,0,node)
        worksheet.write_formula(start_row  , i+1, references[node], formats['center_bold'],value=node)
        update_widths(widths,i+1,node)

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
                val = FS.DEFAULT_SYMBOL_INAPPLICABLE
                worksheet.write(row,col,val, formats["center"])
                worksheet.data_validation(xlrc(row,col), {"validate": "list", "source": ["N.A."]})
            else:
                val = content[from_idx,to_idx]
                worksheet.write(row,col, content[from_idx,to_idx], formats["center_unlocked"])
                if boolean_choice:
                    worksheet.data_validation(xlrc(row,col), {"validate": "list", "source": ["Y","N"]})
                    worksheet.conditional_format(xlrc(row,col), {'type': 'cell','criteria':'equal to','value':'"Y"','format':formats['unlocked_boolean_true']})
                    worksheet.conditional_format(xlrc(row,col), {'type': 'cell','criteria':'equal to','value':'"N"','format':formats['unlocked_boolean_false']})
            table_references[(nodes[from_idx],nodes[to_idx])] = xlrc(row,col,True,True) # Store reference to this interaction
            values_written[table_references[(nodes[from_idx],nodes[to_idx])]] = val

    next_row = start_row + 1 + len(nodes) + 1
    return next_row,table_references,values_written


class TimeDependentConnections(object):
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
            self.allowed_units = [FS.QUANTITY_TYPE_NUMBER, FS.QUANTITY_TYPE_PROBABILITY]
        elif self.type == 'interaction':
            self.enable_diagonal = True
            self.allowed_units = [FS.DEFAULT_SYMBOL_INAPPLICABLE]
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
                units = vals[3].lower().strip() if vals[3] else None
                if units is None:
                    raise AtomicaException(str('The units for transfer "%s" ("%s"->"%s") cannot be empty' % (full_name,from_pop,to_pop)))
                assumption = vals[4] # This is the assumption cell
                assert vals[5].strip().lower() == 'or' # Double check we are reading a time-dependent row with the expected shape
                ts = TimeSeries(units=units)
                if assumption is not None:
                    ts.insert(None, assumption)
                for t, v in zip(tvec, vals[6:]):
                    if v is not None:
                        ts.insert(t, v)
                ts_entries[(from_pop,to_pop)] = ts

        if not ts_entries:
            logger.warning('TDC "%s" did not contain any data - is this intentional?' % (full_name))

        return TimeDependentConnections(code_name, full_name, tvec, pops, interaction_type, ts=ts_entries)

    def write(self,worksheet,start_row,formats,references=None, widths = None):

        if not references:
            references = {x:x for x in self.pops} # Default null mapping for populations

        ### First, write the titles
        current_row = start_row
        worksheet.write(current_row, 0, 'Abbreviation', formats["center_bold"])
        update_widths(widths, 0, 'Abbreviation')
        worksheet.write(current_row, 1, 'Full Name', formats["center_bold"])
        update_widths(widths, 1, 'Full Name')

        current_row += 1
        worksheet.write(current_row, 0, self.code_name)
        update_widths(widths, 0, self.code_name)
        worksheet.write(current_row, 1, self.full_name)
        references[self.code_name] = "='%s'!%s" % (worksheet.name, xlrc(current_row, 0, True, True))
        references[self.full_name] = "='%s'!%s" % (worksheet.name, xlrc(current_row, 1, True, True))  # Reference to the full name

        ### Then, write the matrix
        current_row += 2 # Leave a blank row below the matrix

        # Note - table_references are local to this TimeDependentConnections instance
        # For example, there could be two transfers, and each of them could potentially transfer between 0-4 and 5-14
        # so the worksheet might contain two references from 0-4 to 5-14 but they would be for different transfers and thus
        # the time-dependent rows would depend on different boolean table cells
        current_row,table_references,values_written = write_matrix(worksheet,current_row,self.pops,self.ts,formats,references,enable_diagonal=self.enable_diagonal,boolean_choice=True,widths=widths)

        ### Finally, write the time dependent part
        headings = []
        headings.append('') # From
        headings.append('') # --->
        headings.append('') # To
        headings.append('Units')
        headings.append('Constant')
        headings.append('') # OR
        headings += [float(x) for x in self.tvec] # Times
        for i, entry in enumerate(headings):
            worksheet.write(current_row, i, entry, formats['center_bold'])
            update_widths(widths,i,entry)

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
                    worksheet.write(current_row, 3, ts.units.title(), format)
                    update_widths(widths, 3, ts.units.title())

                    if self.allowed_units:
                        worksheet.data_validation(xlrc(current_row, 3), {"validate": "list", "source": [x.title() for x in self.allowed_units]})
                    worksheet.write(current_row, 4, ts.assumption, format)
                    worksheet.write_formula(current_row, 5, gate_content('OR', entry_cell), formats['center'], value='OR')
                    # update_widths(widths, 5,  '...') # The largest length it will be here is '...' so use that

                else:
                    worksheet.write_formula(current_row, 0, gate_content(references[from_pop], entry_cell), formats['center_bold'], value='...')
                    worksheet.write_formula(current_row, 1, gate_content('--->', entry_cell), formats['center'], value='...')
                    worksheet.write_formula(current_row, 2, gate_content(references[to_pop], entry_cell), formats['center_bold'], value='...')
                    worksheet.write_blank(current_row, 3, '', format)

                    if self.allowed_units:
                        worksheet.data_validation(xlrc(current_row, 3), {"validate": "list", "source": [x.title() for x in self.allowed_units]})
                    worksheet.write_blank(current_row, 4, '', format)
                    worksheet.write_formula(current_row, 5, gate_content('OR', entry_cell), formats['center'], value='...')
                    # update_widths(widths, 5,  '...')

                # Write hyperlink - it's a bit convoluted because we can't read back the contents of the original cell to know
                # whether it was originally Y or N
                if values_written[entry_cell] != FS.DEFAULT_SYMBOL_INAPPLICABLE:
                    worksheet.write_url(entry_cell, 'internal:%s!%s' % (worksheet.name, xlrc(current_row, 2)),cell_format=formats['center_unlocked'],string=values_written[entry_cell])

                offset = 6  # The time values start in this column (zero based index)
                content = [None]*len(self.tvec)

                if ts:
                    for t, v in zip(ts.t, ts.vals):
                        idx = np.where(self.tvec == t)[0][0]
                        content[idx] = v

                for idx, v in enumerate(content):
                    if v is None:
                        worksheet.write_blank(current_row, offset + idx, v, format)
                    else:
                        worksheet.write(current_row, offset + idx, v, format)

                # Conditional formatting for the assumption, depending on whether time-values were entered
                fcn_empty_times = 'COUNTIF(%s:%s,"<>" & "")>0' % (xlrc(current_row, offset), xlrc(current_row, offset + idx))
                worksheet.conditional_format(xlrc(current_row, 4), {'type': 'formula', 'criteria': '=' + fcn_empty_times, 'format': formats['ignored']})
                worksheet.conditional_format(xlrc(current_row, 4), {'type': 'formula', 'criteria': '=AND(%s,NOT(ISBLANK(%s)))' % (fcn_empty_times, xlrc(current_row, 4)), 'format': formats['ignored_warning']})

                # Conditional formatting for the row - it has a white background if the gating cell is 'N'
                worksheet.conditional_format('%s:%s' % (xlrc(current_row, 3), xlrc(current_row, 4)), {'type': 'formula', 'criteria': '=%s<>"Y"' % (entry_cell), 'format': formats['white_bg']})
                worksheet.conditional_format('%s:%s' % (xlrc(current_row, offset), xlrc(current_row, offset + idx)), {'type': 'formula', 'criteria': '=%s<>"Y"' % (entry_cell), 'format': formats['white_bg']})

        current_row += 2

        return current_row


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

    """

    # A TDVE table is used for representing Characteristics and Parameters that appear in the Parset, a quantity
    # that has one sparse time array for each population. A TDVE table contains
    # - An ordered list of TimeSeries objects
    # - A name for the quantity (as this is what gets printed and read, it's usually a full name rather than a code name)
    # - Optionally a list of allowed units - All TimeSeries objects must have units contained in this list
    # - A time axis (e.g. np.arange(2000,2019)) - all TimeSeries time values must exactly match one of the values here
    #   i.e. you cannot try to write a TimeSeries that has a time value that doesn't appear as a table heading

    def __init__(self, name, tvec, ts=None, allowed_units=None, comment=None):
        """ Instantiate a new TimeDepedentValuesEntry table object

        :param name: The name/title for this table
        :param tvec: Specify the time values for this table. All TimeSeries in the ts dict should have corresponding time values
        :param ts: Optionally specify an odict() of TimeSeries objects populating the rows. Could be populated after
        :param allowed_units: Optionally specify a list of allowed units that will appear as a dropdown
        :param comment: Optionally specify descriptive text that will be added as a comment to the name cell
        """

        # ts - An odict where the key is a population name and the value is a TimeSeries
        # name - This is the name of the quantity i.e. the full name of the characteristic or parameter
        # tvec - The time values that will be written in the headings
        # allowed_units - Possible values for the unit selection dropdown
        if ts is None:
            ts = sc.odict()

        self.name = name
        self.comment = comment
        self.tvec = tvec
        self.ts = ts
        self.allowed_units = [x.title() if x in FS.STANDARD_UNITS else x for x in allowed_units] if allowed_units is not None else None # Otherwise, can be an odict with keys corresponding to ts - leave as None for no restriction

    def __repr__(self):
        output= sc.prepr(self)
        return output

    @property
    def has_data(self):
        # Returns True if any of the time series
        return any([x.has_data for x in self.ts.values()])

    @staticmethod
    def from_rows(rows):
        # Given a set of openpyxl rows, instantiate a TimeDependentValuesEntry object
        # That is, the parent object e.g. Databook() is responsible for finding where the TDVE table is,
        # and reading all of the rows associated with it (skipping #ignored rows) and then passing those rows,
        # unparsed, to this function
        #
        # 'units', 'uncertainty', and 'constant' are optional - if 'constant' is present then expect
        # that the column after it contains 'or'

        from .structure import TimeSeries # Import here to avoid circular reference

        # First, read the headings
        vals = [x.value for x in rows[0]]

        if vals[0] is None:
            raise AtomicaException('In cell %s of the spreadsheet, the name of the table is missing. This can also happen if extra rows have been added without a "#ignore" entry in the first column' % (rows[0][0].coordinate))
        elif not sc.isstring(vals[0]):
            raise AtomicaException('In cell %s of the spreadsheet, the name of the quantity assigned to this table needs to be a string' % rows[0][0].coordinate)
        name = vals[0].strip()

        lowered_headings = [x.lower().strip() if sc.isstring(x) else x for x in vals]

        # We can optionally have units, uncertainty, and constant
        # nb. finding the index means this is robust to extra empty
        # columns, a user adding one of the these fields to a single table on a page
        # might introduce a blank column to all of the other TDVE elements on the page too
        # so the code below should be able to deal with this
        offset = 1 # This is the column where the time values start

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
            t_end = offset+vals[offset:].index(None)
        else:
            t_end = len(vals)
        tvec = np.array(vals[offset:t_end],dtype=float)
        ts_entries = sc.odict()

        # For each TimeSeries that we will instantiate
        for row in rows[1:]:
            vals = [x.value for x in row]
            if not sc.isstring(vals[0]):
                raise AtomicaException('In cell %s of the spreadsheet, the name of the entry was expected to be a string, but it was not. The left-most column is expected to be a name. If you are certain the value is correct, add an single quote character at the start of the cell to ensure it remains as text' % row[0].coordinate)
            series_name = vals[0].strip()

            if units_index is not None:
                assert sc.isstring(vals[units_index]), "The 'units' quantity needs to be specified as text e.g. 'probability'"
                if vals[units_index]:
                    units = vals[units_index]
                    if units.lower().strip() in FS.STANDARD_UNITS:
                        units = units.lower().strip() # Only lower and strip units if they are standard units
                else:
                    units = None
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
                assert vals[offset - 1].strip().lower() == 'or', 'Error with validating row in TDVE table "%s" (did not find the text "OR" in the expected place)' % (name)  # Check row is as expected

            data_cells = row[offset:t_end]

            for t,cell in zip(tvec,data_cells):
                if np.isfinite(t): # Ignore any times that are NaN - this happens if the cell was empty and casted to a float
                    ts.insert(t,cell_get_number(cell)) # If cell_get_number returns None, this gets handled accordingly by ts.insert()
            ts_entries[series_name] = ts

        tvec = tvec[np.isfinite(tvec)] # Remove empty entries from the array
        return TimeDependentValuesEntry(name,tvec,ts_entries)

    def write(self,worksheet,start_row,formats,references=None,widths=None,assumption_heading='Constant',write_units=True,write_uncertainty=False,write_assumption=True):
        # references is a dict where the key is a string value and the content is a cell
        # Any populations that appear in this dict will have their value replaced by a reference
        # formats should be the dict returned by `excel.standard_formats` when it was called to add
        # formatting to the Workbook containing the worksheet passed in here.
        #
        # widths should be a dict that will store sizing information for some of the columns
        # it is updated in place
        # - assumption_heading : This is the string heading for the 'Constant'/'Assumption' (constant in databook, assumption in progbook)

        if not references:
            references = dict()

        current_row = start_row

        # First, assemble and write the headings
        headings = []
        headings.append(self.name)
        offset = 1 # This is the column where the time values start

        if write_units:
            headings.append('Units')
            units_index = offset # Column to write the units in
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
        for i,entry in enumerate(headings):
            if entry in references:
                worksheet.write_formula(current_row, 0, references[entry], formats['center_bold'],value=entry)
            else:
                worksheet.write(current_row, i, entry, formats['center_bold'])
            update_widths(widths,i,entry)

            if i == 0 and self.comment:
                worksheet.write_comment(xlrc(current_row,i), self.comment)

        # Now, write the TimeSeries objects - self.ts is an odict and whatever pops are present will be written in whatever order they are in
        for row_name, row_ts in self.ts.items():
            current_row += 1

            # Write the name
            if row_name in references:
                worksheet.write_formula(current_row, 0, references[row_name], formats['center_bold'],value=row_name)
                update_widths(widths, 0, row_name)
            else:
                worksheet.write_string(current_row, 0, row_name, formats['center_bold'])
                update_widths(widths, 0, row_name)

            # Write the units
            if write_units:

                if row_ts.units:
                    if row_ts.units.lower().strip() in FS.STANDARD_UNITS: # Preserve case if nonstandard unit
                        unit = row_ts.units.title().strip()
                    else:
                        unit = row_ts.units.strip()
                    worksheet.write(current_row,units_index,unit)
                    update_widths(widths, units_index, unit)
                else:
                    worksheet.write(current_row,units_index,FS.DEFAULT_SYMBOL_INAPPLICABLE)

                if self.allowed_units and isinstance(self.allowed_units,dict) and row_name in self.allowed_units: # Add dropdown selection if there is more than one valid choice for the units
                    allowed = self.allowed_units[row_name]
                elif self.allowed_units and not isinstance(self.allowed_units,dict):
                    allowed = self.allowed_units
                else:
                    allowed = None

                if allowed:
                    worksheet.data_validation(xlrc(current_row, units_index),{"validate": "list", "source": allowed})

            if write_uncertainty:
                if row_ts.sigma is None:
                    worksheet.write(current_row,uncertainty_index, row_ts.sigma,formats['unlocked'])
                else:
                    worksheet.write(current_row,uncertainty_index,row_ts.sigma,formats['not_required'])

            if row_ts.has_data:
                format = formats['not_required']
            else:
                format = formats['unlocked']

            if write_assumption:
                # Write the assumption
                worksheet.write(current_row,constant_index,row_ts.assumption, format)
                # Write the separator between the assumptions and the time values
                worksheet.write(current_row,constant_index+1,'OR',formats['center'])
                update_widths(widths, constant_index+1, 'OR')

            # Write the time values
            content = [None]*len(self.tvec) # Initialize an empty entry for every time in the TDVE's tvec

            for t,v in zip(row_ts.t,row_ts.vals):
                # If the TimeSeries contains data for that time point, then insert it now
                idx = np.where(self.tvec == t)[0]
                if len(idx):
                    content[idx[0]] = v

            for idx,v in enumerate(content):
                if v is None:
                    worksheet.write_blank(current_row, offset+idx, v, format)
                else:
                    worksheet.write(current_row, offset+idx, v, format)

            # Conditional formatting for the assumption
            fcn_empty_times = 'COUNTIF(%s:%s,"<>" & "")>0' % (xlrc(current_row,offset),xlrc(current_row,offset+idx))
            # Hatched out if the cell will be ignored
            worksheet.conditional_format(xlrc(current_row, 2), {'type': 'formula', 'criteria':'='+fcn_empty_times,'format':formats['ignored']})
            worksheet.conditional_format(xlrc(current_row, 2), {'type': 'formula', 'criteria':'=AND(%s,NOT(ISBLANK(%s)))' % (fcn_empty_times,xlrc(current_row,2)),'format':formats['ignored_warning']})

        return current_row+2 # Add two so there is a blank line after this table

def cell_require_string(cell):
    # Take in an openpyxl Cell instance, if it doesn't contain a string, then throw a helpful error
    if not sc.isstring(cell.value):
        raise AtomicaException('Cell %s needs to contain a string (i.e. not a number, date, or other cell type)' % cell.coordinate)

def cell_get_number(cell,dtype=float):
    # This function is to guard against accidentally having strings.
    # If a cell contains a formula that has evaluated to a number, then the type should be numeric
    if cell.value is None:
        return None
    elif cell.data_type == 'n': # Numeric type
        return dtype(cell.value)
    elif cell.data_type == 's': # Only do relatively expensive string processing if it's actually a string type
        s = cell.value.lower().strip()
        if s == FS.DEFAULT_SYMBOL_INAPPLICABLE:
            return None
        elif not s.replace('-',''):
            return None

    raise AtomicaException('Cell %s needs to contain a number' % cell.coordinate)
