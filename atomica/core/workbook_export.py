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


class SheetRange:
    def __init__(self, first_row, first_col, num_rows, num_cols):
        self.first_row = first_row
        self.first_col = first_col

        self.num_rows = num_rows
        self.num_cols = num_cols

        self.last_row = self.first_row + self.num_rows - 1
        self.last_col = self.first_col + self.num_cols - 1

        self.start = xw.utility.xl_rowcol_to_cell(self.first_row, self.first_col)
        self.end = xw.utility.xl_rowcol_to_cell(self.last_row, self.last_col) 

    def param_refs(self, sheet_name, column_number=1):
        """ gives the list of references to the entries in the row names (which are parameters) """
        par_range = range(self.first_row, self.last_row + 1)
        
        range_vals = []
        for row in par_range: 
            cell_address = xw.utility.xl_rowcol_to_cell(row, self.first_col + column_number, row_abs=True, col_abs=True)
            range_vals.append("='%s'!%s" % (sheet_name, cell_address))
        return range_vals


class TitledRange(object):
    FIRST_COL = 2
    ROW_INTERVAL = 3

    def __init__(self, sheet=None, first_row=None, content=None):
        self.sheet = sheet
        self.content = content
        first_data_col = TitledRange.FIRST_COL
        num_data_rows = len(self.content["row_names"])

        if self.content["row_levels"] is not None:
            first_data_col += 1
            num_data_rows *= len(self.content["row_levels"])
            num_data_rows += len(self.content["row_names"]) - 1

        self.data_range = SheetRange(first_row + 2, first_data_col, num_data_rows, len(self.content["column_names"]))
        self.first_row = first_row

    def num_rows(self):
        return self.data_range.num_rows + 2

    def emit(self, content_rules, formats, rc_row_align='right', rc_title_align='right'):  # only important for row/col titles
        """ Emits the range and returns the new current row in the given sheet """
        # top-top headers
        
        self.sheet.write(self.first_row, 0, self.content["name"], formats['bold'])
        
        if self.content["assumption"] and self.first_row == 0 and self.content["assumption_properties"]['title'] is not None:
            content_rules.write_rowcol_name(sheet=self.sheet, row=self.first_row, col=self.data_range.last_col + 2,
                                      name=self.content["assumption_properties"]['title'], align='left', wrap='F')

        # headers
        for i, name in enumerate(self.content["column_names"]):
            content_rules.write_rowcol_name(self.sheet, self.first_row + 1, self.data_range.first_col + i, name,
                                      rc_title_align, )

        if self.content["assumption"]:
            for index, col_name in enumerate(self.content["assumption_properties"]['columns']):
                content_rules.write_rowcol_name(self.sheet, self.first_row + 1, self.data_range.last_col + 2 + index,
                                          col_name)

        current_row = self.data_range.first_row
        num_levels = len(self.content["row_levels"]) if self.content["row_levels"] is not None else 1
        
        # Get row names and formats
        if self.content["row_levels"] is None:
            row_names = [[name] for name in self.content["row_names"]]
            row_formats = [self.content["row_format"] for name in self.content["row_names"]]
        else:
            row_names = [[name, level] for name in self.content["row_names"] for level in self.content["row_levels"]]
            if self.content["row_formats"] is not None:
                row_formats = [row_format for name in self.content["row_names"] for row_format in self.content["row_formats"]]
            else:
                row_formats = [self.content["row_format"] for name in self.content["row_names"] for level in self.content["row_levels"]]

        # iterate over rows, incrementing current_row as we go
        for i, names_format in enumerate(zip(row_names, row_formats)):
            names, row_format = names_format
            if row_format=='g':
                import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
            start_col = self.data_range.first_col - len(names)
            # emit row name(s)
            for n, name in enumerate(names):
                content_rules.write_rowcol_name(self.sheet, current_row, start_col + n, name, rc_row_align, wrap='F')
            # emit data if present
            savedata = False
            if self.content["data"] is not None:
                try:
                    for j, item in enumerate(self.content["data"][i]):
                        content_rules.write_unlocked(self.sheet, current_row, self.data_range.first_col + j, item, row_format)
                    savedata = True  # It saved successfully
                except:
                    errormsg = 'WARNING, failed to save "%s" with data:\n%s' % (self.content["name"], self.content["data"])
                    print(errormsg)
                    savedata = False
            if not savedata:
                for j in range(self.data_range.num_cols):
                    content_rules.write_empty_unlocked(self.sheet, current_row, self.data_range.first_col + j, row_format)
            # emit assumption
            if self.content["assumption"]:

                self.sheet.write(current_row, self.data_range.last_col + 1,
                                     self.content["assumption_properties"]['connector'],
                                     formats['center_bold'])

                for index, col_name in enumerate(self.content["assumption_properties"]['columns']):
                    saveassumptiondata = False
                    if self.content["assumption_data"] is not None:
                        try:
                            assumptiondata = self.content["assumption_data"][i]
                            if isinstance(assumptiondata, list):  # Check to see if it's a list
                                if len(assumptiondata) != 1:  # Check to see if it has the right length
                                    errormsg = 'WARNING, assumption "%s" appears to have the wrong length:\n%s' % (
                                        self.content["name"], assumptiondata)
                                    print(errormsg)
                                    saveassumptiondata = False
                                else:  # It has length 1, it's good to go
                                    assumptiondata = assumptiondata[0]  # Just pull out the only element
                            content_rules.write_unlocked(self.sheet, current_row, self.data_range.last_col + 2 + index,
                                                   assumptiondata, row_format)
                            saveassumptiondata = True
                        except Exception as E:
                            errormsg = 'WARNING, failed to save assumption "%s" with data:\n%s\nError message:\n (%s)' % (
                                self.content["name"], assumptiondata, repr(E))
                            print(errormsg)
                            saveassumptiondata = False
                            raise E
                    if not saveassumptiondata:
                        content_rules.write_empty_unlocked(self.sheet, current_row, self.data_range.last_col + 2 + index,
                                                     row_format)
            current_row += 1
            if num_levels > 1 and ((i + 1) % num_levels) == 0:  # shift between the blocks
                current_row += 1
        # done! return the new current_row plus spacing
        return current_row + TitledRange.ROW_INTERVAL  # for spacing

    def param_refs(self, column_number=0):
        return self.data_range.param_refs(self.sheet.get_name(), column_number)



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

