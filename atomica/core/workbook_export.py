import sciris.core as sc
import xlsxwriter as xw
from xlsxwriter.utility import xl_rowcol_to_cell as xlrc

from .excel import AtomicaSpreadsheet, standard_formats
import io


# %% Classes

class ContentRules:

    def __init__(self, formats):
        self.formats = formats

    def write_rowcol_name(self, sheet, row, col, name, align='right', wrap='T'):
        sheet.write(row, col, name, self.formats['rc_title'][align][wrap])

    # special processing for bool values (to keep the content separate from representation)
    def write_unlocked(self, sheet, row, col, data, row_format='unlocked'):
        if type(data) == bool:
            bool_data = 'TRUE' if data else 'FALSE'
            sheet.write(row, col, bool_data, self.formats[row_format])
        else:
            sheet.write(row, col, data, self.formats[row_format])

    def write_empty_unlocked(self, sheet, row, col, row_format='unlocked'):
        sheet.write_blank(row, col, None, self.formats[row_format])





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
        self.formats = standard_formats(self.book)
        self.content_rules = ContentRules(self.formats) 

        self.generate_targeting()
        self.generate_costcovdata()
        self.generate_covoutdata()

        self.book.close()

        # Dump the file content into a AtomicaSpreadsheet
        return AtomicaSpreadsheet(f)


    def set_content(self, name=None, row_names=None, column_names=None, row_levels=None, data=None,
                    row_format='general', row_formats=None, assumption_properties=None, assumption_data=None, assumption=True):
        # Set the content
        if assumption_properties is None:
            assumption_properties = {'title': None, 'connector': 'OR', 'columns': ['Assumption']}
        self.assumption_data = assumption_data
        return sc.odict([("name",            name),
                         ("row_names",       row_names),
                         ("column_names",    column_names),
                         ("row_levels",      row_levels),
                         ("row_format",      row_format),
                         ("row_formats",     row_formats),
                         ("data",            data),
                         ("assumption_properties", assumption_properties),
                         ("assumption_data", assumption_data),
                         ("assumption",      assumption)])
        

    def generate_targeting(self):
        # Generate targeting sheet
        sheet = self.book.add_worksheet('Program targeting')

        # Set column width
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 40)
        sheet.set_column(6, 6, 12)
        sheet.set_column(7, 7, 16)
        sheet.set_column(8, 8, 16)
        sheet.set_column(9, 9, 12)
        current_row = 0

        # Write descriptions of targeting
        sheet.write(0, 5, "Targeted to (populations)", self.formats["bold"])
        sheet.write(0, 6 + len(self.pops), "Targeted to (compartments)", self.formats["bold"])

        # Write populations and compartments for targeting
        coded_params = []
        for item in self.progs:
            if type(item) is dict:
                name = item['name']
                short = item['short']
                target_pops = [''] + ['' for popname in self.pops]
                target_comps = [''] + ['' for comp in self.comps]
            coded_params.append([short, name] + target_pops + target_comps)

        # Make column names
        column_names = ['Short name', 'Long name', ''] + self.pops + [''] + self.comps
        content = self.set_content(row_names=range(1,len(self.progs)+1),
                                   column_names=column_names,
                                   data=coded_params,
                                   assumption=False)
        
        self.prog_range = TitledRange(sheet=sheet, first_row=current_row, content=content)
        current_row = self.prog_range.emit(self.content_rules, self.formats, rc_title_align='left')
        self.ref_prog_range = self.prog_range


    def generate_costcovdata(self):
        # Generate cost-coverage sheet
        sheet = self.book.add_worksheet('Spending data')

        current_row = 0
        sheet.set_column('C:C', 20)
        row_levels = ['Total spend', 'Capacity constraints', 'Unit cost: best', 'Unit cost: low',
                      'Unit cost: high']
        content = self.set_content(row_names=self.ref_prog_range.param_refs(),
                                   column_names=range(int(self.data_start), int(self.data_end + 1)),
                                   row_formats=['general']*5,
                                   row_levels=row_levels)

        the_range = TitledRange(sheet, current_row, content)
        current_row = the_range.emit(self.content_rules, self.formats)

    def generate_covoutdata(self):
        # Generate coverage-outcome sheet
        sheet = self.book.add_worksheet('Program effects')

        current_row = 0
        sheet.set_column(1, 1, 30)
        sheet.set_column(2, 2, 12)
        sheet.set_column(3, 3, 12)
        sheet.set_column(4, 4, 12)
        sheet.set_column(5, 5, 12)
        sheet.set_column(6, 6, 2)

        row_levels = []
        for p in self.pops:
            if self.blh_effects:
                row_levels.extend([p + ': best', p + ': low', p + ': high'])
            else: row_levels.extend([p])

        assumption_properties = {'title': 'Value for a person covered by this program alone:',
                                 'connector': '',
                                 'columns': self.ref_prog_range.param_refs()}

        content = self.set_content(row_names=self.pars,
                                   column_names=['Value if none of the programs listed here are targeting this parameter', 'Coverage interation', 'Impact interaction'],
                                   row_format='general',
                                   assumption_properties=assumption_properties,
                                   row_levels=row_levels)

        the_range = TitledRange(sheet, current_row, content)
        current_row = the_range.emit(self.content_rules, self.formats, rc_title_align='left')


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

