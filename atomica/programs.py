"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

Version: 2018jul30
"""

import sciris as sc
from .system import AtomicaException, logger
from .utils import NamedItem
from numpy import array, exp, ones, prod, minimum, inf
from .structure import TimeSeries
from .excel import standard_formats, AtomicaSpreadsheet, apply_widths, update_widths, read_tables, TimeDependentValuesEntry
from xlsxwriter.utility import xl_rowcol_to_cell as xlrc
import openpyxl
import xlsxwriter as xw
import io

class ProgramInstructions(object):
    def __init__(self,alloc=None,start_year=None,stop_year=None):
        """ Set up a structure that stores instructions for a model on how to use programs. """
        self.start_year = start_year if start_year else 2018.
        self.stop_year = stop_year if stop_year else inf

        # Alloc should be a dict keyed by program name
        # The entries can either be a scalar number, assumed to be spending in the start year, or
        # a TimeSeries object. The alloc is converted to TimeSeries if provided as a scalar
        assert alloc is None or isinstance(alloc,dict), 'Allocation must be a dict keyed by program name, or None'
        self.alloc = dict()
        if alloc:
            for prog_name,spending in alloc.items():
                if isinstance(spending,TimeSeries):
                    self.alloc[prog_name] = sc.dcp(spending)
                else:
                    # Assume it is just a single number
                    self.alloc[prog_name] = TimeSeries(t=self.start_year,vals=spending)

#--------------------------------------------------------------------
# ProgramSet class
#--------------------------------------------------------------------

class ProgramSet(NamedItem):

    def __init__(self, name="default",tvec=None):
        """ Class to hold all programs and programmatic effects. """
        NamedItem.__init__(self,name)

        self.tvec = tvec # This is the data tvec that will be used when writing the progset to a spreadsheet

        # Programs and effects
        self.programs   = sc.odict() # Stores the information on the 'targeting' and 'spending data' sheet
        self.covouts    = sc.odict() # Stores the information on the 'program effects' sheet

        # Populations, parameters, and compartments - these are all the available ones printed when writing a progbook
        self.pops       = sc.odict()
        self.comps      = sc.odict()
        self.pars       = sc.odict()

        # Meta data
        self.created    = sc.now()
        self.modified   = sc.now()

        return None

    def prepare_cache(self):
        # This function is called once at the start of model.py, which allows various checks to be
        # performed once at the start of the simulation rather than at every timestep
        # TODO - deprecate fully if this ends up being unused (it used to do something)
        return

    def __repr__(self):
        ''' Print out useful information'''
        output = sc.prepr(self)
        output += '    Program set name: %s\n'    % self.name
        output += '            Programs: %s\n'    % [prog for prog in self.programs]
        output += '        Date created: %s\n'    % sc.getdate(self.created)
        output += '       Date modified: %s\n'    % sc.getdate(self.modified)
        output += '============================================================\n'

        return output

    #######################################################################################################
    # Methods to add/remove things
    #######################################################################################################

    def get_code_name(self,name):
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
        prog = Program(name=code_name,label=full_name)
        self.programs[prog.name] = prog
        return

    def remove_program(self, name):
        # Remove the program from the progs dict
        code_name = self.get_code_name(name)

        del self.programs[code_name]
        # Remove affected covouts
        for par in self.pars:
            for pop in self.pops:
                if (par,pop) in self.covouts and code_name in self.covouts.progs:
                    del self.covouts[(par,pop)].progs[code_name]
        return

    def add_pop(self,code_name,full_name):
        self.pops[code_name] = full_name
        return

    def remove_pop(self,name):
        # To remove a pop, we need to remove it from all programs, and also remove all affected covouts
        code_name = self.get_code_name(name)
        for prog in self.programs.values():
            if code_name in prog.target_pops:
                prog.target_pops.remove(code_name)
            if (prog.name,code_name) in self.covouts:
                self.covouts.pop((prog.name,code_name))

        del self.pops[code_name]
        return

    def add_comp(self,code_name,full_name):
        self.comps[code_name] = full_name
        return

    def remove_comp(self,name):
        # If we remove a compartment, we need to remove it from every population
        code_name = self.get_code_name(name)
        for prog in self.programs.values():
            if code_name in prog.target_comps:
                prog.target_comps.remove(code_name)
        del self.comps[code_name]
        return

    def add_par(self,code_name,full_name):
        # add an impact parameter
        # a new impact parameter won't have any covouts associated with it, and no programs will be bound to it
        # So all we have to do is add it to the list
        self.pars[code_name] = full_name
        return

    def remove_par(self,name):
        # remove an impact parameter
        # we need to remove all of the covouts that affect it
        code_name = self.get_code_name(name)
        for pop in self.pops:
            if (code_name,pop) in self.covouts:
                del self.covouts[(code_name,pop)]
        del self.pars[code_name]
        return

    #######################################################################################################
    # Methods for data I/O
    #######################################################################################################

    def _set_available(self,framework,data):
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
        for name, label, is_impact in zip(framework.pars.index, framework.pars['display name'],framework.pars['is impact']):
            if is_impact == 'y':
                self.pars[name] = label

    @staticmethod
    def from_spreadsheet(spreadsheet=None, framework=None, data=None, project=None):
        '''Make a program set by loading in a spreadsheet.'''

        # Check framework/data requirements - people can EITHER provide:
        #  - a data and framework
        #  - a project containing data and a framework
        # Try to get them from the data/framework
        if data is None or framework is None:
            if project is None:
                errormsg = 'To read in a ProgramSet, please supply one of the following sets of inputs: (a) a Framework and a ProjectData, (b) a Project.'
                raise AtomicaException(errormsg)
            else:
                data = project.data
                framework = project.framework

        # Populate the available pops, comps, and pars based on the framework and data provided at this step
        self = ProgramSet()
        self._set_available(framework,data)

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

    def save(self,fname):
        # Shortcut for saving to disk - FE RPC will probably use `to_spreadsheet()` but BE users will probably use `save()`
        ss = self.to_spreadsheet()
        ss.save(fname)

    def _read_targeting(self,sheet):
        # This function reads a targeting sheet and instantiates all of the programs with appropriate targets, putting them
        # into `self.programs`
        tables, start_rows = read_tables(sheet) # NB. only the first table will be read, so there can be other tables for comments on the first page
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
        pop_idx = dict() # Map table index to pop full name
        for i in range(pop_start_idx,comp_start_idx):
            if headers[i]:
                pop_idx[i] = headers[i]

        comp_idx = dict() # Map table index to comp full name
        for i in range(comp_start_idx, len(headers)):
            if headers[i]:
                comp_idx[i] = headers[i]

        pop_codenames = {v.lower().strip():x for x,v in self.pops.items()}
        comp_codenames = {v.lower().strip():x for x,v in self.comps.items()}

        for row in tables[0][2:]: # For each program to instantiate
            target_pops = []
            target_comps = []

            for i in range(pop_start_idx, comp_start_idx):
                if row[i].value and sc.isstring(row[i].value) and row[i].value.lower().strip() == 'y':
                    target_pops.append(pop_codenames[pop_idx[i]]) # Append the pop's codename

            for i in range(comp_start_idx, len(headers)):
                if row[i].value and sc.isstring(row[i].value) and row[i].value.lower().strip() == 'y':
                    target_comps.append(comp_codenames[comp_idx[i]])  # Append the pop's codename

            short_name = row[0].value.strip()
            if short_name.lower() == 'all':
                raise AtomicaException('A program was named "all", which is a reserved keyword and cannot be used as a program name')
            long_name = row[1].value.strip()

            self.programs[short_name] = Program(name=short_name,label=long_name,target_pops=target_pops,target_comps=target_comps)

    def _write_targeting(self):
        sheet = self._book.add_worksheet("Program targeting")
        widths = dict()

        # Work out the column offset associated with each population label and comp label
        pop_block_offset = 2 # This is the co
        sheet.write(0, pop_block_offset, "Targeted to (populations)", self._formats['rc_title']['left']['F'])
        comp_block_offset = 2+len(self.pops)+1
        sheet.write(0, comp_block_offset, "Targeted to (compartments)", self._formats['rc_title']['left']['F'])

        pop_col = {n:i+pop_block_offset for i,n in enumerate(self.pops.keys())}
        comp_col = {n:i+comp_block_offset for i,n in enumerate(self.comps.keys())}

        # Write the header row
        sheet.write(1, 0, 'Abbreviation', self._formats["center_bold"])
        update_widths(widths,0,'Abbreviation')
        sheet.write(1, 1, 'Display name', self._formats["center_bold"])
        update_widths(widths,1,'Abbreviation')
        for pop,full_name in self.pops.items():
            col = pop_col[pop]
            sheet.write(1, col, full_name, self._formats['rc_title']['left']['T'])
            self._references[full_name] = "='%s'!%s" % (sheet.name,xlrc(1,col,True,True))
            widths[col] = 12 # Wrap population names

        for comp,full_name in self.comps.items():
            col = comp_col[comp]
            sheet.write(1, col, full_name, self._formats['rc_title']['left']['T'])
            self._references[full_name] = "='%s'!%s" % (sheet.name,xlrc(1, col,True,True))
            widths[col] = 12 # Wrap compartment names

        row = 2
        self._references['reach_pop'] = dict() # This is storing cells e.g. self._references['reach_pop'][('BCG','0-4')]='$A$4' so that conditional formatting can be done
        for prog in self.programs.values():
            sheet.write(row, 0, prog.name)
            self._references[prog.name] = "='%s'!%s" % (sheet.name,xlrc(row, 0,True,True))
            update_widths(widths, 0, prog.name)
            sheet.write(row, 1, prog.label)
            self._references[prog.label] = "='%s'!%s" % (sheet.name,xlrc(row, 1,True,True))
            update_widths(widths, 1, prog.label)

            for pop in self.pops:
                col = pop_col[pop]
                if pop in prog.target_pops:
                    sheet.write(row,col, 'Y', self._formats["center"])
                else:
                    sheet.write(row,col, 'N', self._formats["center"])
                self._references['reach_pop'][(prog.name,pop)] = "'%s'!%s" % (sheet.name,xlrc(row,col,True,True))
                sheet.data_validation(xlrc(row, col), {"validate": "list", "source": ["Y", "N"]})
                sheet.conditional_format(xlrc(row, col), {'type': 'cell', 'criteria': 'equal to', 'value': '"Y"', 'format': self._formats['unlocked_boolean_true']})
                # sheet.conditional_format(xlrc(row, col), {'type': 'cell', 'criteria': 'equal to', 'value': '"N"', 'format': self._formats['unlocked_boolean_false']})

            for comp in self.comps:
                col = comp_col[comp]
                if comp in prog.target_comps:
                    sheet.write(row,col, 'Y', self._formats["center"])
                else:
                    sheet.write(row,col, 'N', self._formats["center"])
                sheet.data_validation(xlrc(row, col), {"validate": "list", "source": ["Y", "N"]})
                sheet.conditional_format(xlrc(row, col), {'type': 'cell', 'criteria': 'equal to', 'value': '"Y"', 'format': self._formats['unlocked_boolean_true']})
                # sheet.conditional_format(xlrc(row, col), {'type': 'cell', 'criteria': 'equal to', 'value': '"N"', 'format': self._formats['unlocked_boolean_false']})

            row += 1

        apply_widths(sheet,widths)

    def _read_spending(self,sheet):
        # Read the spending table and populate the program data
        tables, start_rows = read_tables(sheet)
        times = set()
        for table in tables:
            tdve = TimeDependentValuesEntry.from_rows(table)
            prog = self.programs[tdve.name]
            prog.spend_data = tdve.ts['Total spend']
            prog.capacity = tdve.ts['Capacity constraints']
            prog.unit_cost = tdve.ts['Unit cost']
            prog.coverage = tdve.ts['Coverage']
            times.update(set(tdve.tvec))
        self.tvec = array(sorted(list(times)))

    def _write_spending(self):
        sheet = self._book.add_worksheet("Spending data")
        widths = dict()
        next_row = 0


        for prog in self.programs.values():
            # Make a TDVE table for
            tdve = TimeDependentValuesEntry(prog.name,self.tvec)
            prog = self.programs[tdve.name]
            tdve.ts['Total spend'] = prog.spend_data
            tdve.ts['Capacity constraints'] = prog.capacity
            tdve.ts['Unit cost'] = prog.unit_cost
            tdve.ts['Coverage'] = prog.coverage

            # NOTE - If the ts contains time values that aren't in the ProgramSet's tvec, then an error will be thrown
            # However, if the ProgramSet's tvec contains values that the ts does not, then that's fine, there
            # will just be an empty cell in the spreadsheet
            next_row = tdve.write(sheet, next_row, self._formats, self._references, widths,assumption_heading='Assumption',write_units=False,write_uncertainty=True)

        apply_widths(sheet,widths)

    def _read_effects(self,sheet):
        # Read the program effects sheet. Here we instantiate a costcov object for every non-empty row

        tables, start_rows = read_tables(sheet)
        pop_codenames = {v.lower().strip():x for x,v in self.pops.items()}
        par_codenames = {v.lower().strip():x for x,v in self.pars.items()}

        self.covouts = sc.odict()

        for table in tables:
            par_name = par_codenames[table[0][0].value.strip().lower()] # Code name of the parameter we are working with
            headers = [x.value.strip() if sc.isstring(x.value) else x.value for x in table[0]]
            idx_to_header = {i:h for i,h in enumerate(headers)} # Map index to header

            for row in table[1:]:
                # For each covout row, we will initialize
                pop_name = pop_codenames[row[0].value.lower().strip()] # Code name of the population we are working on
                progs = sc.odict()

                baseline = None
                cov_interaction = None
                imp_interaction = None
                uncertainty = None

                for i,x in enumerate(row[1:]):
                    i = i+1 # Offset of 1 because the loop is over row[1:] not row[0:]

                    if idx_to_header[i] is None: # If the header row had a blank cell, ignore everything in that column - we don't know what it is otherwise
                        continue
                    elif idx_to_header[i].lower() == 'baseline value':
                        if x.value is not None: # test `is not None` because it might be entered as 0
                            baseline = float(x.value)
                    elif idx_to_header[i].lower() == 'coverage interaction':
                        if x.value:
                            cov_interaction =  x.value.strip().lower() # additive, nested, etc.
                    elif idx_to_header[i].lower() == 'impact interaction':
                        if x.value:
                            imp_interaction =  x.value.strip().lower() # additive, nested, etc.
                    elif idx_to_header[i].lower() == 'uncertainty':
                        if x.value is not None: # test `is not None` because it might be entered as 0
                            uncertainty = float(x.value)
                    elif x.value is not None: # If the header isn't empty, then it should be one of the program names
                        if idx_to_header[i] not in self.programs:
                            raise AtomicaException('The heading "%s" was not recognized as a program name or a special token - spelling error?' % (idx_to_header[i]))
                        progs[idx_to_header[i]] = float(x.value)

                if baseline is not None or progs: # Only instantiate covout objects if they have programs associated with them
                    self.covouts[(par_name,pop_name)] = Covout(par=par_name,pop=pop_name,cov_interaction= cov_interaction, imp_interaction = imp_interaction, uncertainty=uncertainty,baseline=baseline,progs=progs)

    def _write_effects(self):
        # TODO - Use the framework to exclude irrelevant programs and populations
        sheet = self._book.add_worksheet("Program effects")
        widths = dict()

        current_row = 0

        for par_name,par_label in self.pars.items():
            sheet.write(current_row, 0, par_label, self._formats['rc_title']['left']['F'])
            update_widths(widths,0,par_label)

            for i,s in enumerate(['Baseline value','Coverage interaction','Impact interaction','Uncertainty']):
                sheet.write(current_row, 1+i, s, self._formats['rc_title']['left']['T'])
                widths[1+i] = 12 # Fixed width, wrapping
            sheet.write_comment(xlrc(current_row,1), 'In this column, enter the baseline value for "%s" if none of the programs reach this parameter (e.g., if the coverage is 0)' % (par_label))

            applicable_progs = self.programs.values() # All programs - could filter this later on
            prog_col = {p.name:i+6 for i,p in enumerate(applicable_progs)} # add any extra padding columns to the indices here too

            for prog in applicable_progs:
                sheet.write_formula(current_row, prog_col[prog.name], self._references[prog.name], self._formats['center_bold'],value=prog.name)
                update_widths(widths, prog_col[prog.name], prog.name)
            current_row += 1

            applicable_covouts = {x.pop:x for x in self.covouts.values() if x.par == par_name}
            applicable_pops = self.pops.keys() # All pops - could filter these (by both program coverage and covouts)

            for pop_name in applicable_pops:

                if pop_name not in applicable_covouts: # There is currently no covout
                    covout = None
                else:
                    covout = applicable_covouts[pop_name]

                sheet.write_formula(current_row, 0, self._references[self.pops[pop_name]],value=self.pops[pop_name])
                update_widths(widths, 0, self.pops[pop_name])

                if covout and covout.baseline is not None:
                    sheet.write(current_row, 1, covout.baseline,self._formats['not_required'])
                else:
                    sheet.write(current_row, 1, None, self._formats['unlocked'])

                if covout and covout.cov_interaction is not None:
                    sheet.write(current_row, 2, covout.cov_interaction,self._formats['not_required'])
                else:
                    sheet.write(current_row, 2, None, self._formats['unlocked'])
                sheet.data_validation(xlrc(current_row, 2), {"validate": "list", "source": ["Random","Additive","Nested"]})

                if covout and covout.imp_interaction is not None:
                    sheet.write(current_row, 3, covout.imp_interaction,self._formats['not_required'])
                else:
                    sheet.write(current_row, 3, None, self._formats['unlocked'])
                sheet.data_validation(xlrc(current_row, 3), {"validate": "list", "source": ["Synergistic","Best"]})

                if covout and covout.sigma is not None:
                    sheet.write(current_row, 4, covout.sigma,self._formats['not_required'])
                else:
                    sheet.write(current_row, 4, None, self._formats['unlocked'])

                for prog in applicable_progs:
                    if covout and prog.name in covout.progs:
                        sheet.write(current_row, prog_col[prog.name], covout.progs[prog.name],self._formats['not_required'])
                    else:
                        sheet.write(current_row, prog_col[prog.name], None,self._formats['unlocked'])

                    fcn_pop_not_reached = '%s<>"Y"' % (self._references['reach_pop'][(prog.name, pop_name)])  # Excel formula returns FALSE if pop was 'N' (or blank)
                    sheet.conditional_format(xlrc(current_row, prog_col[prog.name]), {'type': 'formula', 'criteria': '=AND(%s,NOT(ISBLANK(%s)))' % (fcn_pop_not_reached, xlrc(current_row, prog_col[prog.name])), 'format': self._formats['ignored_warning']})
                    sheet.conditional_format(xlrc(current_row, prog_col[prog.name]), {'type': 'formula', 'criteria':  '=' + fcn_pop_not_reached, 'format': self._formats['ignored_not_required']})

                current_row += 1

            current_row += 1

        apply_widths(sheet,widths)

    @staticmethod
    def new(name=None, tvec=None, progs=None, project=None, framework=None, data=None,pops=None, comps=None, pars=None):
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
        #       - A list of pop full names (these will need to match a databook when the progset is read in)
        # - comps : manually specify the compartments. Can be
        #       - A number of comps
        #       - A list of comp full names (needs to match framework when the progset is read in)
        # - pars : manually specify the impact parameters. Can be
        #       - A number of pars
        #       - A list of parameter full names (needs to match framework when the progset is read in)

        assert tvec is not None, 'You must specify the time points where data will be entered'
        # Prepare programs
        if sc.isnumber(progs):
            nprogs = progs
            progs = sc.odict()
            for p in range(nprogs):
                progs['Prog %i' % (p+1)] = 'Program %i' % (p+1)
        elif isinstance(progs,dict): # will also match odict
            pass
        else: 
            errormsg = 'Please just supply a number of programs, not "%s"' % (type(progs))
            raise AtomicaException(errormsg)

        # First, assign the data and framework
        if framework is None and project:
            framework = project.framework
        if data is None and project:
            data = project.data

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
            assert isinstance(pops,dict) # Needs dict input

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
            assert isinstance(comps,dict) # Needs dict input

        # Assign the comps
        if pars is None:
            # Get pars from framework
            pars = sc.odict()
            for _, spec in framework.pars.iterrows():
                if spec['is impact'] == 'y':
                    pars[spec.name] = spec['display name']
        elif sc.isnumber(pars):
            npars = pars
            pars = sc.odict()  # Create real compartments list
            for p in range(npars):
                pars['Par %i' % (p + 1)] = 'Parameter %i' % (p + 1)
        else:
            assert isinstance(pars, dict)  # Needs dict input

        newps = ProgramSet(name,tvec)
        [newps.add_comp(k,v) for k,v in comps.items()]
        [newps.add_par(k,v) for k,v in pars.items()]
        [newps.add_pop(k,v) for k,v in pops.items()]
        [newps.add_program(k,v) for k,v in progs.items()]
        return newps

    def validate(self):
        # Some basic validation checks
        for prog in self.programs.values():
            if not prog.target_comps:
                raise AtomicaException('Program "%s" does not target any compartments' % (prog.name))
            if not prog.target_pops:
                raise AtomicaException('Program "%s" does not target any populations' % (prog.name))

    #######################################################################################################
    # Methods for getting core response summaries: budget, allocations, coverages, outcomes, etc
    #######################################################################################################        
    def get_alloc(self,instructions=None,tvec=None):
        # Get time-varying alloc for each program
        # Input
        # - instructions : program instructions
        # - t : np.array vector of time values (years)
        #
        # Returns a dict where the key is the program name and
        # the value is an array of spending values the same size as t
        # Spending will be drawn from the instructions if it exists. The `instructions.alloc`
        # can either be:
        # - None
        # - A dict in which a program may or may not appear
        # - A dict in which a program appears and has a TimeSeries of spending but has no associated data
        #
        # Validate inputs
        if tvec is None:
            tvec = instructions.start_year
        tvec = sc.promotetoarray(tvec)

        if instructions is None: # If no instructions provided, just return the default budget
            return self.get_budgets(year=tvec)
        else:
            if instructions.alloc is None:
                return self.get_budgets(year=tvec)
            else: 
                alloc = sc.odict()
                for prog in self.programs.values():
                    if prog.name in instructions.alloc:
                        alloc[prog.name] = instructions.alloc[prog.name].interpolate(tvec)
                    else:
                        alloc[prog.name] = prog.get_spend(tvec)
                return alloc

    def get_budgets(self, year=None, optimizable=None):
        ''' Extract the budget if cost data has been provided; if optimizable is True, then only return optimizable programs '''
        
        default_budget = sc.odict() # Initialise outputs

        # Validate inputs
        if year is not None: year = sc.promotetoarray(year)
        if optimizable is None: optimizable = False # Return only optimizable indices

        # Get cost data for each program 
        for prog in self.programs.values():
            default_budget[prog.name] = prog.get_spend(year)

        return default_budget

    def get_num_covered(self, year=None, alloc=None):
        ''' Extract the number of people covered by a program, optionally specifying an overwrite for the alloc '''
        
        num_covered = sc.odict() # Initialise outputs

        # Validate inputs
        if year is not None: year = sc.promotetoarray(year)

        # Get cost data for each program 
        for prog in self.programs.values():
            if alloc and prog.name in alloc:
                spending = alloc[prog.name]
            else:
                spending = None

            num_covered[prog.name] = prog.get_num_covered(year=year, budget=spending)

        return num_covered

    def get_prop_covered(self, year=None, denominator=None, unit_cost=None, capacity=None, alloc=None, sample='best'):
        '''Returns proportion covered for a time/spending vector and denominator.
        Denominator is expected to be a dictionary.'''
        # INPUT
        # denominator - dict of denominator values keyed by program name
        # alloc - dict of spending values (arrays) keyed by program name (same thing returned by self.get_alloc)
        prop_covered = sc.odict() # Initialise outputs

        # Make sure that denominator has been supplied
        if denominator is None:
            errormsg = 'Must provide denominators to calculate proportion covered.'
            raise AtomicaException(errormsg)
            
        for prog in self.programs.values():
            if alloc and prog.name in alloc:
                spending = alloc[prog.name]
            else:
                spending = None

            num = prog.get_num_covered(year=year, unit_cost=unit_cost, capacity=capacity, budget=spending, sample=sample)
            denom = denominator[prog.name]            
            prop_covered[prog.name] = minimum(num/denom, 1.) # Ensure that coverage doesn't go above 1
            
        return prop_covered

    def get_coverage(self, year=None, denominator=None, unit_cost=None, capacity=None, alloc=None, sample='best'):
        '''Returns proportion OR number covered for a time/spending vector. Returns proportion if denominator is provided'''
        if denominator is not None:
            return self.get_prop_covered(year=year, denominator=denominator, unit_cost=unit_cost, capacity=capacity, alloc=alloc, sample=sample)
        else:
            return self.get_num_covered(year=year, unit_cost=unit_cost, capacity=capacity, alloc=alloc, sample=sample)

    def get_outcomes(self, coverage):
        ''' Get a dictionary of parameter values associated with coverage levels'''
        # TODO - add sampling back in once we've decided how to do it
        # INPUTS
        # - coverage : dict with coverage values {prog_name:np.array}
        # OUTPUTS
        # - outcomes : a dict {(par,pop):vals}

        for covkey in coverage.keys(): # Ensure coverage level values are arrays
            coverage[covkey] = sc.promotetoarray(coverage[covkey])
            for item in coverage[covkey]:
                if item<0 or item>1:
                    errormsg = 'Expecting coverage to be a proportion, value for entry %s is %s' % (covkey, item)
                    raise AtomicaException(errormsg)

        # Initialise output
        outcomes = dict()
        for covout in self.covouts.values():
            outcomes[(covout.par,covout.pop)] = covout.get_outcome(coverage)
        return outcomes

#--------------------------------------------------------------------
# Program class
#--------------------------------------------------------------------
class Program(NamedItem):
    ''' Defines a single program.'''

    def __init__(self, name=None, label=None, target_pops=None, target_pars=None, target_comps=None):
        '''Initialize'''
        NamedItem.__init__(self,name)
        assert name is not None, 'You must supply a name for a program'
        self.name               = name # Short name of program
        self.label              = name if label is None else label # Full name of the program
        self.target_pars        = [] if target_pars is None else target_pars # Dict of parameters targeted by program, in form {'param': par.short, 'pop': pop} # TODO - remove this, this info is in the Covout
        self.target_pops        = [] if target_pops is None else target_pops # List of populations targeted by the program
        self.target_comps       = [] if target_comps is None else target_comps # Compartments targeted by the program - used for calculating coverage denominators
        self.baseline_spend     = TimeSeries(assumption=0.0) # A TimeSeries with any baseline spending data - currently not exposed in progbook
        self.spend_data         = TimeSeries() # TimeSeries with spending data
        self.unit_cost          = TimeSeries() # TimeSeries with unit cost of program
        self.capacity           = TimeSeries() # TimeSeries with capacity of program - optional - if not supplied, cost function is assumed to be linear
        self.coverage           = TimeSeries() # TimeSeries with capacity of program - optional - if not supplied, cost function is assumed to be linear
        return None

    def __repr__(self):
        ''' Print out useful info'''
        output = sc.prepr(self)
        output += '          Program name: %s\n'    % self.short
        output += '         Program label: %s\n'    % self.label
        output += '  Targeted populations: %s\n'    % self.target_pops
        output += '   Targeted parameters: %s\n'    % self.target_pars
        output += ' Targeted compartments: %s\n'    % self.target_comps
        output += '\n'
        return output

    def get_spend(self, year=None, total=False):
        ''' Convenience function for getting spending data'''
        if total:
            return self.spend_data.interpolate(year) + self.baseline_spend.interpolate(year)
        else:
            return self.spend_data.interpolate(year)

    def get_unit_cost(self, year=None):
        return self.unit_cost.interpolate(year)

    def optimizable(self, doprint=False, partial=False):
        '''
        Return whether or not a program can be optimized.
        
        Arguments:
            doprint = whether or not to print out why a program can't be optimized
            partial = flag programs that are only partially ready for optimization (some data entered), skipping those that have no data entered
        '''
        valid = True # Assume the best
        tests = {}
        try:
            tests['target_pops invalid'] = len(self.target_pops)<1
            tests['target_pars invalid'] = len(self.target_pars)<1
            tests['unit_cost invalid']   = not(sc.isnumber(self.get_unit_cost()))
            tests['capacity invalid']   = self.capacity is None
            if any(tests.values()):
                valid = False # It's looking like it can't be optimized
                if partial and all(tests.values()): valid = True # ...but it's probably just an other program, so skip it
                if not valid and doprint:
                    print('Program not optimizable for the following reasons: %s' % '\n'.join([key for key,val in tests.items() if val]))
                
        except Exception as E:
            valid = False
            if doprint:
                print('Program not optimizable because an exception was encountered: %s' % E.message)
        
        return valid

    def has_budget(self):
        return self.spend_data.has_data()

    def get_num_covered(self, year=None, unit_cost=None, capacity=None, budget=None, sample=False):
        '''Returns number covered for a time/spending vector'''
        # TODO - implement sampling - might just be replacing 'interpolate' with 'sample'?

        num_covered = 0.

        # Validate inputs
        if budget is None:
            budget = self.spend_data.interpolate(year)
        budget = sc.promotetoarray(budget)
                
        if unit_cost is None:
            unit_cost = self.unit_cost.interpolate(year)
        unit_cost = sc.promotetoarray(unit_cost)
            
        if capacity is None and self.capacity.has_data:
            capacity = self.capacity.interpolate(year)
            
        # Use a linear cost function if capacity has not been set
        if capacity is not None:
            num_covered = 2*capacity/(1+exp(-2*budget/(capacity*unit_cost)))-capacity
            
        # Use a saturating cost function if capacity has been set
        else:
            num_covered = budget/unit_cost

        return num_covered


    def get_prop_covered(self, year=None, denominator=None, unit_cost=None, capacity=None, budget=None, sample='best'):
        '''Returns proportion covered for a time/spending vector and denominator'''
        
        # Make sure that denominator has been supplied
        if denominator is None:
            errormsg = 'Must provide denominators to calculate proportion covered.'
            raise AtomicaException(errormsg)
            
        # TODO: error checking to ensure that the dimension of year is the same as the dimension of the denominator
        # Example: year = [2015,2016], denominator = [30000,40000]
        num_covered = self.get_num_covered(unit_cost=unit_cost, capacity=capacity, budget=budget, year=year, sample=sample)
        prop_covered = minimum(num_covered/denominator, 1.) # Ensure that coverage doesn't go above 1
        return prop_covered


    def get_coverage(self, year=None, as_proportion=False, denominator=None, unit_cost=None, capacity=None, budget=None, sample='best'):
        '''Returns proportion OR number covered for a time/spending vector.'''
        
        if as_proportion and denominator is None:
            print('Can''t return proportions because denominators not supplied. Returning numbers instead.')
            as_proportion = False
            
        if as_proportion:
            return self.get_prop_covered(year=year, denominator=denominator, unit_cost=unit_cost, capacity=capacity, budget=budget, sample=sample)
        else:
            return self.get_num_covered(year=year, unit_cost=unit_cost, capacity=capacity, budget=budget, sample=sample)


#--------------------------------------------------------------------
# Covout
#--------------------------------------------------------------------
class Covout(object):
    '''
    Coverage-outcome object 

    Example:
    Covout(par='contacts',
           pop='Adults',
           baseline=120,
           progs={'Prog1':[15,10,10], 'Prog2':20}
           )
    '''
    
    def __init__(self, par=None, pop=None, cov_interaction=None, imp_interaction=None, uncertainty=0.0,baseline=None,progs=None):
        logger.debug('Initializing Covout for par=%s, pop=%s, baseline=%s' % (par, pop, baseline))
        self.par = par
        self.pop = pop
        self.cov_interaction = cov_interaction if cov_interaction is not None else 'additive'
        self.imp_interaction = imp_interaction if imp_interaction is not None else 'best'
        self.sigma = uncertainty
        self.baseline = baseline
        self.progs = sc.odict() if progs is None else progs
        assert self.cov_interaction in ['additive','random','nested']
        assert self.imp_interaction in ['best','synergistic']
        return None
    
    def __repr__(self):
        output = sc.prepr(self)
        output  = sc.indent('   Parameter: ', self.par)
        output += sc.indent('  Population: ', self.pop)
        output += sc.indent('Baseline val: ', self.baseline)
        output += sc.indent('    Programs: ', ', '.join(['%s: %s' % (key,val) for key,val in self.progs.items()]))
        output += '\n'
        return output

    def get_outcome(self,coverage):
        # coverage is a dict with {prog_name:coverage} at least containing all of the
        # programs in self.progs.
        # Don't forget that this covout instance is already specific to a (par,pop) combination

        # We have been given the coverage for all programs
        outcome = self.baseline

        # Pre-check for additive calc
        if self.cov_interaction == 'additive':
            total_coverage = 0.0
            for prog in self.progs:
                total_coverage += coverage[prog]
            if total_coverage > 1:
                logger.warning('Coverage of the programs %s, all of which target parameter %s, sums to %s, which is more than 100 per cent, and additive interaction was selected. Resetting to random... ' % (list(self.progs.keys()), [self.par, self.pop], total_coverage))
                self.cov_interaction = 'random'

        # ADDITIVE CALCULATION
        # NB, if there's only one program targeting this parameter, just do simple additive calc
        if self.cov_interaction == 'additive' or len(self.progs) == 1:
            # Outcome += c1*delta_out1 + c2*delta_out2
            for prog,prog_outcome in self.progs.items():
                outcome += coverage[prog] * (prog_outcome - self.baseline)

        # NESTED CALCULATION
        elif self.cov_interaction == 'nested':
            # Outcome += c3*max(delta_out1,delta_out2,delta_out3) + (c2-c3)*max(delta_out1,delta_out2) + (c1 -c2)*delta_out1, where c3<c2<c1.
            cov, delt = [], []
            for prog,prog_outcome in self.progs.items():
                cov.append(coverage[prog])
                delt.append(prog_outcome - self.baseline)
            cov_tuple = sorted(zip(cov, delt))  # A tuple storing the coverage and delta out, ordered by coverage
            for j in range(len(cov_tuple)):  # For each entry in here
                if j == 0:
                    c1 = cov_tuple[j][0]
                else:
                    c1 = cov_tuple[j][0] - cov_tuple[j - 1][0]
                outcome += c1 * max([ct[1] for ct in cov_tuple[j:]])

        # RANDOM CALCULATION
        elif self.cov_interaction == 'random':
            # Outcome += c1(1-c2)* delta_out1 + c2(1-c1)*delta_out2 + c1c2* max(delta_out1,delta_out2)

            cov, delt = [], []
            for prog,prog_outcome in self.progs.items():
                cov.append(coverage[prog])
                delt.append(prog_outcome - self.baseline)

            # Recursion over overlap levels
            def overlap_calc(indexes, target_depth):
                if len(indexes) < target_depth:
                    output = 0.0
                    for j in range(indexes[-1] + 1, len(cov)):
                        output += overlap_calc(indexes + [j], target_depth)
                    return output
                else:
                    output = 1.0
                    for i in range(0,len(cov)):
                        if i in indexes:
                            output *= cov[i]
                        else:
                            output *= (1-cov[i])

                    output *= max([delt[x] for x in indexes], key=abs)
                    return output

            # Iterate over overlap levels
            for i in range(1, len(cov)):  # Iterate over numbers of overlapping programs
                for j in range(0, len(cov)):  # Iterate over the index of the first program in the sum
                    outcome += overlap_calc([j], i)

            # All programs together
            outcome += prod(array(cov), 0) * max([c for c in delt])

        else:
            raise AtomicaException('Unknown reachability type "%s"', self.cov_interaction)

        return outcome
