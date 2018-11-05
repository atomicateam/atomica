"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.


Version: 2018jul30
"""

import sciris as sc
from .system import AtomicaException, logger, reraise_modify
from .utils import NamedItem
from numpy import array, exp, minimum, inf
from .structure import TimeSeries
from .structure import FrameworkSettings as FS
from .excel import standard_formats, AtomicaSpreadsheet, apply_widths, update_widths, read_tables, TimeDependentValuesEntry
from xlsxwriter.utility import xl_rowcol_to_cell as xlrc
import openpyxl
import xlsxwriter as xw
import io
import numpy as np


class ProgramInstructions(object):
    def __init__(self, alloc=None, start_year=None, stop_year=None, coverage=None):
        """ Set up a structure that stores instructions for a model on how to use programs. """
        # Instantiate a new ProgramInstructions instance. ProgramInstructions specify how to use programs
        # - specifically, which years the programs are applied from, and any funding overwrites from the
        # allocations specified in the progbook.
        #
        # INPUTS
        # - alloc : The allocation. It can be
        #           - A dict keyed by program name, containing a scalar spend, or a TimeSeries of spending values. If the spend is
        #             scalar, it will be assigned to the start year
        #           - A ProgramSet instance, in which case an allocation will be assigned by interpolating the ProgramSet's
        #             spending onto the program start year. This is a shortcut to ensure that budget scenarios and optimizations
        #             where spending is specified in future years ramp correctly from the program start year (and not the last year
        #             that data was entered for)
        # - coverage : Overwrites to proportion coverage. It can be
        #           - A dict keyed by program name, containing a scalar coverage or a TimeSeries of coverage values
        #   Note that coverage overwrites have no effect

        self.start_year = start_year if start_year else 2018.
        self.stop_year = stop_year if stop_year else inf

        # Alloc should be a dict keyed by program name
        # The entries can either be a scalar number, assumed to be spending in the start year, or
        # a TimeSeries object. The alloc is converted to TimeSeries if provided as a scalar
        self.alloc = sc.odict()
        if isinstance(alloc, ProgramSet):
            for prog in alloc.programs.values():
                self.alloc[prog.name] = TimeSeries(t=self.start_year, vals=prog.spend_data.interpolate(self.start_year))
        elif alloc:
            for prog_name, spending in alloc.items():
                if isinstance(spending, TimeSeries) and spending.has_data:
                    self.alloc[prog_name] = sc.dcp(spending)
                elif spending is not None:
                    self.alloc[prog_name] = TimeSeries(t=self.start_year, vals=spending)

        self.coverage = sc.odict()  # Dict keyed by program name that stores a time series of coverages
        if coverage:
            for prog_name, cov_values in coverage.items():
                if isinstance(cov_values, TimeSeries):
                    self.coverage[prog_name] = sc.dcp(cov_values)
                else:
                    self.coverage[prog_name] = TimeSeries(t=self.start_year, vals=cov_values)

# --------------------------------------------------------------------
# ProgramSet class
# --------------------------------------------------------------------


class ProgramSet(NamedItem):
    """ Representation of a single program

    A Program object will be instantiated for every program listed on the 'Program Targeting'
    sheet in the program book

    """

    def __init__(self, name="default", tvec=None):
        """

        :param name: Optionally specify the name of the ProgramSet
        :param tvec: Optionally specify the years for data entry

        """

        NamedItem.__init__(self, name)

        self.tvec = tvec  # This is the data tvec that will be used when writing the progset to a spreadsheet

        # Programs and effects
        self.programs = sc.odict()  # Stores the information on the 'targeting' and 'spending data' sheet
        self.covouts = sc.odict()  # Stores the information on the 'program effects' sheet

        # Populations, parameters, and compartments - these are all the available ones printed when writing a progbook
        self.pops = sc.odict()
        self.comps = sc.odict()
        self.pars = sc.odict()

        # Metadata
        self.created = sc.now()
        self.modified = sc.now()
        self.currency = '$'  # The symbol for currency that will be used in the progbook

    def __repr__(self):
        ''' Print out useful information'''
        output = sc.prepr(self)
        output += '    Program set name: %s\n' % self.name
        output += '            Programs: %s\n' % [prog for prog in self.programs]
        output += '        Date created: %s\n' % sc.getdate(self.created)
        output += '       Date modified: %s\n' % sc.getdate(self.modified)
        output += '============================================================\n'
        return output

    #######################################################################################################
    # Methods to add/remove things
    #######################################################################################################

    def get_code_name(self, name):
        # This function returns a code name given either a full name or a code name
        # This allows pops/comps/pars/progs to be removed by full name or code name
        if name in self.pars or name in self.comps or name in self.pops or name in self.programs:
            return name

        for code_name, full_name in self.pops.items():
            if name == full_name:
                return code_name

        for code_name, full_name in self.comps.items():
            if name == full_name:
                return code_name

        for code_name, full_name in self.pars.items():
            if name == full_name:
                return code_name

        for prog in self.programs.values():
            if name == prog.label:
                return prog.name

        raise AtomicaException('Could not find full name for quantity "%s" (n.b. this is case sensitive)' % (name))

    def add_program(self, code_name, full_name):
        # To add a program, we just need to construct one
        prog = Program(name=code_name, label=full_name, currency=self.currency)
        self.programs[prog.name] = prog
        return

    def remove_program(self, name):
        # Remove the program from the progs dict
        code_name = self.get_code_name(name)

        del self.programs[code_name]
        # Remove affected covouts
        for par in self.pars:
            for pop in self.pops:
                if (par, pop) in self.covouts and code_name in self.covouts.progs:
                    del self.covouts[(par, pop)].progs[code_name]
        return

    def add_pop(self, code_name, full_name):
        self.pops[code_name] = full_name
        return

    def remove_pop(self, name):
        # To remove a pop, we need to remove it from all programs, and also remove all affected covouts
        code_name = self.get_code_name(name)
        for prog in self.programs.values():
            if code_name in prog.target_pops:
                prog.target_pops.remove(code_name)
            if (prog.name, code_name) in self.covouts:
                self.covouts.pop((prog.name, code_name))

        del self.pops[code_name]
        return

    def add_comp(self, code_name, full_name):
        self.comps[code_name] = full_name
        return

    def remove_comp(self, name):
        # If we remove a compartment, we need to remove it from every population
        code_name = self.get_code_name(name)
        for prog in self.programs.values():
            if code_name in prog.target_comps:
                prog.target_comps.remove(code_name)
        del self.comps[code_name]
        return

    def add_par(self, code_name, full_name):
        # add an impact parameter
        # a new impact parameter won't have any covouts associated with it, and no programs will be bound to it
        # So all we have to do is add it to the list
        self.pars[code_name] = full_name
        return

    def remove_par(self, name):
        # remove an impact parameter
        # we need to remove all of the covouts that affect it
        code_name = self.get_code_name(name)
        for pop in self.pops:
            if (code_name, pop) in self.covouts:
                del self.covouts[(code_name, pop)]
        del self.pars[code_name]
        return

    #######################################################################################################
    # Methods for data I/O
    #######################################################################################################

    def _set_available(self, framework, data):
        # Given framework and data, set the available pops, comps, and pars
        # noting that these are matched to the framework and data even though
        # the programs may not reach all of them. This gets used during both
        # from_spreadsheet() and new()
        self.pops = sc.odict()
        for x, v in data.pops.items():
            self.pops[x] = v['label']

        self.comps = sc.odict()
        for _, spec in framework.comps.iterrows():
            if spec['is source'] == 'y' or spec['is sink'] == 'y' or spec['is junction'] == 'y':
                continue
            else:
                self.comps[spec.name] = spec['display name']

        self.pars = sc.odict()
        for name, label, is_impact in zip(framework.pars.index, framework.pars['display name'], framework.pars['targetable']):
            if is_impact == 'y':
                self.pars[name] = label

    @staticmethod
    def validate_inputs(framework, data, project):
        # To load a spreadsheet or make a new ProgramSet, people can pass in
        # framework, data, and/or a project. If the framework and data are not explicitly specified,
        # they get drawn from the project
        if (framework is None and project is None) or (data is None and project is None):
            errormsg = 'To read in a ProgramSet, please supply one of the following sets of inputs: (a) a Framework and a ProjectData, (b) a Project.'
            raise AtomicaException(errormsg)

        if framework is None:
            if project.framework is None:
                errormsg = 'A Framework was not provided, and the Project has not been initialized with a Framework'
                raise AtomicaException(errormsg)
            else:
                framework = project.framework

        if data is None:
            if project.data is None:
                errormsg = 'Project data has not been loaded yet'
                raise AtomicaException(errormsg)
            else:
                data = project.data

        return framework, data

    @staticmethod
    def from_spreadsheet(spreadsheet=None, framework=None, data=None, project=None):
        '''Make a program set by loading in a spreadsheet.'''

        framework, data = ProgramSet.validate_inputs(framework, data, project)

        # Populate the available pops, comps, and pars based on the framework and data provided at this step
        self = ProgramSet()
        self._set_available(framework, data)

        # Create and load spreadsheet
        if sc.isstring(spreadsheet):
            spreadsheet = AtomicaSpreadsheet(spreadsheet)

        workbook = openpyxl.load_workbook(spreadsheet.get_file(), read_only=True, data_only=True)  # Load in read-only mode for performance, since we don't parse comments etc.

        # Load individual sheets
        self._read_targeting(workbook['Program targeting'])
        self._read_spending(workbook['Spending data'])
        self._read_effects(workbook['Program effects'])

        return self

    def to_spreadsheet(self):
        ''' Write the contents of a program set to a spreadsheet. '''
        f = io.BytesIO()  # Write to this binary stream in memory

        self._book = xw.Workbook(f)
        self._formats = standard_formats(self._book)
        self._references = {}  # Reset the references dict

        self._write_targeting()
        self._write_spending()
        self._write_effects()

        self._book.close()

        # Dump the file content into a ScirisSpreadsheet
        spreadsheet = AtomicaSpreadsheet(f)

        # Clear everything
        f.close()
        self._book = None
        self._formats = None
        self._references = None

        # Return the spreadsheet
        return spreadsheet

    def save(self, filename=None, folder=None):
        # Shortcut for saving to disk - FE RPC will probably use `to_spreadsheet()` but BE users will probably use `save()`
        full_path = sc.makefilepath(filename=filename, folder=folder, default='Programs', ext='xlsx')
        ss = self.to_spreadsheet()
        ss.save(full_path)
        return full_path

    def _read_targeting(self, sheet):
        # This function reads a targeting sheet and instantiates all of the programs with appropriate targets, putting them
        # into `self.programs`
        tables, start_rows = read_tables(sheet)  # NB. only the first table will be read, so there can be other tables for comments on the first page
        self.programs = sc.odict()
        sup_header = [x.value.lower().strip() if sc.isstring(x.value) else x.value for x in tables[0][0]]
        headers = [x.value.lower().strip() if sc.isstring(x.value) else x.value for x in tables[0][1]]

        # Get the indices where the pops and comps start
        pop_start_idx = sup_header.index('targeted to (populations)')
        comp_start_idx = sup_header.index('targeted to (compartments)')

        # Check the first two columns are as expected
        assert headers[0] == 'abbreviation'
        assert headers[1] == 'display name'

        # Now, prepare the pop and comp lookups
        pop_idx = dict()  # Map table index to pop full name
        for i in range(pop_start_idx, comp_start_idx):
            if headers[i]:
                pop_idx[i] = headers[i]

        comp_idx = dict()  # Map table index to comp full name
        for i in range(comp_start_idx, len(headers)):
            if headers[i]:
                comp_idx[i] = headers[i]

        pop_codenames = {v.lower().strip(): x for x, v in self.pops.items()}
        comp_codenames = {v.lower().strip(): x for x, v in self.comps.items()}

        for row in tables[0][2:]:  # For each program to instantiate
            target_pops = []
            target_comps = []

            for i in range(pop_start_idx, comp_start_idx):
                if row[i].value and sc.isstring(row[i].value) and row[i].value.lower().strip() == 'y':
                    if pop_idx[i] not in pop_codenames:
                        message = 'There was a mismatch between the populations in the databook and the populations in the program book'
                        message += '\nThe program book contains population "%s", while the databook contains: %s' % (pop_idx[i], [str(x) for x in pop_codenames.keys()])
                        raise AtomicaException(message)

                    target_pops.append(pop_codenames[pop_idx[i]])  # Append the pop's codename

            for i in range(comp_start_idx, len(headers)):
                if row[i].value and sc.isstring(row[i].value) and row[i].value.lower().strip() == 'y':
                    if comp_idx[i] not in comp_codenames:
                        message = 'There was a mismatch between the compartments in the databook and the compartments in the Framework file'
                        message += '\nThe program book contains compartment "%s", while the Framework contains: %s' % (comp_idx[i], [str(x) for x in comp_codenames.keys()])
                        raise AtomicaException(message)

                    target_comps.append(comp_codenames[comp_idx[i]])  # Append the pop's codename

            short_name = row[0].value.strip()
            if short_name.lower() == 'all':
                raise AtomicaException('A program was named "all", which is a reserved keyword and cannot be used as a program name')
            long_name = row[1].value.strip()

            self.programs[short_name] = Program(name=short_name, label=long_name, target_pops=target_pops, target_comps=target_comps)

    def _write_targeting(self):
        sheet = self._book.add_worksheet("Program targeting")
        widths = dict()

        # Work out the column offset associated with each population label and comp label
        pop_block_offset = 2  # This is the co
        sheet.write(0, pop_block_offset, "Targeted to (populations)", self._formats['rc_title']['left']['F'])
        comp_block_offset = 2 + len(self.pops) + 1
        sheet.write(0, comp_block_offset, "Targeted to (compartments)", self._formats['rc_title']['left']['F'])

        pop_col = {n: i + pop_block_offset for i, n in enumerate(self.pops.keys())}
        comp_col = {n: i + comp_block_offset for i, n in enumerate(self.comps.keys())}

        # Write the header row
        sheet.write(1, 0, 'Abbreviation', self._formats["center_bold"])
        update_widths(widths, 0, 'Abbreviation')
        sheet.write(1, 1, 'Display name', self._formats["center_bold"])
        update_widths(widths, 1, 'Abbreviation')
        for pop, full_name in self.pops.items():
            col = pop_col[pop]
            sheet.write(1, col, full_name, self._formats['rc_title']['left']['T'])
            self._references[full_name] = "='%s'!%s" % (sheet.name, xlrc(1, col, True, True))
            widths[col] = 12  # Wrap population names

        for comp, full_name in self.comps.items():
            col = comp_col[comp]
            sheet.write(1, col, full_name, self._formats['rc_title']['left']['T'])
            self._references[full_name] = "='%s'!%s" % (sheet.name, xlrc(1, col, True, True))
            widths[col] = 12  # Wrap compartment names

        row = 2
        self._references['reach_pop'] = dict()  # This is storing cells e.g. self._references['reach_pop'][('BCG','0-4')]='$A$4' so that conditional formatting can be done
        for prog in self.programs.values():
            sheet.write(row, 0, prog.name)
            self._references[prog.name] = "='%s'!%s" % (sheet.name, xlrc(row, 0, True, True))
            update_widths(widths, 0, prog.name)
            sheet.write(row, 1, prog.label)
            self._references[prog.label] = "='%s'!%s" % (sheet.name, xlrc(row, 1, True, True))
            update_widths(widths, 1, prog.label)

            for pop in self.pops:
                col = pop_col[pop]
                if pop in prog.target_pops:
                    sheet.write(row, col, 'Y', self._formats["center"])
                else:
                    sheet.write(row, col, 'N', self._formats["center"])
                self._references['reach_pop'][(prog.name, pop)] = "'%s'!%s" % (sheet.name, xlrc(row, col, True, True))
                sheet.data_validation(xlrc(row, col), {"validate": "list", "source": ["Y", "N"]})
                sheet.conditional_format(xlrc(row, col), {'type': 'cell', 'criteria': 'equal to', 'value': '"Y"', 'format': self._formats['unlocked_boolean_true']})
                # sheet.conditional_format(xlrc(row, col), {'type': 'cell', 'criteria': 'equal to', 'value': '"N"', 'format': self._formats['unlocked_boolean_false']})

            for comp in self.comps:
                col = comp_col[comp]
                if comp in prog.target_comps:
                    sheet.write(row, col, 'Y', self._formats["center"])
                else:
                    sheet.write(row, col, 'N', self._formats["center"])
                sheet.data_validation(xlrc(row, col), {"validate": "list", "source": ["Y", "N"]})
                sheet.conditional_format(xlrc(row, col), {'type': 'cell', 'criteria': 'equal to', 'value': '"Y"', 'format': self._formats['unlocked_boolean_true']})
                # sheet.conditional_format(xlrc(row, col), {'type': 'cell', 'criteria': 'equal to', 'value': '"N"', 'format': self._formats['unlocked_boolean_false']})

            row += 1

        apply_widths(sheet, widths)

    def _read_spending(self, sheet):
        # Read the spending table and populate the program data
        tables, start_rows = read_tables(sheet)
        times = set()
        for table, start_row in zip(tables, start_rows):
            try:
                tdve = TimeDependentValuesEntry.from_rows(table)
            except Exception as e:
                message = 'Error on sheet "%s" while trying to read a TDVE table starting on row %d -> ' % (sheet.title, start_row)
                reraise_modify(e, message)

            prog = self.programs[tdve.name]

            def set_ts(prog, field_name, ts):
                # Set Program timeseries based on TDVE, handling the case where the TDVE has no units
                if ts.units is None:
                    ts.units = getattr(prog, field_name).units
                setattr(prog, field_name, ts)

            if 'Total spend' in tdve.ts:  # This is a compatibility statement around 19/10/18, progbooks generated during the WB workshop would have 'Total spend'
                set_ts(prog, 'spend_data', tdve.ts['Total spend'])
            else:
                set_ts(prog, 'spend_data', tdve.ts['Annual spend'])

            set_ts(prog, 'capacity', tdve.ts['Capacity'])
            set_ts(prog, 'unit_cost', tdve.ts['Unit cost'])
            set_ts(prog, 'coverage', tdve.ts['Coverage'])
            set_ts(prog, 'saturation', tdve.ts['Saturation'])

            if '/year' in prog.unit_cost.units and '/year' in prog.coverage.units:
                logger.warning('Program %s: Typically if the unit cost is `/year` then the coverage would not be `/year`', prog.label)
            times.update(set(tdve.tvec))

        self.tvec = array(sorted(list(times)))  # NB. This means that the ProgramSet's tvec (used when writing new programs) is based on the last Program to be read in

    def _write_spending(self):
        sheet = self._book.add_worksheet("Spending data")
        widths = dict()
        next_row = 0

        for prog in self.programs.values():
            # Make a TDVE table for
            tdve = TimeDependentValuesEntry(prog.name, self.tvec)
            prog = self.programs[tdve.name]
            tdve.ts['Annual spend'] = prog.spend_data
            tdve.ts['Unit cost'] = prog.unit_cost
            tdve.ts['Capacity'] = prog.capacity
            tdve.ts['Saturation'] = prog.saturation
            tdve.ts['Coverage'] = prog.coverage

            tdve.allowed_units = {
                'Unit cost': [self.currency + '/person (one-off)', self.currency + '/person/year'],
                'Capacity': ['people/year', 'people']
            }

            # NOTE - If the ts contains time values that aren't in the ProgramSet's tvec, then an error will be thrown
            # However, if the ProgramSet's tvec contains values that the ts does not, then that's fine, there
            # will just be an empty cell in the spreadsheet
            next_row = tdve.write(sheet, next_row, self._formats, self._references, widths, assumption_heading='Assumption', write_units=True, write_uncertainty=True)

        apply_widths(sheet, widths)

    def _read_effects(self, sheet):
        # Read the program effects sheet. Here we instantiate a costcov object for every non-empty row

        tables, start_rows = read_tables(sheet)
        pop_codenames = {v.lower().strip(): x for x, v in self.pops.items()}
        par_codenames = {v.lower().strip(): x for x, v in self.pars.items()}

        self.covouts = sc.odict()

        for table in tables:
            par_name = par_codenames[table[0][0].value.strip().lower()]  # Code name of the parameter we are working with
            headers = [x.value.strip() if sc.isstring(x.value) else x.value for x in table[0]]
            idx_to_header = {i: h for i, h in enumerate(headers)}  # Map index to header

            for row in table[1:]:
                # For each covout row, we will initialize
                pop_name = pop_codenames[row[0].value.lower().strip()]  # Code name of the population we are working on
                progs = sc.odict()

                baseline = None
                cov_interaction = None
                imp_interaction = None
                uncertainty = None

                for i, x in enumerate(row[1:]):
                    i = i + 1  # Offset of 1 because the loop is over row[1:] not row[0:]

                    if idx_to_header[i] is None:  # If the header row had a blank cell, ignore everything in that column - we don't know what it is otherwise
                        continue
                    elif idx_to_header[i].lower() == 'baseline value':
                        if x.value is not None:  # test `is not None` because it might be entered as 0
                            baseline = float(x.value)
                    elif idx_to_header[i].lower() == 'coverage interaction':
                        if x.value:
                            cov_interaction = x.value.strip().lower()  # additive, nested, etc.
                    elif idx_to_header[i].lower() == 'impact interaction':
                        if x.value:
                            imp_interaction = x.value.strip()  # additive, nested, etc.
                    elif idx_to_header[i].lower() == 'uncertainty':
                        if x.value is not None:  # test `is not None` because it might be entered as 0
                            uncertainty = float(x.value)
                    elif x.value is not None:  # If the header isn't empty, then it should be one of the program names
                        if idx_to_header[i] not in self.programs:
                            raise AtomicaException('The heading "%s" was not recognized as a program name or a special token - spelling error?' % (idx_to_header[i]))
                        progs[idx_to_header[i]] = float(x.value)

                if baseline is not None or progs:  # Only instantiate covout objects if they have programs associated with them
                    self.covouts[(par_name, pop_name)] = Covout(par=par_name, pop=pop_name, cov_interaction=cov_interaction, imp_interaction=imp_interaction, uncertainty=uncertainty, baseline=baseline, progs=progs)

    def _write_effects(self):
        # TODO - Use the framework to exclude irrelevant programs and populations
        sheet = self._book.add_worksheet("Program effects")
        widths = dict()

        current_row = 0

        for par_name, par_label in self.pars.items():
            sheet.write(current_row, 0, par_label, self._formats['rc_title']['left']['F'])
            update_widths(widths, 0, par_label)

            for i, s in enumerate(['Baseline value', 'Coverage interaction', 'Impact interaction', 'Uncertainty']):
                sheet.write(current_row, 1 + i, s, self._formats['rc_title']['left']['T'])
                widths[1 + i] = 12  # Fixed width, wrapping
            # sheet.write_comment(xlrc(current_row,1), 'In this column, enter the baseline value for "%s" if none of the programs reach this parameter (e.g., if the coverage is 0)' % (par_label))

            applicable_progs = self.programs.values()  # All programs - could filter this later on
            prog_col = {p.name: i + 6 for i, p in enumerate(applicable_progs)}  # add any extra padding columns to the indices here too

            for prog in applicable_progs:
                sheet.write_formula(current_row, prog_col[prog.name], self._references[prog.name], self._formats['center_bold'], value=prog.name)
                update_widths(widths, prog_col[prog.name], prog.name)
            current_row += 1

            applicable_covouts = {x.pop: x for x in self.covouts.values() if x.par == par_name}
            applicable_pops = self.pops.keys()  # All pops - could filter these (by both program coverage and covouts)

            for pop_name in applicable_pops:

                if pop_name not in applicable_covouts:  # There is currently no covout
                    covout = None
                else:
                    covout = applicable_covouts[pop_name]

                sheet.write_formula(current_row, 0, self._references[self.pops[pop_name]], value=self.pops[pop_name])
                update_widths(widths, 0, self.pops[pop_name])

                if covout and covout.baseline is not None:
                    sheet.write(current_row, 1, covout.baseline, self._formats['not_required'])
                else:
                    sheet.write(current_row, 1, None, self._formats['unlocked'])

                if covout and covout.cov_interaction is not None:
                    sheet.write(current_row, 2, covout.cov_interaction.title(), self._formats['not_required'])
                else:
                    sheet.write(current_row, 2, 'Additive', self._formats['unlocked'])
                sheet.data_validation(xlrc(current_row, 2), {"validate": "list", "source": ["Random", "Additive", "Nested"]})

                if covout and covout.imp_interaction is not None:
                    sheet.write(current_row, 3, covout.imp_interaction, self._formats['not_required'])
                else:
                    sheet.write(current_row, 3, None, self._formats['unlocked'])
                sheet.data_validation(xlrc(current_row, 3), {"validate": "list", "source": ["Synergistic", "Best"]})

                if covout and covout.sigma is not None:
                    sheet.write(current_row, 4, covout.sigma, self._formats['not_required'])
                else:
                    sheet.write(current_row, 4, None, self._formats['unlocked'])

                for prog in applicable_progs:
                    if covout and prog.name in covout.progs:
                        sheet.write(current_row, prog_col[prog.name], covout.progs[prog.name], self._formats['not_required'])
                    else:
                        sheet.write(current_row, prog_col[prog.name], None, self._formats['unlocked'])

                    fcn_pop_not_reached = '%s<>"Y"' % (self._references['reach_pop'][(prog.name, pop_name)])  # Excel formula returns FALSE if pop was 'N' (or blank)
                    sheet.conditional_format(xlrc(current_row, prog_col[prog.name]), {'type': 'formula', 'criteria': '=AND(%s,NOT(ISBLANK(%s)))' % (fcn_pop_not_reached, xlrc(current_row, prog_col[prog.name])), 'format': self._formats['ignored_warning']})
                    sheet.conditional_format(xlrc(current_row, prog_col[prog.name]), {'type': 'formula', 'criteria': '=' + fcn_pop_not_reached, 'format': self._formats['ignored_not_required']})

                # Conditional formatting for the impact interaction - hatched out if no single-program outcomes
                fcn_empty_outcomes = 'COUNTIF(%s:%s,"<>" & "")<2' % (xlrc(current_row, 5), xlrc(current_row, 5 + len(applicable_progs)))
                sheet.conditional_format(xlrc(current_row, 3), {'type': 'formula', 'criteria': '=' + fcn_empty_outcomes, 'format': self._formats['ignored']})
                sheet.conditional_format(xlrc(current_row, 3), {'type': 'formula', 'criteria': '=AND(%s,NOT(ISBLANK(%s)))' % (fcn_empty_outcomes, xlrc(current_row, 3)), 'format': self._formats['ignored_warning']})

                current_row += 1

            current_row += 1

        apply_widths(sheet, widths)

    @staticmethod
    def new(name=None, tvec=None, progs=None, project=None, framework=None, data=None, pops=None, comps=None, pars=None):
        ''' Generate a new progset with blank data. '''
        # INPUTS
        # - name : the name for the progset
        # - tvec : an np.array() with the time values to write
        # - progs : This can be
        #       - A number of progs
        #       - An odict of {code_name:display name} programs
        # - project : specify a project to use the project's framework and data to initialize the comps, pars, and pops
        # - framework : specify a framework to use the framework's comps and pars
        # - data : specify a data to use the data's pops
        # - pops : manually specify the populations. Can be
        #       - A number of pops
        #       - A dict of pop {code name:full name} (these will need to match a databook when the progset is read in)
        # - comps : manually specify the compartments. Can be
        #       - A number of comps
        #       - A dict of comp {code name:full name} (needs to match framework when the progset is read in)
        # - pars : manually specify the impact parameters. Can be
        #       - A number of pars
        #       - A dict of parameter {code name:full name} (needs to match framework when the progset is read in)

        assert tvec is not None, 'You must specify the time points where data will be entered'
        # Prepare programs
        if sc.isnumber(progs):
            nprogs = progs
            progs = sc.odict()
            for p in range(nprogs):
                progs['Prog %i' % (p + 1)] = 'Program %i' % (p + 1)
        elif isinstance(progs, dict):  # will also match odict
            pass
        else:
            errormsg = 'Please just supply a number of programs, not "%s"' % (type(progs))
            raise AtomicaException(errormsg)

        framework, data = ProgramSet.validate_inputs(framework, data, project)

        # Assign the pops
        if pops is None:
            # Get populations from data
            pops = sc.odict([(k, v['label']) for k, v in data.pops.iteritems()])
        elif sc.isnumber(pops):
            npops = pops
            pops = sc.odict()  # Create real pops dict
            for p in range(npops):
                pops['Pop %i' % (p + 1)] = 'Population %i' % (p + 1)
        else:
            assert isinstance(pops, dict)  # Needs dict input

        # Assign the comps
        if comps is None:
            # Get comps from framework
            comps = sc.odict()
            for _, spec in framework.comps.iterrows():
                if spec['is source'] == 'y' or spec['is sink'] == 'y' or spec['is junction'] == 'y':
                    continue
                else:
                    comps[spec.name] = spec['display name']
        elif sc.isnumber(comps):
            ncomps = comps
            comps = sc.odict()  # Create real compartments list
            for p in range(ncomps):
                comps['Comp %i' % (p + 1)] = 'Compartment %i' % (p + 1)
        else:
            assert isinstance(comps, dict)  # Needs dict input

        # Assign the comps
        if pars is None:
            # Get pars from framework
            pars = sc.odict()
            for _, spec in framework.pars.iterrows():
                if spec['targetable'] == 'y':
                    pars[spec.name] = spec['display name']
            if not pars:
                logger.warning('No parameters were marked as "Targetable" in the Framework, so there are no program effects')
        elif sc.isnumber(pars):
            npars = pars
            pars = sc.odict()  # Create real compartments list
            for p in range(npars):
                pars['Par %i' % (p + 1)] = 'Parameter %i' % (p + 1)
        else:
            assert isinstance(pars, dict)  # Needs dict input

        newps = ProgramSet(name, tvec)
        [newps.add_comp(k, v) for k, v in comps.items()]
        [newps.add_par(k, v) for k, v in pars.items()]
        [newps.add_pop(k, v) for k, v in pops.items()]
        [newps.add_program(k, v) for k, v in progs.items()]
        return newps

    def validate(self):
        """ Perform basic validation checks

        :raises AtomicaException is anything is invalid
        :return: None
        """
        for prog in self.programs.values():
            if not prog.target_comps:
                raise AtomicaException('Program "%s" does not target any compartments' % (prog.name))
            if not prog.target_pops:
                raise AtomicaException('Program "%s" does not target any populations' % (prog.name))

    #######################################################################################################
    # Methods for getting core response summaries: budget, allocations, coverages, outcomes, etc
    #######################################################################################################

    def get_alloc(self, tvec, instructions=None):
        """ Return the spending allocation for each program

        :param tvec: array of times (in years) - this is required to interpolate time-varying spending values
        :param instructions: optionally specify instructions, which can supply a spending overwrite
        :return: Dict like {prog_name: np.array()} with spending on each program (in units of $/year or currency equivalent)
        """

        tvec = sc.promotetoarray(tvec)

        alloc = sc.odict()
        for prog in self.programs.values():
            if instructions is None or prog.name not in instructions.alloc:
                alloc[prog.name] = prog.get_spend(tvec)
            else:
                alloc[prog.name] = instructions.alloc[prog.name].interpolate(tvec)

        return alloc

    def get_num_coverage(self, tvec, dt, instructions=None, sample=False):
        """ Return the number coverage of each program

        :param tvec: array of times (in years) - this is required to interpolate time-varying unit costs and capacity constraints
        :param dt: scalar timestep size - this is required to adjust spending on incidence-type programs
        :param instructions: optionally specify instructions, which can supply a spending overwrite
        :param sample: TODO implement sampling
        :return: Dict like {prog_name: np.array()} with number of people covered at each timestep (in units of people)
        """

        # Validate inputs
        tvec = sc.promotetoarray(tvec)
        alloc = self.get_alloc(tvec, instructions)

        # Get number covered for each program
        num_coverage = sc.odict()  # Initialise outputs
        for prog in self.programs.values():
            if prog.name in alloc:
                spending = alloc[prog.name]
            else:
                spending = None
            num_coverage[prog.name] = prog.get_num_covered(tvec=tvec, dt=dt, spending=spending, sample=False)

        return num_coverage

    def get_prop_coverage(self, tvec, num_coverage, denominator, instructions=None, sample=False):
        """ Return the fractional coverage of each program

        Note the evaluating the proportion coverage for a ProgramSet is not a straight division because
        - instructions can override the coverage (for coverage scenarios)
        - Programs can contain saturation constraints

        :param tvec: array of times (in years) - this is required to interpolate time-varying saturation values
        :param num_coverage: dict of program coverages, should match the available programs (typically the output of ProgramSet.get_num_coverage()
        :param denominator: dict of number of people covered by each program, computed externally and with one entry for each program
        :param instructions: optionally specify instructions, which can supply a coverage overwrite
        :param sample: TODO implement sampling
        :return: Dict like {prog_name: np.array()} with fractional coverage values (dimensionless)
        """

        prop_coverage = sc.odict()  # Initialise outputs
        for prog in self.programs.values():
            if instructions is None or prog.name not in instructions.coverage:
                prop_coverage[prog.name] = prog.get_prop_covered(tvec, num_coverage[prog.name], denominator[prog.name], sample=sample)
            else:
                prop_coverage[prog.name] = instructions.coverage[prog.name].interpolate(tvec)
        return prop_coverage

    def get_outcomes(self, prop_coverage=None, sample=False):
        """ Get a dictionary of parameter values associated with coverage levels (at a single point in time)

        Since the modality interactions in Covout.get_outcome() assume that the coverage is scalar, this function
        will also only work for scalar coverage. Therefore, the prop coverage would normally come from
        ProgramSet.get_prop_coverage(tvec,...) where tvec was only one year

        :param prop_coverage: dict with coverage values {prog_name:val}
        :param sample: TODO implement sampling
        :return: dict {(par,pop):val} containing parameter value overwrites
        """

        return {(covout.par, covout.pop): covout.get_outcome(prop_coverage, sample=sample) for covout in self.covouts.values()}

# --------------------------------------------------------------------
# Program class
# --------------------------------------------------------------------


class Program(NamedItem):
    """ Representation of a single program

    A Program object will be instantiated for every program listed on the 'Program Targeting'
    sheet in the program book

    """

    def __init__(self, name, label=None, target_pops=None, target_comps=None, currency='$'):
        """
        :param name: Short name of the program
        :param label: Full name of the program
        :param target_pops: List of population code names for pops targeted by the program
        :param target_comps: List of compartment code names for compartments targeted by the program
        :param currency: The currency to use (for display purposes only) - normally this would be set to `ProgramSet.currency` by `ProgramSet.add_program()`
        """

        NamedItem.__init__(self, name)
        self.name = name  # Short name of program
        self.label = name if label is None else label  # Full name of the program
        self.target_pops = [] if target_pops is None else target_pops  # List of populations targeted by the program
        self.target_comps = [] if target_comps is None else target_comps  # Compartments targeted by the program - used for calculating coverage denominators
        self.baseline_spend = TimeSeries(assumption=0.0, units=currency + '/year')  # A TimeSeries with any baseline spending data - currently not exposed in progbook
        self.spend_data = TimeSeries(units=currency + '/year')  # TimeSeries with spending data
        self.unit_cost = TimeSeries(units=currency + '/person (one-off)')  # TimeSeries with unit cost of program
        self.capacity = TimeSeries(units='people/year')  # TimeSeries with capacity of program - optional - if not supplied, cost function is assumed to be linear
        self.saturation = TimeSeries(units=FS.DEFAULT_SYMBOL_INAPPLICABLE)
        self.coverage = TimeSeries(units='people/year')  # TimeSeries with capacity of program - optional - if not supplied, cost function is assumed to be linear

    def __repr__(self):
        ''' Print out useful info'''
        output = sc.prepr(self)
        output += '          Program name: %s\n' % self.name
        output += '         Program label: %s\n' % self.label
        output += '  Targeted populations: %s\n' % self.target_pops
        output += ' Targeted compartments: %s\n' % self.target_comps
        output += '\n'
        return output

    def get_spend(self, year=None, total=False):
        ''' Convenience function for getting spending data'''
        if total:
            return self.spend_data.interpolate(year) + self.baseline_spend.interpolate(year)
        else:
            return self.spend_data.interpolate(year)

    def get_num_covered(self, tvec, spending, dt, sample=False):
        '''Returns number covered for a time/spending vector'''
        # INPUTS
        # - tvec : scalar tvec
        # - dt : timestep (to adjust spending)
        # - num_covered : scalar num covered e.g. from `Prog.get_num_coverage(tvec,dt)`
        # - denominator : scalar denominator (computed from a model object/Result)
        # TODO - implement sampling

        # Validate inputs
        spending = sc.promotetoarray(spending)

        unit_cost = self.unit_cost.interpolate(tvec)
        if '/year' not in self.unit_cost.units:
            # The spending is $/tvec, and the /tvec gets eliminated if the unit cost is also per tvec. If that's not the case, then
            # we need to multiply the spending by the timestep to get the correct units
            spending *= dt

        num_covered = spending / unit_cost

        if self.capacity.has_data:
            capacity = self.capacity.interpolate(tvec)
            if '/year' in self.capacity.units:
                # The capacity constraint is applied to a number of people. If it is /year, then it must be multiplied by the timestep first
                capacity *= dt
            num_covered = np.minimum(capacity, num_covered)

        return num_covered

    def get_prop_covered(self, tvec, num_covered, denominator, sample=False):
        '''Returns proportion covered for a time/spending vector and denominator, taking into account any coverage saturation contained within this program'''
        # INPUTS
        # - tvec : scalar tvec
        # - num_covered : scalar num covered e.g. from `Prog.get_num_coverage(tvec,dt)`
        # - denominator : scalar denominator (computed from a model object/Result)
        # TODO - implement sampling

        tvec = sc.promotetoarray(tvec)
        denominator = sc.promotetoarray(denominator)
        num_covered = sc.promotetoarray(num_covered)

        if self.saturation.has_data:
            # If the denominator is 0, then we need to use the saturation value
            prop_covered = np.divide(num_covered, denominator, out=np.full(num_covered.shape, np.inf), where=denominator != 0)
            saturation = self.saturation.interpolate(tvec)
            prop_covered = 2 * saturation / (1 + exp(-2 * prop_covered / saturation)) - saturation
            prop_covered = minimum(prop_covered, 1.)  # Ensure that coverage doesn't go above 1 (if saturation is < 1)
        else:
            # The division below means that 0/0 is treated as returning 1
            prop_covered = np.divide(num_covered, denominator, out=np.ones_like(num_covered), where=denominator > num_covered)

        return prop_covered

# --------------------------------------------------------------------
# Covout
# --------------------------------------------------------------------


class Covout(object):
    '''
    Coverage-outcome object

    Example:
    Covout(par='contacts',
           pop='Adults',
           baseline=120,
           progs={'Prog1':5, 'Prog2':20}
           )
    '''

    def __init__(self, par, pop, progs, cov_interaction=None, imp_interaction=None, uncertainty=0.0, baseline=0.0):
        # Construct new Covout instance
        # INPUTS
        # - par : string with the code name of the parameter being overwritten
        # - pop : string with the code name of the population being overwritten
        # - progs : a dict containing {prog_name:outcome} with the single program outcomes
        # - cov_interaction: one of 'additive', 'random', 'nested'
        # - imp_interaction : a parsable string like 'Prog1+Prog2=10,Prog2+Prog3=20' with the interaction outcomes
        # - uncertainty : a scalar standard deviation for the outcomes
        # - baseline : the zero coverage baseline value

        if cov_interaction is None:
            cov_interaction = 'additive'
        else:
            assert cov_interaction in ['additive', 'random', 'nested'], 'Coverage interaction must be set to "additive", "random", or "nested"'

        self.par = par
        self.pop = pop
        self.cov_interaction = cov_interaction
        self.imp_interaction = imp_interaction
        self.sigma = uncertainty
        self.baseline = baseline
        self.update_progs(progs)

    def update_progs(self, progs):
        # Call this function with the program outcomes are changed
        # Could be because program outcomes were sampled using sigma?
        # This is important because it also updates the modality interaction outcomes
        # These are otherwise expensive to compute

        # First, sort the program dict by the magnitude of the outcome
        prog_tuple = [(k, v) for k, v in progs.items()]
        prog_tuple = sorted(prog_tuple, key=lambda x: -abs(x[1]))
        self.progs = sc.odict()
        for item in prog_tuple:
            self.progs[item[0]] = item[1]
        self.deltas = np.array([x[1] - self.baseline for x in prog_tuple])  # Internally cache the deltas which are used
        self.n_progs = len(progs)

        # Parse any impact interactions that are present
        self._interactions = dict()
        if self.imp_interaction and not self.imp_interaction.lower() in ['best', 'synergistic']:
            for interaction in self.imp_interaction.split(','):
                combo, val = interaction.split('=')
                combo = frozenset([x.strip() for x in combo.split('+')])
                for x in combo:
                    assert x in self.progs, 'The impact interaction refers to a program "%s" which does not appear in the available programs' % (x)
                self._interactions[combo] = float(val) - self.baseline

        # Precompute the combinations and associated modality interaction outcomes - it's computationally expensive otherwise
        # We need to store it in two forms
        # - An (ordered) vector of outcomes, which is used by additive and random to do the modality interaction in vectorized form
        # - A dict of outcomes, which is used by nested to look up the outcome using a tupled key of program indices
        combination_strings = [bin(x)[2:].rjust(self.n_progs, '0') for x in range(2 ** self.n_progs)]  # ['00','01','10',...]
        self.combinations = np.array([list(int(y) for y in x) for x in combination_strings])
        combination_outcomes = []
        for prog_combination in self.combinations.astype(bool):
            combination_outcomes.append(self.compute_impact_interaction(progs=prog_combination))
        self.combination_outcomes = np.array(combination_outcomes)  # Reshape to column vector, since that's the shape of combination_coverage

    def __repr__(self):
        output = sc.prepr(self)
        output = sc.indent('   Parameter: ', self.par)
        output += sc.indent('  Population: ', self.pop)
        output += sc.indent('Baseline val: ', self.baseline)
        output += sc.indent('    Programs: ', ', '.join(['%s: %s' % (key, val) for key, val in self.progs.items()]))
        output += '\n'
        return output

    def get_outcome(self, prop_covered, sample=False):
        """ Return parameter value given program coverages

        The :py:class:`Covout` object contains a set of programs and outcomes. The :py:meth:`Covout.get_outcome`
        returns the outcome value associated for coverage of each program. Don't forget that any given Covout instance
        is already specific to a (par,pop) combination

        :param prop_covered: A `dict` with {prog_name:coverage} containing at least all of the
                             programs in `self.progs`. Note that `coverage` is expected to be a `np.array`
                             (such that that generated by :py:meth:`ProgramSet.get_prop_coverage`). However,
                             because the modality calculations only work for scalars, only the first entry
                             in the array will be used.
        :param sample: TODO
        :return: A scalar outcome (of type `np.double` or similar i.e. _not_ an array)

        """

        # Put coverages and deltas into array form
        outcome = self.baseline  # Accumulate the outcome by adding the deltas onto this

        if self.n_progs == 0:
            return outcome  # If there are no programs active, return the baseline value immediately
        elif self.n_progs == 1:
            return outcome + prop_covered[self.progs.keys()[0]][0] * self.deltas[0]

        cov = []
        for prog in self.progs.keys():
            cov.append(prop_covered[prog][0])
        cov = np.array(cov)

        # ADDITIVE CALCULATION
        if self.cov_interaction == 'additive':
            # Outcome += c1*delta_out1 + c2*delta_out2

            # If sum(cov)<0 then there will be a divide by zero error. Also, need to divide by max(sum(cov),1) rather than sum(cov)
            # because otherwise, the coverages will be scaled UP to 1. So fastest just to check here
            if np.sum(cov) > 1:
                # Only keep the programs with nonzero coverage
                additive = np.maximum(cov - np.maximum(cov - (1 - (np.cumsum(cov) - cov)), 0), 0)
                remainder = 1 - additive
                random = cov - additive
                # If remainder is 0, then random must also be 0 i.e. it's always 0/0
                # This happens if the best program has coverage of exactly 1.0 which means it's entirely additive but also has no remainder
                random_portion = np.divide(random, remainder, out=np.zeros_like(random), where=remainder != 0)
                additive_portion_coverage = self.combinations * additive
                net_random = self.combinations * random_portion + (self.combinations ^ 1) * (1 - random_portion)
                combination_coverage = np.zeros((net_random.shape[0],))
                for i in range(0, net_random.shape[1]):
                    contribution = np.ones((net_random.shape[0], ))
                    for j in range(0, net_random.shape[1]):
                        if i == j:
                            contribution *= additive_portion_coverage[:, j]
                        else:
                            contribution *= net_random[:, j]
                    combination_coverage += contribution
                outcome += np.sum(combination_coverage * self.combination_outcomes.ravel())
            else:
                outcome += np.sum(cov * self.deltas)

        # NESTED CALCULATION
        elif self.cov_interaction == 'nested':
            # Outcome += c3*max(delta_out1,delta_out2,delta_out3) + (c2-c3)*max(delta_out1,delta_out2) + (c1 -c2)*delta_out1, where c3<c2<c1.
            idx = np.argsort(cov)
            prog_mask = np.full(cov.shape, fill_value=True)
            combination_coverage = np.zeros((self.combinations.shape[0],))

            for i in range(0, len(cov)):
                combination_index = int('0b' + ''.join(['1' if x else '0' for x in prog_mask]), 2)
                if i == 0:
                    combination_coverage[combination_index] = cov[idx[i]]
                else:
                    combination_coverage[combination_index] = cov[idx[i]] - cov[idx[i - 1]]
                prog_mask[idx[i]] = False  # Disable this program at the next iteration

            outcome += np.sum(combination_coverage * self.combination_outcomes.ravel())

        # RANDOM CALCULATION
        elif self.cov_interaction == 'random':
            # Outcome += c1(1-c2)* delta_out1 + c2(1-c1)*delta_out2 + c1c2* max(delta_out1,delta_out2)
            combination_coverage = np.product(self.combinations * cov + (self.combinations ^ 1) * (1 - cov), axis=1)
            outcome += np.sum(combination_coverage.ravel() * self.combination_outcomes.ravel())
        else:
            raise AtomicaException('Unknown reachability type "%s"', self.cov_interaction)

        return outcome

    def compute_impact_interaction(self, progs=None):
        # Takes in boolean array of active programs, which matches the order in
        # self.progs and self.deltas

        if progs is not None and not any(progs):
            return 0.0
        else:
            progs_active = frozenset(np.array(self.progs.keys())[progs])

        if progs_active in self._interactions:
            # If the combination of programs has an explicitly specified outcome, then use it
            return self._interactions[progs_active]
        elif self.imp_interaction is not None and self.imp_interaction.lower() == 'synergistic':
            raise NotImplementedError
        else:
            # Otherwise, do the 'best' interaction and return the delta with the largest magnitude
            tmp = self.deltas[progs]
            idx = np.argmax(abs(tmp))
            return tmp[idx]
