"""
Implementation of Databook functionality

This module defines the :class:`ProjectData` class, which serves as a
Python-based representation of the Databook, as well as providing methods for
reading Databooks into `ProjectData` instances, and saving `ProjectData` back
to Excel files.

"""

from .utils import TimeSeries
import sciris as sc
from xlsxwriter.utility import xl_rowcol_to_cell as xlrc
import openpyxl
from .excel import cell_require_string, standard_formats, read_tables, TimeDependentValuesEntry, TimeDependentConnections, apply_widths, update_widths, validate_category
import xlsxwriter as xw
import io
import numpy as np
from .system import NotFoundError
from . import logger
from .system import FrameworkSettings as FS
from collections import defaultdict


class ProjectData(sc.prettyobj):
    """
    Store project data: class-equivalent of Databooks

    This class is used to load and work with data that is entered in databooks. It
    provides the interface for

    - Loading data
    - Modifying data (values, adding/removing populations etc.
    - Saving modified data
    - Writing new databooks

    To instantiate, the ``ProjectData`` constructor is normally not used. Instead, use
    the static methods

    - ``ProjectData.new()`` to create a new instance/databook given a :class:`ProjectFramework`
    - ``ProjectData.from_spreadsheet()`` to load a databook

    """

    def __init__(self):
        # This is just an overview of the structure of ProjectData
        # There are two pathways to a ProjectData
        # - Could load an existing one, with ProjectData.from_spreadsheet()
        # - Could make a new one, with ProjectData.new()
        self.pops = sc.odict()  #: This is an odict mapping code_name:{'label':full_name}
        self.transfers = list()  #: This stores a list of :class:`TimeDependentConnections` instances for transfers
        self.interpops = list()  #: This stores a list of :class:`TimeDependentConnections` instances for interactions
        self.tvec = None  #: This is the data's tvec used when instantiating new tables. Not _guaranteed_ to be the same for every TDVE/TDC table
        self.tdve = sc.odict()  #: This is an odict storing :class:`TimeDependentValuesEntry` instances keyed by the code name of the TDVE
        self.tdve_pages = sc.odict()  #: This is an odict mapping worksheet name to a list of TDVE code names appearing on that sheet

        # Internal storage used with methods while writing
        self._formats = None  #: Temporary storage for the Excel formatting while writing a databook
        self._book = None  #: Temporary storage for the workbook while writing a databook
        self._references = None  #: Temporary storage for cell references while writing a databook

    @property
    def start_year(self) -> float:
        """
        Return the start year from the databook

        The ProjectData start year is defined as the earliest time point in
        any of the TDVE/TDC tables (noting that it it is possible for the TDVE tables to
        have different time values). This quantity should be used when changing the simulation
        start year, if using all of the data in the databook is desired.

        :return: The earliest year in the databook

        """

        start_year = np.inf
        for td_table in list(self.tdve.values()) + self.transfers + self.interpops:
            start_year = min(start_year, np.amin(td_table.tvec))
        return start_year

    @property
    def end_year(self) -> float:
        """
        Return the start year from the databook

        The ProjectData end year is defined as the latest time point in
        any of the TDVE/TDC tables (noting that it it is possible for the TDVE tables to
        have different time values). This quantity should be used when changing the simulation
        end year, if using all of the data in the databook is desired.

        :return: The latest year in the databook

        """

        end_year = -np.inf
        for td_table in list(self.tdve.values()) + self.transfers + self.interpops:
            end_year = max(end_year, np.amax(td_table.tvec))
        return end_year

    def change_tvec(self, tvec: np.array) -> None:
        """
        Change the databook years

        This function can be used to change the time vector in all of the TDVE/TDC tables.
        There are two ways to change the time arrays:

        - Setting ``ProjectData.tvec`` directly will only affect newly added tables, and will keep existing tables
          as they are
        - Calling ``ProjectData.change_tvec()`` will modify all existing tables

        Note that the TDVE/TDC tables store time/value pairs sparsely within their :class:`TimeSeries` objects.
        Therefore, changing the time array won't modify any of the data - it will only have an effect the next time
        a databook is written (so typically this method would be called as part of preparing a modified databook).

        :param tvec: A float, list, or array containing time values (in years) for the databook

        """

        self.tvec = sc.promotetoarray(tvec).copy()
        for td_table in list(self.tdve.values()) + self.transfers + self.interpops:
            td_table.tvec = tvec

    def get_ts(self, name: str, key=None):
        """
        Extract a TimeSeries from a TDVE table or TDC table

        :param name: The code name for the container storing the :class:`TimeSeries`
                    - The code name of a transfer, interaction, or compartment/characteristic/parameter
                    - The name of a transfer parameter instantiated in model.build e.g. 'age_0-4_to_5-14'.
                    this is mainly useful when retrieving data for plotting, where variables are organized according
                    to names like 'age_0-4_to_5-14'
        :param key: Specify the identifier for the :class:`TimeSeries`
                        - If `name` is a comp/charac/par, then key should be a pop name
                        - If `name` is a transfer or interaction, then key should be a tuple (from_pop,to_pop)
                        - If `name` is the name of a model transfer parameter, then `key` should be left as `None`
        :return: A :class:`TimeSeries`, or ``None`` if there were no matches

        Regarding the specification of the key - the same transfer could be specified as

        - ``name='age', key=('0-4','5-14')``
        - ``name='age_0-4_to_5-14', key=None``

        where the former is typically used when working with data and calibrations, and the latter is used in :class:`Model` and
        is therefore encountered on the :class:`Result` and plotting side.

        """

        # Exit immediately if the name is not specified
        if not name:
            return None

        # First, check if it's the name of a TDVE
        if name in self.tdve:
            if key in self.tdve[name].ts:
                return self.tdve[name].ts[key]

        # Then, if the key is None, we are working on a transfer parameter. So reconstruct the key
        if key is None:
            x = name.split('_to_')
            code_name, from_pop = x[0].split('_', 1)
            to_pop = x[1]
            name = code_name
            key = (from_pop, to_pop)

        for tdc in self.transfers + self.interpops:
            if name == tdc.code_name:
                return tdc.ts[key]

        return None

    def get_tdve_page(self, code_name) -> str:
        """
        Given a code name for a TDVE quantity, find which page it is on

        :param code_name: The code name for a TDVE quantity
        :return: The sheet that it appears on

        """

        for sheet, content in self.tdve_pages.items():
            if code_name in content:
                return sheet
        else:
            raise NotFoundError('The quantity "%s" does not appear on any TDVE sheets' % (code_name))

    @staticmethod
    def new(framework, tvec, pops, transfers):
        """
        Make a new databook/``ProjectData`` instance

        This method should be used (instead of the standard constructor) to produce a new
        class instance (e.g. if creating a new databook).

        :param framework: A :class:`ProjectFramework` instance
        :param tvec: A scalar, list, or array of times (typically would be generated with ``numpy.arange()``)
        :param pops: A number of populations, or a dict with specific names and labels for the pops
        :param transfers: A number of transfers, or a dict with names and labels for the transfers
        :return: A new :class:`ProjectData` instance

        """

        if sc.isnumber(pops):
            new_pops = sc.odict()
            for i in range(0, pops):
                new_pops['pop_%d' % (i)] = 'Population %d' % (i)
        else:
            new_pops = pops

        if not new_pops:
            raise Exception('A new databook must have at least 1 population')

        if sc.isnumber(transfers):
            new_transfers = sc.odict()
            for i in range(0, transfers):
                new_transfers['transfer_%d' % (i)] = 'Transfer %d' % (i)
        else:
            new_transfers = transfers

        # Make all of the empty TDVE objects - need to store them by page, and the page information is in the Framework
        data = ProjectData()
        data.tvec = sc.promotetoarray(tvec)
        pages = defaultdict(list)  # This will store {sheet_name:(code_name,databook_order)} which will then get sorted further

        for df in [framework.comps, framework.characs, framework.pars]:
            for _, spec in df.iterrows():
                databook_page = spec.get('databook page')
                databook_order = spec.get('databook order')
                full_name = spec['display name']
                if databook_page is not None:
                    if databook_order is None:
                        order = np.inf
                    else:
                        order = databook_order
                    pages[databook_page].append((spec.name, order))
                    data.tdve[spec.name] = TimeDependentValuesEntry(full_name, tvec, allowed_units=[framework.get_databook_units(full_name)], comment=spec['guidance'])

        # Now convert pages to full names and sort them into the correct order
        for _, spec in framework.sheets['databook pages'][0].iterrows():

            if spec['datasheet code name'] in pages:
                pages[spec['datasheet code name']].sort(key=lambda x: x[1])
                data.tdve_pages[spec['datasheet title']] = [x[0] for x in pages[spec['datasheet code name']]]
            else:
                data.tdve_pages[spec['datasheet title']] = list()

        # Now, proceed to add pops, transfers, and interactions
        for code_name, full_name in new_pops.items():
            data.add_pop(code_name, full_name)

        for code_name, full_name in new_transfers.items():
            data.add_transfer(code_name, full_name)

        for _, spec in framework.interactions.iterrows():
            interpop = data.add_interaction(spec.name, spec['display name'])
            if 'default value' in spec and spec['default value']:
                for from_pop in interpop.pops:
                    for to_pop in interpop.pops:
                        ts = TimeSeries(units=interpop.allowed_units[0])
                        ts.insert(None, spec['default value'])
                        interpop.ts[(from_pop, to_pop)] = ts

        # Finally, insert parameter and characteristic default values
        for df in [framework.comps, framework.characs, framework.pars]:
            for _, spec in df.iterrows():
                # In order to write a default value
                # - The default value should be present and not None
                # - The quantity should appear in the databook
                if 'default value' in spec and (spec['default value'] is not None) and spec['databook page']:
                    tdve = data.tdve[spec.name]
                    for ts in tdve.ts.values():
                        ts.insert(None, spec['default value'])

        return data

    @staticmethod
    def from_spreadsheet(spreadsheet, framework):
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

        if sc.isstring(spreadsheet):
            spreadsheet = sc.Spreadsheet(spreadsheet)

        workbook = openpyxl.load_workbook(spreadsheet.tofile(), read_only=True, data_only=True)  # Load in read-only mode for performance, since we don't parse comments etc.
        validate_category(workbook, 'atomica:databook')

        # These sheets are optional - if none of these are provided in the databook
        # then they will remain empty
        self.transfers = list()
        self.interpops = list()

        for sheet in workbook.worksheets:

            if sheet.title.startswith('#ignore'):
                continue

            if sheet.title == 'Population Definitions':
                try:
                    self._read_pops(sheet)
                except Exception as e:
                    message = 'An error was detected on the "Population Definitions" sheet'
                    raise Exception('%s -> %s' % (message, e)) from e
            elif sheet.title == 'Transfers':
                try:
                    self._read_transfers(sheet)
                except Exception as e:
                    message = 'An error was detected on the "Transfers" sheet'
                    raise Exception('%s -> %s' % (message, e)) from e
            elif sheet.title == 'Interactions':
                try:
                    self._read_interpops(sheet)
                except Exception as e:
                    message = 'An error was detected on the "Interactions" sheet'
                    raise Exception('%s -> %s' % (message, e)) from e
            elif sheet.title == 'Metadata':
                continue
            else:
                self.tdve_pages[sheet.title] = []
                tables, start_rows = read_tables(sheet)
                for table, start_row in zip(tables, start_rows):

                    try:
                        tdve = TimeDependentValuesEntry.from_rows(table)
                    except Exception as e:
                        message = 'Error on sheet "%s" while trying to read a TDVE table starting on row %d' % (sheet.title, start_row)
                        raise Exception('%s -> %s' % (message, e)) from e

                    # If the TDVE is not in the Framework, that's a critical stop error, because the framework needs to at least declare
                    # what kind of variable this is - otherwise, we don't know the allowed units and cannot write the databook back properly
                    try:
                        spec, item_type = framework.get_variable(tdve.name)
                    except NotFoundError:
                        message = 'Error on sheet "%s" while reading TDVE table "%s" (row %d). The variable was not found in the Framework' % (sheet.title, tdve.name, start_row)
                        raise Exception(message)

                    code_name = spec.name
                    tdve.allowed_units = [framework.get_databook_units(code_name)]

                    # Migrate the units (20181114)
                    # All TimeSeries instances in databook TDVE tables should have the same units as the allowed units
                    # However, if the user entered something that is wrong, we need to keep it and alert them during validation
                    # Therefore, we can migrate as long as the _old_ units made sense
                    for ts in tdve.ts.values():
                        if ts.units != tdve.allowed_units[0]:
                            if not ts.units or ts.units.strip().lower() == tdve.allowed_units[0].strip().split()[0].strip().lower():
                                ts.units = tdve.allowed_units[0]

                    if not spec['databook page']:
                        logger.warning('A TDVE table for "%s" (%s) was read in and will be used, but the Framework did not mark this quantity as appearing in the databook', tdve.name, code_name)
                    tdve.comment = spec['guidance']

                    if code_name in self.tdve:
                        raise Exception('A TDVE table for "%s" (%s) appears more than once in the databook. The first table was on sheet "%s" and the first duplicate table is on sheet "%s" starting on row %d' % (tdve.name, code_name, [k for k,v in self.tdve_pages.items() if code_name in v][0], sheet.title, start_row))

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

    def validate(self, framework) -> bool:
        """
        Check if the ProjectData instance can be used to run simulations

        A databook can be 'valid' in two senses

        - The Excel file adheres to the correct syntax and it can be parsed into a ProjectData object
        - The resulting ProjectData object contains sufficient information to run a simulation

        Sometimes it is desirable for ProjectData to be valid in one sense rather than the other. For example,
        in order to run a simulation, the ProjectData needs to contain at least one value for every TDVE table.
        However, the TDVE table does _not_ need to contain values if all we want to do is add another key pop
        Thus, the first stage of validation is the ProjectData constructor - if that runs, then users can
        access methods like 'add_pop','remove_transfer' etc.

        On the other hand, to actually run a simulation, the _contents_ of the databook need to satisfy various conditions
        These tests are implemented here. The typical workflow would be that ProjectData.validate() should be used
        if a simulation is going to be run. In the first instance, this can be done in `Project.load_databook` but
        the FE might want to perform this check at a different point if the databook manipulation methods e.g.
        `add_pop` are going to be exposed in the interface

        This function throws an informative error if there are any problems identified or otherwise returns True

        :param framework: A :class:`ProjectFramework` instance to validate the data against
        :return: True if ProjectData is valid. An error will be raised otherwise

        """

        # Make sure that all of the quantities the Framework says we should read in have been read in, and that
        # those quantities all have some data values associated with them
        for df in [framework.comps, framework.characs, framework.pars]:
            for _, spec in df.iterrows():

                if spec.name in self.pops:
                    raise Exception('Code name "%s" has been used for both a population and a framework quantity - population names must be unique' % (spec.name))

                if spec['databook page'] is not None:
                    if spec.name not in self.tdve:
                        if spec['default value'] is None:
                            raise Exception('The databook did not contain a required TDVE table named "%s" (code name "%s")' % (spec['display name'], spec.name))
                        else:
                            logger.warning('TDVE table "%s" (code name "%s") is missing from the databook. Using default values from the framework' % (spec['display name'], spec.name))
                            units = framework.get_databook_units(spec.name)
                            self.tdve[spec.name] = TimeDependentValuesEntry(spec['display name'], self.tvec.copy(), allowed_units=[units], comment=spec['guidance'])
                            for pop in self.pops.keys():
                                self.tdve[spec.name].ts[pop] = TimeSeries(assumption=spec['default value'],units=units)
                            tdve_page = framework.sheets['databook pages'][0][framework.sheets['databook pages'][0]['datasheet code name'] == spec['databook page']]['datasheet title'].values[0]
                            if tdve_page in self.tdve_pages:
                                self.tdve_pages[tdve_page].append(spec.name)
                            else:
                                self.tdve_pages[tdve_page] = [spec.name]
                    else:
                        framework_units = framework.get_databook_units(spec.name)  # Get the expected databook units
                        tdve = self.tdve[spec.name]
                        tdve_sheet = self.get_tdve_page(spec.name)
                        for name, ts in self.tdve[spec.name].ts.items():
                            location = 'Error in TDVE table "%s" on sheet "%s"' % (tdve.name, tdve_sheet)
                            assert name in self.pops, '%s. Population "%s" not recognized. Should be one of: %s' % (location, name, self.pops.keys())
                            assert ts.has_data, '%s. Data values missing for %s (%s)' % (location, self.tdve[spec.name].name, name)
                            assert ts.units is not None, '%s. Units missing for %s (%s)' % (location, self.tdve[spec.name].name, name)
                            if ts.units.strip().lower() != framework_units.strip().lower():
                                # If the units don't match the framework's 'databook' units, see if they at least match the standard unit (for legacy databooks)
                                if 'format' in spec and spec['format'] is not None and ts.units.lower().strip() != spec['format'].lower().strip():
                                    assert ts.units == framework_units, '%s. Unit "%s" for %s (%s) does not match the declared units from the Framework (expecting "%s")' % (location, ts.units, self.tdve[spec.name].name, name, framework_units)

        for _, spec in framework.interactions.iterrows():
            for tdc in self.interpops:
                if tdc.code_name == spec.name:
                    for (to_pop, from_pop), ts in tdc.ts.items():
                        assert to_pop in self.pops, 'Population "%s" in "%s" not recognized. Should be one of: %s' % (to_pop, spec.name, self.pops.keys())
                        assert from_pop in self.pops, 'Population "%s" in "%s" not recognized. Should be one of: %s' % (from_pop, spec.name, self.pops.keys())
                        assert ts.has_data, 'Data values missing for interaction %s, %s->%s' % (spec.name, to_pop, from_pop)
                        assert ts.units.lower().title() == FS.DEFAULT_SYMBOL_INAPPLICABLE.lower().title(), 'Units error in interaction %s, %s->%s. Interaction units must be "N.A."' % (spec.name, to_pop, from_pop)
                    break
            else:
                raise Exception('Required interaction "%s" not found in databook' % spec.name)

        for tdc in self.transfers:
            for (to_pop, from_pop), ts in tdc.ts.items():
                assert to_pop in self.pops, 'Population "%s" in "%s" not recognized. Should be one of: %s' % (to_pop, tdc.full.name, self.pops.keys())
                assert from_pop in self.pops, 'Population "%s" in "%s" not recognized. Should be one of: %s' % (from_pop, tdc.full.name, self.pops.keys())
                assert ts.has_data, 'Data values missing for transfer %s, %s->%s' % (tdc.full_name, to_pop, from_pop)
                assert ts.units is not None, 'Units are missing for transfer %s, %s->%s' % (tdc.full_name, to_pop, from_pop)
        return True

    def to_spreadsheet(self, write_uncertainty=None):
        """
        Return content as an :class:`AtomicaSpreadsheet`

        :param write_uncertainty: If True, uncertainty cells will always be printed.
                                  If None, cells will be printed only for TDVEs with uncertainty values.
                                  IF False, cells will not be shown at all even if data existed
        :return: An :class:`AtomicaSpreadsheet` instance

        """

        # Initialize the bytestream
        f = io.BytesIO()

        # Open a workbook
        self._book = xw.Workbook(f)
        self._book.set_properties({'category': 'atomica:databook'})
        self._formats = standard_formats(self._book)
        self._references = {}  # Reset the references dict

        # Write the contents
        self._write_pops()
        self._write_tdve(write_uncertainty=write_uncertainty)
        self._write_interpops(write_uncertainty=write_uncertainty)
        self._write_transfers(write_uncertainty=write_uncertainty)

        # Close the workbook
        self._book.close()

        # Dump the file content into a ScirisSpreadsheet
        spreadsheet = sc.Spreadsheet(f)

        # Clear everything
        f.close()
        self._book = None
        self._formats = None
        self._references = None

        # Return the spreadsheet
        return spreadsheet

    def save(self, fname, write_uncertainty=None) -> None:
        """
        Save databook to disk

        This function provides a shortcut to generate a spreadsheet and immediately save it to disk.

        :param fname: File name to write on disk
        :param write_uncertainty: If True, uncertainty cells will always be printed.
                                  If None, cells will be printed only for TDVEs with uncertainty values.
                                  IF False, cells will not be shown at all even if data existed

        """

        ss = self.to_spreadsheet(write_uncertainty=write_uncertainty)
        ss.save(fname + '.xlsx' if not fname.endswith('.xlsx') else fname)

    def add_pop(self, code_name, full_name):
        # Add a population with the given name and label (full name)
        code_name = code_name.strip()
        assert len(code_name) > 1, 'Population code name (abbreviation) "%s" is not valid - it must be at least two characters long' % (code_name)
        assert code_name not in self.pops, 'Population with name "%s" already exists' % (code_name)

        if code_name.lower() in FS.RESERVED_KEYWORDS:
            raise Exception('Population name "%s" is a reserved keyword' % (code_name.lower()))

        self.pops[code_name] = {'label': full_name}
        for interaction in self.transfers + self.interpops:
            interaction.pops.append(code_name)
        for tdve in self.tdve.values():
            # Since TDVEs in databooks must have the unit set in the framework, all ts objects must share the same units
            # And, there is only supposed to be one type of unit allowed for TDVE tables (if the unit is empty, it will be 'N.A.')
            # so can just pick the first of the allowed units
            tdve.ts[code_name] = TimeSeries(units=tdve.allowed_units[0])

    def rename_pop(self, existing_code_name, new_code_name, new_full_name):
        # Rename an existing pop
        existing_code_name = existing_code_name.strip()
        new_code_name = new_code_name.strip()
        assert len(new_code_name) > 1, 'New population code name (abbreviation) "%s" is not valid - it must be at least two characters long' % (new_code_name)

        assert existing_code_name in self.pops, 'A population with code name "%s" is not present' % (existing_code_name)
        assert new_code_name not in self.pops, 'Population with name "%s" already exists' % (new_code_name)

        if new_code_name.lower() in FS.RESERVED_KEYWORDS:
            raise Exception('Population name "%s" is a reserved keyword' % (new_code_name.lower()))

        # First change the name of the key
        self.pops.rename(existing_code_name, new_code_name)

        # Then change the full name
        self.pops[new_code_name]['label'] = new_full_name

        # Update interactions and transfers - need to change all of the to/from tuples
        for interaction in self.transfers + self.interpops:
            idx = interaction.pops.index(existing_code_name)
            interaction.pops[idx] = new_code_name
            for from_pop, to_pop in interaction.ts.keys():
                if to_pop == existing_code_name and from_pop == existing_code_name:
                    interaction.ts.rename((from_pop, to_pop), (new_code_name, new_code_name))
                elif from_pop == existing_code_name:
                    interaction.ts.rename((from_pop, to_pop), (new_code_name, to_pop))
                elif to_pop == existing_code_name:
                    interaction.ts.rename((from_pop, to_pop), (from_pop, new_code_name))

        # Update TDVE tables
        for tdve in self.tdve.values():
            if existing_code_name in tdve.ts:
                tdve.ts.rename(existing_code_name, new_code_name)

    def remove_pop(self, pop_name):
        # Remove population with given code name
        del self.pops[pop_name]

        for interaction in self.transfers + self.interpops:
            interaction.pops.remove(pop_name)
            for k in list(interaction.ts.keys()):
                if k[0] == pop_name or k[1] == pop_name:
                    del interaction.ts[k]

        for tdve in self.tdve.values():
            for k in list(tdve.ts.keys()):
                if k == pop_name:
                    del tdve.ts[k]

    def add_transfer(self, code_name: str, full_name: str) -> TimeDependentConnections:
        """
        Add a new empty transfer

        :param code_name: The code name of the transfer to create
        :param full_name: The full name of the transfer to create
        :return: Newly instantiated TimeDependentConnections object (also added to ``ProjectData.transfers``)

        """

        for transfer in self.transfers:
            assert code_name != transfer.code_name, 'Transfer with name "%s" already exists' % (code_name)

        new_transfer = TimeDependentConnections(code_name, full_name, self.tvec, list(self.pops.keys()), type='transfer', ts=None)
        self.transfers.append(new_transfer)
        return new_transfer

    def rename_transfer(self, existing_code_name: str, new_code_name: str, new_full_name: str) -> None:
        """
        Rename an existing transfer

        :param existing_code_name: The existing code name to change
        :param new_code_name: The new code name
        :param new_full_name: The new full name

        """

        # Check no name collisions
        for transfer in self.transfers:
            assert new_code_name != transfer.code_name, 'Transfer with name "%s" already exists' % (new_code_name)

        # Find the transfer to change
        for transfer in self.transfers:
            if existing_code_name == transfer.code_name:
                transfer_to_change = transfer
                break
        else:
            raise NotFoundError('Transfer with name "%s" was not found' % (existing_code_name))

        # Modify it
        transfer_to_change.code_name = new_code_name
        transfer_to_change.full_name = new_full_name

    def remove_transfer(self, code_name: str) -> None:
        """
        Remove a transfer

        :param code_name: Code name of the transfer to remove
        """

        names = [x.code_name for x in self.transfers]
        idx = names.index(code_name)
        del self.transfers[idx]

    # NB. Differences in the model will only happen if the model knows what to do with the new interaction
    def add_interaction(self, code_name: str, full_name: str) -> TimeDependentConnections:
        """
        Add a new empty interaction

        :param code_name: The code name of the interaction to create
        :param full_name: The full name of the interaction to create
        :return: Newly instantiated TimeDependentConnections object (also added to ``ProjectData.interpops``)

        """

        for interaction in self.interpops:
            assert code_name != interaction.code_name, 'Interaction with name "%s" already exists' % (code_name)
        interpop = TimeDependentConnections(code_name, full_name, self.tvec, list(self.pops.keys()), type='interaction', ts=None)
        self.interpops.append(interpop)
        return interpop

    def remove_interaction(self, code_name: str) -> None:
        """
        Remove an interaction

        :param code_name: Code name of the interaction to remove
        """

        names = [x.code_name for x in self.interpops]
        idx = names.index(code_name)
        del self.interpops[idx]

    def _read_pops(self, sheet) -> None:
        """
        Reads the 'Population Definitions' sheet

        """

        # TODO - can modify _read_pops() and _write_pops() if there are more population attributes
        tables = read_tables(sheet)[0]
        assert len(tables) == 1, 'Population Definitions page should only contain one table'

        self.pops = sc.odict()
        cell_require_string(tables[0][0][0])
        cell_require_string(tables[0][0][1])
        assert tables[0][0][0].value.strip().lower() == 'abbreviation'
        assert tables[0][0][1].value.strip().lower() == 'full name'

        for row in tables[0][1:]:
            cell_require_string(row[0])
            cell_require_string(row[1])
            pop_name = row[0].value.strip()
            assert len(pop_name) > 1, 'Population code name (abbreviation) "%s" is not valid - it must be at least two characters long' % (pop_name)

            if pop_name.lower() in FS.RESERVED_KEYWORDS:
                raise Exception('Population name "%s" is a reserved keyword' % (pop_name.lower()))
            self.pops[pop_name] = {'label': row[1].value.strip()}

    def _write_pops(self) -> None:
        """
        Writes the 'Population Definitions' sheet

        """

        sheet = self._book.add_worksheet("Population Definitions")
        sheet.set_tab_color('#FFC000')  # this tab is orange
        widths = dict()

        current_row = 0
        sheet.write(current_row, 0, 'Abbreviation', self._formats["center_bold"])
        update_widths(widths, 0, 'Abbreviation')
        sheet.write(current_row, 1, 'Full Name', self._formats["center_bold"])
        update_widths(widths, 1, 'Abbreviation')

        for name, content in self.pops.items():
            current_row += 1
            sheet.write(current_row, 0, name, self._formats['unlocked'])
            update_widths(widths, 0, name)
            sheet.write(current_row, 1, content['label'], self._formats['unlocked'])
            update_widths(widths, 1, content['label'])
            self._references[name] = "='%s'!%s" % (sheet.name, xlrc(current_row, 0, True, True))
            self._references[content['label']] = "='%s'!%s" % (sheet.name, xlrc(current_row, 1, True, True))  # Reference to the full name

        apply_widths(sheet, widths)

    def _read_transfers(self, sheet) -> None:
        """
        Writes the 'Transfers' sheet

        """

        tables, start_rows = read_tables(sheet)
        assert len(tables) % 3 == 0, 'There should be 3 subtables for every transfer'
        self.transfers = []
        for i in range(0, len(tables), 3):
            self.transfers.append(TimeDependentConnections.from_tables(tables[i:i + 3], 'transfer'))

    def _write_transfers(self, write_uncertainty) -> None:
        """
        Writes the 'Transfers' sheet

        """
        # Writes a sheet for every transfer

        # Skip if no transfers
        if not self.transfers:
            return

        sheet = self._book.add_worksheet("Transfers")
        sheet.set_tab_color('#808080')
        # sheet.hide()
        widths = dict()
        next_row = 0
        for transfer in self.transfers:
            next_row = transfer.write(sheet, next_row, self._formats, self._references, widths, write_units=True, write_assumption=True, write_uncertainty=write_uncertainty)
        apply_widths(sheet, widths)

    def _read_interpops(self, sheet) -> None:
        """
        Writes the 'Interactions' sheet

        """
        tables, start_rows = read_tables(sheet)
        assert len(tables) % 3 == 0, 'There should be 3 subtables for every transfer'
        self.interpops = []
        for i in range(0, len(tables), 3):
            self.interpops.append(TimeDependentConnections.from_tables(tables[i:i + 3], 'interaction'))
        return

    def _write_interpops(self, write_uncertainty) -> None:
        """
        Writes the 'Interactions' sheet

        """

        # Skip if no interpops
        if not self.interpops:
            return

        sheet = self._book.add_worksheet("Interactions")
        sheet.set_tab_color('#808080')
        widths = dict()
        next_row = 0
        for interpop in self.interpops:
            next_row = interpop.write(sheet, next_row, self._formats, self._references, widths, write_units=True, write_assumption=True, write_uncertainty=write_uncertainty)
        apply_widths(sheet, widths)

    def _write_tdve(self, write_uncertainty) -> None:
        """
        Writes the TDVE tables

        This method will create multiple sheets, one for each custom page specified
        in the Framework.

        """


        for sheet_name, code_names in self.tdve_pages.items():
            sheet = self._book.add_worksheet(sheet_name)
            widths = dict()

            next_row = 0
            has_editable_content = False
            for code_name in code_names:
                has_editable_content = has_editable_content or (not self.tdve[code_name].has_data)  # there is editable content if any TDVE is missing data, so blue cells are present
                next_row = self.tdve[code_name].write(sheet, next_row, self._formats, references=self._references, widths=widths, write_units=True, write_assumption=True, write_uncertainty=write_uncertainty)

            if has_editable_content:
                sheet.set_tab_color('#92D050')
            else:
                sheet.set_tab_color('#808080')

            apply_widths(self._book.get_worksheet_by_name(sheet_name), widths)
