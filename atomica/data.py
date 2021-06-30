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
from .excel import cell_get_string, standard_formats, read_tables, TimeDependentValuesEntry, TimeDependentConnections, apply_widths, update_widths, validate_category
import xlsxwriter as xw
import io
import numpy as np
from .system import NotFoundError
from . import logger
from .system import FrameworkSettings as FS
from collections import defaultdict

_DEFAULT_PROVENANCE = "Framework-supplied default"

__all__ = ["ProjectData"]


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

    def __init__(self, framework):
        self.pops = sc.odict()  #: This is an odict mapping code_name:{'label':full_name, 'type':pop_type}
        self.transfers = list()  #: This stores a list of :class:`TimeDependentConnections` instances for transfers
        self.interpops = list()  #: This stores a list of :class:`TimeDependentConnections` instances for interactions
        self.tvec = None  #: This is the data's tvec used when instantiating new tables. Not _guaranteed_ to be the same for every TDVE/TDC table
        self.tdve = sc.odict()  #: This is an odict storing :class:`TimeDependentValuesEntry` instances keyed by the code name of the TDVE
        self.tdve_pages = sc.odict()  #: This is an odict mapping worksheet name to an (ordered) list of TDVE code names appearing on that sheet

        # Internal storage used with methods while writing
        self._pop_types = list(framework.pop_types.keys())  # : Store set of valid population types from framework
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
            if len(td_table.tvec) and np.amin(td_table.tvec) < start_year:
                start_year = np.amin(td_table.tvec)
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
            if len(td_table.tvec) and np.amax(td_table.tvec) > end_year:
                end_year = np.amax(td_table.tvec)
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
            x = name.split("_to_")
            code_name, from_pop = x[0].split("_", 1)
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
        :param pops: A number of populations, or a ``dict`` with either ``{name:label}`` or ``{name:{label:label,type:type}}``. Type defaults
                     to the first population type in the framework
        :param transfers: A number of transfers, or a ``dict`` with either ``{name:label}`` or ``{name:{label:label,type:type}}``.
                     The type defaults to the first population type in the framework. Transfers can only take place between populations of the
                     same type.
        :return: A new :class:`ProjectData` instance

        """

        new_pops = sc.odict()
        default_pop_type = list(framework.pop_types.keys())[0]

        if sc.isnumber(pops):
            for i in range(0, pops):
                new_pops["pop_%d" % (i)] = {"label": "Population %d" % (i), "type": default_pop_type}
        else:
            for code_name, spec in pops.items():
                if sc.isstring(spec):
                    new_pops[code_name] = {"label": spec, "type": default_pop_type}
                else:
                    new_pops[code_name] = spec

        if not new_pops:
            raise Exception("A new databook must have at least 1 population")

        new_transfers = sc.odict()
        if sc.isnumber(transfers):
            for i in range(0, transfers):
                new_transfers["transfer_%d" % (i)] = {"label": "Transfer %d" % (i), "type": default_pop_type}
        else:
            for code_name, spec in transfers.items():
                if sc.isstring(spec):
                    new_transfers[code_name] = {"label": spec, "type": default_pop_type}
                else:
                    new_transfers[code_name] = spec

        # Make all of the empty TDVE objects - need to store them by page, and the page information is in the Framework
        data = ProjectData(framework=framework)
        data.tvec = sc.promotetoarray(tvec)
        pages = defaultdict(list)  # This will store {sheet_name:(code_name,databook_order)} which will then get sorted further

        for obj_type, df in zip(["comps", "characs", "pars"], [framework.comps, framework.characs, framework.pars]):
            for _, spec in df.iterrows():
                databook_page = spec.get("databook page")
                if databook_page is not None:
                    pop_type = spec.get("population type")
                    databook_order = spec.get("databook order")
                    full_name = spec["display name"]

                    if databook_order is None:
                        order = np.inf
                    else:
                        order = databook_order
                    pages[databook_page].append((spec.name, order))
                    data.tdve[spec.name] = TimeDependentValuesEntry(full_name, data.tvec, allowed_units=[framework.get_databook_units(full_name)], comment=spec["guidance"])
                    data.tdve[spec.name].write_units = True
                    data.tdve[spec.name].write_uncertainty = True
                    if obj_type == "pars":
                        data.tdve[spec.name].write_assumption = True
                        if spec["timed"] == "y":
                            data.tdve[spec.name].tvec = []  # If parameter is timed, don't show any years
                            data.tdve[spec.name].write_uncertainty = False  # Don't show uncertainty for timed parameters. In theory users could manually add the column and sample over it, but because the duration is rounded to the timestep, it's likely to have confusing stepped effects
                    data.tdve[spec.name].pop_type = pop_type

        # Now convert pages to full names and sort them into the correct order
        for _, spec in framework.sheets["databook pages"][0].iterrows():

            if spec["datasheet code name"] in pages:
                pages[spec["datasheet code name"]].sort(key=lambda x: x[1])
                data.tdve_pages[spec["datasheet title"]] = [x[0] for x in pages[spec["datasheet code name"]]]
            else:
                data.tdve_pages[spec["datasheet title"]] = list()

        # Now, proceed to add pops, transfers, and interactions
        for code_name, spec in new_pops.items():
            data.add_pop(code_name, spec["label"], pop_type=spec["type"])

        for code_name, spec in new_transfers.items():
            data.add_transfer(code_name, spec["label"], pop_type=spec["type"])

        for _, spec in framework.interactions.iterrows():
            interpop = data.add_interaction(spec.name, spec["display name"], from_pop_type=spec["from population type"], to_pop_type=spec["to population type"])
            if "default value" in spec and np.isfinite(spec["default value"]):
                for from_pop in interpop.from_pops:
                    for to_pop in interpop.to_pops:
                        ts = TimeSeries(units=interpop.allowed_units[0])
                        ts.insert(None, spec["default value"])
                        interpop.ts[(from_pop, to_pop)] = ts
                        interpop.ts_attributes["Provenance"][(from_pop, to_pop)] = _DEFAULT_PROVENANCE

        # Finally, insert parameter and characteristic default values
        for df in [framework.comps, framework.characs, framework.pars]:
            for _, spec in df.iterrows():
                # In order to write a default value
                # - The default value should be present and not None
                # - The quantity should appear in the databook
                if "default value" in spec and np.isfinite(spec["default value"]) and spec["databook page"]:
                    tdve = data.tdve[spec.name]
                    for key, ts in tdve.ts.items():
                        ts.insert(None, spec["default value"])
                        tdve.ts_attributes["Provenance"][key] = _DEFAULT_PROVENANCE

        return data

    @staticmethod
    def from_spreadsheet(spreadsheet, framework):
        """
        Construct ProjectData from spreadsheet

        The framework is needed because the databook does not read in or otherwise store
            - The valid units for quantities
            - Which population type is associated with TDVE tables

        :param spreadsheet: The name of a spreadsheet, or a `sc.Spreadsheet`
        :param framework: A :class:`ProjectFramework` instance
        :return: A new :class:`ProjectData` instance

        """

        # Basically the strategy is going to be
        # 1. Read in all of the stuff - pops, transfers, interpops can be directly added to Data
        # 2. Read in all the other TDVE content, and then store it in the data specs according to the variable type defined in the Framework
        # e.g. the fact that 'Alive' is a Characteristic is stored in the Framework and Data but not in the Databook. So for example, we read in
        # a TDVE table called 'Alive', but it needs to be stored in data.specs['charac']['ch_alive'] and the 'charac' and 'ch_alive' are only available in the Framework

        import openpyxl

        self = ProjectData(framework=framework)

        if not isinstance(spreadsheet, sc.Spreadsheet):
            spreadsheet = sc.Spreadsheet(spreadsheet)

        workbook = openpyxl.load_workbook(spreadsheet.tofile(), read_only=True, data_only=True)  # Load in read-only mode for performance, since we don't parse comments etc.
        validate_category(workbook, "atomica:databook")

        # These sheets are optional - if none of these are provided in the databook
        # then they will remain empty
        self.transfers = list()
        self.interpops = list()

        for sheet in workbook.worksheets:

            if sheet.title.startswith("#ignore"):
                continue

            if sheet.title == "Population Definitions":
                try:
                    self._read_pops(sheet)
                except Exception as e:
                    message = 'An error was detected on the "Population Definitions" sheet'
                    raise Exception("%s -> %s" % (message, e)) from e
            elif sheet.title == "Transfers":
                try:
                    self._read_transfers(sheet)
                except Exception as e:
                    message = 'An error was detected on the "Transfers" sheet'
                    raise Exception("%s -> %s" % (message, e)) from e
            elif sheet.title == "Interactions":
                try:
                    self._read_interpops(sheet)
                except Exception as e:
                    message = 'An error was detected on the "Interactions" sheet'
                    raise Exception("%s -> %s" % (message, e)) from e
            elif sheet.title == "Metadata":
                continue
            else:
                self.tdve_pages[sheet.title] = []
                tables, start_rows = read_tables(sheet)
                for table, start_row in zip(tables, start_rows):

                    try:
                        tdve = TimeDependentValuesEntry.from_rows(table)
                    except Exception as e:
                        message = 'Error on sheet "%s" while trying to read a TDVE table starting on row %d' % (sheet.title, start_row)
                        raise Exception("%s -> %s" % (message, e)) from e

                    # If the TDVE is not in the Framework, that's a critical stop error, because the framework needs to at least declare
                    # what kind of variable this is - otherwise, we don't know the allowed units and cannot write the databook back properly
                    try:
                        spec, item_type = framework.get_variable(tdve.name)
                    except NotFoundError:
                        message = 'Error on sheet "%s" while reading TDVE table "%s" (row %d). The variable was not found in the Framework' % (sheet.title, tdve.name, start_row)
                        raise Exception(message)

                    code_name = spec.name
                    tdve.allowed_units = [framework.get_databook_units(code_name)]
                    tdve.pop_type = spec["population type"]

                    # Migrate the units (20181114)
                    # All TimeSeries instances in databook TDVE tables should have the same units as the allowed units
                    # However, if the user entered something that is wrong, we need to keep it and alert them during validation
                    # Therefore, we can migrate as long as the _old_ units made sense
                    for ts in tdve.ts.values():
                        if ts.units != tdve.allowed_units[0]:
                            if not ts.units or ts.units.strip().lower() == tdve.allowed_units[0].strip().split()[0].strip().lower():
                                ts.units = tdve.allowed_units[0]

                    if not spec["databook page"]:
                        logger.warning('A TDVE table for "%s" (%s) was read in and will be used, but the Framework did not mark this quantity as appearing in the databook', tdve.name, code_name)
                    tdve.comment = spec["guidance"]

                    if code_name in self.tdve:
                        raise Exception('A TDVE table for "%s" (%s) appears more than once in the databook. The first table was on sheet "%s" and the first duplicate table is on sheet "%s" starting on row %d' % (tdve.name, code_name, [k for k, v in self.tdve_pages.items() if code_name in v][0], sheet.title, start_row))

                    self.tdve[code_name] = tdve
                    # Store the TDVE on the page it was actually on, rather than the one in the framework. Then, if users move anything around, the change will persist
                    self.tdve_pages[sheet.title].append(code_name)

        tvals = set()
        for tdve in self.tdve.values():
            tvals.update(tdve.tvec)
        for tdc in self.transfers + self.interpops:
            tvals.update(tdc.tvec)
        self.tvec = np.array(sorted(tvals))

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
        for pop in self.pops.values():
            if pop["type"] is None:
                pop["type"] = self._pop_types[0]
            assert pop["type"] in self._pop_types, 'Error in population "%s": population type "%s" not found in framework. If the framework defines a non-default population type, then it must be explicitly specified in databooks and program books.' % (pop["label"], pop["type"])

        for obj_type, df in zip(["comps", "characs", "pars"], [framework.comps, framework.characs, framework.pars]):
            for spec_name, spec in zip(df.index, df.to_dict(orient="records")):
                if spec_name in self.pops:
                    raise Exception('Code name "%s" has been used for both a population and a framework quantity - population names must be unique' % (spec_name))

                if spec["databook page"] is not None:
                    if spec_name not in self.tdve:
                        if not np.isfinite(spec["default value"]):
                            raise Exception('The databook did not contain a required TDVE table named "%s" (code name "%s")' % (spec["display name"], spec_name))
                        else:
                            logger.warning('TDVE table "%s" (code name "%s") is missing from the databook. Using default values from the framework' % (spec["display name"], spec_name))
                            units = framework.get_databook_units(spec_name)
                            self.tdve[spec_name] = TimeDependentValuesEntry(spec["display name"], self.tvec.copy(), allowed_units=[units], comment=spec["guidance"])
                            for pop in self.pops.keys():
                                self.tdve[spec_name].ts[pop] = TimeSeries(assumption=spec["default value"], units=units)
                            tdve_page = framework.sheets["databook pages"][0][framework.sheets["databook pages"][0]["datasheet code name"] == spec["databook page"]]["datasheet title"].values[0]
                            if tdve_page in self.tdve_pages:
                                self.tdve_pages[tdve_page].append(spec_name)
                            else:
                                self.tdve_pages[tdve_page] = [spec_name]
                    else:
                        framework_units = framework.get_databook_units(spec_name)  # Get the expected databook units
                        tdve = self.tdve[spec_name]
                        tdve_sheet = self.get_tdve_page(spec_name)
                        location = 'Error in TDVE table "%s" on sheet "%s"' % (tdve.name, tdve_sheet)
                        assert tdve.pop_type in self._pop_types, '%s. Population type "%s" did not match any in the framework' % (location, tdve.pop_type)

                        required_pops = [x for x, y in self.pops.items() if y["type"] == tdve.pop_type]  # The TDVE should contain values for all populations of that type, otherwise cannot construct the ParameterSet. Check that these populations are all present
                        missing_pops = set(required_pops).difference(tdve.ts.keys())
                        if missing_pops:
                            raise Exception("%s. The following populations were not supplied but are required: %s" % (location, missing_pops))

                        for name, ts in self.tdve[spec_name].ts.items():
                            assert ts.has_data, "%s. Data values missing for %s (%s)" % (location, tdve.name, name)
                            assert ts.units is not None, "%s. Units missing for %s (%s)" % (location, tdve.name, name)
                            if ts.units.strip().lower() != framework_units.strip().lower():
                                # If the units don't match the framework's 'databook' units, see if they at least match the standard unit (for legacy databooks)
                                # For compartments and characteristics, the units must match exactly
                                if obj_type in ["comps", "characs"] or ("format" in spec and spec["format"] is not None and ts.units.lower().strip() != spec["format"].lower().strip()):
                                    assert ts.units == framework_units, '%s. Unit "%s" for %s (%s) does not match the declared units from the Framework (expecting "%s")' % (location, ts.units, tdve.name, name, framework_units)
                            if obj_type == "par" and spec["timed"] == "y":
                                assert not ts.has_time_data, "%s. Parameter %s (%s) is marked as a timed transition in the Framework, so it must have a constant value (i.e., the databook cannot contain time-dependent values for this parameter)" % (location, tdve.name, name)

        for tdc in self.interpops + self.transfers:
            if tdc.from_pop_type is None:  # Supply default pop type
                tdc.from_pop_type = self._pop_types[0]
            assert tdc.from_pop_type in self._pop_types, 'Error in transfer/interaction "%s": from population type "%s" not found in framework. If the framework defines a non-default population type, then it must be explicitly specified in databooks and program books.' % (tdc.full_name, tdc.from_pop_type)
            if tdc.to_pop_type is None:  # Supply default pop type
                tdc.to_pop_type = self._pop_types[0]
            assert tdc.to_pop_type in self._pop_types, 'Error in transfer/interaction "%s": to population type "%s" not found in framework. If the framework defines a non-default population type, then it must be explicitly specified in databooks and program books.' % (tdc.full_name, tdc.to_pop_type)

        for _, spec in framework.interactions.iterrows():
            for tdc in self.interpops:
                if tdc.code_name == spec.name:
                    for (from_pop, to_pop), ts in tdc.ts.items():
                        assert to_pop in self.pops, 'Population "%s" in "%s" not recognized. Should be one of: %s' % (to_pop, spec.name, self.pops.keys())
                        assert self.pops[to_pop]["type"] == tdc.to_pop_type, 'Interaction "%s" has to-population type "%s", but contains Population "%s", which is type "%s"' % (tdc.full_name, tdc.to_pop_type, to_pop, self.pops[to_pop]["type"])
                        assert from_pop in self.pops, 'Population "%s" in "%s" not recognized. Should be one of: %s' % (from_pop, spec.name, self.pops.keys())
                        assert self.pops[from_pop]["type"] == tdc.from_pop_type, 'Interaction "%s" has from-population type "%s", but contains Population "%s", which is type "%s"' % (tdc.full_name, tdc.from_pop_type, from_pop, self.pops[from_pop]["type"])
                        assert ts.has_data, "Data values missing for interaction %s, %s->%s" % (spec.name, to_pop, from_pop)
                        assert ts.units.lower().title() == FS.DEFAULT_SYMBOL_INAPPLICABLE.lower().title(), 'Units error in interaction %s, %s->%s. Interaction units must be "N.A."' % (spec.name, to_pop, from_pop)
                    break
            else:
                raise Exception('Required interaction "%s" not found in databook' % spec.name)

        for tdc in self.transfers:
            for (from_pop, to_pop), ts in tdc.ts.items():
                assert to_pop in self.pops, 'Population "%s" in "%s" not recognized. Should be one of: %s' % (to_pop, tdc.full.name, self.pops.keys())
                assert self.pops[to_pop]["type"] == tdc.to_pop_type, 'Transfer "%s" has population type "%s", but contains Population "%s", which is type "%s"' % (tdc.full_name, tdc.to_pop_type, to_pop, self.pops[to_pop]["type"])
                assert from_pop in self.pops, 'Population "%s" in "%s" not recognized. Should be one of: %s' % (from_pop, tdc.full.name, self.pops.keys())
                assert self.pops[from_pop]["type"] == tdc.from_pop_type, 'Transfer "%s" has population type "%s", but contains Population "%s", which is type "%s"' % (tdc.full_name, tdc.from_pop_type, from_pop, self.pops[from_pop]["type"])
                assert ts.has_data, "Data values missing for transfer %s, %s->%s" % (tdc.full_name, to_pop, from_pop)
                assert ts.units is not None, "Units are missing for transfer %s, %s->%s" % (tdc.full_name, to_pop, from_pop)
        return True

    def to_workbook(self) -> tuple:
        """
        Return an open workbook for the databook

        This allows the xlsxwriter workbook to be manipulated prior to closing the
        filestream e.g. to append extra sheets. This prevents issues related to cached
        data values when reloading a workbook to append or modify content

        Warning - the workbook is backed by a BytesIO instance and needs to be closed.
        See the usage of this method in the :meth`to_spreadsheet` function.

        :return: A tuple (bytes, workbook) with a BytesIO instance and a corresponding *open* xlsxwriter workbook instance

        """

        # Initialize the bytestream
        f = io.BytesIO()
        wb = xw.Workbook(f, {"in_memory": True})

        # Open a workbook
        self._book = wb
        self._book.set_properties({"category": "atomica:databook"})
        self._formats = standard_formats(self._book)
        self._references = {}  # Reset the references dict

        # Write the contents
        self._write_pops()
        self._write_tdve()
        self._write_interpops()
        self._write_transfers()

        # Clean internal variables related to writing the worbkook
        self._book = None
        self._formats = None
        self._references = None

        return f, wb

    def to_spreadsheet(self) -> sc.Spreadsheet:
        """
        Return content as a Sciris Spreadsheet

        :return: A :class:`sciris.Spreadsheet` instance

        """

        f, wb = self.to_workbook()
        wb.close()  # Close the workbook to flush any xlsxwriter content
        spreadsheet = sc.Spreadsheet(f)  # Wrap it in a spreadsheet instance
        return spreadsheet

    def save(self, fname) -> None:
        """
        Save databook to disk

        This function provides a shortcut to generate a spreadsheet and immediately save it to disk.

        :param fname: File name to write on disk

        """

        ss = self.to_spreadsheet()
        ss.save(fname)

    def add_pop(self, code_name: str, full_name: str, pop_type: str = None) -> None:
        """
        Add a population

        This will add a population to the databook. The population type should match
        one of the population types in the framework

        :param code_name: The code name for the new population
        :param full_name: The full name/label for the new population
        :param pop_type: String with the population type code name

        """

        if pop_type is None:
            pop_type = self._pop_types[0]
        assert pop_type in self._pop_types, 'Population type "%s" not found in framework' % (pop_type)

        code_name = code_name.strip()
        assert len(code_name) > 1, 'Population code name (abbreviation) "%s" is not valid - it must be at least two characters long' % (code_name)
        assert code_name not in self.pops, 'Population with name "%s" already exists' % (code_name)

        if code_name.lower() in FS.RESERVED_KEYWORDS:
            raise Exception('Population name "%s" is a reserved keyword' % (code_name.lower()))

        self.pops[code_name] = {"label": full_name, "type": pop_type}

        for interaction in self.transfers + self.interpops:
            if interaction.from_pop_type == pop_type:
                interaction.from_pops.append(code_name)
            if interaction.to_pop_type == pop_type:
                interaction.to_pops.append(code_name)

        for tdve in self.tdve.values():
            # Since TDVEs in databooks must have the unit set in the framework, all ts objects must share the same units
            # And, there is only supposed to be one type of unit allowed for TDVE tables (if the unit is empty, it will be 'N.A.')
            # so can just pick the first of the allowed units
            if tdve.pop_type == pop_type:
                tdve.ts[code_name] = TimeSeries(units=tdve.allowed_units[0])

    def rename_pop(self, existing_code_name: str, new_code_name: str, new_full_name: str) -> None:
        """
        Rename a population

        :param existing_code_name: Existing code name of a population
        :param new_code_name: New code name to assign
        :param new_full_name: New full name/label to assign

        """

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
        self.pops[new_code_name]["label"] = new_full_name

        # Update interactions and transfers - need to change all of the to/from tuples
        for interaction in self.transfers + self.interpops:
            idx = interaction.from_pops.index(existing_code_name)
            interaction.from_pops[idx] = new_code_name

            idx = interaction.to_pops.index(existing_code_name)
            interaction.to_pops[idx] = new_code_name

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
            interaction.to_pops.remove(pop_name)
            interaction.from_pops.remove(pop_name)

            for k in list(interaction.ts.keys()):
                if k[0] == pop_name or k[1] == pop_name:
                    del interaction.ts[k]

        for tdve in self.tdve.values():
            for k in list(tdve.ts.keys()):
                if k == pop_name:
                    del tdve.ts[k]

    def add_transfer(self, code_name: str, full_name: str, pop_type: str = None) -> TimeDependentConnections:
        """
        Add a new empty transfer

        :param code_name: The code name of the transfer to create
        :param full_name: The full name of the transfer to create
        :param pop_type: Code name of the population type. Default is first population type in the framework
        :return: Newly instantiated TimeDependentConnections object (also added to ``ProjectData.transfers``)

        """

        if pop_type is None:
            pop_type = self._pop_types[0]

        assert pop_type in self._pop_types, "Population type %s not found in framework" % (pop_type)

        for transfer in self.transfers:
            assert code_name != transfer.code_name, 'Transfer with name "%s" already exists' % (code_name)

        pop_names = [name for name, pop_spec in self.pops.items() if pop_spec["type"] == pop_type]

        # Here, need to list all relevant populations
        new_transfer = TimeDependentConnections(code_name, full_name, self.tvec, from_pops=pop_names, to_pops=pop_names, interpop_type="transfer", ts=None, from_pop_type=pop_type, to_pop_type=pop_type)
        new_transfer.write_units = True
        new_transfer.write_assumption = True
        new_transfer.write_uncertainty = True
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
    def add_interaction(self, code_name: str, full_name: str, from_pop_type: str = None, to_pop_type: str = None) -> TimeDependentConnections:
        """
        Add a new empty interaction

        Normally this method would only be manually called if a framework had been
        updated to contain a new interaction, and the databook now required updating.
        Therefore, this method would generally only be used when an interaction
        with given code name, full name, and pop type had already been added to a framework.

        :param code_name: The code name of the interaction to create
        :param full_name: The full name of the interaction to create
        :param from_pop_type: The name of a population type, which will identify the populations to be added. Default is first population type in the framework
        :param to_pop_type: The name of a population type, which will identify the populations to be added. Default is first population type in the framework
        :return: Newly instantiated TimeDependentConnections object (also added to ``ProjectData.interpops``)

        """

        if from_pop_type is None:
            from_pop_type = self._pop_types[0]
        if to_pop_type is None:
            to_pop_type = self._pop_types[0]

        assert from_pop_type in self._pop_types, "Population type %s not found in framework" % (from_pop_type)
        assert to_pop_type in self._pop_types, "Population type %s not found in framework" % (to_pop_type)

        for interaction in self.interpops:
            assert code_name != interaction.code_name, 'Interaction with name "%s" already exists' % (code_name)

        from_pops = [name for name, pop_spec in self.pops.items() if pop_spec["type"] == from_pop_type]
        to_pops = [name for name, pop_spec in self.pops.items() if pop_spec["type"] == to_pop_type]
        interpop = TimeDependentConnections(code_name, full_name, tvec=self.tvec, from_pops=from_pops, to_pops=to_pops, interpop_type="interaction", ts=None, from_pop_type=from_pop_type, to_pop_type=to_pop_type)
        interpop.write_units = True
        interpop.write_assumption = True
        interpop.write_uncertainty = True
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
        assert len(tables) == 1, "Population Definitions page should only contain one table"

        self.pops = sc.odict()
        assert cell_get_string(tables[0][0][0]).lower() == "abbreviation"
        assert cell_get_string(tables[0][0][1]).lower() == "full name"

        # If pop typ column exists, check the heading is correct
        if len(tables[0][0]) > 2:
            assert cell_get_string(tables[0][0][2]).lower() == "population type"

        for row in tables[0][1:]:

            pop_name = cell_get_string(row[0])
            assert len(pop_name) > 1, 'Population code name (abbreviation) "%s" is not valid - it must be at least two characters long' % (pop_name)

            label = cell_get_string(row[1])
            assert len(label) > 1, 'Population full name "%s" is not valid - it must be at least two characters long' % (label)

            if pop_name.lower() in FS.RESERVED_KEYWORDS:
                raise Exception('Population name "%s" is a reserved keyword' % (pop_name.lower()))

            poptype = None
            if len(row) > 2 and row[2].value is not None:
                poptype = cell_get_string(row[2])

            self.pops[pop_name] = {"label": label, "type": poptype}

    def _write_pops(self) -> None:
        """
        Writes the 'Population Definitions' sheet

        """

        sheet = self._book.add_worksheet("Population Definitions")
        sheet.set_tab_color("#FFC000")  # this tab is orange
        widths = dict()

        current_row = 0
        sheet.write(current_row, 0, "Abbreviation", self._formats["center_bold"])
        update_widths(widths, 0, "Abbreviation")
        sheet.write(current_row, 1, "Full Name", self._formats["center_bold"])
        update_widths(widths, 1, "Abbreviation")
        sheet.write(current_row, 2, "Population type", self._formats["center_bold"])
        update_widths(widths, 2, "Population type")

        for name, content in self.pops.items():
            current_row += 1
            sheet.write(current_row, 0, name, self._formats["unlocked"])
            update_widths(widths, 0, name)
            sheet.write(current_row, 1, content["label"], self._formats["unlocked"])
            update_widths(widths, 1, content["label"])
            sheet.write(current_row, 2, content["type"], self._formats["not_required"])
            update_widths(widths, 2, content["type"])

            self._references[name] = "='%s'!%s" % (sheet.name, xlrc(current_row, 0, True, True))
            self._references[content["label"]] = "='%s'!%s" % (sheet.name, xlrc(current_row, 1, True, True))  # Reference to the full name

        apply_widths(sheet, widths)

    def _read_transfers(self, sheet) -> None:
        """
        Writes the 'Transfers' sheet

        """

        tables, start_rows = read_tables(sheet)
        assert len(tables) % 3 == 0, "There should be 3 subtables for every transfer"
        self.transfers = []
        for i in range(0, len(tables), 3):
            self.transfers.append(TimeDependentConnections.from_tables(tables[i : i + 3], "transfer"))

    def _write_transfers(self) -> None:
        """
        Writes the 'Transfers' sheet

        """
        # Writes a sheet for every transfer

        # Skip if no transfers
        if not self.transfers:
            return

        sheet = self._book.add_worksheet("Transfers")
        sheet.set_tab_color("#808080")
        # sheet.hide()
        widths = dict()
        next_row = 0
        for transfer in self.transfers:
            next_row = transfer.write(sheet, next_row, self._formats, self._references, widths)
        apply_widths(sheet, widths)

    def _read_interpops(self, sheet) -> None:
        """
        Writes the 'Interactions' sheet

        """
        tables, start_rows = read_tables(sheet)
        assert len(tables) % 3 == 0, "There should be 3 subtables for every transfer"
        self.interpops = []
        for i in range(0, len(tables), 3):
            self.interpops.append(TimeDependentConnections.from_tables(tables[i : i + 3], "interaction"))
        return

    def _write_interpops(self) -> None:
        """
        Writes the 'Interactions' sheet

        """

        # Skip if no interpops
        if not self.interpops:
            return

        sheet = self._book.add_worksheet("Interactions")
        sheet.set_tab_color("#808080")
        widths = dict()
        next_row = 0
        for interpop in self.interpops:
            next_row = interpop.write(sheet, next_row, self._formats, self._references, widths)
        apply_widths(sheet, widths)

    def _write_tdve(self) -> None:
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
                next_row = self.tdve[code_name].write(sheet, next_row, self._formats, references=self._references, widths=widths)

            if has_editable_content:
                sheet.set_tab_color("#92D050")
            else:
                sheet.set_tab_color("#808080")

            apply_widths(self._book.get_worksheet_by_name(sheet_name), widths)
