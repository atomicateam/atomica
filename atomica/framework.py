# -*- coding: utf-8 -*-
"""
Atomica project-framework file.
Contains all information describing the context of a project.
This includes a description of the Markov chain network underlying project dynamics.
"""
import openpyxl
import pandas as pd
import sciris as sc
from .system import AtomicaException, NotFoundError, logger
from .excel import read_tables, AtomicaSpreadsheet
from .structure import FrameworkSettings as FS
from .version import version
import numpy as np
from .cascade import validate_cascade

class InvalidFramework(AtomicaException):
    pass

class ProjectFramework(object):
    """ The object that defines the transition-network structure of models generated by a project. """

    def __init__(self,inputs=None,name=None):
        # Instantiate a Framework
        # INPUTS
        # - inputs: A string (which will load an Excel file from disk) or an AtomicaSpreadsheet
        # - A dict of sheets, which will just set the sheets attribute
        # - None, which will set the sheets to an empty dict ready for content

        # Define metadata
        self.uid = sc.uuid()
        self.version = version
        self.gitinfo = sc.gitinfo(__file__)
        self.created = sc.now()
        self.modified = sc.now()

        # Load Framework from disk
        if sc.isstring(inputs):
            self.spreadsheet = AtomicaSpreadsheet(inputs)
        elif isinstance(inputs,AtomicaSpreadsheet):
            self.spreadsheet = inputs
        else:
            self.name = name
            self.sheets = sc.odict()
            self.spreadsheet = None
            return

        workbook = openpyxl.load_workbook(self.spreadsheet.get_file(), read_only=True, data_only=True)  # Load in read-write mode so that we can correctly dump the file

        self.sheets = sc.odict()

        # For some pages, we only ever want to read in one DataFrame, and we want empty lines to be ignored. For example, on the
        # 'compartments' sheet, we want to ignore blank lines, while on the 'cascades' sheet we want the blank line to delimit the
        # start of a new cascade. So, for the sheet names below, multiple tables will be compressed to one table
        merge_tables = {'databook pages','compartments','parameters','characteristics','transitions','interactions','plots'}

        for worksheet in workbook.worksheets:
            sheet_title = worksheet.title.lower()
            tables, start_rows = read_tables(worksheet)  # Read the tables
            if sheet_title in merge_tables:
                tables = [[row for table in tables for row in table]] # Flatten the tables into one big table
            self.sheets[sheet_title] = list()
            for table in tables:
                # Get a dataframe
                df = pd.DataFrame.from_records(table).applymap(lambda x: x.value)
                df.dropna(axis=1, how='all', inplace=True) # If a column is completely empty, including the header, ignore it. Helps avoid errors where blank cells are loaded by openpyxl due to extra non-value content
                if sheet_title == 'cascades':
                    # On the cascades sheet, the user-entered name appears in the header row. We must preserve case for this
                    # name so that things like 'TB cascade' don't become 'tb cascade'
                    df.columns = [df.iloc[0, 0]] + list(df.iloc[0,1:].str.lower())
                else:
                    df.columns = df.iloc[0].str.lower()
                df = df[1:]
                self.sheets[sheet_title].append(df)

        self._validate()
        if name is not None:
            self.name = name

    def save(self,fname):
        # This function saves an Excel file with the original spreadsheet
        if self.spreadsheet is None:
            raise AtomicaException('Spreadsheet is not present, cannot save Framework as xlsx')
        else:
            self.spreadsheet.save(fname)

    # The primary data storage in the Framework are DataFrames with the contents of the Excel file
    # The convenience methods below enable easy access of frequency used contents without having
    # to store them separately or going via the DataFrames every time
    @property
    def comps(self):
        # Shortcut to compartments sheet
        return self.sheets['compartments'][0]

    @comps.setter
    def comps(self, value):
        assert isinstance(value,pd.DataFrame)
        self.sheets['compartments'] = [value]

    def get_comp(self,comp_name):
        return self.comps.loc[comp_name]

    @property
    def characs(self):
        # Shortcut to Characteristics sheet
        return self.sheets['characteristics'][0]

    @characs.setter
    def characs(self, value):
        assert isinstance(value,pd.DataFrame)
        self.sheets['characteristics'] = [value]

    def get_charac(self,charac_name):
        return self.characs.loc[charac_name]

    def get_charac_includes(self,includes):
        # Given a characteristic, compartment, or list of characs and compartments, return a list
        # of all included compartments
        if not isinstance(includes,list):
            includes = [includes]

        expanded = []
        for include in includes:
            if include in self.characs.index:
                components = [x.strip() for x in self.characs.at[include, 'components'].split(',')]
                expanded += self.get_charac_includes(components)
            else:
                expanded.append(str(include)) # Use 'str()' to get `'sus'` in the error message instead of  `u'sus'`
        return expanded

    @property
    def pars(self):
        # Shortcut to Parameters sheet
        return self.sheets['parameters'][0]

    @pars.setter
    def pars(self, value):
        assert isinstance(value,pd.DataFrame)
        self.sheets['parameters'] = [value]

    def get_par(self,par_name):
        return self.pars.loc[par_name]

    @property
    def interactions(self):
        # Shortcut to Interactions sheet
        return self.sheets['interactions'][0]

    @interactions.setter
    def interactions(self, value):
        assert isinstance(value,pd.DataFrame)
        self.sheets['interactions'] = [value]

    @property
    def cascades(self):
        # If the Cascades sheet is present, return an odict where the key is the name of the cascade
        # and the value is the corresponding dataframe

        if 'cascades' not in self.sheets:
            return sc.odict() # Return an empty dict will let code downstream iterate over d.keys() and fail gracefully (no iterations) if no cascades were present

        cascade_list = self.sheets['cascades']
        data_present = False # If there is a cascade sheet but only has headings, then treat it like it wasn't defined
        d = sc.odict()

        for df in cascade_list:
            cascade_name = df.columns[0].strip()
            if cascade_name is None or len(cascade_name) == 0:
                raise AtomicaException('A cascade was found without a name')

            if cascade_name in d:
                raise InvalidFramework('A cascade with name "%s" was already read in' % (cascade_name))

            d[cascade_name] = df
            if df.shape[0]:
                data_present = True

        if data_present:
            return d
        else:
            return sc.odict()

    def get_interaction(self,interaction_name):
        return self.interactions.loc[interaction_name]

    def get_variable(self,name):
        # This function will return either a Comp, a Charac, Par, or Interaction
        # Lookup can be based on code name or full name
        for df,item_type in zip([self.comps,self.characs,self.pars,self.interactions],[FS.KEY_COMPARTMENT,FS.KEY_CHARACTERISTIC,FS.KEY_PARAMETER,FS.KEY_INTERACTION]):
            if name in df.index:
                return df.loc[name], item_type
            elif name in set(df['display name']):
                return df.loc[df['display name'] == name].iloc[0], item_type

        raise NotFoundError('Variable "%s" not found in Framework' % (name))

    def __contains__(self,item):
        # An item is contained in this Framework if `get_variable` would return something
        for df in [self.comps,self.characs,self.pars,self.interactions]:
            if item in df.index:
                return True
        return False

    def _process_transitions(self):
        # Parse the dataframe associated with the transition sheet into an edge-list representation
        # with a dict where the key is a parameter name and the value is a list of (from,to) tuples
        #
        # Expects a sheet called 'Transitions' to be present and correctly filled out
        t = self.sheets['transitions'][0].copy() # Copy the dataframe on this sheet
        assert isinstance(t,pd.DataFrame) # This could be a list if there was more than one item present, but this should have been dealt with earlier

        self.transitions = {x:list() for x in list(self.pars.index)}
        comp_names = set(self.comps.index)

        for _,from_row in t.iterrows(): # For each row in the transition matrix
            from_row.dropna(inplace=True)
            from_comp = from_row[0]
            if from_comp not in comp_names:
                raise InvalidFramework('A compartment "%s" appears in the first column of the matrix on the Transitions sheet, but it was not defined on the Compartments sheet' % (from_comp))
            from_row = from_row[1:]
            for to_comp,par_names in from_row.iteritems():
                for par_name in par_names.split(','):
                    par_name = par_name.strip()
                    if par_name not in self.transitions:
                        raise InvalidFramework('Parameter %s appears in the transition matrix but not on the Parameters page' % (par_name))
                    if to_comp not in comp_names:
                        raise InvalidFramework('A compartment "%s" appears in the first row of the matrix on the Transitions sheet, but it was not defined on the Compartments sheet' % (to_comp))
                    self.transitions[par_name].append((from_comp,to_comp))

    def _validate(self):
        # This function validates the content of Framework. There are two aspects to this
        # - Adding in any missing values using appropriate defaults
        # - Checking that the provided information is internally consistent

        # Check for required sheets
        for page in ['databook pages','compartments','parameters','characteristics','transitions']:
            if page not in self.sheets:
                raise InvalidFramework('The Framework file is missing a required sheet: "%s"' % (page))

        ### VALIDATE METADATA

        # Validate 'About' sheet - it must have a name
        if 'about' not in self.sheets:
            self.sheets['about'] = [pd.DataFrame.from_records([('Unnamed','No description available')],columns=['name','description'])]

        # Get the dataframe which has the name in it - the first one on the page, if there were multiple pages
        name_df = self.sheets['about'][0]
        required_columns = ['name']
        defaults = dict()
        valid_content = {
            'name': None,  # Valid content being `None` means that it just cannot be empty
        }

        try:
            name_df = sanitize_dataframe(name_df, required_columns, defaults, valid_content)
        except Exception as e:
            message = 'An occurred while reading the "About" sheet in the Framework -> '
            reraise_modify(e, message)


        try:
            name_df = sanitize_dataframe(name_df, required_columns, defaults, valid_content)
        except:
            message =


        name_df['name'] = name_df['name'].astype(str)
        self.name = name_df['name'].iloc[0]

        if 'cascade' in self.sheets and 'cascades' not in self.sheets:
            logger.warning('A sheet called "Cascade" was found, but it probably should be called "Cascades"')

        if 'plot' in self.sheets and 'plots' not in self.sheets:
            logger.warning('A sheet called "Plot" was found, but it probably should be called "Plots"')

        ### VALIDATE COMPARTMENTS
        required_columns = ['display name']
        defaults = {
            'is sink':'n',
            'is source':'n',
            'is junction':'n',
            'databook page':None,
            'default value':None,
            'databook order':None, # Default is for it to be randomly ordered if the databook page is not None
        }
        valid_content = {
            'display name':None, # Valid content being `None` means that it just cannot be empty
            'is sink':{'y','n'},
            'is source':{'y','n'},
            'is junction':{'y','n'},
        }

        self.comps.set_index('code name',inplace=True)
        self.comps = sanitize_dataframe(self.comps, required_columns, defaults, valid_content)

        # Default setup weight is 1 if in databook or 0 otherwise
        # This is a separate check because the default value depends on other columns
        if 'setup weight' not in self.comps:
            self.comps['setup weight'] = (~self.comps['databook page'].isnull()).astype(int)
        else:
            fill_ones = self.comps['setup weight'].isnull() & self.comps['databook page']
            self.comps['setup weight'][fill_ones] = 1
            self.comps['setup weight'] = self.comps['setup weight'].fillna(0)

        if 'calibrate' not in self.comps:
            # If calibration column is not present, then it calibrate if in the databook
            default_calibrate = ~self.comps['databook page'].isnull()
            self.comps['calibrate'] = None
            self.comps['calibrate'][default_calibrate] = 'y'

        # VALIDATE THE COMPARTMENT SPECIFICATION
        for index,row in self.comps.iterrows():
            n_types = (row[['is sink','is source','is junction']]=='y').astype(int).sum() # This sums the number of Y's for each compartment

            if n_types > 1:
                raise InvalidFramework('Compartment "%s" can only be one of Sink, Source, or Junction' % row.name)

            if (row['setup weight']>0) & (row['is source']=='y' or row['is sink']=='y'):
                raise InvalidFramework('Compartment "%s" is a source or a sink, but has a nonzero setup weight' % row.name)

            if (row['setup weight']>0) & (row['databook page'] is None):
                raise InvalidFramework('Compartment "%s" has a nonzero setup weight, but does not appear in the databook' % row.name)

            if (row['databook page'] is not None) & (row['is source']=='y' or row['is sink']=='y'):
                raise InvalidFramework('Compartment "%s" is a source or a sink, but has a databook page' % row.name)

            # It only makes sense to calibrate comps and characs that appear in the databook, because these are the only ones that
            # will appear in the parset
            if (row['databook page'] is None) & (row['calibrate'] is not None):
                raise InvalidFramework('Compartment "%s" is marked as being eligible for calibration, but it does not appear in the databook' % row.name)

            if (row['databook page'] is None) and (row['databook order'] is not None):
                logger.warning('Compartment "%s" has a databook order, but no databook page' % row.name)

        ### VALIDATE PARAMETERS
        required_columns = ['display name','format']
        defaults = {
            'default value':None,
            'minimum value':None,
            'maximum value':None,
            'function':None,
            'databook page':None,
            'databook order':None,
            'targetable':'n',
        }
        valid_content = {
            'display name': None,
            'targetable':{'y','n'},
        }

        self.pars.set_index('code name',inplace=True)
        self.pars = sanitize_dataframe(self.pars, required_columns, defaults, valid_content)

        # Make sure all units are lowercase
        self.pars['format'] = self.pars['format'].map(lambda x: x.lower() if sc.isstring(x) else x)

        if 'calibrate' not in self.pars:
            default_calibrate = self.pars['targetable'] == 'y'
            self.pars['calibrate'] = None
            self.pars['calibrate'][default_calibrate] = 'y'

        # Parse the transitions matrix
        self._process_transitions()

        # Now validate each parameter
        for i,par in self.pars.iterrows():
            if self.transitions[par.name]: # If this parameter is associated with transitions

                # Units must be specified if this is a function parameter (in which case the databook does not specify the units)
                if (par['function'] is not None) and (par['format'] is None):
                    raise InvalidFramework('Parameter %s has a custom function and is a transition parameter, so needs to have a format specified in the Framework' % par.name)

                from_comps = [x[0] for x in self.transitions[par.name]]
                to_comps = [x[1] for x in self.transitions[par.name]]

                # Avoid discussions about how to disaggregate parameters with multiple links from the same compartment.
                if len(from_comps) != len(set(from_comps)):
                    raise InvalidFramework('Parameter "%s" cannot be associated with more than one transition from the same compartment' % par.name)

                n_source_outflow = 0
                for comp in from_comps:
                    comp_spec = self.get_comp(comp)
                    if comp_spec['is sink']=='y':
                        raise InvalidFramework('Parameter "%s" has an outflow from Compartment "%s" which is a sink' % par.name,comp)
                    elif comp_spec['is source']=='y':
                        n_source_outflow += 1
                        if par['format'] != FS.QUANTITY_TYPE_NUMBER:
                            raise InvalidFramework('Parameter "%s" has an outflow from a source compartment, so it needs to be in "number" units' % par.name)
                    elif comp_spec['is junction']=='y':
                        if par['format'] != FS.QUANTITY_TYPE_PROPORTION:
                            raise InvalidFramework('Parameter "%s" has an outflow from a junction, so it must be in "proportion" units' % par.name)

                    if (par['format'] == FS.QUANTITY_TYPE_PROPORTION) and (comp_spec['is junction']!='y'):
                        raise InvalidFramework('"Parameter "%s" has units of "proportion" which means all of its outflows must be from junction compartments, which Compartment "%s" is not',par.name,comp)

                if n_source_outflow > 1:
                    raise InvalidFramework('Parameter "%s" has an outflow from more than one source compartment, which prevents disaggregation from working correctly' % par.name)

                for comp in to_comps:
                    if self.get_comp(comp)['is source']=='y':
                        raise InvalidFramework('Parameter "%s" has an inflow to Compartment "%s" which is a source' % par.name,comp)

        ### VALIDATE CHARACTERISTICS

        required_columns = ['display name']
        defaults = {
            'components':None,
            'denominator':None,
            'default value':None,
            'function':None,
            'databook page': None,
            'databook order':None,
        }
        valid_content = {
            'display name': None,
            'components':None,
        }

        self.characs.set_index('code name',inplace=True)
        self.characs = sanitize_dataframe(self.characs, required_columns, defaults, valid_content)

        if 'setup weight' not in self.characs:
            self.characs['setup weight'] = (~self.characs['databook page'].isnull()).astype(int)
        else:
            fill_ones = self.characs['setup weight'].isnull() & self.characs['databook page']
            self.characs['setup weight'][fill_ones] = 1
            self.characs['setup weight'] = self.characs['setup weight'].fillna(0)

        if 'calibrate' not in self.characs:
            # If calibration column is not present, then it calibrate if in the databook
            default_calibrate = ~self.characs['databook page'].isnull()
            self.characs['calibrate'] = None
            self.characs['calibrate'][default_calibrate] = 'y'

        for i,row in self.characs.iterrows():

            # Block this out because that way, can validate that there are some nonzero setup weights. Otherwise, user could set setup weights but
            # not put them in the databook, causing an error when actually trying to run the simulation
            if (row['setup weight']>0) and (row['databook page'] is None):
                raise InvalidFramework('Characteristic "%s" has a nonzero setup weight, but does not appear in the databook' % row.name)

            if row['denominator'] is not None:
                if not (row['denominator'] in self.comps.index or row['denominator'] in self.characs.index):
                    raise InvalidFramework('In Characteristic "%s", denominator "%s" was not recognized as a Compartment or Characteristic' % (row.name, component))
                if row['denominator'] in self.comps.index:
                    if not (self.comps.loc[row['denominator']]['denominator'] is None):
                        raise InvalidFramework('Characteristic "%s" uses the characteristic "%s" as a denominator. However, "%s" also has a denominator, which means that it cannot itself be used as a denominator for "%s"' % (row.name,row['denominator'],row['denominator'],row.name))

            if (row['databook page'] is None) and (row['calibrate'] is not None):
                raise InvalidFramework('Compartment "%s" is marked as being eligible for calibration, but it does not appear in the databook' % row.name)

            for component in row['components'].split(','):
                if not (component.strip() in self.comps.index or component.strip() in self.characs.index):
                    raise InvalidFramework('In Characteristic "%s", included component "%s" was not recognized as a Compartment or Characteristic' % (row.name,component))

        ### VALIDATE INTERACTIONS

        if 'interactions' not in self.sheets:
            self.sheets['interactions'] = [pd.DataFrame(columns=['code name','display name'])]

        required_columns = ['display name']
        defaults = {
            'default value':None,
        }
        valid_content = {
            'display name': None,
        }

        self.interactions.set_index('code name',inplace=True)
        self.interactions = sanitize_dataframe(self.interactions, required_columns, defaults, valid_content)

        ### VALIDATE NAMES - No collisions, no keywords

        code_names = list(self.comps.index) + list(self.characs.index) + list(self.pars.index) + list(self.interactions.index)
        tmp = set()
        for name in code_names:

            if FS.RESERVED_SYMBOLS.intersection(name):
                raise InvalidFramework('Code name "%s" is not valid: it cannot contain any of these reserved symbols %s' % (name,FS.RESERVED_SYMBOLS))

            if name in FS.RESERVED_KEYWORDS:
                raise InvalidFramework('Requested code name "%s" is a reserved keyword' % name)

            if name not in tmp:
                tmp.add(name)
            else:
                raise InvalidFramework('Duplicate code name "%s"' % name)

        display_names = list(self.comps['display name']) + list(self.characs['display name']) + list(self.pars['display name']) + list(self.interactions['display name'])
        tmp = set()
        for name in display_names:
            if name not in tmp:
                tmp.add(name)
            else:
                raise InvalidFramework('Duplicate display name "%s"' % name)

        ### VALIDATE CASCADES

        if 'cascades' not in self.sheets:
            # Make the fallback cascade with name 'Default'
            used_fallback_cascade = True
            records = []
            for _, spec in self.characs.iterrows():
                if not spec['denominator']:
                    records.append((spec['display name'],spec.name))
            self.sheets['cascades'] = sc.promotetolist(pd.DataFrame.from_records(records,columns=['Cascade','constituents']))
        else:
            used_fallback_cascade = False

        cascade_names = self.cascades.keys()
        for name in cascade_names:
            if name in FS.RESERVED_KEYWORDS:
                raise InvalidFramework('Requested cascade name "%s" is a reserved keyword' % name)

            if name in code_names:
                raise InvalidFramework('Cascade "%s" cannot have the same name as a compartment, characteristic, or parameter' % (name))
            if name in display_names:
                raise InvalidFramework('Cascade "%s" cannot have the same display name as a compartment, characteristic, or parameter' % (name))

            for stage_name in self.cascades[name].iloc[:,0]:
                if stage_name in FS.RESERVED_KEYWORDS:
                    raise InvalidFramework('Requested cascade stage name "%s" is a reserved keyword' % stage_name)

        # Check that all cascade constituents match a characteristic or compartment
        for df in self.cascades.values():
            for _,spec in df.iterrows():
                for component in spec['constituents'].split(','):
                    if not (component.strip() in self.comps.index or component.strip() in self.characs.index):
                        raise InvalidFramework('In Characteristic "%s", included component "%s" was not recognized as a Compartment or Characteristic' % (spec.name,component))

        # Check that the cascades are validly nested
        # This will also check the fallback cascade
        for cascade_name in self.cascades.keys():
            validate_cascade(self, cascade_name,used_fallback_cascade)

        ### VALIDATE INITIALIZATION
        characs = []
        for _, spec in self.characs.iterrows():
            if spec['databook page'] is not None and spec['setup weight']:
                characs.append(spec.name)

        comps = []
        for _, spec in self.comps.iterrows():
            if spec['is source'] == 'n' and spec['is sink'] == 'n':
                comps.append(spec.name)
            if spec['databook page'] is not None and spec['setup weight']:
                characs.append(spec.name)

        if len(characs) == 0:
            raise AtomicaException('No compartments or characteristics have a setup weight, cannot initialize simulation')

        A = np.zeros((len(characs), len(comps)))
        for i, charac in enumerate(characs):
            for include in self.get_charac_includes(charac):
                A[i, comps.index(include)] = 1.0


        if np.linalg.matrix_rank(A) < len(comps):
            logger.warning('Initialization characteristics are underdetermined - this may be intentional, but check the initial compartment sizes carefully')

    def get_allowed_units(self,code_name):
        # Given a variable's code name, return the allowed units for that variable based on the spec provided in the Framework
        item_spec,item_type = self.get_variable(code_name)

        # State variables are in number amounts unless normalized.
        if item_type in [FS.KEY_COMPARTMENT, FS.KEY_CHARACTERISTIC]:
            if "denominator" in item_spec.index and item_spec["denominator"] is not None:
                allowed_units = [FS.QUANTITY_TYPE_FRACTION]
            else:
                allowed_units = [FS.QUANTITY_TYPE_NUMBER]

        # Modeller's choice for parameters
        elif item_type in [FS.KEY_PARAMETER] and 'format' in item_spec and item_spec['format'] is not None:
            allowed_units = [item_spec['format']]
        else:
            # User choice if a transfer or a transition parameter.
            if item_type in [FS.KEY_TRANSFER] or (item_spec.name in self.transitions and self.transitions[item_spec.name]):
                allowed_units = [FS.QUANTITY_TYPE_NUMBER, FS.QUANTITY_TYPE_PROBABILITY]
            # If not a transition, the format of this parameter is meaningless but can still be used when plotting
            else:
                allowed_units = []

        return allowed_units

