"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

Version: 2018jul30
"""

from sciris.core import odict, today, desc, promotetolist, promotetoarray, indent, isnumber, sanitize, dataframe, checktype, dcp
import sciris.core as sc
from .system import AtomicaException
from .utils import NamedItem
from numpy.random import uniform
from numpy import array, isnan, exp, ones, prod, minimum, inf
from .structure import TimeSeries
from .excel import standard_formats, AtomicaSpreadsheet, apply_widths, update_widths, ProgramEntry
from six import string_types
from xlsxwriter.utility import xl_rowcol_to_cell as xlrc
import xlrd
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
        self.covout         = sc.odict()
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
        self.allpops        = pops
        self.allcomps       = comps
        self.allpars        = pars

        self._covout_valid_cache = None # This will cache whether a Covout can be used - this is populated at the start of model.py

        # Meta data
        self.created = today()
        self.modified = today()

        return None


    def prepare_cache(self):
        # This function is called once at the start of model.py, which allows various checks to be
        # performed once at the start of the simulation rather than at every timestep

        self._covout_valid_cache = {k:v.has_pars() for k,v in self.covout.items()}

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
    @staticmethod
    def from_spreadsheet(spreadsheet=None, data=None, framework=None, project=None):
        '''Make a program set by loading in a spreadsheet.'''

        self = ProgramSet()

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

        # Create and load spreadsheet
        if isinstance(spreadsheet,string_types):
            spreadsheet = AtomicaSpreadsheet(spreadsheet)
        workbook = xlrd.open_workbook(file_contents=spreadsheet.get_file().read()) # Open workbook

        # Load individual sheets
        metadata = workbook.sheet_by_name('Program targeting') 
        costdata = workbook.sheet_by_name('Spending data') 
        effdata = workbook.sheet_by_name('Program effects') 
        
        # Initialise programs
        colindices = []
        programs = []
        for row in range(metadata.nrows):
            thesedata = metadata.row_values(row, start_colx=2) 
            if row==0: # Get metadata from first row
                for col in range(2,metadata.ncols):
                    cell_val = metadata.cell(row, col).value
                    if cell_val!='': colindices.append(col-1)
    
            if row==1: # Get population and compartment data from second row
                pops = thesedata[3:colindices[1]-2]
                self.allcomps = thesedata[colindices[1]-1:]

                # Check if the populations and compartments match those in the data and framework
                if set(pops) != set([p['label'] for p in data.pops.values()]):
                    if set(pops) != set(data.pops.keys()):
                        errormsg = 'The populations in the program data are not the same as those that were loaded from the databook: "%s" vs "%s"' % (pops, [p['label'] for p in data.pops.values()])
                        raise AtomicaException(errormsg)
                else:
                    self.allpops = odict([(k,v['label']) for k,v in data.pops.iteritems()])
                if set(self.allcomps) != set(list(framework.comps.index)):
                    errormsg = 'The compartments in the program data are not the same as those that were loaded from the framework file: "%s" vs "%s"' % (self.allcomps, set(list(framework.comps.index)))
                    raise AtomicaException(errormsg)
    
            else: # Get the program name and targeting data from the rest of the rows 
                if thesedata[0]: 
                    p = Program(name=str(thesedata[0]),
                                label=str(thesedata[1]),
                                target_comps =[compname for i,compname in enumerate(self.allcomps) if thesedata[colindices[1]-1:][i]])
                    programs.append(p)
                    
        # Add the programs
        self.add_programs(progs=programs)
        nprogs=len(programs)

        # Add spending data from the costing datasheet
        self.data_years = [] # Overwrite data years
        for col in range(costdata.ncols):
            thiscell = costdata.cell_value(1,col) # 1 is the 2nd row which is where the year data should be
            if thiscell=='' and len(self.data_years)>0: #  We've gotten to the end
                lastdatacol = col # Store this column number
                break # Quit
            elif thiscell != '': # More years, keep going
                self.data_years.append(float(thiscell)) # Add this year
        assumptioncol = lastdatacol + 1 # Figure out which column the assumptions are in; the "OR" space is in between
        self.data_start = self.data_years[0]
        self.data_end = self.data_years[-1]
    
        for row in range(costdata.nrows):
            progname = costdata.cell_value(row, 1) # Get the name of the program
            if progname != '': # The first column is blank: it's time for the data
                datatype = costdata.cell_value(row, 2) # Get the type of data -- WARNING, could be improved
                if datatype=='Total spend':
                    for col,year in enumerate(self.data_years):
                        spend = costdata.cell_value(row, col+3)
                        if spend: self.programs[progname].add_spend(spend=spend, year=year)
                elif datatype=='Capacity constraints':
                    for col,year in enumerate(self.data_years):
                        capacity = costdata.cell_value(row, col+3)
                        if capacity: self.programs[progname].update(capacity=capacity, year=year)
                elif datatype=='Unit cost':
#                    import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
                    for col,year in enumerate(self.data_years):
                        unit_cost = costdata.cell_value(row, col+3)
                        if unit_cost: self.programs[progname].update(unit_cost=[unit_cost], year=year)
                    
        # Add program effect data from the program effect datasheet
        pop_short_name = {v['label']:k for k,v in data.pops.items()} 
        comp_short_name = lambda x: framework.get_variable(x)[0].name
        self.allpars = []
        for row in range(effdata.nrows): # Even though it loops over every row, skip all except the best rows
            if effdata.cell_value(row, 1)!='': # Data row
                par_name = comp_short_name(effdata.cell_value(row, 1)) # Get the name of the parameter
                pop_name = pop_short_name[effdata.cell_value(row, 2)]
                npi_val = effdata.cell_value(row, 3) if effdata.cell_value(row, 3)!='' else 0.
                cov_interaction = effdata.cell_value(row, 4) if effdata.cell_value(row, 4)!='' else None
                imp_interaction = effdata.cell_value(row, 5) if effdata.cell_value(row, 5)!='' else None
                prog_vals = sc.odict([(pname, pval) for pname,pval in zip(self.programs.keys(),effdata.row_values(row, start_colx=7, end_colx=7+nprogs)) if pval])
                if par_name not in self.allpars: self.allpars.append(par_name)
                if prog_vals: # There are programmatic effects for this parameter, so we add it
                    self.add_covout(par=par_name, pop=pop_name, cov_interaction=cov_interaction, imp_interaction=imp_interaction, npi_val=npi_val, max_val=None, prog=prog_vals)
                    for pname in prog_vals.keys():
                        self.programs[pname].update(target_pars=(par_name,pop_name))

        return self


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
                pops = [p['label'] for p in data.pops.values()]
                comps = []
                for _,spec in framework.comps.iterrows():
                    if spec['is source']=='y' or spec['is sink']=='y' or spec['is junction']=='y':
                        continue
                    else:
                        comps.append(spec.name)
                pars = [] 
                for _,spec in framework.pars.iterrows():
                    if spec['is impact']=='y':
                        pars.append(spec['display name'])

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
                    pops.append('Comp %i' % (p + 1))

            if sc.isnumber(pars):
                npars = pars
                pars = []  # Create real pars list
                for p in range(npars):
                    pars.append('Parameter %i' % (p + 1))
        
        if data_start is None or data_end is None:
            errormsg = 'Please supply a start and end year for program data entry.'
            raise AtomicaException(errormsg)
            
        newps = ProgramSet(name=name, programs=progs, pops=pops, comps=comps, pars=pars, data_start=data_start, data_end=data_end)
        return newps
            
        
    def to_spreadsheet(self, filename=None):
        ''' Write the contents of a program set to a spreadsheet. '''
        f = io.BytesIO() # Write to this binary stream in memory

        self._book = xw.Workbook(f)
        self._formats = standard_formats(self._book)
        self._references = {} # Reset the references dict
            
        self._write_targeting()
        self._write_costcovdata()
        self._write_covoutdata()

        self._book.close()
        spreadsheet = AtomicaSpreadsheet(f)
        return spreadsheet


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

    
    def _write_targeting(self):
        # Generate targeting sheet
        sheet = self._book.add_worksheet('Program targeting')
        
        ## Get other inputs
        pops = self.allpops.values()
        comps = self.allcomps

        # Set column widths
        widths = {1: 5, 2: 30, 3: 30, 4: 2, 5: 11, 5+len(pops): 2, 5+len(pops)+1: 11}
        current_row = 0

        # Write descriptions of targeting
        sheet.write(0, 5, "Targeted to (populations)", self._formats['rc_title']['left']['T'])
        sheet.write(0, 6+len(pops), "Targeted to (compartments)", self._formats['rc_title']['left']['T'])

        # Write populations and compartments for targeting
        existing_data = []
        for prog in self.programs.values():
            label = prog.label
            name = prog.name
            target_pops  = [''] + ['' if pop not in prog.target_pops else 1 for pop in pops]
            target_comps = [''] + ['' if comp not in prog.target_comps else 1 for comp in comps]
            existing_data.append([name, label] + target_pops + target_comps)

        # Make column names
        column_names = ['Short name', 'Long name', ''] + pops + [''] + comps
        content = self.set_content(row_names=range(1,len(self.programs)+1),
                                   column_names=column_names,
                                   data=existing_data,
                                   assumption=False)
        
        self.prog_range = ProgramEntry(sheet=sheet, first_row=current_row, content=content)
        current_row = self.prog_range.emit(self._formats, rc_title_align='left', widths=widths)
        self.ref_prog_range = self.prog_range.param_refs()
        apply_widths(sheet,widths)


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
        for p in pops: row_levels.extend([p])
        assumption_properties = {'title': 'Value for a person covered by this program alone:','connector': '','columns': self.ref_prog_range}

        # Get data if it exists for writing to file
        existing_data = []
        existing_extra = []
        for par in pars:
            for pop in pops.keys():
                npi_val = self.covout[(par,pop)].npi_val.get() if (par,pop) in self.covout.keys() else ''
                cov_interaction = self.covout[(par,pop)].cov_interaction if (par,pop) in self.covout.keys() else ''
                imp_interaction = self.covout[(par,pop)].imp_interaction if (par,pop) in self.covout.keys() else ''
                existing_data.append([npi_val,cov_interaction,imp_interaction])
                prog_vals = [self.covout[(par,pop)].progs[prog.name].get() if (par,pop) in self.covout.keys() and prog.name in self.covout[(par,pop)].progs.keys() else '' for prog in self.programs.values() ]
                existing_extra.append(prog_vals)

        content = self.set_content(row_names=pars,
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
        ''' Remove one or more programs from both the list of programs and also from the covout functions '''
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
            for co in self.covout.values(): # Remove from coverage-outcome functions too
                co.progs.pop(prog, None)
        self.update()
        return None


    def add_covout(self, par=None, pop=None, cov_interaction=None, imp_interaction=None, npi_val=None, max_val=None, prog=None, verbose=False):
        ''' add a single coverage-outcome parameter '''
        # Process inputs
        if verbose: print('Adding single coverage-outcome parameter for par=%s, pop=%s' % (par, pop))
        if cov_interaction is None: cov_interaction = self.default_cov_interaction
        if imp_interaction is None: imp_interaction = self.default_imp_interaction
        self.covout[(par, pop)] = Covout(par=par, pop=pop, cov_interaction=cov_interaction, imp_interaction=imp_interaction, npi_val=npi_val, max_val=max_val, prog=prog)
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
                        npi_val = sanitize(popdata['npi_val'], defaultval=0., label=', '.join([par, pop, 'npi_val']))
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
                        outcomes[par_type][pop]  = self.covout[(par_type,pop)].npi_val.get(sample)
                        thiscov[prog.name]         = coverage[prog.name]
                        delta[prog.name]           = self.covout[(par_type,pop)].progs[prog.name].get(sample) - outcomes[par_type][pop]
                        
                # Pre-check for additive calc
                if self.covout[(par_type,pop)].cov_interaction == 'Additive':
                    if sum(thiscov[:])>1: 
                        print('WARNING: coverage of the programs %s, all of which target parameter %s, sums to %s, which is more than 100 per cent, and additive interaction was selected. Resetting to random... ' % ([p.name for p in relevant_progs[pop]], [par_type, pop], sum(thiscov[:])))
                        self.covout[(par_type,pop)].cov_interaction = 'Random'
                        
                # ADDITIVE CALCULATION
                # NB, if there's only one program targeting this parameter, just do simple additive calc
                if self.covout[(par_type,pop)].cov_interaction == 'Additive' or len(relevant_progs[pop])==1:
                    # Outcome += c1*delta_out1 + c2*delta_out2
                    for prog in relevant_progs[pop]:
                        if not self._covout_valid_cache[(par_type,pop)]:
                            print('WARNING: no coverage-outcome parameters defined for program  "%s", population "%s" and parameter "%s". Skipping over... ' % (prog.name, pop, par_type))
                            outcomes[par_type][pop] = None
                        else: 
                            outcomes[par_type][pop] += thiscov[prog.name]*delta[prog.name]
                        
                # NESTED CALCULATION
                elif self.covout[(par_type,pop)].cov_interaction == 'Nested':
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
                elif self.covout[(par_type,pop)].cov_interaction == 'Random':
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

                else: raise AtomicaException('Unknown reachability type "%s"',self.covout[(par_type,pop)].cov_interaction)
        
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

    def __init__(self, name=None, label=None, spend_data=None, unit_cost=None, year=None, capacity=None, target_pops=None, target_pars=None, target_comps=None):
        '''Initialize'''
        NamedItem.__init__(self,name)

        self.name               = None # Short name of program
        self.label              = None # Full name of the program
        self.target_pars        = None # Parameters targeted by program, in form {'param': par.short, 'pop': pop}
        self.target_par_types   = None # Parameter types targeted by program, should correspond to short names of parameters
        self.target_pops        = None # Populations targeted by the program
        self.target_comps       = [] # Compartments targeted by the program - used for calculating coverage denominators
        self.spend_data         = None # Latest or estimated expenditure
        self.unit_cost          = None # Unit cost of program
        self.capacity           = None # Capacity of program (a number) - optional - if not supplied, cost function is assumed to be linear
        
        # Populate the values
        self.update(name=name, label=label, spend_data=spend_data, unit_cost=unit_cost, year=year, capacity=capacity, target_pops=target_pops, target_pars=target_pars, target_comps=target_comps)
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
    


    def update(self, name=None, label=None, spend_data=None, unit_cost=None, capacity=None, year=None, target_pops=None, target_pars=None, target_comps=None, spend_type=None):
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
        
        def set_unit_cost(unit_cost=None, year=None):
            '''
            Set unit cost.
            
            Unit costs can be specified as a number, a tuple, or a dict. If a dict, they can be 
            specified with val as a tuple, or best, low, high as keys. Examples:
            
            set_unit_cost(21) # Assumes current year and that this is the best value
            set_unit_cost(21, year=2014) # Specifies year
            set_unit_cost(year=2014, unit_cost=[11, 31]) # Specifies year, low, and high
            set_unit_cost({'year':2014', 'best':21}) # Specifies year and best
            set_unit_cost({'year':2014', 'val':(21, 11, 31)}) # Specifies year, best, low, and high
            set_unit_cost({'year':2014', 'best':21, 'low':11, 'high':31) # Specifies year, best, low, and high
            
            Note, this function will typically not be called directly, but rather through the update() methods
            '''
            
            # Preprocessing
            unit_cost_keys = ['year', 'best', 'low', 'high']
            if year is None: year = 2018. # TEMPORARY
            if self.unit_cost is None: self.unit_cost = dataframe(cols=unit_cost_keys) # Create dataframe
            
            # Handle cases
            if isinstance(unit_cost, dataframe): 
                self.unit_cost = unit_cost # Right format already: use directly
            elif checktype(unit_cost, 'arraylike'): # It's a list of....something, either a single year with uncertainty bounds or multiple years
                if isnumber(unit_cost[0]): # It's a number (or at least the first entry is): convert to values and use
                    best,low,high = Val(unit_cost).get('all') # Convert it to a Val to do proper error checking and set best, low, high correctly
                    self.unit_cost.addrow([year, best, low, high])
                else: # It's not a list of numbers, so have to iterate
                    for uc in unit_cost: # Actually a list of unit costs
                        if isinstance(uc, dict): 
                            set_unit_cost(uc) # It's a dict: iterate recursively to add unit costs
                        else:
                            errormsg = 'Could not understand list of unit costs: expecting list of floats or list of dicts, not list containing %s' % uc
                            raise AtomicaException(errormsg)
            elif isinstance(unit_cost, dict): # Other main usage case -- it's a dict
                if any([key not in unit_cost_keys+['val'] for key in unit_cost.keys()]):
                    errormsg = 'Mismatch between supplied keys %s and key options %s' % (unit_cost.keys(), unit_cost_keys)
                    raise AtomicaException(errormsg)
                val = unit_cost.get('val') # First try to get 'val'
                if val is None: # If that fails, get other arguments
                    val = [unit_cost.get(key) for key in ['best', 'low', 'high']] # Get an array of values...
                best,low,high = Val(val).get('all') # ... then sanitize them via Val
                self.unit_cost.addrow([unit_cost.get('year',year), best, low, high]) # Actually add to dataframe
            else:
                errormsg = 'Expecting unit cost of type dataframe, list/tuple/array, or dict, not %s' % type(unit_cost)
                raise AtomicaException(errormsg)
            return None

        
        def set_spend(spend_data=None, year=None, spend_type='spend'):
            ''' Handle the spend data'''
            data_keys = ['year', spend_type]

            # Validate inputs
            if spend_type=='spend': attr_to_set = 'spend_data'
            elif spend_type=='basespend': attr_to_set = 'base_spend_data'
            else:
                errormsg = 'Unknown spend type %s' % spend_type
                raise AtomicaException(errormsg)
            
            if self.__getattribute__(attr_to_set) is None:
                    self.__setattr__(attr_to_set,dataframe(cols=data_keys)) # Create dataframe

            if year is None: year = 2018. # TEMPORARY
            
            # Consider different input possibilities
            if isinstance(spend_data, dataframe): 
                self.__setattr__(attr_to_set,spend_data) # Right format already: use directly
            elif isinstance(spend_data, dict):
                spend_data = {key:promotetolist(spend_data.get(key)) for key in data_keys} # Get full row
                if spend_data['year'] is not None:
                    for n,year in enumerate(spend_data['year']):
                        current_data = self.__getattribute__(attr_to_set).findrow(year,asdict=True) # Get current row as a dictionary
                        if current_data is not None:
                            for key in spend_data.keys():
                                if spend_data[key][n] is None: spend_data[key][n] = current_data[key] # Replace with old data if new data is None
                        these_data = [spend_data['year'][n], spend_data[spend_type][n]] # Get full row - WARNING, FRAGILE TO ORDER!
                        if attr_to_set == 'spend_data': self.spend_data.addrow(these_data) # Add new data
                        elif attr_to_set == 'base_spend_data': self.base_spend_data.addrow(these_data) # Add new data
            elif isinstance(spend_data, list): # Assume it's a list of dicts
                for datum in spend_data:
                    if isinstance(datum, dict):
                        set_spend(datum) # It's a dict: iterate recursively
                    else:
                        errormsg = 'Could not understand list of data: expecting list of dicts, not list containing %s' % datum
                        raise AtomicaException(errormsg)
            else:
                errormsg = 'Can only add data as a dataframe, dict, or list of dicts; this is not valid: %s' % spend_data
                raise AtomicaException(errormsg)

            return None
            
        # Actually set everything
        if name         is not None: self.name           = name # full name
        if label        is not None: self.label          = label # full name
        if target_pops  is not None: self.target_pops    = promotetolist(target_pops, 'string') # key(s) for targeted populations
        if target_pars  is not None: set_target_pars(target_pars) # targeted parameters
        if target_comps is not None: self.target_comps    = promotetolist(target_comps, 'string') # key(s) for targeted populations

        if capacity    is not None: self.capacity       = Val(sanitize(capacity)[-1]) # saturation coverage value - TODO, ADD YEARS
        if unit_cost   is not None: set_unit_cost(unit_cost, year) # unit cost(s)
        if spend_type is not None:
            if spend_data  is not None:
                set_spend(spend_data=spend_data,spend_type=spend_type) # Set spending data
        
        # Finally, check everything
        if self.name is None: # self.name must exist
            errormsg = 'You must supply a name for a program'
            raise AtomicaException(errormsg)
        if self.label is None:       self.label = self.name # If label not supplied, use name
        if self.target_pops is None: self.target_pops = [] # Empty list
        if self.target_pars is None:
            self.target_pars = [] # Empty list
            self.target_par_types = [] # Empty list
            
        return None
    
    
    def add_spend(self, spend_data=None, year=None, spend=None, spend_type='spend'):
        ''' Convenience function for adding data. Use either data as a dict/dataframe, or use kwargs, but not both '''
        if spend_data is None:
            spend_data = {'year':float(year), spend_type:spend}
        self.update(spend_data=spend_data, spend_type=spend_type)

        return None
        
        
    def add_pars(self, unit_cost=None, capacity=None, year=None):
        ''' Convenience function for adding saturation and unit cost. year is ignored if supplied in unit_cost. '''
        # Convert inputs
        if year is not None: year=float(year)
        if unit_cost is not None: unit_cost=promotetolist(unit_cost)
        self.update(unit_cost=unit_cost, capacity=capacity, year=year)
        return None
    
    
    def get_spend(self, year=None, total=False, die=False):
        ''' Convenience function for getting spending data'''
        spend = []
        try:
            if year is not None:
                year = sc.promotetoarray(year)
                for yr in year:
                    this_data = self.spend_data.findrow(yr, closest=True, asdict=True) # Get data
                    this_spend = this_data['spend']
                    if this_spend is None: spend = 0 # If not specified, assume 0
                    if total: 
                        base_spend = this_data['basespend'] # Add baseline spending
                        if base_spend is None: base_spend = 0 # Likewise assume 0
                        this_spend += base_spend
                    spend.append(this_spend)
            else: # Just get the most recent non-nan number
                spend = self.spend_data['spend'][~isnan(array([x for x in self.spend_data['spend']]))][-1] # TODO FIGURE OUT WHY THE SIMPLER WAY DOESN'T WORK
            return spend
        except Exception as E:
            if die:
                errormsg = 'Retrieving spending failed: %s' % E.message
                raise AtomicaException(errormsg)
            else:
                return None
            
    
    def get_unit_cost(self, year=None, die=False):
        ''' Convenience function for getting the current unit cost '''
        if year is None: year = 2018. # TEMPORARY
        unit_cost = []
        year = sc.promotetoarray(year)
        try:
            for yr in year:
                this_data = self.unit_cost.findrow(yr, closest=True, asdict=True) # Get data
                unit_cost.append(this_data['best'])
            return unit_cost
        except Exception as E:
            if die:
                errormsg = 'Retrieving unit cost failed: %s' % E.message
                raise AtomicaException(errormsg)
            else: # If not found, don't die, just return None
                return None
    

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
        return True if not (isnan(array([x for x in self.spend_data['spend']]))).all() else False #TODO, FIGURE OUT WHY SIMPLER WAY DOESN'T WORK!!!


    def get_num_covered(self, year=None, unit_cost=None, capacity=None, budget=None, sample='best'):
        '''Returns number covered for a time/spending vector'''
        num_covered = 0.
        
        # Validate inputs
        if budget is None:
            try:
                budget = self.get_spend(year)
            except Exception as E:
                errormsg = 'Can''t get number covered without a spending amount: %s' % E.message
                raise AtomicaException(errormsg)
            if isnan(budget).any():
                errormsg = 'No spending associated with the year provided: %s'
                raise AtomicaException(errormsg)
        budget = promotetoarray(budget)
                
        if unit_cost is None:
            try: unit_cost = self.get_unit_cost(year)
            except Exception as E:
                errormsg = 'Can''t get number covered without a unit cost: %s' % E.message
                raise AtomicaException(errormsg)
            if isnan(unit_cost).any():
                errormsg = 'No unit cost associated with the year provided: %s' % E.message
                raise AtomicaException(errormsg)
        unit_cost = promotetoarray(unit_cost)
            
        if capacity is None:
            if self.capacity is not None: capacity = self.capacity.get(sample)
            
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
           npi_val=120,
           progs={'Prog1':[15,10,10], 'Prog2':20}
           )
    '''
    
    def __init__(self, par=None, pop=None, cov_interaction=None, imp_interaction=None, npi_val=None, max_val=None, prog=None, verbose=False):
        if verbose: print('Initializing Covout for par=%s, pop=%s, npi_val=%s' % (par, pop, npi_val))
        self.par = par
        self.pop = pop
        self.cov_interaction = cov_interaction
        self.imp_interaction = imp_interaction
        self.npi_val = Val(npi_val)
        self.progs = odict()
        if prog is not None:
            self.add(prog=prog)

        return None
    
    def __repr__(self):
#        output = desc(self)
        output  = indent('   Parameter: ', self.par)
        output += indent('  Population: ', self.pop)
        output += indent('     NPI val: ', self.npi_val.get('all'))
        output += indent('    Programs: ', ', '.join(['%s: %s' % (key,val.get('all')) for key,val in self.progs.items()]))
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
                self.progs[key] = Val(val)
        elif isinstance(prog, (list, tuple)):
            for key,val in prog:
                self.progs[key] = Val(val)
        elif isinstance(prog, string_types) and val is not None:
            self.progs[prog] = Val(val)
        else:
            errormsg = 'Could not understand prog=%s and val=%s' % (prog, val)
            raise AtomicaException(errormsg)
        return None
            

    def has_pars(self, doprint=False):
        ''' Check whether the object has required parameters'''
        valid = True # Assume the best
        tests = {}
        try:
            tests['NPI values invalid']         = not(isnumber(self.npi_val.get() ))
            tests['Program values invalid']     = not(array([isnumber(prog.get()) for prog in self.progs.values()]).any())
            if any(tests.values()):
                valid = False # It's looking like it can't be optimized
                if not valid and doprint:
                    print('Program not optimizable for the following reasons: %s' % '\n'.join([key for key,val in tests.items() if val]))
                
        except Exception as E:
            valid = False
            if doprint:
                print('Program not optimizable because an exception was encountered: %s' % E.message)
        
        return valid


#--------------------------------------------------------------------
# Val
#--------------------------------------------------------------------
class Val(object):
    '''
    A single value including uncertainty
    
    Can be set the following ways:
    v = Val(0.3)
    v = Val([0.2, 0.4])
    v = Val([0.3, 0.2, 0.4])
    v = Val(best=0.3, low=0.2, high=0.4)
    
    Can be called the following ways:
    v() # returns 0.3
    v('best') # returns 0.3
    v(what='best') # returns 0.3
    v('rand') # returns value between low and high (assuming uniform distribution)
    
    Can be updated the following ways:
    v(0.33) # resets best
    v([0.22, 0.44]) # resets everything
    v(best=0.33) # resets best
    
    '''
    
    def __init__(self, best=None, low=None, high=None, dist=None, verbose=False):
        ''' Allow the object to be initialized, but keep the same infrastructure for updating '''
        if verbose: print('Initializing Val for best=%s, low=%s, high=%s' % (best, low, high))
        self.best = None
        self.low = None
        self.high = None
        self.dist = None
        self.update(best=best, low=low, high=high, dist=dist)
        return None
    
    
    def __repr__(self):
        output = desc(self)
        return output
    
    
    def __call__(self, *args, **kwargs):
        ''' Convenience function for both update and get '''
        
        # If it's None or if the key is a string (e.g. 'best'), get the values:
        if len(args)+len(kwargs)==0 or 'what' in kwargs or (len(args) and type(args[0])==str):
            return self.get(*args, **kwargs)
        else: # Otherwise, try to set the values
            self.update(*args, **kwargs)
    
    def __getitem__(self, *args, **kwargs):
        ''' Allows you to call e.g. val['best'] instead of val('best') '''
        return self.get(*args, **kwargs)
    
    
    def update(self, best=None, low=None, high=None, dist=None):
        ''' Actually set the values -- very convoluted, but should be flexible and work :)'''
        
        # Reset these values if already supplied
        if best is None and self.best is not None: best = self.best
        if low  is None and self.low  is not None: low  = self.low 
        if high is None and self.high is not None: high = self.high 
        if dist is None and self.dist is not None: dist = self.dist
        
        # Handle values
        if best is None: # Best is not supplied, so use high and low, e.g. Val(low=0.2, high=0.4)
            if low is None or high is None:
                errormsg = 'If not supplying a best value, you must supply both low and high values'
                raise AtomicaException(errormsg)
            else:
                best = (low+high)/2. # Take the average
        elif isinstance(best, dict):
            self.update(**best) # Assume it's a dict of args, e.g. Val({'best':0.3, 'low':0.2, 'high':0.4})
        else: # Best is supplied
            best = promotetoarray(best)
            if len(best)==1: # Only a single value supplied, e.g. Val(0.3)
                best = best[0] # Convert back to number
                if low is None: low = best # If these are missing, just replace them with best
                if high is None: high = best
            elif len(best)==2: # If length 2, assume high-low supplied, e.g. Val([0.2, 0.4])
                if low is not None and high is not None:
                    errormsg = 'If first argument has length 2, you cannot supply high and low values'
                    raise AtomicaException(errormsg)
                low = best[0]
                high = best[1]
                best = (low+high)/2.
            elif len(best)==3: # Assume it's called like Val([0.3, 0.2, 0.4])
                low, best, high = sorted(best) # Allows values to be provided in any order
            else:
                errormsg = 'Could not understand input of best=%s, low=%s, high=%s' % (best, low, high)
                raise AtomicaException(errormsg)
        
        # Handle distributions
        validdists = ['uniform']
        if dist is None: dist = validdists[0]
        if dist not in validdists:
            errormsg = 'Distribution "%s" not valid; choices are: %s' % (dist, validdists)
            raise AtomicaException(errormsg) 
        
        # Store values
        self.best = float(best)
        self.low  = float(low)
        self.high = float(high)
        self.dist = dist
        if not low<=best<=high:
            errormsg = 'Values are out of order (check that low=%s <= best=%s <= high=%s)' % (low, best, high)
            raise AtomicaException(errormsg) 
        
        return None
    
    
    def get(self, what=None, n=1):
        '''
        Get the value from this distribution. Examples (with best=0.3, low=0.2, high=0.4):
        
        val.get() # returns 0.3
        val.get('best') # returns 0.3
        val.get(['low', 'best',' high']) # returns [0.2, 0.3, 0.4]
        val.get('rand') # returns, say, 0.3664
        val.get('all') # returns [0.3, 0.2, 0.4]
        
        The seed() call should ensure pseudorandomness.
        '''
        
        if what is None or what is 'best': val = self.best# Haha this is funny but works
        elif what is 'low':                val = self.low
        elif what is 'high':               val = self.high
        elif what is 'all':                val = [self.best, self.low, self.high]
        elif what in ['rand','random']:
            if self.dist=='uniform':       val = uniform(low=self.low, high=self.high, size=n)
            else:
                errormsg = 'Distribution %s is not implemented, sorry' % self.dist
                raise AtomicaException(errormsg)
        elif type(what)==list:             val = [self.get(wh) for wh in what]# Allow multiple values to be used
        else:
            errormsg = 'Could not understand %s, expecting a valid string (e.g. "best") or list' % what
            raise AtomicaException(errormsg)
        return val
    
    

