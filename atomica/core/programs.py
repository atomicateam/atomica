"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

Version: 2018jul30
"""

from sciris.core import odict, today, desc, promotetolist, promotetoarray, indent, isnumber, sanitize, dataframe, checktype, dcp
import sciris.core as sc
from .system import AtomicaException, logger
from .utils import NamedItem
from numpy.random import uniform
from numpy import array, isnan, exp, ones, prod, minimum, inf
from .structure import TimeSeries
from .excel import standard_formats, AtomicaSpreadsheet, apply_widths, update_widths, ProgramEntry, read_tables, TimeDependentValuesEntry
from six import string_types
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
                    self.alloc[prog_name] = dcp(spending)
                else:
                    # Assume it is just a single number
                    self.alloc[prog_name] = TimeSeries(t=self.start_year,vals=spending)

#--------------------------------------------------------------------
# ProgramSet class
#--------------------------------------------------------------------

class ProgramSet(NamedItem):

    def __init__(self, name="default", programs=None, covouts=None, pops=None, comps=None, pars=None, data_start=None, data_end=None, default_cov_interaction="Additive", default_imp_interaction="best"):
        """ Class to hold all programs and programmatic effects. """
        NamedItem.__init__(self,name)

        # Programs and effects
        self.programs       = sc.odict()
        self.covouts         = sc.odict()
        if programs is not None: self.add_programs(programs)
        if covouts is not None:  self.add_covouts(covouts)
        self.default_cov_interaction = default_cov_interaction
        self.default_imp_interaction = default_imp_interaction
        self.relevant_progs = dict()    # This dictionary will store programs per parameters they target.

        # Data years
        self.data_start     = data_start
        self.data_end       = data_end
        if self.data_start is not None and self.data_end is not None:
            self.data_years     = sc.inclusiverange(self.data_start,self.data_end+1) # Initialize data years

        # Populations, parameters, and compartments 
        self.pops = None # These are all of the pops available based on the ProjectData used to load the ProgramSet
        self.comps = None # These are all of the comps available based on the ProjectFramework used to load the ProgramSet
        self.pars = None # # These are all of the pars available based on the ProjectFramework used to load the ProgramSet

        # TODO - this cache can be deprecated but might be replaced by something else later
        self._covout_valid_cache = None # This will cache whether a Covout can be used - this is populated at the start of model.py

        # Meta data
        self.created = today()
        self.modified = today()

        return None

    def prepare_cache(self):
        # This function is called once at the start of model.py, which allows various checks to be
        # performed once at the start of the simulation rather than at every timestep

        self._covout_valid_cache = {k:v.has_pars() for k,v in self.covouts.items()}

    def __repr__(self):
        ''' Print out useful information'''
        output = sc.desc(self)
        output += '    Program set name: %s\n'    % self.name
        output += '            Programs: %s\n'    % [prog for prog in self.programs]
        output += '        Date created: %s\n'    % sc.getdate(self.created)
        output += '       Date modified: %s\n'    % sc.getdate(self.modified)
        output += '============================================================\n'
        
        return output


    #######################################################################################################
    # Methods for data I/O
    #######################################################################################################

    def _set_available(self,framework,data):
        # Given framework and data, set the available pops, comps, and pars
        # noting that these are matched to the framework and data even though
        # the programs may not reach all of them
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
        if isinstance(spreadsheet,string_types):
            spreadsheet = AtomicaSpreadsheet(spreadsheet)

        workbook = openpyxl.load_workbook(spreadsheet.get_file(), read_only=True, data_only=True)  # Load in read-only mode for performance, since we don't parse comments etc.

        # Load individual sheets
        self._read_targeting(workbook['Program targeting'],framework,data)
        self._read_spending(workbook['Spending data'])
        self._read_effects(workbook['Program effects'],framework,data)

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

    def _read_targeting(self,sheet,framework,data):
        # This function reads a targeting sheet and instantiates all of the programs with appropriate targets, putting them
        # into `self.programs`

        tables = read_tables(sheet)
        assert len(tables) == 1, 'Targeting page should only contain one table'

        self.programs = sc.odict()
        sup_header = [x.value.lower().strip() if isinstance(x.value,string_types) else x.value for x in tables[0][0]]
        headers = [x.value.lower().strip() if isinstance(x.value,string_types) else x.value for x in tables[0][1]]

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
                if row[i].value and isinstance(row[i].value,string_types) and row[i].value.lower().strip() == 'y':
                    target_pops.append(pop_codenames[pop_idx[i]]) # Append the pop's codename

            for i in range(comp_start_idx, len(headers)):
                if row[i].value and isinstance(row[i].value,string_types) and row[i].value.lower().strip() == 'y':
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
        sheet.write(1, 1, 'Full Name', self._formats["center_bold"])
        update_widths(widths,1,'Abbreviation')
        for pop,full_name in self.pops.items():
            col = pop_col[pop]
            sheet.write(1, col, full_name, self._formats['rc_title']['left']['T'])
            widths[col] = 12 # Wrap population names

        for comp,full_name in self.comps.items():
            col = comp_col[comp]
            sheet.write(1, col, full_name, self._formats['rc_title']['left']['T'])
            widths[col] = 12 # Wrap compartment names

        row = 2
        for prog in self.programs.values():
            sheet.write(row, 0, prog.name)
            update_widths(widths, 0, prog.name)
            sheet.write(row, 1, prog.label)
            update_widths(widths, 1, prog.label)

            for pop in self.pops:
                col = pop_col[pop]
                if pop in prog.target_pops:
                    sheet.write(row,col, 'Y', self._formats["center"])
                else:
                    sheet.write(row,col, 'N', self._formats["center"])
                sheet.data_validation(xlrc(row, col), {"validate": "list", "source": ["Y", "N"]})
                sheet.conditional_format(xlrc(row, col), {'type': 'cell', 'criteria': 'equal to', 'value': '"Y"', 'format': self._formats['unlocked_boolean_true']})
                sheet.conditional_format(xlrc(row, col), {'type': 'cell', 'criteria': 'equal to', 'value': '"N"', 'format': self._formats['unlocked_boolean_false']})

            for comp in self.comps:
                col = comp_col[comp]
                if comp in prog.target_comps:
                    sheet.write(row,col, 'Y', self._formats["center"])
                else:
                    sheet.write(row,col, 'N', self._formats["center"])
                sheet.data_validation(xlrc(row, col), {"validate": "list", "source": ["Y", "N"]})
                sheet.conditional_format(xlrc(row, col), {'type': 'cell', 'criteria': 'equal to', 'value': '"Y"', 'format': self._formats['unlocked_boolean_true']})
                sheet.conditional_format(xlrc(row, col), {'type': 'cell', 'criteria': 'equal to', 'value': '"N"', 'format': self._formats['unlocked_boolean_false']})

            row += 1

        apply_widths(sheet,widths)


    def _read_spending(self,sheet):
        # Read the spending table and populate the program data
        tables = read_tables(sheet)
        for table in tables:
            tdve = TimeDependentValuesEntry.from_rows(table)
            prog = self.programs[tdve.name]
            prog.spend_data = tdve.ts['Total spend']
            prog.capacity = tdve.ts['Capacity constraints']
            prog.unit_cost = tdve.ts['Unit cost']
            prog.coverage = tdve.ts['Coverage']

    def _write_spending(self):
        sheet = self._book.add_worksheet("Spending data")

    def _read_effects(self,sheet,framework,data):
        # Read the program effects sheet. Here we instantiate a costcov object for every non-empty row

        tables = read_tables(sheet)
        pop_codenames = {v.lower().strip():x for x,v in self.pops.items()}
        par_codenames = {v.lower().strip():x for x,v in self.pars.items()}

        self.covouts = sc.odict()

        for table in tables:
            par_name = par_codenames[table[0][0].value.strip().lower()] # Code name of the parameter we are working with
            headers = [x.value.strip() if isinstance(x.value,string_types) else x.value for x in table[0]]
            idx_to_header = {i:h for i,h in enumerate(headers)} # Map index to header

            for row in table[1:]:
                # For each covout row, we will initialize
                pop_name = pop_codenames[row[0].value.lower().strip()] # Code name of the population we are working on
                progs = sc.odict()
                for i,x in enumerate(row[1:]):
                    i = i+1 # Offset of 1 because the loop is over row[1:] not row[0:]
                    if idx_to_header[i].lower() == 'baseline value':
                        if x.value is not None: # test `is not None` because it might be entered as 0
                            baseline = float(x.value)
                        else:
                            baseline = None
                    elif idx_to_header[i].lower() == 'coverage interaction':
                        if x.value:
                            cov_interaction =  x.value.strip().lower() # additive, nested, etc.
                        else:
                            cov_interaction = None
                    elif idx_to_header[i].lower() == 'impact interaction':
                        if x.value:
                            imp_interaction =  x.value.strip().lower() # additive, nested, etc.
                        else:
                            imp_interaction = None
                    elif idx_to_header[i].lower() == 'uncertainty':
                        if x.value is not None: # test `is not None` because it might be entered as 0
                            uncertainty = float(x.value)
                        else:
                            uncertainty = None
                    elif x.value is not None: # If the header isn't empty, then it should be one of the program names
                        progs[idx_to_header[i]] = float(x.value)

                if baseline is not None or progs: # Only instantitate covout objects if they have programs associated with them
                    self.covouts[(par_name,pop_name)] = Covout(par=par_name,pop=pop_name,cov_interaction= cov_interaction, imp_interaction = imp_interaction, uncertainty=uncertainty,baseline=baseline,progs=progs)

    def _write_effects(self):
        sheet = self._book.add_worksheet("Program effects")




    @staticmethod
    def new(filename, name=None, progs=None, pops=None, comps=None, pars=None, project=None, framework=None, data=None, data_start=None, data_end=None):
        ''' Generate a new progset with blank data. '''

        # Validate and process inputs
        if sc.isnumber(progs):
            nprogs = progs
            progs = []  # Create real program list
            for p in range(nprogs):
                progs.append({'name': 'Prog %i' % (p + 1), 'label': 'Program %i' % (p + 1)})
        else: 
            errormsg = 'Please just supply a number of programs, not "%s"' % (type(progs))
            raise AtomicaException(errormsg)

        # Complex checking of framework/data requirements - people can EITHER provide:
        #  - a number of compartments, a number of populations, and a number of parameters
        #  - a data and framework 
        #  - a project containing data and a framework
        if pops is None or comps is None or pars is None:
            # Try to get them from the data/framework            
            if data is None or framework is None:
                if project is None:
                    errormsg = 'To initialise a ProgramSet, please supply one of the following sets of inputs: (a) the number of populations and compartments you want, (b) a framework and ProjectData structure, (c) a Project.'
                    raise AtomicaException(errormsg)
                else:
                    data = project.data
                    framework = project.framework
                pops = odict([(k,v['label']) for k,v in data.pops.iteritems()])
                comps = odict()
                for _,spec in framework.comps.iterrows():
                    if spec['is source']=='y' or spec['is sink']=='y' or spec['is junction']=='y':
                        continue
                    else:
                        comps[spec.name] = spec['display name']
                pars = odict() 
                for _,spec in framework.pars.iterrows():
                    if spec['is impact']=='y':
                        pars[spec.name] = spec['display name']

        else:
            # Starting totally from scratch with integer arguments: just create lists with empty entries
            if sc.isnumber(pops):
                npops = pops
                pops = []  # Create real pops dict
                for p in range(npops):
                    pops.append(('Pop %i' % (p + 1), 'Population %i' % (p + 1)))
            pops = sc.odict(pops)
        
            if sc.isnumber(comps):
                ncomps = comps
                comps = []  # Create real compartments list
                for p in range(ncomps):
                    comps.append(('Comp %i' % (p + 1), 'Compartment %i' % (p + 1)))
            comps = sc.odict(comps)

            if sc.isnumber(pars):
                npars = pars
                pars = odict()  # Create real pars list
                for p in range(npars):
                    pars.append(('Par %i' % (p + 1), 'Parameter %i' % (p + 1)))
            pars = sc.odict(pars)
        
        if data_start is None or data_end is None:
            errormsg = 'Please supply a start and end year for program data entry.'
            raise AtomicaException(errormsg)
            
        newps = ProgramSet(name=name, programs=progs, pops=pops, comps=comps, pars=pars, data_start=data_start, data_end=data_end)
        return newps
            
        



    def save(self,fname):
        ''' Shortcut for saving to disk, copied from data.py'''
        ss = self.to_spreadsheet()
        ss.save(fname)


    #######################################################################################################
    # Helper methods for data I/O
    #######################################################################################################
    def set_content(self, name=None, row_names=None, column_names=None, row_levels=None, data=None,
                    row_format='general', row_formats=None, validation=None, assumption_properties=None, assumption_data=None, assumption=True):
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
                         ("validation",      validation),
                         ("assumption_properties", assumption_properties),
                         ("assumption_data", assumption_data),
                         ("assumption",      assumption)])

    def _write_costcovdata(self):
        # Generate cost-coverage sheet
        widths = dict()
        sheet = self._book.add_worksheet('Spending data')

        # Get data
        existing_data = []
        for prog in self.programs.values():
            spend = [prog.spend_data.findrow(year)[1] if prog.spend_data and prog.spend_data.findrow(year) is not None else '' for year in self.data_years]
            capacity = [prog.capacity.findrow(year)[1] if prog.capacity and prog.capacity.findrow(year) is not None else '' for year in self.data_years]
            unit_cost = [prog.unit_cost.findrow(year)[1] if prog.unit_cost and prog.unit_cost.findrow(year) is not None else '' for year in self.data_years]
            existing_data.extend([spend,capacity,unit_cost])
            
        current_row = 0
        sheet.set_column('C:C', 20)
        row_levels = ['Total spend', 'Capacity constraints', 'Unit cost']
        content = self.set_content(row_names=self.ref_prog_range,
                                   column_names=range(int(self.data_start), int(self.data_end + 1)),
                                   row_formats=['general']*5,
                                   data=existing_data,
                                   row_levels=row_levels)

        the_range = ProgramEntry(sheet=sheet, first_row=current_row, content=content)
        current_row = the_range.emit(self._formats, widths=widths)
        apply_widths(sheet,widths)


    def _write_covoutdata(self):
        # Generate coverage-outcome sheet
        sheet = self._book.add_worksheet('Program effects')
        pops = self.allpops
        pars = self.allpars

        # Set column widths and other initial data
        widths = {0: 20, 2: 10, 3: 16, 4: 16, 5: 2}
        current_row = 0
        row_levels = []
        for p in pops.values(): row_levels.extend([p])
        assumption_properties = {'title': 'Value for a person covered by this program alone:','connector': '','columns': self.ref_prog_range}

        # Get data if it exists for writing to file
        existing_data = []
        existing_extra = []
        for par in pars.keys():
            for pop in pops.keys():
                npi_val = self.covouts[(par, pop)].npi_val.get() if (par, pop) in self.covouts.keys() else ''
                cov_interaction = self.covouts[(par, pop)].cov_interaction if (par, pop) in self.covouts.keys() else ''
                imp_interaction = self.covouts[(par, pop)].imp_interaction if (par, pop) in self.covouts.keys() else ''
                existing_data.append([npi_val,cov_interaction,imp_interaction])
                prog_vals = [self.covouts[(par, pop)].progs[prog.name].get() if (par, pop) in self.covouts.keys() and prog.name in self.covouts[(par, pop)].progs.keys() else '' for prog in self.programs.values()]
                existing_extra.append(prog_vals)

        content = self.set_content(row_names=pars.values(),
                                   column_names=['Value if none of the programs listed here are targeting this parameter', 'Coverage interation', 'Impact interaction'],
                                   row_format='general',
                                   data=existing_data,
                                   assumption_data=existing_extra,
                                   assumption_properties=assumption_properties,
                                   validation={3:["Random","Additive","Nested"],4:["Synergistic","best"]},
                                   row_levels=row_levels)

        the_range = ProgramEntry(sheet=sheet, first_row=current_row, content=content)
        current_row = the_range.emit(self._formats, rc_title_align='left', widths=widths)
        apply_widths(sheet,widths)

        
    def update(self):
        ''' Update (run this is you change something... )'''

        def set_target_pars(self):
            '''Update model parameters targeted by some program in the response'''
            self.target_pars = []
            if self.programs:
                for prog in self.programs.values():
                    for pop in prog.target_pars: self.target_pars.append(pop)
        
        def set_target_par_types(self):
            '''Update model parameter types targeted by some program in the response'''
            self.target_par_types = []
            if self.programs:
                for prog in self.programs.values():
                    for par_type in prog.target_par_types: self.target_par_types.append(par_type)
                self.target_par_types = list(set(self.target_par_types))
    
        def set_target_pops(self):
            '''Update populations targeted by some program in the response'''
            self.target_pops = []
            if self.programs:
                for prog in self.programs.values():
                    for pop in prog.target_pops: self.target_pops.append(pop)
                self.target_pops = list(set(self.target_pops))
    
        set_target_pars(self)
        set_target_par_types(self)
        set_target_pops(self)

        # Pre-build a dictionary of programs targeted by parameters.
        self.relevant_progs = dict()
        for par_type in self.target_par_types:
            self.relevant_progs[par_type] = self.progs_by_target_par(par_type)
        return None


    #######################################################################################################
    # Methods to add or remove programs, populations, parameters
    #######################################################################################################        
    def add_programs(self, progs=None, replace=False):
        ''' Add a list of programs '''
        
        # Process programs
        if progs is not None:
            progs = sc.promotetolist(progs)
        else:
            errormsg = 'Programs to add should not be None'
            raise AtomicaException(errormsg)
        if replace:
            self.programs = sc.odict()
        for prog in progs:
            if isinstance(prog, dict):
                prog = Program(**prog)
            if type(prog)!=Program:
                errormsg = 'Programs to add must be either dicts or program objects, not %s' % type(prog)
                raise AtomicaException(errormsg)
            
            # Save it
            self.programs[prog.name] = prog

        self.update()
        return None


    def rm_programs(self, progs=None, die=True):
        ''' Remove one or more programs from both the list of programs and also from the covouts functions '''
        if progs is None:
            self.programs = odict() # Remove them all
        progs = promotetolist(progs)
        for prog in progs:
            try:
                self.programs.pop[prog]
            except:
                errormsg = 'Could not remove program named %s' % prog
                if die: raise AtomicaException(errormsg)
                else: print(errormsg)
            for co in self.covouts.values(): # Remove from coverage-outcome functions too
                co.progs.pop(prog, None)
        self.update()
        return None


    def add_covout(self, par=None, pop=None, cov_interaction=None, imp_interaction=None, npi_val=None, max_val=None, prog=None, verbose=False):
        ''' add a single coverage-outcome parameter '''
        # Process inputs
        if verbose: print('Adding single coverage-outcome parameter for par=%s, pop=%s' % (par, pop))
        if cov_interaction is None: cov_interaction = self.default_cov_interaction
        if imp_interaction is None: imp_interaction = self.default_imp_interaction
        self.covouts[(par, pop)] = Covout(par=par, pop=pop, cov_interaction=cov_interaction, imp_interaction=imp_interaction, npi_val=npi_val, max_val=max_val, prog=prog)
        if verbose: print('Done with add_covout().')
        return None


    def add_covouts(self, covouts=None, prog_effects=None, pop_short_name=None, verbose=False):
        '''
        Add an odict of coverage-outcome parameters. Note, assumes a specific structure, as follows:
        covouts[parname][popname] = odict()
        '''
        # Process inputs
        if verbose: print('Adding coverage-outcome effects')
        if covouts is not None:
            if isinstance(covouts, list) or isinstance(covouts,type(array([]))):
                errormsg = 'Expecting a dictionary with specific structure, not a list'
                raise AtomicaException(errormsg)
        else:
            errormsg = 'Covout list not supplied.'
            raise AtomicaException(errormsg)
            
            
        for par,pardata in covouts.iteritems():
            if verbose: print('  Adding coverage-outcome effect for parameter %s' % par)
            if par in prog_effects.keys():
                for pop,popdata in covouts[par].iteritems():
                    pop = pop_short_name[pop]
                    if pop in prog_effects[par].keys():
                        # Sanitize inputs
                        if verbose: print('    For population %s' % pop)
                        npi_val = sanitize(popdata['baseline'], defaultval=0., label=', '.join([par, pop, 'baseline']))
                        self.add_covout(par=par, pop=pop, npi_val=npi_val, prog=prog_effects[par][pop])
        
        return None


    def progs_by_target_pop(self, filter_pop=None):
        '''Return a dictionary with:
             keys: all populations targeted by programs
             values: programs targeting that population '''
        progs_by_target_pop = odict()
        for prog in self.programs.values():
            target_pops = prog.target_pops if prog.target_pops else None
            if target_pops:
                for pop in target_pops:
                    if pop not in progs_by_target_pop: progs_by_target_pop[pop] = []
                    progs_by_target_pop[pop].append(prog)
        if filter_pop: return progs_by_target_pop[filter_pop]
        else: return progs_by_target_pop


    def progs_by_target_par_type(self, filter_par_type=None):
        '''Return a dictionary with:
             keys: all parameter types targeted by programs
             values: programs targeting that population '''
        progs_by_target_par_type = odict()
        for prog in self.programs.values():
            target_par_types = prog.target_par_types if prog.target_par_types else None
            if target_par_types:
                for par_type in target_par_types:
                    if par_type not in progs_by_target_par_type: progs_by_target_par_type[par_type] = []
                    progs_by_target_par_type[par_type].append(prog)
        if filter_par_type: return progs_by_target_par_type[filter_par_type]
        else: return progs_by_target_par_type


    def progs_by_target_par(self, filter_par_type=None):
        '''Return a dictionary with:
             keys: all parameters targeted by programs
             values: programs targeting that population '''
        progs_by_target_par = odict()
        for par_type in self.target_par_types:
            progs_by_target_par[par_type] = odict()
            for prog in self.progs_by_target_par_type(par_type):
                target_pars = prog.target_pars if prog.target_pars else None
                for target_par in target_pars:
                    if par_type == target_par['param']:
                        if target_par['pop'] not in progs_by_target_par[par_type]: progs_by_target_par[par_type][target_par['pop']] = []
                        progs_by_target_par[par_type][target_par['pop']].append(prog)
            progs_by_target_par[par_type] = progs_by_target_par[par_type]
        if filter_par_type: return progs_by_target_par[filter_par_type]
        else: return progs_by_target_par


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
        
        default_budget = odict() # Initialise outputs

        # Validate inputs
        if year is not None: year = promotetoarray(year)
        if optimizable is None: optimizable = False # Return only optimizable indices

        # Get cost data for each program 
        for prog in self.programs.values():
            default_budget[prog.name] = prog.get_spend(year)

        return default_budget


    def get_num_covered(self, year=None, unit_cost=None, capacity=None, alloc=None, sample='best', optimizable=None):
        ''' Extract the number covered if cost data has been provided; if optimizable is True, then only return optimizable programs '''
        
        num_covered = odict() # Initialise outputs

        # Validate inputs
        if year is not None: year = promotetoarray(year)
        if optimizable is None: optimizable = False # Return only optimizable indices

        # Get cost data for each program 
        for prog in self.programs.values():
            if alloc and prog.name in alloc:
                spending = alloc[prog.name]
            else:
                spending = None

            num_covered[prog.name] = prog.get_num_covered(year=year, unit_cost=unit_cost, capacity=capacity, budget=spending, sample=sample)

        return num_covered


    def get_prop_covered(self, year=None, denominator=None, unit_cost=None, capacity=None, alloc=None, sample='best'):
        '''Returns proportion covered for a time/spending vector and denominator.
        Denominator is expected to be a dictionary.'''
        # INPUT
        # denominator - dict of denominator values keyed by program name
        # alloc - dict of spending values (arrays) keyed by program name (same thing returned by self.get_alloc)
        prop_covered = odict() # Initialise outputs

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


    def get_coverage(self, year=None, as_proportion=False, denominator=None, unit_cost=None, capacity=None, budget=None, sample='best'):
        '''Returns proportion OR number covered for a time/spending vector.'''
        
        if as_proportion and denominator is None:
            print('Can''t return proportions because denominators not supplied. Returning numbers instead.')
            as_proportion = False
            
        if as_proportion:
            return self.get_prop_covered(year=year, denominator=denominator, unit_cost=unit_cost, capacity=capacity, budget=budget, sample=sample)
        else:
            return self.get_num_covered(year=year, unit_cost=unit_cost, capacity=capacity, budget=budget, sample=sample)


    def get_outcomes(self, coverage=None, year=None, sample='best'):
        ''' Get a dictionary of parameter values associated with coverage levels'''

        # Validate inputs
        if year is None: year = 2018. # TEMPORARY
        if coverage is None:
            raise AtomicaException('Please provide coverage to calculate outcomes')
        if not isinstance(coverage, dict): # Only acceptable format at the moment
            errormsg = 'Expecting coverage to be a dict, not %s' % type(coverage)
            raise AtomicaException(errormsg)
        for covkey in coverage.keys(): # Ensure coverage level values are arrays
            coverage[covkey] = promotetoarray(coverage[covkey])
            for item in coverage[covkey]:
                if item<0 or item>1:
                    errormsg = 'Expecting coverage to be a proportion, value for entry %s is %s' % (covkey, item)
                    raise AtomicaException(errormsg)
        if self._covout_valid_cache is None:
            self.prepare_cache()

        # Initialise output
        outcomes = odict()

        # Loop over parameter types
        for par_type in self.target_par_types:
            outcomes[par_type] = odict()

            relevant_progs = self.relevant_progs[par_type]
            # Loop over populations relevant for this parameter type
            for popno, pop in enumerate(relevant_progs.keys()):

                delta, thiscov = odict(), odict()
                
                # Loop over the programs that target this parameter/population combo
                for prog in relevant_progs[pop]:
                    if not self._covout_valid_cache[(par_type,pop)]:
                        print('WARNING: no coverage-outcome function defined for optimizable program  "%s", skipping over... ' % (prog.name))
                        outcomes[par_type][pop] = None
                    else:
                        outcomes[par_type][pop]  = self.covouts[(par_type, pop)].npi_val.get(sample)
                        thiscov[prog.name]         = coverage[prog.name]
                        delta[prog.name]           = self.covouts[(par_type, pop)].progs[prog.name].get(sample) - outcomes[par_type][pop]
                        
                # Pre-check for additive calc
                if self.covouts[(par_type, pop)].cov_interaction == 'Additive':
                    if sum(thiscov[:])>1: 
                        print('WARNING: coverage of the programs %s, all of which target parameter %s, sums to %s, which is more than 100 per cent, and additive interaction was selected. Resetting to random... ' % ([p.name for p in relevant_progs[pop]], [par_type, pop], sum(thiscov[:])))
                        self.covouts[(par_type, pop)].cov_interaction = 'Random'
                        
                # ADDITIVE CALCULATION
                # NB, if there's only one program targeting this parameter, just do simple additive calc
                if self.covouts[(par_type, pop)].cov_interaction == 'Additive' or len(relevant_progs[pop])==1:
                    # Outcome += c1*delta_out1 + c2*delta_out2
                    for prog in relevant_progs[pop]:
                        if not self._covout_valid_cache[(par_type,pop)]:
                            print('WARNING: no coverage-outcome parameters defined for program  "%s", population "%s" and parameter "%s". Skipping over... ' % (prog.name, pop, par_type))
                            outcomes[par_type][pop] = None
                        else: 
                            outcomes[par_type][pop] += thiscov[prog.name]*delta[prog.name]
                        
                # NESTED CALCULATION
                elif self.covouts[(par_type, pop)].cov_interaction == 'Nested':
                    # Outcome += c3*max(delta_out1,delta_out2,delta_out3) + (c2-c3)*max(delta_out1,delta_out2) + (c1 -c2)*delta_out1, where c3<c2<c1.
                    cov,delt = [],[]
                    for prog in thiscov.keys():
                        cov.append(thiscov[prog])
                        delt.append(delta[prog])
                    cov_tuple = sorted(zip(cov,delt)) # A tuple storing the coverage and delta out, ordered by coverage
                    for j in range(len(cov_tuple)): # For each entry in here
                        if j == 0: c1 = cov_tuple[j][0]
                        else: c1 = cov_tuple[j][0]-cov_tuple[j-1][0]
                        outcomes[par_type][pop] += c1*max([ct[1] for ct in cov_tuple[j:]])                
            
                # RANDOM CALCULATION
                elif self.covouts[(par_type, pop)].cov_interaction == 'Random':
                    # Outcome += c1(1-c2)* delta_out1 + c2(1-c1)*delta_out2 + c1c2* max(delta_out1,delta_out2)

                    for prog1 in thiscov.keys():
                        product = ones(thiscov[prog1].shape)
                        for prog2 in thiscov.keys():
                            if prog1 != prog2:
                                product *= (1-thiscov[prog2])
        
                        outcomes[par_type][pop] += delta[prog1]*thiscov[prog1]*product 

                    # Recursion over overlap levels
                    def overlap_calc(indexes,target_depth):
                        if len(indexes) < target_depth:
                            accum = 0
                            for j in range(indexes[-1]+1,len(thiscov)):
                                accum += overlap_calc(indexes+[j],target_depth)
                            output = thiscov.values()[indexes[-1]]*accum
                            return output
                        else:
                            output = thiscov.values()[indexes[-1]]* max(delta.values()[0],0)
                            return output

                    # Iterate over overlap levels
                    for i in range(2,len(thiscov)): # Iterate over numbers of overlapping programs
                        for j in range(0,len(thiscov)-1): # Iterate over the index of the first program in the sum
                            outcomes[par_type][pop] += overlap_calc([j],i)[0]

                    # All programs together
                    outcomes[par_type][pop] += prod(array(thiscov.values()),0)*max([c for c in delta.values()]) 

                else: raise AtomicaException('Unknown reachability type "%s"', self.covouts[(par_type, pop)].cov_interaction)
        
        return outcomes
        
        
    def export(self):
        '''Export progset data to a progbook'''
        pass

    def reconcile(self):
        '''Reconcile parameters'''
        pass


#--------------------------------------------------------------------
# Program class
#--------------------------------------------------------------------
class Program(NamedItem):
    ''' Defines a single program.'''

    def __init__(self, name=None, label=None, baseline_spend=None, spend_data=None, unit_cost=None, coverage=None, capacity=None, target_pops=None, target_pars=None, target_comps=None):
        '''Initialize'''
        NamedItem.__init__(self,name)

        assert name is not None, 'You must supply a name for a program'
        self.name               = name # Short name of program
        self.label              = name if label is None else label # Full name of the program
        self.target_pars        = None # Dict of parameters targeted by program, in form {'param': par.short, 'pop': pop}
        self.target_par_types   = None # List of parameter types targeted by program, should correspond to short names of parameters
        self.target_pops        = [] # List of populations targeted by the program
        self.target_comps       = [] # Compartments targeted by the program - used for calculating coverage denominators
        self.baseline_spend     = TimeSeries(assumption=0.0) if baseline_spend is None else baseline_spend # A TimeSeries with any baseline spending data
        self.spend_data         = TimeSeries() if spend_data is None else spend_data # TimeSeries with spending data
        self.unit_cost          = TimeSeries() if unit_cost is None else unit_cost # TimeSeries with unit cost of program
        self.capacity           = TimeSeries() if capacity is None else capacity # TimeSeries with capacity of program - optional - if not supplied, cost function is assumed to be linear
        self.coverage           = TimeSeries() if coverage is None else coverage # TimeSeries with capacity of program - optional - if not supplied, cost function is assumed to be linear

        # Populate the values
        self.update_targets(target_pops=target_pops, target_pars=target_pars, target_comps=target_comps)
        return None


    def __repr__(self):
        ''' Print out useful info'''
        output = sc.desc(self)
        output += '          Program name: %s\n'    % self.name
        output += '         Program label: %s\n'    % self.label
        output += '  Targeted populations: %s\n'    % self.target_pops
        output += '   Targeted parameters: %s\n'    % self.target_pars
        output += ' Targeted compartments: %s\n'    % self.target_comps
        output += '\n'
        return output
    

    def update_targets(self, target_pops=None, target_pars=None, target_comps=None):
        ''' Add data to a program, or otherwise update the values. Same syntax as init(). '''
        
        def set_target_pars(target_pars=None):
            ''' Set target parameters'''
            target_par_keys = ['param', 'pop']
            target_pars = promotetolist(target_pars) # Let's make sure it's a list before going further
            target_par_types = []
            target_pops = []
            for tp,target_par in enumerate(target_pars):
                if isinstance(target_par, dict): # It's a dict, as it needs to be
                    thesekeys = sorted(target_par.keys())
                    if thesekeys==target_par_keys: # Keys are correct -- main usage case!!
                        target_pars[tp] = target_par
                        target_par_types.append(target_par['param'])
                        target_pops.append(target_par['pop'])
                    else:
                        errormsg = 'Keys for a target parameter must be %s, not %s' % (target_par_keys, thesekeys)
                        raise AtomicaException(errormsg)
                elif isinstance(target_par, tuple): # It's a list, assume it's in the usual order
                    if len(target_par)==2:
                        target_pars[tp] = {'param':target_par[0], 'pop':target_par[1]} # If a list or tuple, assume this order
                        target_par_types.append(target_par[0])
                        target_pops.append(target_par[1])
                    else:
                        errormsg = 'When supplying a target_par as a list or tuple, it must have length 2, not %s' % len(target_par)
                        raise AtomicaException(errormsg)
                else:
                    errormsg = 'Targetpar must be string, tuple, or dict, not %s' % type(target_par)
                    raise AtomicaException(errormsg)
            self.target_pars.extend(target_pars) # Add the new values
            old_target_pops = self.target_pops
            old_target_pops.extend(target_pops)
            self.target_pops = list(set(old_target_pops)) # Add the new values
            old_target_par_types = self.target_par_types
            old_target_par_types.extend(target_par_types)
            self.target_par_types = list(set(old_target_par_types)) # Add the new values
            return None

        if target_pops  is not None: self.target_pops    = promotetolist(target_pops, 'string') # key(s) for targeted populations
        if target_pars  is not None: set_target_pars(target_pars) # targeted parameters
        if target_comps is not None: self.target_comps    = promotetolist(target_comps, 'string') # key(s) for targeted populations

        if self.target_pops is None: self.target_pops = [] # Empty list
        if self.target_pars is None:
            self.target_pars = [] # Empty list
            self.target_par_types = [] # Empty list
            
        return None

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
            tests['unit_cost invalid']   = not(isnumber(self.get_unit_cost()))
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
        budget = promotetoarray(budget)
                
        if unit_cost is None:
            unit_cost = self.unit_cost.interpolate(year)
        unit_cost = promotetoarray(unit_cost)
            
        if capacity is None:
            if self.capacity is not None:
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
    
    def __init__(self, par=None, pop=None, cov_interaction='additive', imp_interaction='best', uncertainty=0.0,baseline=None,progs=None):
        logger.debug('Initializing Covout for par=%s, pop=%s, baseline=%s' % (par, pop, baseline))
        self.par = par
        self.pop = pop
        self.cov_interaction = cov_interaction
        self.imp_interaction = imp_interaction
        self.sigma = uncertainty
        self.baseline = baseline
        self.progs = sc.odict() if progs is None else progs
        return None
    
    def __repr__(self):
#        output = desc(self)
        output  = indent('   Parameter: ', self.par)
        output += indent('  Population: ', self.pop)
        output += indent('Baseline val: ', self.baseline)
        output += indent('    Programs: ', ', '.join(['%s: %s' % (key,val) for key,val in self.progs.items()]))
        output += '\n'
        return output
        
    
    def add(self, prog=None, val=None):
        ''' 
        Accepts either
        self.add([{'FSW':[0.3,0.1,0.4]}, {'SBCC':[0.1,0.05,0.15]}])
        or
        self.add('FSW', 0.3)
        '''
        if isinstance(prog, dict):
            for key,val in prog.items():
                self.progs[key] = val
        elif isinstance(prog, (list, tuple)):
            for key,val in prog:
                self.progs[key] = val
        elif isinstance(prog, string_types) and val is not None:
            self.progs[prog] = val
        else:
            errormsg = 'Could not understand prog=%s and val=%s' % (prog, val)
            raise AtomicaException(errormsg)
        return None
            