def sanitize_dataframe(df,required_columns,defaults,valid_content):
    # Take in a DataFrame and sanitize it
    # INPUTS
    # - df : The DataFrame being sanitized
    # - required : A list of column names that *must* be present
    # - defaults : A dict/odict mapping column names to default values. If a column is not present, it will be initialized with this value. If entries in this column are None, they will be assigned this value
    #              The default value can be a lambda function
    # - valid_content : A dict mapping column names to valid content. If specified, all elements of the column must be members of the iterable (normally this would be a set)
    #                   If 'valid_content' is None, then instead it will be checked that all of the values are NOT null i.e. use valid_content=None to specify it cannot be empty

    # First check required columns are present
    if any(df.index.isnull()):
        raise InvalidFramework('The first column contained an empty cell (this probably indicates that a "code name" was left empty')

    for col in required_columns:
        if col not in df:
            raise InvalidFramework('A required column "%s" is missing' % col)

    # Then fill in default values
    for col, default_value in defaults.items():
        if col not in df:
            df[col] = default_value
        elif default_value is not None:
            df[col] = df[col].fillna(default_value)

    # Finally check content
    for col, validation in valid_content.items():
        if col not in df:
            raise InvalidFramework('While validating, a required column "%s" was missing' % col) # NB. This error is likely to be the result of a developer adding validation for a column without setting a default for it

        if validation is None:
            if df[col].isnull().any():
                raise InvalidFramework('The column "%s" cannot contain any empty cells' % (col))
        else:
            validation = set(validation)
            if not set(df[col]).issubset(validation):
                raise InvalidFramework('The column "%s" can only contain the following values: %s' % (col,validation))

    # Strip all strings
    df.applymap(lambda x: x.strip() if sc.isstring(x) else x)
    if df.columns.isnull().any():
        raise InvalidFramework('There cannot be any empty cells in the header row')
    df.columns = [x.strip() for x in df.columns]

    return df



