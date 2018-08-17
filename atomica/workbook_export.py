import sciris.core as sc
import xlsxwriter as xw
from xlsxwriter.utility import xl_rowcol_to_cell as xlrc

from .excel import AtomicaSpreadsheet, standard_formats
import io


# %% COMPLETELY INDEPENDENT CODE TO MAKE A SPREADSHEET FOR PROGRAMS.
# TODO: reconcile these!!!

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
        self.formats['center'] = self.book.add_format({'align': 'center'})
        self.formats['center_bold'] = self.book.add_format({'bold': 1, 'align': 'center'})
        self.formats['rc_title'] = {}
        self.formats['rc_title']['right'] = {}
        self.formats['rc_title']['right']['T'] = self.book.add_format({'bold': 1, 'align': 'right', 'text_wrap': True})
        self.formats['rc_title']['right']['F'] = self.book.add_format({'bold': 1, 'align': 'right', 'text_wrap': False})
        self.formats['rc_title']['left'] = {}
        self.formats['rc_title']['left']['T'] = self.book.add_format({'bold': 1, 'align': 'left', 'text_wrap': True})
        self.formats['rc_title']['left']['F'] = self.book.add_format({'bold': 1, 'align': 'left', 'text_wrap': False})
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

    def write_rowcol_name(self, sheet, row, col, name, align='right', wrap='T'):
        sheet.write(row, col, name, self.formats['rc_title'][align][wrap])

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

    def param_refs(self, sheet_name, column_number=1):
        """ gives the list of references to the entries in the row names (which are parameters) """
        par_range = range(self.first_row, self.last_row + 1)
        return ["='%s'!%s" % (sheet_name, self.get_cell_address(row, self.first_col + column_number)) for row in
                par_range]


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

    def emit(self, formats, rc_row_align='right', rc_title_align='right'):  # only important for row/col titles
        """ Emits the range and returns the new current row in the given sheet """
        # top-top headers
        formats.write_block_name(self.sheet, self.content.name, self.first_row)

        if self.content.assumption and self.first_row == 0 and self.content.assumption_properties['title'] is not None:
            formats.write_rowcol_name(sheet=self.sheet, row=self.first_row, col=self.data_range.last_col + 2,
                                      name=self.content.assumption_properties['title'], align='left', wrap='F')

        # headers
        for i, name in enumerate(self.content.column_names):
            formats.write_rowcol_name(self.sheet, self.first_row + 1, self.data_range.first_col + i, name,
                                      rc_title_align, )

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
                formats.write_rowcol_name(self.sheet, current_row, start_col + n, name, rc_row_align, wrap='F')
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

    def __init__(self, name=None, row_names=None, column_names=None, row_levels=None, data=None,
                 assumption_properties=None, assumption_data=None, assumption=True):
        self.name = name
        self.row_names = row_names
        self.column_names = column_names
        self.data = data
        self.assumption = assumption
        self.row_levels = row_levels
        self.row_format = AtomicaFormats.GENERAL
        self.row_formats = None
        if assumption_properties is None:
            self.assumption_properties = {'title': None, 'connector': 'OR', 'columns': ['Assumption']}
        else:
            self.assumption_properties = assumption_properties
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

# %% Program spreadsheet exports.

