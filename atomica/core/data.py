# -*- coding: utf-8 -*-
"""
Atomica data file.
Sets out a structure to store context-specific databook-imported values relating to a model.
"""

from .structure import TimeSeries
import sciris.core as sc
from xlsxwriter.utility import xl_rowcol_to_cell as xlrc
import openpyxl
from .excel import standard_formats, AtomicaSpreadsheet, read_tables, TimeDependentValuesEntry, TimeDependentConnections
import xlsxwriter as xw
import io
import numpy as np
from .system import AtomicaException
from .structure import FrameworkSettings as FS
from collections import defaultdict

# Data maps to a databook
# On construction, we first make some blank data, and then we write a databook in the same way as if we actually had
# data values
class ProjectData(object):

    def __init__(self):
        # This is just an overview of the structure of ProjectData
        # There are two pathways to a ProjectData
        # - Could load an existing one, with ProjectData.from_spreadsheet()
        # - Could make a new one, with ProjectData.new()
        self.pops = sc.odict() # This is an odict mapping code_name:{'label':full_name}
        self.transfers = list()
        self.interpops = list()
        self.tvec = None # This is the data's tvec used when instantiating new tables. Not _guaranteed_ to be the same for every TDVE/TDC table
        self.tdve = {}
        self.tdve_pages = sc.odict()

        # Internal storage used with methods while writing
        self._formats = None
        self._book = None
        self._references = None

    @property
    def start_year(self):
        # The ProjectData start year is defined as the earliest time point in
        # any of the TDVE/TDC tables. This should be used when changing the simulation
        # start year
        start_year = np.inf
        for td_table in list(self.tdve.values()) + self.transfers + self.interpops:
            start_year = min(start_year,np.amin(td_table.tvec))
        return start_year

    @property
    def end_year(self):
        # The ProjectData start year is defined as the earliest time point in
        # any of the TDVE/TDC tables. This should be used when changing the simulation
        # start year
        end_year = -np.inf
        for td_table in list(self.tdve.values()) + self.transfers + self.interpops:
            end_year = max(end_year,np.amax(td_table.tvec))
        return end_year

    def change_tvec(self, tvec):
        # Set tvec in all TDVE/TDC tables contained in the ProjectData
        # - Setting `ProjectData.tvec = <>` will only affect tables created afterwards
        # - Calling `ProjectData.change_tvec()` will modify all existing tables
        self.tvec = tvec.copy()
        for td_table in list(self.tdve.values()) + self.transfers + self.interpops:
            td_table.tvec = tvec

    def get_ts(self,name,key=None):
        # This extracts a TimeSeries from a TDVE table or TDC table
        #
        # INPUTS
        # - name: - The code name of a transfer, interaction, or compartment/characteristic/parameter
        #         - The name of a transfer parameter instantiated in model.build e.g. 'age_0-4_to_5-14'.
        #           this is mainly useful when retrieving data for plotting, where variables are organized according
        #           to names like 'age_0-4_to_5-14'
        # - key: - If `name` is a comp/charac/par, then key should be a pop name
        #        - If `name` is a transfer or interaction, then key should be a tuple (from_pop,to_pop)
        #        - If `name` is the name of a model transfer parameter, then `key` should be left as `None`
        #
        # If the key was not found, return None

        # First, check if it's the name of a TDVE
        if name in self.tdve:
            return self.tdve[name].ts[key]

        # Then, if the key is None, we are working on a transfer parameter. So reconstruct the key
        if key is None:
            x = name.split('_to_')
            code_name,from_pop = x[0].split('_',1)
            to_pop = x[1]
            name = code_name
            key = (from_pop,to_pop)

        for tdc in self.transfers + self.interpops:
            if name == tdc.code_name:
                return tdc.ts[key]

        return None

    @staticmethod
    def new(framework,tvec,pops,transfers):
        # Make a brand new databook
        # pops - Can be a number, or an odict with names and labels
        # transfers - Can be a number, or an odict with names and labels
        # interactions - Can be a number, or an odict with names and labels

        if not isinstance(pops,dict):
            new_pops = sc.odict()
            for i in range(0,pops):
                new_pops['pop_%d' % (i)] = 'Population %d' % (i)
        else:
            new_pops = pops

        if not new_pops:
            raise AtomicaException('A new databook must have at least 1 population')

        if not isinstance(transfers,dict):
            new_transfers = sc.odict()
            for i in range(0,transfers):
                new_transfers['transfer_%d' % (i)] = 'Transfer %d' % (i)
        else:
            new_transfers = transfers

        # Make all of the empty TDVE objects - need to store them by page, and the page information is in the Framework
        data = ProjectData()
        data.tvec = tvec

        raise('Working on this next')
        pages = defaultdict(list) # This will store {sheet_name:(code_name,databook_order)}
        item_types = [FS.KEY_PARAMETER,FS.KEY_CHARACTERISTIC,FS.KEY_COMPARTMENT]
        for item_type in item_types:
            for code_name,spec in framework.specs[item_type].items():
                if 'datapage' in spec and 'datapage_order' in spec and spec['datapage_order'] != -1:
                    if spec['datapage_order'] is None:
                        order = np.inf
                    else:
                        order = spec['datapage_order']
                    pages[spec['datapage']].append((code_name,order))
                    data.tdve[code_name] = TimeDependentValuesEntry(name=spec['label'],tvec=tvec,allowed_units=framework.get_allowed_units(code_name))

        # Now convert pages to full names and sort them into the correct order
        for page_name,spec in framework.specs['datapage'].items():

            # TODO: Work out how to get rid of these pages properly
            # Also, work out how the 'Parameters' and 'State Variables' tabs work
            if page_name in ['pop','transfer','transferdata','interpop']:
                continue

            if page_name in pages:
                pages[page_name].sort(key=lambda x: x[1])
                data.tdve_pages[spec['label']] = [x[0] for x in pages[page_name]]
            else:
                data.tdve_pages[spec['label']] = list()

        # Now, proceed to add the pops, transfers, and interactions
        for code_name,full_name in new_pops.items():
            data.add_pop(code_name,full_name)

        for code_name,full_name in new_transfers.items():
            data.add_transfer(code_name,full_name)

        for name,spec in framework.specs['interpop'].items():
            interpop = data.add_interaction(name, spec['label'])
            if 'default_value' in spec and spec['default_value']:
                for from_pop in interpop.pops:
                    for to_pop in interpop.pops:
                        ts = TimeSeries(format=interpop.allowed_units[0],units=interpop.allowed_units[0])
                        ts.insert(None,spec['default_value'])
                        interpop.ts[(from_pop,to_pop)] = ts
        return data

    @staticmethod
    def from_spreadsheet(spreadsheet,framework):
        # The framework is needed because ProjectData
        # Instantiate a new Databook given a spreadsheet

        # Basically the strategy is going to be
        # 1. Read in all of the stuff - pops, transfers, interpops can be directly added to Data
        # 2. Read in all the other TDVE content, and then store it in the data specs according to the variable type defined in the Framework
        # e.g. the fact that 'Alive' is a Characteristic is stored in the Framework and Data but not in the Databook. So for example, we read in
        # a TDVE table called 'Alive', but it needs to be stored in data.specs['charac']['ch_alive'] and the 'charac' and 'ch_alive' are only available in the Framework
        #
        # spreadsheet - A ScirisSpreadsheet object
        # framework - A ProjectFramework object
        #
        # This static method will return a new Databook instance given the provided databook Excel file and Framework
        self = ProjectData()

        if isinstance(spreadsheet,str):
            spreadsheet = AtomicaSpreadsheet(spreadsheet)

        workbook = openpyxl.load_workbook(spreadsheet.get_file(),read_only=True,data_only=True) # Load in read-only mode for performance, since we don't parse comments etc.

        for sheet in workbook.worksheets:
            if sheet.title.startswith('#ignore'):
                continue

            if sheet.title == 'Population Definitions':
                self._read_pops(sheet)
            elif sheet.title == 'Transfers':
                self._read_transfers(sheet)
            elif sheet.title == 'Interactions':
                self._read_interpops(sheet)
            elif sheet.title == 'Metadata':
                continue
            else:
                self.tdve_pages[sheet.title] = []
                for table in read_tables(sheet):
                    tdve = TimeDependentValuesEntry.from_rows(table)

                    # If this fails, the TDVE was not found in the framework. That's a critical stop error, because the framework needs to at least declare what kind of variable this is
                    code_name = framework.get_variable(tdve.name)[0].name
                    tdve.allowed_units = [x.title() for x in framework.get_allowed_units(code_name)]

                    self.tdve[code_name] = tdve
                    # Store the TDVE on the page it was actually on, rather than the one in the framework. Then, if users move anything around, the change will persist
                    self.tdve_pages[sheet.title].append(code_name)

        # Set the ProjectData's tvec based on the first TDVE table
        # 99.9% of the time, all of the tables will have the same values and so this is generally safe
        # The only time unexpected behaviour might occur is if the first TDVE table has exotic data points
        # and the user loads the databook, then adds a new transfer/interpop, the new table will have those same
        # modified data points. But what does the user expect, if the databook has mixed times
        self.tvec = self.tdve[self.tdve_pages[0][0]].tvec

        return self

    def validate(self,framework):
        # Check if the contents of the ProjectData can be used to run simulations
        #
        # A databook can be 'valid' in two senses
        #
        # - The Excel file adheres to the correct syntax and it can be parsed into a ProjectData object
        # - The resulting ProjectData object contains sufficient information to run a simulation
        #
        # Sometimes it is desirable for ProjectData to be valid in one sense rather than the other. For example,
        # in order to run a simulation, the ProjectData needs to contain at least one value for every TDVE table.
        # However, the TDVE table does _not_ need to contain values if all we want to do is add another key pop
        # Thus, the first stage of validation is the ProjectData constructor - if that runs, then users can
        # access methods like 'add_pop','remove_transfer' etc.
        #
        # However, to actually run a simulation, the _contents_ of the databook need to satisfy various conditions
        # These tests are implemented here. The typical workflow would be that ProjectData.validate() should be used
        # if a simulation is going to be run. In the first instance, this can be done in `Project.load_databook` but
        # the FE might want to perform this check at a different point if the databook manipulation methods e.g.
        # `add_pop` are going to be exposed in the interface
        #
        # This function throws an informative error if there are any problems identified or otherwise returns True
        #
        # Make sure that all of the quantities the Framework says we should read in have been read in, and that
        # those quantities all have some data values associated with them
        for df in [framework.comps, framework.characs, framework.pars]:
            for _, spec in df.iterrows():
                if spec['Databook Page'] is not None:
                    if spec.name not in self.tdve:
                        raise AtomicaException('Databook did not find any values for "%s" (%s)' % (spec['Display Name'],spec.name))
                    else:
                        allowed_units = framework.get_allowed_units(spec.name)
                        for name,ts in self.tdve[spec.name].ts.items():
                            assert name in self.pops, 'Population "%s" in "%s" not recognized. Should be one of: %s' % (name,self.tdve[spec.name].name,self.pops.keys())
                            assert ts.has_data, 'Data values missing for %s (%s)' % (self.tdve[spec.name].name, name)
                            assert ts.format is not None, 'Formats missing for %s (%s)' % (self.tdve[spec.name].name, name)
                            assert ts.units is not None, 'Units missing for %s (%s)' % (self.tdve[spec.name].name, name)
                            if allowed_units:
                                assert ts.units in allowed_units, 'Unit "%s" for %s (%s) do not match allowed units (%s)' % (ts.units,self.tdve[spec.name].name, name,allowed_units)
        return True

    def to_spreadsheet(self):
        # Initialize the bytestream
        f = io.BytesIO()

        # Open a workbook
        self._book = xw.Workbook(f)
        self._formats = standard_formats(self._book)
        self._references = {} # Reset the references dict

        # Write the contents
        self._write_pops()
        self._write_transfers()
        self._write_interpops()
        self._write_tdve()

        # Close the workbook
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

    def add_pop(self,code_name,full_name):
        # Add a population with the given name and label (full name)
        assert code_name not in self.pops, 'Population with name "%s" already exists' % (code_name)

        if code_name.strip().lower() == 'all':
            raise AtomicaException('A population was named "all", which is a reserved keyword and cannot be used as a population name')

        self.pops[code_name] = {'label':full_name}
        for interaction in self.transfers+self.interpops:
            interaction.pops.append(code_name)
        for tdve in self.tdve.values():
            default_unit = tdve.allowed_units[0] if tdve.allowed_units else None
            tdve.ts[code_name] = TimeSeries(format=default_unit,units=default_unit)

    def remove_pop(self,pop_name):
        # Remove population with given code name
        del self.pops[pop_name]

        for interaction in self.transfers+self.interpops:
            interaction.pops.remove(pop_name)
            for k in list(interaction.ts.keys()):
                if k[0] == pop_name or k[1] == pop_name:
                    del interaction.ts[k]

        for tdve in self.tdve.values():
            for k in list(tdve.ts.keys()):
                if k == pop_name:
                    del tdve.ts[k]

    def add_transfer(self,code_name,full_name):
        for transfer in self.transfers:
            assert code_name != transfer.code_name, 'Transfer with name "%s" already exists' % (code_name)
        self.transfers.append(TimeDependentConnections(code_name, full_name, self.tvec, list(self.pops.keys()), type='transfer', ts=None))

    def remove_transfer(self,code_name):
        names = [x.code_name for x in self.transfers]
        idx = names.index(code_name)
        del self.transfers[idx]

    # NB. Differences in the model will only happen if the model knows what to do with the new interaction
    def add_interaction(self,code_name,full_name):
        for interaction in self.interpops:
            assert code_name != interaction.code_name, 'Interaction with name "%s" already exists' % (code_name)
        interpop = TimeDependentConnections(code_name, full_name, self.tvec, list(self.pops.keys()), type='interaction', ts=None)
        self.interpops.append(interpop)
        return interpop

    def remove_interaction(self,code_name):
        names = [x.code_name for x in self.interpops]
        idx = names.index(code_name)
        del self.interpops[idx]

    def _read_pops(self, sheet):
        # TODO - can modify _read_pops() and _write_pops() if there are more population attributes
        tables = read_tables(sheet)
        assert len(tables) == 1, 'Population Definitions page should only contain one table'

        self.pops = sc.odict()
        assert tables[0][0][0].value.strip() == 'Abbreviation'
        assert tables[0][0][1].value.strip() == 'Full Name'

        for row in tables[0][1:]:
            if row[0].value.strip().lower() == 'all':
                raise AtomicaException('A population was named "all", which is a reserved keyword and cannot be used as a population name')
            self.pops[row[0].value.strip()] = {'label':row[1].value.strip()}

    def _write_pops(self):
        # Writes the 'Population Definitions' sheet
        sheet = self._book.add_worksheet("Population Definitions")

        current_row = 0
        sheet.write(current_row, 0, 'Abbreviation', self._formats["center_bold"])
        sheet.write(current_row, 1, 'Full Name', self._formats["center_bold"])

        for name,content in self.pops.items():
            current_row += 1
            sheet.write(current_row, 0, name)
            sheet.write(current_row, 1, content['label'])
            self._references[name] = "='%s'!%s" % (sheet.name,xlrc(current_row,0,True,True))
            self._references[content['label']] = "='%s'!%s" % (sheet.name,xlrc(current_row,1,True,True)) # Reference to the full name

    def _read_transfers(self,sheet):
        tables = read_tables(sheet)
        assert len(tables)%3==0, 'There should be 3 subtables for every transfer'
        self.transfers = []
        for i in range(0,len(tables),3):
            self.transfers.append(TimeDependentConnections.from_tables(tables[i:i+3],'transfer'))
        return

    def _write_transfers(self):
        # Writes a sheet for every transfer
        sheet = self._book.add_worksheet("Transfers")
        next_row = 0
        for transfer in self.transfers:
            next_row = transfer.write(sheet,next_row,self._formats,self._references)

    def _read_interpops(self,sheet):
        tables = read_tables(sheet)
        assert len(tables)%3==0, 'There should be 3 subtables for every transfer'
        self.interpops = []
        for i in range(0,len(tables),3):
            self.interpops.append(TimeDependentConnections.from_tables(tables[i:i+3],'interaction'))
        return

    def _write_interpops(self):
        # Writes a sheet for every
        sheet = self._book.add_worksheet("Interactions")
        next_row = 0
        for interpop in self.interpops:
            next_row = interpop.write(sheet,next_row,self._formats,self._references)

    def _write_tdve(self):
        # Writes several sheets, one for each custom page specified in the Framework
        for sheet_name,code_names in self.tdve_pages.items():
            sheet = self._book.add_worksheet(sheet_name)
            current_row = 0
            for code_name in code_names:
                current_row = self.tdve[code_name].write(sheet,current_row,self._formats,self._references)




