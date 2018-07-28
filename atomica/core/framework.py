# -*- coding: utf-8 -*-
"""
Atomica project-framework file.
Contains all information describing the context of a project.
This includes a description of the Markov chain network underlying project dynamics.
"""
import sciris.core as sc
from .system import logger, AtomicaException, NotAllowedError, NotFoundError
from .excel import read_tables, AtomicaSpreadsheet
import openpyxl
import pandas as pd
import numpy as np
from .structure import FrameworkSettings as FS

class ProjectFramework(object):
    """ The object that defines the transition-network structure of models generated by a project. """

    def __init__(self,inputs=None):
        # Instantiate a Framework
        # INPUTS
        # - inputs: A string (which will load an Excel file from disk
        # - A dict of sheets, which will just set the sheets attribute
        # - None, which will set the sheets to an empty dict ready for content

        # Load Framework from disk
        if isinstance(inputs,str):
            spreadsheet = AtomicaSpreadsheet(inputs)
            workbook = openpyxl.load_workbook(spreadsheet.get_file(), read_only=True, data_only=True)  # Load in read-write mode so that we can correctly dump the file
            self.sheets = sc.odict()

            for worksheet in workbook.worksheets:
                tables = read_tables(worksheet)  # Read the tables
                self.sheets[worksheet.title] = list()
                for table in tables:
                    # Get a dataframe
                    df = pd.DataFrame.from_records(table).applymap(lambda x: x.value)
                    df.columns = df.iloc[0]
                    df = df[1:]
                    self.sheets[worksheet.title].append(df)

                # For convenience, if there is only one table (which is the case for most of the sheets) then
                # don't store it as a list. So there will only be a list of DataFrames if there was more than
                # one table on the page (e.g. for cascades)
                if len(self.sheets[worksheet.title]) == 1:
                    self.sheets[worksheet.title] = self.sheets[worksheet.title][0]

            self._validate()

        elif isinstance(inputs,dict):
            self.sheets = inputs
        else:
            self.sheets = sc.odict()

    def to_spreadsheet(self):
        raise NotImplementedError()

    # The primary data storage in the Framework are DataFrames with the contents of the Excel file
    # The convenience methods below enable easy access of frequency used contents without having
    # to store them separately or going via the DataFrames every time
    @property
    def comps(self):
        # Shortcut to Compartments sheet
        return self.sheets['Compartments']

    @comps.setter
    def comps(self, value):
        assert isinstance(value,pd.DataFrame)
        self.sheets['Compartments'] = value

    def get_comp(self,comp_name):
        return self.comps.loc[comp_name]

    @property
    def characs(self):
        # Shortcut to Characteristics sheet
        return self.sheets['Characteristics']

    @characs.setter
    def characs(self, value):
        assert isinstance(value,pd.DataFrame)
        self.sheets['Characteristics'] = value

    def get_charac(self,charac_name):
        return self.characs.loc[charac_name]

    @property
    def pars(self):
        # Shortcut to Parameters sheet
        return self.sheets['Parameters']

    @pars.setter
    def pars(self, value):
        assert isinstance(value,pd.DataFrame)
        self.sheets['Parameters'] = value

    def get_par(self,par_name):
        return self.pars.loc[par_name]

    @property
    def interactions(self):
        # Shortcut to Characteristics sheet
        return self.sheets['Interactions']

    @interactions.setter
    def interactions(self, value):
        assert isinstance(value,pd.DataFrame)
        self.sheets['Interactions'] = value

    def get_interaction(self,interaction_name):
        return self.interactions.loc[interaction_name]

    def get_variable(self,name):
        # This function will return either a Comp, a Charac, Par, or Interaction
        # Lookup can be based on code name or full name
        for df,item_type in zip([self.comps,self.characs,self.pars,self.interactions],[FS.KEY_COMPARTMENT,FS.KEY_CHARACTERISTIC,FS.KEY_PARAMETER,FS.KEY_INTERACTION]):
            if name in df.index:
                return df.loc[name], item_type
            elif name in set(df['Display Name']):
                return df.loc[df['Display Name'] == name].iloc[0], item_type

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
        t = self.sheets['Transitions'].copy() # Copy the dataframe on this sheet
        assert isinstance(t,pd.DataFrame) # This will be a list if there was more than one item present

        self.transitions = {x:list() for x in list(self.pars.index)}
        comp_names = set(self.comps.index)

        for _,from_row in t.iterrows(): # For each row in the transition matrix
            from_row.dropna(inplace=True)
            from_comp = from_row[0]
            assert from_comp in comp_names
            from_row = from_row[1:]
            for to_comp,par_name in from_row.iteritems():
                assert par_name in self.transitions, 'Parameter %s appears in the transition matrix but not on the Parameters page' % (par_name)
                assert to_comp in comp_names
                self.transitions[par_name].append((from_comp,to_comp))

    def _validate(self):
        # This function validates the content of Framework. There are two aspects to this
        # - Adding in any missing values using appropriate defaults
        # - Checking that the provided information is internally consistent

        # Check for required sheets
        for page in ['Databook Pages','Compartments','Parameters','Characteristics','Transitions','Interactions']:
            assert page in self.sheets, 'Framework File missing required sheet "%s"' % (page)

        ### VALIDATE COMPARTMENTS
        required = ['Display Name','Is Source', 'Is Sink','Is Junction','Databook Page']
        defaults = {
            'Is Sink':'n',
            'Is Source':'n',
            'Is Junction':'n',
            'Can Calibrate':'n',
            'Databook Order':None, # Default is for it to be randomly ordered if the Databook Page is not None
        }
        valid_content = {
            'Display Name':None,
            'Is Sink':{'y','n'},
            'Is Source':{'y','n'},
            'Is Junction':{'y','n'},
            'Can Calibrate':{'y','n'},
        }

        self.comps.set_index('Code Name',inplace=True)
        self.comps = sanitize_dataframe(self.comps, required, defaults, valid_content)

        # Default setup weight is 1 if in databook or 0 otherwise
        # This is a separate check because the default value depends on other columns
        if 'Setup Weight' not in self.comps:
            self.comps['Setup Weight'] = (~self.comps['Databook Page'].isnull()).astype(int)
        else:
            fill_ones = self.comps['Setup Weight'].isnull() & self.comps['Databook Page']
            self.comps['Setup Weight'][fill_ones] = 1
            self.comps['Setup Weight'].fillna(0, inplace=True)

        # VALIDATE THE COMPARTMENT SPECIFICATION
        for index,row in self.comps.iterrows():
            n_types = (row[['Is Sink','Is Source','Is Junction']]=='y').astype(int).sum() # This sums the number of Y's for each compartment
            assert n_types <= 1, 'Compartment "%s" can only be one of Sink, Source, or Junction' % row.name

            if (row['Setup Weight']>0) & (row['Is Source']=='y' or row['Is Sink']=='y'):
                raise AtomicaException('Compartment "%s" is a source or a sink, but has a nonzero setup weight' % row.name)

            if (row['Databook Page'] is not None) & (row['Is Source']=='y' or row['Is Sink']=='y'):
                raise AtomicaException('Compartment "%s" is a source or a sink, but has a Databook Page' % row.name)

            if (row['Databook Page'] is None) and (row['Databook Order'] is not None):
                logger.warning('Compartment "%s" has a databook order, but no databook page' % row.name)

        ### VALIDATE PARAMETERS

        required = ['Display Name','Format','Databook Page']
        defaults = {
            'Default Value':None,
            'Minimum Value':None,
            'Maximum Value':None,
            'Function':None,
            'Databook Order':None,
            'Is Impact':'n',
            'Can Calibrate':'n',
        }
        valid_content = {
            'Display Name': None,
            'Is Impact':{'y','n'},
            'Can Calibrate':{'y','n'},
        }

        self.pars.set_index('Code Name',inplace=True)
        self.pars = sanitize_dataframe(self.pars, required, defaults, valid_content)

        # Parse the transitions matrix
        self._process_transitions()

        # Now validate each parameter
        for i,par in self.pars.iterrows():
            if self.transitions[par.name]: # If this parameter is associated with transitions

                # Units must be specified if this is a function parameter (in which case the databook does not specify the units)
                if (par['Function'] is not None) and (par['Format'] is None):
                    raise AtomicaException('Parameter %s has a custom function and is a transition parameter, so needs to have a format specified in the Framework' % par.name)

                from_comps = [x[0] for x in self.transitions[par.name]]
                to_comps = [x[1] for x in self.transitions[par.name]]

                # Avoid discussions about how to disaggregate parameters with multiple links from the same compartment.
                if len(from_comps) != len(set(from_comps)):
                    raise AtomicaException('Parameter "%s" cannot be associated with more than one transition from the same compartment' % par.name)

                n_special_outflow = 0
                for comp in from_comps:
                    comp_spec = self.get_comp(comp)
                    if comp_spec['Is Sink']=='y':
                        raise AtomicaException('Parameter "%s" has an outflow from Compartment "%s" which is a sink' % par.name,comp)
                    elif comp_spec['Is Source']=='y':
                        n_special_outflow += 1
                        assert par['Format'] == FS.QUANTITY_TYPE_NUMBER, 'Parameter "%s" has an outflow from a source compartment, so it needs to be in "number" units' % par.name
                    elif comp_spec['Is Junction']=='y':
                        n_special_outflow += 1
                        assert par['Format'] == FS.QUANTITY_TYPE_PROPORTION, 'Parameter "%s" has an outflow from a junction, so it must be in "proportion" units' % par.name

                    if (par['Format'] == FS.QUANTITY_TYPE_PROPORTION) and (comp_spec['Is Junction']!='y'):
                        raise AtomicaException('"Parameter "%s" has units of "proportion" which means all of its outflows must be from junction compartments, which Compartment "%s" is not',par.name,comp)

                if n_special_outflow > 1:
                    raise AtomicaException('Parameter "%s" has an outflow more than one source compartment or junction, which prevents disaggregation from working correctly' % par.name)

                for comp in to_comps:
                    if self.get_comp(comp)['Is Source']=='y':
                        raise AtomicaException('Parameter "%s" has an inflow to Compartment "%s" which is a source' % par.name,comp)

        ### VALIDATE CHARACTERISTICS
        required = ['Display Name','Databook Page']
        defaults = {
            'Components':None,
            'Denominator':None,
            'Default Value':None,
            'Function':None,
            'Databook Order':None,
            'Can Calibrate':'n',
        }
        valid_content = {
            'Display Name': None,
            'Components':None,
            'Can Calibrate':{'y','n'},
        }

        self.characs.set_index('Code Name',inplace=True)
        self.characs = sanitize_dataframe(self.characs, required, defaults, valid_content)

        if 'Setup Weight' not in self.characs:
            self.characs['Setup Weight'] = (~self.characs['Databook Page'].isnull()).astype(int)
        else:
            fill_ones = self.characs['Setup Weight'].isnull() & self.characs['Databook Page']
            self.characs['Setup Weight'][fill_ones] = 1
            self.characs['Setup Weight'].fillna(0, inplace=True)

        for i,spec in self.characs.iterrows():

            for component in spec['Components'].split(','):
                assert component.strip() in self.comps.index or component.strip() in self.characs.index, 'In Characteristic "%s", included component "%s" was not recognized as a Compartment or Characteristic' % (spec.name,component)

                if spec['Denominator'] is not None:
                    assert spec['Denominator'] in self.comps.index or spec['Denominator'] in self.characs.index, 'In Characteristic "%s", denominator "%s" was not recognized as a Compartment or Characteristic' % (spec.name, component)

        # VALIDATE INTERACTIONS
        self.interactions.set_index('Code Name',inplace=True)


    def get_allowed_units(self,code_name):
        # Given a variable's code name, return the allowed units for that variable based on the spec provided in the Framework
        item_spec,item_type = self.get_variable(code_name)

        # State variables are in number amounts unless normalized.
        if item_type in [FS.KEY_COMPARTMENT, FS.KEY_CHARACTERISTIC]:
            if "Denominator" in item_spec.index and item_spec["Denominator"] is not None:
                allowed_units = [FS.QUANTITY_TYPE_FRACTION]
            else:
                allowed_units = [FS.QUANTITY_TYPE_NUMBER]

        # Modeller's choice for parameters
        elif item_type in [FS.KEY_PARAMETER] and "Format" in item_spec and item_spec["Format"] is not None:
            allowed_units = [item_spec["Format"]]
        else:
            # User choice if a transfer or a transition parameter.
            if item_type in [FS.KEY_TRANSFER] or self.transitions[item_spec.name]:
                allowed_units = [FS.QUANTITY_TYPE_NUMBER, FS.QUANTITY_TYPE_PROBABILITY]
            # If not a transition, the format of this parameter is meaningless but can still be used when plotting
            else:
                allowed_units = []

        return allowed_units

    @staticmethod
    def new(num_comps=0, num_characs=0, num_pars=0, num_datapages=0, num_interpops=0):
        # This function returns a new Framework object

        sheets = sc.odict()

        ### Create default sheets and template DataFrames
        # Note that the first column needs to be provided in the template DataFrame here, because it is expected to be present
        # when it is assigned to the index name after validation (for Compartments, Characteristics and Parameters)
        sheets['Databook Pages'] = pd.DataFrame(index=None,columns=['Title'])
        sheets['Compartments'] = pd.DataFrame(index=None,columns=['Code Name','Display Name','Is Sink','Is Source','Is Junction','Setup Weight','Can Calibrate','Databook Page','Databook Order'])
        sheets['Transitions'] = pd.DataFrame() # This is a dummy
        sheets['Characteristics'] = pd.DataFrame(index=None,columns=['Display Name','Components','Denominator','Default Value','Setup Weight','Can Calibrate','Databook Page','Databook Order'])
        sheets['Interactions'] = pd.DataFrame(index=None,columns=['Display Name','Default Value'])
        sheets['Parameters'] = pd.DataFrame(index=None,columns=['Display Name','Format','Default Value','Minimum Value','Maximum Value','Function','Is Impact','Can Calibrate','Databook Page','Databook Order'])
        sheets['Cascades'] = pd.DataFrame(index=None,columns=['<Cascade Name>','Constituents'])
        sheets['Plots'] = pd.DataFrame(index=None,columns=['Full Name','Type','Quantities','Aggregate pops','Plot Group'])

        # Insert the number of requested items into the relevant DataFrames
        for i in range(0,num_datapages):
            sheets['Databook Pages'].loc['shortname_%d' % (i)] = {'Title':'Worksheet name %d' % (i)}

        for i in range(0, num_comps):
            sheets['Compartments'].loc[i] = ['comp_%d' % i, 'Compartment %d' % i, 'n','n','n',None,'n',None,None]

        for i in range(0, num_characs):
            sheets['Characteristics'].loc[i] = ['charac_%d' % i, 'Characteristic %d' % i, None,None,None,'n',None,None]

        for i in range(0, num_pars):
            sheets['Parameters'].loc[i] = ['par_%d' % i, 'Parameter %d' % i, None,None,None,None,'n','n',None,None]

        for i in range(0, num_interpops):
            sheets['Interactions'].loc[i] = ['interaction_%d' % i, 'Interaction %d' % i, None]

        sheets['Compartments'].set_index('Code Name', inplace=True)
        sheets['Characteristics'].set_index('Code Name', inplace=True)
        sheets['Parameters'].set_index('Code Name', inplace=True)

        self.transitions = {x:list() for x in list(sheets['Parameters']['Code Names'])}



def sanitize_dataframe(df,required,defaults,valid_content):
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
        raise AtomicaException('DataFrame index cannot be done (this probably means a "Code Name" was left empty')

    for col in required:
        assert col in df, 'DataFrame did not contain the required column "%s"' % col

    # Then fill in default values
    for col, default_value in defaults.items():
        if col not in df:
            df[col] = default_value
        elif default_value is not None:
            df[col].fillna(default_value,inplace=True)

    # Finally check content
    for col, validation in valid_content.items():
        assert col in df, 'DataFrame does not contain column "%s" which was specified for validation' % (col)
        if validation is None:
            assert not df[col].isnull().any(), 'DataFrame column "%s" cannot contain any empty cells' % (col)
        else:
            validation = set(validation)
            assert set(df[col]).issubset(validation), 'DataFrame column "%s" can only contain the following values: %s' % (col,validation)

    # Strip all strings
    df.applymap(lambda x: x.strip() if type(x) is str else x)
    df.columns = [x.strip() for x in df.columns]

    return df