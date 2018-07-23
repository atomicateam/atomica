# -*- coding: utf-8 -*-
"""
Atomica data file.
Sets out a structure to store context-specific databook-imported values relating to a model.
"""

from .structure_settings import TimeDependentValuesEntry, TimeDependentConnections
from .structure import TimeSeries
import sciris.core as sc
from xlsxwriter.utility import xl_rowcol_to_cell as xlrc
import openpyxl
from .excel import standard_formats, ScirisSpreadsheet, read_tables
import xlsxwriter as xw
import io
import numpy as np
from .system import AtomicaException
from .structure_settings import DataSettings as DS

# Data maps to a databook
# On construction, we first make some blank data, and then we write a databook in the same way as if we actually had
# data values
class ProjectData(object):

    def __init__(self):
        # This is just an overview of the structure of ProjectData
        # There are two pathways to a ProjectData
        # - Could load an existing one, with ProjectData.from_spreadsheet()
        # - Could make a new one, with ProjectData.new()
        self.pops = None
        self.transfers = None
        self.interpops = None
        self.tdve = {}
        self.tdve_pages = sc.odict()

    @property
    def tvec(self):
        tdve_keys = list(self.tdve.keys())
        return self.tdve[tdve_keys[0]].tvec.copy()

    @tvec.setter
    def tvec(self, tvec):
        # Set tvec in all TDVE/TDC tables contained in the ProjectData
        for td_table in list(self.tdve.values()) + self.transfers + self.interpops:
            td_table.tvec = tvec

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

        workbook = openpyxl.load_workbook(spreadsheet.get_file(),read_only=True,data_only=True) # Load in read-write mode so that we can correctly dump the file

        for sheet in workbook.worksheets:
            if sheet.title == 'Population Definitions':
                self.read_pops(sheet)
            elif sheet.title == 'Transfers':
                self.read_transfers(sheet)
            elif sheet.title == 'Interactions':
                self.read_interpops(sheet)
            elif sheet.title == 'Metadata':
                continue
            else:
                self.tdve_pages[sheet.title] = []
                for table in read_tables(sheet):
                    tdve = TimeDependentValuesEntry.from_rows(table)

                    # If this fails, the TDVE was not found in the framework. That's a critical stop error, because the framework needs to at least declare what kind of variable this is
                    code_name = framework.get_spec_name(tdve.name)
                    tdve.allowed_units = framework.get_allowed_units(code_name)

                    self.tdve[code_name] = tdve
                    # Store the TDVE on the page it was actually on, rather than the one in the framework. Then, if users move anything around, the change will persist
                    self.tdve_pages[sheet.title].append(code_name)

        # Now do some validation
        #
        # Check that all of the TDVE/TDC tables have the same time values
        tvec = self.tvec
        for td_table in list(self.tdve.values()) + self.transfers + self.interpops:
            assert np.all(td_table.tvec == tvec)

        # Make sure that all of the quantities the Framework says we should read in have been read in
        for item_type in [DS.KEY_PARAMETER,DS.KEY_COMPARTMENT,DS.KEY_CHARACTERISTIC]:
            for item_name,spec in framework.specs[item_type].items():
                if spec['datapage_order'] != -1:
                    if item_name not in self.tdve:
                        raise AtomicaException('Databook did not find any values for "%s" (%s)' % (spec['label'],item_name))

        return self

    def read_pops(self,sheet):
        # TODO - can modify read_pops() and write_pops() if there are more population attributes
        tables = read_tables(sheet)
        assert len(tables) == 1, 'Population Definitions page should only contain one table'

        self.pops = sc.odict()
        for row in tables[0][1:]:
            self.pops[row[0].value] = {'label':row[1].value}

    def write_pops(self):
        # Writes the 'Population Definitions' sheet
        sheet = self.book.add_worksheet("Population Definitions")

        current_row = 0
        sheet.write(current_row, 0, 'Abbreviation', self.formats["center_bold"])
        sheet.write(current_row, 1, 'Full Name', self.formats["center_bold"])

        for name,content in self.pops.items():
            current_row += 1
            sheet.write(current_row, 0, name)
            sheet.write(current_row, 1, content['label'])
            self.references[name] = "='%s'!%s" % (sheet.name,xlrc(current_row,0,True,True))
            self.references[content['label']] = "='%s'!%s" % (sheet.name,xlrc(current_row,1,True,True)) # Reference to the full name

    def read_transfers(self,sheet):
        tables = read_tables(sheet)
        assert len(tables)%3==0, 'There should be 3 subtables for every transfer'
        self.transfers = []
        for i in range(0,len(tables),3):
            self.transfers.append(TimeDependentConnections.from_tables(tables[i:i+3],'transfer'))
        return

    def write_transfers(self):
        # Writes a sheet for every transfer
        sheet = self.book.add_worksheet("Transfers")
        next_row = 0
        for transfer in self.transfers:
            next_row = transfer.write(sheet,next_row,self.formats,self.references)

    def read_interpops(self,sheet):
        tables = read_tables(sheet)
        assert len(tables)%3==0, 'There should be 3 subtables for every transfer'
        self.interpops = []
        for i in range(0,len(tables),3):
            self.interpops.append(TimeDependentConnections.from_tables(tables[i:i+3],'interaction'))
        return

    def write_interpops(self):
        # Writes a sheet for every
        sheet = self.book.add_worksheet("Interactions")
        next_row = 0
        for interpop in self.interpops:
            next_row = interpop.write(sheet,next_row,self.formats,self.references)

    def write_tdve(self):
        # Writes several sheets, one for each custom page specified in the Framework
        for sheet_name,code_names in self.tdve_pages.items():
            sheet = self.book.add_worksheet(sheet_name)
            current_row = 0
            for code_name in code_names:
                current_row = self.tdve[code_name].write(sheet,current_row,self.formats,self.references)

    def to_spreadsheet(self):
        # Initialize the bytestream
        f = io.BytesIO()

        # Open a workbook
        self.book = xw.Workbook(f)
        self.formats = standard_formats(self.book)

        # Write the contents
        self.references = {} # Reset the references dict
        self.write_pops()
        self.write_transfers()
        self.write_interpops()
        self.write_tdve()

        # Close the workbook
        self.book.close()

        # Dump the file content into a ScirisSpreadsheet
        spreadsheet = ScirisSpreadsheet(f)

        # Return the spreadsheet
        return spreadsheet

    @staticmethod
    def new(framework,pops,transfers,interactions):
        # Make a brand new databook
        # pops - Can be a number, or an odict with names and labels
        # transfers - Can be a number, or an odict with names and labels
        # interactions - Can be a number, or an odict with names and labels

        return

    def add_pop(self,pop_name,pop_label):
        # Add a population with the given name and label (full name)
        assert pop_name not in self.pops, 'Population with name "%s" already exists' % (pop_name)

        self.pops[pop_name] = {'label':pop_label}
        for interaction in self.transfers+self.interpops:
            interaction.pops.append(pop_name)
        for tdve in self.tdve.values():
            default_unit = tdve.allowed_units[0] if tdve.allowed_units else None
            tdve.ts[pop_name] = TimeSeries(format=default_unit,units=default_unit)

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
        self.interpops.append(TimeDependentConnections(code_name, full_name, self.tvec, list(self.pops.keys()), type='interaction', ts=None))

    def remove_interaction(self,code_name):
        names = [x.code_name for x in self.interpops]
        idx = names.index(code_name)
        del self.interpops[idx]