class ProgramSpreadsheet(object):
    def __init__(self, pops, comps, progs, pars, data_start=None, data_end=None, blh_effects=False):

        self.book = None
        self.formats = None

        self.pops = pops
        self.comps = comps
        self.progs = progs
        self.pars = pars.values()
        self.blh_effects = blh_effects

        self.data_start = data_start if data_start is not None else 2015.0 # WARNING, remove
        self.data_end = data_end if data_end is not None else 2018.0 # WARNING, remove
        self.prog_range = None
        self.ref_pop_range = None
        self.data_range = range(int(self.data_start), int(self.data_end + 1))

        self.npops = len(pops)
        self.nprogs = len(progs)

    def to_spreadsheet(self):
        # Return a AtomicaSpreadsheet with the contents of this Workbook
        f = io.BytesIO() # Write to this binary stream in memory

        self.book = xw.Workbook(f)
        self.formats = AtomicaFormats(self.book) # TODO - move some of the AtomicaFormats methods to excel.py

        self.generate_targeting()
        self.generate_costcovdata()
        self.generate_covoutdata()

        self.book.close()

        # Dump the file content into a AtomicaSpreadsheet
        return AtomicaSpreadsheet(f)

    def generate_targeting(self):

        sheet = self.book.add_worksheet('Program targeting')

        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 40)
        sheet.set_column(6, 6, 12)
        sheet.set_column(7, 7, 16)
        sheet.set_column(8, 8, 16)
        sheet.set_column(9, 9, 12)
        current_row = 0

        coded_params = []
        for item in self.progs:
            if type(item) is dict:
                name = item['name']
                short = item['short']
                target_pops = [''] + ['' for popname in self.pops]
                target_comps = [''] + ['' for comp in self.comps]
            coded_params.append([short, name] + target_pops + target_comps)

        # Hard-coded writing of target descriptions in sheet.
        sheet.write(0, 5, "Targeted to (populations)", self.formats.formats["center_bold"])
        sheet.write(0, 6 + len(self.pops), "Targeted to (compartments)",
                                 self.formats.formats["center_bold"])

        column_names = ['Short name', 'Long name', ''] + self.pops + [''] + self.comps
        content = AtomicaContent(name='',
                                 row_names=range(1, len(self.progs) + 1),
                                 column_names=column_names,
                                 data=coded_params,
                                 assumption=False)
        self.prog_range = TitledRange(sheet=sheet, first_row=current_row, content=content)
        current_row = self.prog_range.emit(self.formats, rc_title_align='left')
        self.ref_prog_range = self.prog_range

    def generate_costcovdata(self):

        sheet = self.book.add_worksheet('Spending data')

        current_row = 0
        sheet.set_column('C:C', 20)
        row_levels = ['Total spend', 'Capacity constraints', 'Unit cost: best', 'Unit cost: low',
                      'Unit cost: high']
        content = AtomicaContent(name='',
                                 row_names=self.ref_prog_range.param_refs(),
                                 column_names=range(int(self.data_start), int(self.data_end + 1)))
        content.row_formats = [AtomicaFormats.GENERAL, AtomicaFormats.GENERAL, AtomicaFormats.GENERAL,
                               AtomicaFormats.GENERAL, AtomicaFormats.GENERAL]
        content.assumption = True
        content.row_levels = row_levels
        the_range = TitledRange(sheet, current_row, content)
        content.get_row_formats()
        current_row = the_range.emit(self.formats)

    def generate_covoutdata(self):

        sheet = self.book.add_worksheet('Program effects')

        current_row = 0
        sheet.set_column(1, 1, 30)
        sheet.set_column(2, 2, 12)
        sheet.set_column(3, 3, 12)
#        sheet.set_column(4, 4, 12)
#        sheet.set_column(5, 5, 2)
        sheet.set_column(4, 4, 2)

        row_levels = []
        for p in self.pops:
            if self.blh_effects:
                row_levels.extend([p + ': best', p + ': low', p + ': high'])
            else: row_levels.extend([p])
        content = AtomicaContent(row_names=self.pars,
                                 column_names=['Value if none of the programs listed here are targeting this parameter'])
        content.row_format = AtomicaFormats.GENERAL
        content.row_levels = row_levels

        assumption_properties = {'title': 'Value for a person covered by this program alone:',
                                 'connector': '',
                                 'columns': self.ref_prog_range.param_refs()}

        content.assumption_properties = assumption_properties
        the_range = TitledRange(sheet, current_row, content)
        current_row = the_range.emit(self.formats, rc_title_align='left')


def make_progbook(filename, pops, comps, progs, pars, data_start=None, data_end=None, blh_effects=False):
    """ Generate the Atomica programs spreadsheet """

    # An integer argument is given: just create a pops dict using empty entries
    if sc.isnumber(pops):
        npops = pops
        pops = []  # Create real pops list
        for p in range(npops):
            pops.append('Pop %i' % (p + 1))

    if sc.isnumber(comps):
        ncomps = comps
        comps = []  # Create real compartments list
        for p in range(ncomps):
            pops.append('Comp %i' % (p + 1))

    if sc.isnumber(progs):
        nprogs = progs
        progs = []  # Create real pops list
        for p in range(nprogs):
            progs.append({'short': 'Prog %i' % (p + 1), 'name': 'Program %i' % (p + 1)})

    book = ProgramSpreadsheet(pops=pops, comps=comps, progs=progs, pars=pars, data_start=data_start, data_end=data_end, blh_effects=blh_effects)
    ss = book.to_spreadsheet()
    ss.save(filename)
    return filename

