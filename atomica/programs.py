"""
Classes for implementing Programs

This module principally defines the Program and ProgramSet classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

"""

import io
from datetime import timezone

import numpy as np
import xlsxwriter as xw
from numpy import inf, array, exp
from xlsxwriter.utility import xl_rowcol_to_cell as xlrc

import sciris as sc
from .excel import standard_formats, apply_widths, update_widths, read_tables, TimeDependentValuesEntry, validate_category
from .system import logger, FrameworkSettings as FS
from .utils import NamedItem, TimeSeries
from .version import version, gitinfo

__all__ = ["ProgramInstructions", "ProgramSet", "Program", "Covout"]


class ProgramInstructions:
    """
    Store instructions for applying programs

    A :class:`ProgramSet` contains a Python representation of the program book, with
    a collection of programs, their effects, and quantities like historical spending.
    However, to run a simulation with programs, additional information is required - for
    example, which year to switch from databook parameters to program-computed parameters.
    This type of information is specific to the simulation being run, rather than being an
    intrinsic property of a set of programs. Therefore, that information is stored in
    a :class:`ProgramInstructions` instance.

    At minimum, the :class:`ProgramInstructions` must contain the year to turn on programs.
    It can also optionally contain the year to turn off programs. In addition to the start/stop
    years, the :class:`ProgramInstructions` also contains any overwrites that should be applied
    to

    - Spending (in units of people/year)
    - Capacity (in units of people/year)
    - Fraction/proportion coverage
        - For continuous programs, specified as a dimensionless fraction
        - For one-off programs, specified as a 'fraction/year' coverage

    which thus provides the underlying implementation for program-related scenarios. The
    :class:`ProgramSet` and :class:`Program` methods access and use the :class:`ProgramInstructions`
    instances. The overwrites for spending in particular are widely used - for example, budget
    optimization is a mapping from one set of :class:`ProgramInstructions` to another, and thus
    during optimization, :class:`ProgramInstructions` instances are used to test different allocations.

    Note that the program calculation proceeds by

    1. Using spending and unit cost to compute capacity
    2. Using capacity and the compartment sizes to compute fractional coverage
    3. Using fractional coverage to compute program outcomes

    Overwrites to each quantity (spending, capacity, coverage) are applied at their
    respective stages, so if the :class:`ProgramInstructions` contains more than one
    type of overwrite, they will be applied in this same order (and later stages
    will take precedence e.g. if both capacity and coverage are overwritten, it will be
    the coverage overwrite that impacts the final parameter value).

    Finally, for simplicity, if an overwrite is provided, it entirely replaces the values
    in the program book, in contrast to parameter scenarios, which contain more complex logic
    for interpolating between databook and scenario values.

    :param start_year: Year to switch to program-calculated parameters
    :param stop_year: Year to switch back to databook parameters
    :param alloc: The allocation. It can be
              - A dict keyed by program name, containing a scalar spend, or a TimeSeries of spending values. If the spend is
                scalar, it will be assigned to the start year
              - A ProgramSet instance, in which case an allocation will be assigned by interpolating the ProgramSet's
                spending onto the program start year. This is a shortcut to ensure that budget scenarios and optimizations
                where spending is specified in future years ramp correctly from the program start year (and not the last year
                that data was entered for)
    :param capacity: Overwrites to capacity. This is a dict keyed by program name, containing a scalar capacity or a TimeSeries of capacity values
                     For convenience, the capacity overwrite should be in units of 'people/year' and it will be automatically
                     converted to a per-timestep value based on the units for the program's unit cost.
    :param coverage: Overwrites to proportion coverage. This is a dict keyed by program name, containing a scalar coverage or a TimeSeries
                     of coverage values. The overwrite is specified in dimensionless units for continuous programs, and '/year' units for
                     one-off programs.

    """

    def __init__(self, start_year: float, stop_year: float = None, alloc=None, coverage: dict = None, capacity: dict = None):
        self.start_year = start_year
        self.stop_year = stop_year if stop_year else inf

        self.alloc = sc.odict()
        if isinstance(alloc, ProgramSet):
            for prog in alloc.programs.values():
                self.alloc[prog.name] = TimeSeries(t=self.start_year, vals=prog.spend_data.interpolate(self.start_year, method="previous"))
        elif alloc:
            for prog_name, spending in alloc.items():
                if isinstance(spending, TimeSeries) and spending.has_data:
                    self.alloc[prog_name] = sc.dcp(spending)
                elif spending is not None:
                    self.alloc[prog_name] = TimeSeries(t=self.start_year, vals=spending)

        self.capacity = sc.odict()  # Dict keyed by program name that stores a time series of capacities
        if capacity:
            for prog_name, vals in capacity.items():
                if isinstance(vals, TimeSeries):
                    self.capacity[prog_name] = sc.dcp(vals)
                else:
                    self.capacity[prog_name] = TimeSeries(t=self.start_year, vals=vals)

        self.coverage = sc.odict()  # Dict keyed by program name that stores a time series of coverages

        if coverage:
            for prog_name, vals in coverage.items():
                if isinstance(vals, TimeSeries):
                    self.coverage[prog_name] = sc.dcp(vals)
                else:
                    self.coverage[prog_name] = TimeSeries(t=self.start_year, vals=vals)

    def scale_alloc(self, scale_factor: float) -> None:
        """
        Scale allocation by a constant

        This method multiplies the budget by a constant to scale the total budget up or down.
        The scale factor is applied at all time points.

        :param scale_factor: Multiplicative factor for spending
        :return: A new, scaled copy of the instructions

        """
        assert scale_factor >= 0, "Cannot have a negative scale factor"
        new = sc.dcp(self)
        for ts in new.alloc.values():
            ts.vals = [x * scale_factor for x in ts.vals]
            ts.assumption = ts.assumption * scale_factor if ts.assumption is not None else None
            ts.sigma = ts.sigma * scale_factor if ts.sigma is not None else None
        return new


class ProgramSet(NamedItem):
    """
    Representation of a single program

    A ProgramSet object is the code representation of a program book. It provides an interface for reading and
    writing the program book, as well as retrieving program outcomes (due to interactions between programs, they
    must be computed using the entire collection of programs).

    :param name: Optionally specify the name of the ProgramSet
    :param tvec: Optionally specify the years for data entry

    """

    def __init__(self, name="default", framework=None, data=None, tvec=None):

        assert framework is not None, "Must specify framework and data when instantiating a ProgramSet"
        assert data is not None, "Must specify framework and data when instantiating a ProgramSet"

        NamedItem.__init__(self, name)
        self.version = version  # Track versioning information for the result. This might change due to migration (whereas by convention, the model version does not)
        self.gitinfo = gitinfo

        self.tvec = tvec  # This is the data tvec that will be used when writing the progset to a spreadsheet

        # Programs and effects
        self.programs = sc.odict()  # Stores the information on the 'targeting' and 'spending data' sheet
        self.covouts = sc.odict()  # Stores the information on the 'program effects' sheet

        # Populations, parameters, and compartments - these are all the available ones printed when writing a progbook
        # They are all of the form {code_name:{'label':full_name, 'type':pop_type}}
        self.pops = sc.dcp(data.pops)  # ProjectData already stores dicts with 'label' and 'type' keys

        # Get comps from framework
        self.comps = sc.odict()
        for _, spec in framework.comps.iterrows():
            if spec["is source"] == "y" or spec["is sink"] == "y" or spec["is junction"] == "y":
                self.comps[spec.name] = {"label": spec["display name"], "type": spec["population type"], "non_targetable": True}
            else:
                self.comps[spec.name] = {"label": spec["display name"], "type": spec["population type"], "non_targetable": False}

        # Get pars from framework
        self.pars = sc.odict()
        for _, spec in framework.pars.iterrows():
            if spec["targetable"] == "y":
                self.pars[spec.name] = {"label": spec["display name"], "type": spec["population type"]}

        self._pop_types = list(framework.pop_types.keys())

        # Metadata
        self.created = sc.now(utc=True)
        self.modified = sc.now(utc=True)
        self.currency = "$"  # The symbol for currency that will be used in the progbook

        # Internal caches
        self._book = None
        self._formats = None
        self._references = None

    def __setstate__(self, d):
        from .migration import migrate

        self.__dict__ = d
        progset = migrate(self)
        self.__dict__ = progset.__dict__

    def __repr__(self):
        output = sc.prepr(self)
        output += "    Program set name: %s\n" % self.name
        output += "            Programs: %s\n" % [prog for prog in self.programs]
        output += "        Date created: %s\n" % sc.getdate(self.created.replace(tzinfo=timezone.utc).astimezone(tz=None), dateformat="%Y-%b-%d %H:%M:%S %Z")
        output += "       Date modified: %s\n" % sc.getdate(self.modified.replace(tzinfo=timezone.utc).astimezone(tz=None), dateformat="%Y-%b-%d %H:%M:%S %Z")
        output += "============================================================\n"
        return output

    def _get_code_name(self, name: str) -> str:
        """
        Return code name given code or full name

        This function converts the input name to a code name, thereby allowing operations
        like removing pops/comps/pars/progs to be performed by code name or by full name

        Code names are unique because they key the program dictionary. Full names are likely unique
        but may not be. Code names will be returned as-is so take precedence over full names. For example,
        if you have a program with a particular code name, and other programs with that same name used as
        the full name, this method will return the program with the matching code name.

        :param name: A code name or full name
        :return: A code name

        """

        if name in self.pars or name in self.comps or name in self.pops or name in self.programs:
            return name

        for code_name, spec in self.pops.items():
            if name == spec["label"]:
                return code_name

        for code_name, spec in self.comps.items():
            if name == spec["label"]:
                return code_name

        for code_name, spec in self.pars.items():
            if name == spec["label"]:
                return code_name

        for prog in self.programs.values():
            if name == prog.label:
                return prog.name

        raise Exception('Could not find full name for quantity "%s" (n.b. this is case sensitive)' % (name))

    def add_program(self, code_name: str, full_name: str) -> None:
        """
        Add a program to the ProgramSet

        :param code_name: The code name of the new program
        :param full_name: The full name of the new program

        """
        # To add a program, we just need to construct one
        prog = Program(name=code_name, label=full_name, currency=self.currency)
        if prog.name in self.programs:
            raise Exception('Program with name "%s" is already present in the ProgramSet' % (prog.name))
        self.programs[prog.name] = prog

    def remove_program(self, name: str) -> None:
        """
        Remove a program from the ProgramSet

        :param name: The code name or full name of the program to remove

        """
        # Remove the program from the progs dict
        code_name = self._get_code_name(name)

        del self.programs[code_name]
        # Remove affected covouts
        for par in self.pars:
            for pop in self.pops:
                if (par, pop) in self.covouts and code_name in self.covouts[(par, pop)].progs:
                    del self.covouts[(par, pop)].progs[code_name]

    def add_pop(self, code_name: str, full_name: str, pop_type: str = None) -> None:
        """
        Add a population to the ``ProgramSet``

        At this level, we can add any arbitrarily named population. When the progbook is loaded in,
        the populations contained in the ``ProgramSet`` will be validated against the specified ProjectData
        instance.

        :param code_name: The code name of the new population
        :param full_name: The full name of the new population

        """

        if pop_type is None:
            pop_type = self._pop_types[0]

        self.pops[code_name] = {"label": full_name, "type": pop_type}

    def remove_pop(self, name: str) -> None:
        """
        Remove a population from the ``ProgramSet``

        This method will remove the population from the ProgramSet, as well as
        from all program target pops and will also remove the covout objects
        for the affected population.

        :param name: Code name or full name of the population to remove

        """

        code_name = self._get_code_name(name)

        for prog in self.programs.values():
            if code_name in prog.target_pops:
                prog.target_pops.remove(code_name)
            if (prog.name, code_name) in self.covouts:
                self.covouts.pop((prog.name, code_name))

        del self.pops[code_name]

    def add_comp(self, code_name: str, full_name: str, pop_type: str = None) -> None:
        """
        Add a compartment

        The primary use case would be when an existing project has a change made to the framework and it's
        desired to update an already filled out program book.

        :param code_name: Code name of the compartment to add
        :param full_name: Full name of the compartment to add

        """
        if pop_type is None:
            pop_type = self._pop_types[0]

        self.comps[code_name] = {"label": full_name, "type": pop_type}

    def remove_comp(self, name: str) -> None:
        """
        Remove a compartment

        The primary use case would be when an existing project has a change made to the framework and it's
        desired to update an already filled out program book.

        Note that removing a compartment also requires removing it as a target compartment from all
        programs, which is automatically handled by this method.

        :param code_name: Code name or full name of the compartment to remove

        """

        code_name = self._get_code_name(name)

        for prog in self.programs.values():
            if code_name in prog.target_comps:
                prog.target_comps.remove(code_name)
        del self.comps[code_name]

    def add_par(self, code_name: str, full_name: str, pop_type: str = None) -> None:
        """
        Add a parameter

        The primary use case would be when an existing project has a change made to the framework and it's
        desired to update an already filled out program book.

        :param code_name: Code name of the parameter to add
        :param full_name: Full name of the parameter to add
        :param pop_type: Code name of the population type

        """

        if pop_type is None:
            pop_type = self._pop_types[0]

        # add an impact parameter
        # a new impact parameter won't have any covouts associated with it, and no programs will be bound to it
        # So all we have to do is add it to the list
        self.pars[code_name] = {"label": full_name, "type": pop_type}

    def remove_par(self, name: str) -> None:
        """
        Remove a parameter

        The primary use case would be when an existing project has a change made to the framework and it's
        desired to update an already filled out program book.

        Note that removing a parameter also requires removing all of the :class:`Covout` instances associated with it.

        :param name: Code name or full name of the parameter to remove

        """

        code_name = self._get_code_name(name)

        for pop in self.pops:
            if (code_name, pop) in self.covouts:
                del self.covouts[(code_name, pop)]
        del self.pars[code_name]

    #######################################################################################################
    # Methods for data I/O
    #######################################################################################################

    @staticmethod
    def _normalize_inputs(framework, data, project) -> tuple:
        """
        Normalize constructor inputs

        A :class:`ProjectFramework` is constructed against a particular framework
        and data. For convenience, these can be specified by passing in a Project
        containing the framework and data. This function takes in all of the inputs
        provided to the constructor (whether making a blank instance or reading a
        spreadsheet) and returns the framework and data. The order of precedence is

        - If separate framework or data is provided, it will be used
        - Otherwise, they will be drawn from the project

        So for example, a project and data could be provided, in which case the framework
        would come from the project and the data would come from the explicit argument
        (even if the project also contained data).

        :param framework: Optionally a :class:`ProjectFramework` instance
        :param data: Optionally a :class:`ProjectData` instance
        :param project: Optionally a :class:`Project` instance
        :return: Tuple containing ``(framework,data)``

        """

        if (framework is None and project is None) or (data is None and project is None):
            errormsg = "To read in a ProgramSet, please supply one of the following sets of inputs: (a) a Framework and a ProjectData, (b) a Project."
            raise Exception(errormsg)

        if framework is None:
            if project.framework is None:
                errormsg = "A Framework was not provided, and the Project has not been initialized with a Framework"
                raise Exception(errormsg)
            else:
                framework = project.framework

        if data is None:
            if project.data is None:
                errormsg = "Project data has not been loaded yet"
                raise Exception(errormsg)
            else:
                data = project.data

        return framework, data

    @staticmethod
    def from_spreadsheet(spreadsheet=None, framework=None, data=None, project=None, name=None, _allow_missing_data=False):
        """
        Instantiate a ProgramSet from a spreadsheet

        To load a spreadsheet, need to either pass in

            - A Project containing a framework and data
            - ProjectFramework and ProjectData instances without a project

        :param spreadsheet: A string file path, or an sc.Spreadsheet
        :param framework: A :py:class:`ProjectFramework` instance
        :param data: A :py:class:`ProjectData` instance
        :param project: A :py:class:`Project` instance
        :param name: Optionally specify the name of the ProgramSet to create
        :param _allow_missing_data: Internal only - optionally allow missing unit costs and spending (used for loading template progbook files)
        :return: A :class:`ProgramSet`

        """
        import openpyxl

        framework, data = ProgramSet._normalize_inputs(framework, data, project)

        # Populate the available pops, comps, and pars based on the framework and data provided at this step
        self = ProgramSet(name=name, framework=framework, data=data)

        # Create and load spreadsheet
        if not isinstance(spreadsheet, sc.Spreadsheet):
            spreadsheet = sc.Spreadsheet(spreadsheet)

        workbook = openpyxl.load_workbook(spreadsheet.tofile(), read_only=True, data_only=True)  # Load in read-only mode for performance, since we don't parse comments etc.
        validate_category(workbook, "atomica:progbook")

        # Load individual sheets
        self._read_targeting(workbook["Program targeting"], framework=framework)
        self._read_spending(workbook["Spending data"], _allow_missing_data=_allow_missing_data)
        self._read_effects(workbook["Program effects"], framework=framework, data=data)

        return self

    def to_workbook(self) -> tuple:
        """
        Return an open workbook for the ProgramSet

        This allows the xlsxwriter workbook to be manipulated prior to closing the
        filestream e.g. to append extra sheets. This prevents issues related to cached
        data values when reloading a workbook to append or modify content

        Warning - the workbook is backed by a BytesIO instance and needs to be closed.
        See the usage of this method in the :meth`to_spreadsheet` function.

        :return: A tuple (bytes, workbook) with a BytesIO instance and a corresponding *open* xlsxwriter workbook instance

        """
        f = io.BytesIO()  # Write to this binary stream in memory
        wb = xw.Workbook(f)

        self._book = wb
        self._book.set_properties({"category": "atomica:progbook"})
        self._formats = standard_formats(self._book)
        self._references = {}  # Reset the references dict

        self._write_targeting()
        self._write_spending()
        self._write_effects()

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

    def save(self, fname):
        ss = self.to_spreadsheet()
        ss.save(fname)

    def _read_targeting(self, sheet, framework) -> None:
        # This function reads a targeting sheet and instantiates all of the programs with appropriate targets, putting them
        # into `self.programs`
        tables, start_rows = read_tables(sheet)  # NB. only the first table will be read, so there can be other tables for comments on the first page
        self.programs = sc.odict()
        sup_header = [x.value.lower().strip() if sc.isstring(x.value) else x.value for x in tables[0][0]]
        headers = [x.value.lower().strip() if sc.isstring(x.value) else x.value for x in tables[0][1]]

        # Get the indices where the pops and comps start
        pop_start_idx = sup_header.index("targeted to (populations)")
        comp_start_idx = sup_header.index("targeted to (compartments)")

        # Check the first two columns are as expected
        assert headers[0] == "abbreviation"
        assert headers[1] == "display name"

        # Now, prepare the pop and comp lookups
        pop_idx = dict()  # Map table index to pop full name
        for i in range(pop_start_idx, comp_start_idx):
            if headers[i]:
                pop_idx[i] = headers[i]

        comp_idx = dict()  # Map table index to comp full name
        for i in range(comp_start_idx, len(headers)):
            if headers[i]:
                comp_idx[i] = headers[i]

        pop_codenames = {v["label"].lower().strip(): x for x, v in self.pops.items()}
        comp_codenames = {v["label"].lower().strip(): x for x, v in self.comps.items()}

        for row in tables[0][2:]:  # For each program to instantiate
            target_pops = []
            target_comps = []

            for i in range(pop_start_idx, comp_start_idx):
                if row[i].value and sc.isstring(row[i].value) and row[i].value.lower().strip() == "y":
                    if pop_idx[i] not in pop_codenames:
                        message = "There was a mismatch between the populations in the databook and the populations in the program book"
                        message += '\nThe program book contains population "%s", while the databook contains: %s' % (pop_idx[i], [str(x) for x in pop_codenames.keys()])
                        raise Exception(message)

                    target_pops.append(pop_codenames[pop_idx[i]])  # Append the pop's codename

            for i in range(comp_start_idx, len(headers)):
                if row[i].value and sc.isstring(row[i].value) and row[i].value.lower().strip() == "y":
                    if comp_idx[i] not in comp_codenames:
                        if comp_idx[i] in set(framework.comps["display name"].str.lower().str.strip()):
                            # It's a valid compartment of some sort (not actually targetable - for use with coverage scenarios only)
                            logger.warning(f'Compartment "{comp_idx[i]}" is a non-standard compartment that cannot be targeted. The ProgramSet can be used with coverage scenarios only')
                            spec = framework.comps.loc[framework.comps["display name"].str.lower().str.strip() == comp_idx[i]]
                            self.add_comp(code_name=spec.index[0], full_name=spec["display name"][0], pop_type=spec["population type"][0])
                            target_comps.append(spec.index[0])  # Append the pop's codename
                        else:
                            message = "There was a mismatch between the compartments in the databook and the compartments in the Framework file"
                            message += '\nThe program book contains compartment "%s", while the Framework contains: %s' % (comp_idx[i], [str(x) for x in comp_codenames.keys()])
                            raise Exception(message)
                    else:
                        target_comps.append(comp_codenames[comp_idx[i]])  # Append the pop's codename

            short_name = row[0].value.strip()
            if short_name.lower() == "all":
                raise Exception('A program was named "all", which is a reserved keyword and cannot be used as a program name')
            long_name = row[1].value.strip()

            self.programs[short_name] = Program(name=short_name, label=long_name, target_pops=target_pops, target_comps=target_comps)

    def _write_targeting(self):
        sheet = self._book.add_worksheet("Program targeting")
        widths = dict()

        # Work out the column offset associated with each population label and comp label
        pop_block_offset = 2  # This is the co
        sheet.write(0, pop_block_offset, "Targeted to (populations)", self._formats["rc_title"]["left"]["F"])
        comp_block_offset = 2 + len(self.pops) + 1
        sheet.write(0, comp_block_offset, "Targeted to (compartments)", self._formats["rc_title"]["left"]["F"])

        comps_in_use = set()
        for prog in self.programs.values():
            comps_in_use.update(prog.target_comps)
        comps_to_write = {k: v for k, v in self.comps.items() if k in comps_in_use or not v["non_targetable"]}

        pop_col = {n: i + pop_block_offset for i, n in enumerate(self.pops.keys())}
        comp_col = {n: i + comp_block_offset for i, n in enumerate(comps_to_write.keys())}

        # Write the header row
        sheet.write(1, 0, "Abbreviation", self._formats["center_bold"])
        update_widths(widths, 0, "Abbreviation")
        sheet.write(1, 1, "Display name", self._formats["center_bold"])
        update_widths(widths, 1, "Abbreviation")
        for pop, spec in self.pops.items():
            col = pop_col[pop]
            sheet.write(1, col, spec["label"], self._formats["rc_title"]["left"]["T"])
            self._references[spec["label"]] = "='%s'!%s" % (sheet.name, xlrc(1, col, True, True))
            widths[col] = 12  # Wrap population names

        for comp, spec in comps_to_write.items():
            if spec["non_targetable"] and comp not in comps_in_use:
                continue
            col = comp_col[comp]
            sheet.write(1, col, spec["label"], self._formats["rc_title"]["left"]["T"])
            self._references[spec["label"]] = "='%s'!%s" % (sheet.name, xlrc(1, col, True, True))
            widths[col] = 12  # Wrap compartment names

        row = 2
        self._references["reach_pop"] = dict()  # This is storing cells e.g. self._references['reach_pop'][('BCG','0-4')]='$A$4' so that conditional formatting can be done
        for prog in self.programs.values():
            sheet.write(row, 0, prog.name)
            self._references[prog.name] = "='%s'!%s" % (sheet.name, xlrc(row, 0, True, True))
            update_widths(widths, 0, prog.name)
            sheet.write(row, 1, prog.label)
            self._references[prog.label] = "='%s'!%s" % (sheet.name, xlrc(row, 1, True, True))
            update_widths(widths, 1, prog.label)

            for pop in self.pops.keys():
                col = pop_col[pop]
                if pop in prog.target_pops:
                    sheet.write(row, col, "Y", self._formats["center"])
                else:
                    sheet.write(row, col, "N", self._formats["center"])
                self._references["reach_pop"][(prog.name, pop)] = "'%s'!%s" % (sheet.name, xlrc(row, col, True, True))
                sheet.data_validation(xlrc(row, col), {"validate": "list", "source": ["Y", "N"]})
                sheet.conditional_format(xlrc(row, col), {"type": "cell", "criteria": "equal to", "value": '"Y"', "format": self._formats["unlocked_boolean_true"]})
                # sheet.conditional_format(xlrc(row, col), {'type': 'cell', 'criteria': 'equal to', 'value': '"N"', 'format': self._formats['unlocked_boolean_false']})

            for comp in comps_to_write.keys():
                col = comp_col[comp]
                if comp in prog.target_comps:
                    sheet.write(row, col, "Y", self._formats["center"])
                else:
                    sheet.write(row, col, "N", self._formats["center"])
                sheet.data_validation(xlrc(row, col), {"validate": "list", "source": ["Y", "N"]})
                sheet.conditional_format(xlrc(row, col), {"type": "cell", "criteria": "equal to", "value": '"Y"', "format": self._formats["unlocked_boolean_true"]})
                # sheet.conditional_format(xlrc(row, col), {'type': 'cell', 'criteria': 'equal to', 'value': '"N"', 'format': self._formats['unlocked_boolean_false']})

            row += 1

        apply_widths(sheet, widths)

    def _read_spending(self, sheet, _allow_missing_data=False):
        """
        Internal method to read the spending data

        :param sheet:
        :param _allow_missing_data: If False, an error will be raised if unit costs or total spending is missing.
                                   However, the FE requires loading in a progset with missing spending data. In that case,
                                   having these values missing is be allowed
        :return:
        """
        # Read the spending table and populate the program data
        tables, start_rows = read_tables(sheet)
        times = set()
        for table, start_row in zip(tables, start_rows):
            try:
                tdve = TimeDependentValuesEntry.from_rows(table)
            except Exception as e:
                message = 'Error on sheet "%s" while trying to read a TDVE table starting on row %d -> ' % (sheet.title, start_row)
                raise Exception("%s -> %s" % (message, e)) from e

            prog = self.programs[tdve.name]

            def set_ts(prog, field_name, ts):
                # Set Program timeseries based on TDVE, handling the case where the TDVE has no units
                if ts.units is None:
                    ts.units = getattr(prog, field_name).units
                setattr(prog, field_name, ts)

            if "Total spend" in tdve.ts:  # This is a compatibility statement around 19/10/18, progbooks generated during the WB workshop would have 'Total spend'
                set_ts(prog, "spend_data", tdve.ts["Total spend"])
            else:
                set_ts(prog, "spend_data", tdve.ts["Annual spend"])

            if "Capacity" in tdve.ts:  # Old progbooks have 'capacity' instead of 'capacity constraint'
                set_ts(prog, "capacity_constraint", tdve.ts["Capacity"])
            else:
                set_ts(prog, "capacity_constraint", tdve.ts["Capacity constraint"])

            set_ts(prog, "unit_cost", tdve.ts["Unit cost"])
            set_ts(prog, "coverage", tdve.ts["Coverage"])
            set_ts(prog, "saturation", tdve.ts["Saturation"])

            if not _allow_missing_data:
                assert prog.unit_cost.has_data, 'Unit cost data for %s not was not entered (in table on sheet "%s" starting on row %d' % (prog.name, sheet.title, start_row)
                assert prog.spend_data.has_data, 'Spending data for %s not was not entered (in table on sheet "%s" starting on row %d' % (prog.name, sheet.title, start_row)

            if "/year" in prog.unit_cost.units and "/year" in prog.coverage.units:
                logger.warning("Program %s: Typically if the unit cost is `/year` then the coverage would not be `/year`", prog.label)
            times.update(set(tdve.tvec))

        # Work out the currency
        units = set([x.spend_data.units.split("/")[0].strip() for x in self.programs.values()])
        units.update([x.unit_cost.units.split("/")[0].strip() for x in self.programs.values()])

        if len(units) == 1:
            self.currency = list(units)[0]
        else:
            raise Exception("The progbook contains multiple currencies: (%s). All spending must be specified in the same currency" % units)

        self.tvec = array(sorted(list(times)))  # NB. This means that  the ProgramSet's tvec (used when writing new programs) is based on the last Program to be read in

    def _write_spending(self):
        sheet = self._book.add_worksheet("Spending data")
        widths = dict()
        next_row = 0

        for prog in self.programs.values():
            # Make a TDVE table for
            tdve = TimeDependentValuesEntry(prog.name, self.tvec)
            prog = self.programs[tdve.name]
            tdve.ts["Annual spend"] = prog.spend_data
            tdve.ts["Unit cost"] = prog.unit_cost
            tdve.ts["Capacity constraint"] = prog.capacity_constraint
            tdve.ts["Saturation"] = prog.saturation
            tdve.ts["Coverage"] = prog.coverage

            tdve.assumption_heading = "Assumption"
            tdve.write_assumption = True
            tdve.write_units = True
            tdve.write_uncertainty = True

            tdve.allowed_units = {"Unit cost": [self.currency + "/person (one-off)", self.currency + "/person/year"], "Capacity": ["people/year", "people"]}

            # NOTE - If the ts contains time values that aren't in the ProgramSet's tvec, then an error will be thrown
            # However, if the ProgramSet's tvec contains values that the ts does not, then that's fine, there
            # will just be an empty cell in the spreadsheet
            next_row = tdve.write(sheet, next_row, self._formats, self._references, widths)

        apply_widths(sheet, widths)

    def _read_effects(self, sheet, framework, data):
        # Read the program effects sheet. Here we instantiate a costcov object for every non-empty row

        tables, start_rows = read_tables(sheet)
        pop_codenames = {v["label"].lower().strip(): x for x, v in self.pops.items()}
        par_codenames = {v["label"].lower().strip(): x for x, v in self.pars.items()}
        transfer_names = set()
        for transfer in data.transfers:
            for pops in transfer.ts.keys():
                transfer_names.add(("%s_%s_to_%s" % (transfer.code_name, pops[0], pops[1])).lower())

        self.covouts = sc.odict()

        for table in tables:
            par_label = table[0][0].value.strip()
            if par_label.lower() in par_codenames:
                par_name = par_codenames[par_label.lower()]  # Code name of the parameter we are working with
            elif par_label.lower() in transfer_names:
                par_name = table[0][0].value.strip()  # Preserve case
            else:
                raise Exception('Program name "%s" was not found in the framework parameters or in the databook transfers' % (table[0][0].value.strip()))
            headers = [x.value.strip() if sc.isstring(x.value) else x.value for x in table[0]]
            idx_to_header = {i: h for i, h in enumerate(headers)}  # Map index to header

            for row in table[1:]:
                # For each covout row, we will initialize
                pop_label = row[0].value.strip()
                if pop_label.lower() not in pop_codenames:
                    raise Exception(f'Population "{pop_label}" was not found in the databook')
                pop_name = pop_codenames[pop_label.lower()]

                # Code name of the population we are working on
                if self.pars[par_name]["type"] != self.pops[pop_name]["type"]:
                    raise Exception(f'On the Effects sheet, Parameter "{par_label}" belongs to population type "{self.pars[par_name]["type"]}" but Population "{pop_label}" (Cell {row[0].coordinate}) has population type "{self.pops[pop_name]["type"]}"')

                progs = sc.odict()

                baseline = None
                cov_interaction = None
                imp_interaction = None
                uncertainty = None

                for i, x in enumerate(row[1:]):
                    i = i + 1  # Offset of 1 because the loop is over row[1:] not row[0:]

                    if idx_to_header[i] is None:  # If the header row had a blank cell, ignore everything in that column - we don't know what it is otherwise
                        continue
                    elif idx_to_header[i].lower() == "baseline value":
                        if x.value is not None:  # test `is not None` because it might be entered as 0
                            baseline = float(x.value)
                    elif idx_to_header[i].lower() == "coverage interaction":
                        if x.value:
                            cov_interaction = x.value.strip().lower()  # additive, nested, etc.
                    elif idx_to_header[i].lower() == "impact interaction":
                        if x.value:
                            imp_interaction = x.value.strip()  # additive, nested, etc.
                    elif idx_to_header[i].lower() == "uncertainty":
                        if x.value is not None:  # test `is not None` because it might be entered as 0
                            uncertainty = float(x.value)
                    elif x.value is not None:  # If the header isn't empty, then it should be one of the program names
                        if idx_to_header[i] not in self.programs:
                            raise Exception('The heading "%s" was not recognized as a program name or a special token - spelling error?' % (idx_to_header[i]))
                        progs[idx_to_header[i]] = float(x.value)

                if baseline is None and progs:
                    raise Exception(f'On the "Effects" sheet for Parameter "{table[0][0].value.strip()}" in population "{row[0].value.strip()}", program outcomes are defined but the baseline value is missing')
                if baseline is not None or progs:  # Only instantiate covout objects if they have programs associated with them
                    self.covouts[(par_name, pop_name)] = Covout(par=par_name, pop=pop_name, cov_interaction=cov_interaction, imp_interaction=imp_interaction, uncertainty=uncertainty, baseline=baseline, progs=progs)

    def _write_effects(self):
        sheet = self._book.add_worksheet("Program effects")
        widths = dict()

        current_row = 0

        for par_name, par_spec in self.pars.items():
            sheet.write(current_row, 0, par_spec["label"], self._formats["rc_title"]["left"]["F"])
            update_widths(widths, 0, par_spec["label"])

            for i, s in enumerate(["Baseline value", "Coverage interaction", "Impact interaction", "Uncertainty"]):
                sheet.write(current_row, 1 + i, s, self._formats["rc_title"]["left"]["T"])
                widths[1 + i] = 12  # Fixed width, wrapping
            # sheet.write_comment(xlrc(current_row,1), 'In this column, enter the baseline value for "%s" if none of the programs reach this parameter (e.g., if the coverage is 0)' % (par_label))

            applicable_progs = self.programs.values()  # All programs - could filter this later on
            prog_col = {p.name: i + 6 for i, p in enumerate(applicable_progs)}  # add any extra padding columns to the indices here too

            for prog in applicable_progs:
                sheet.write_formula(current_row, prog_col[prog.name], self._references[prog.name], self._formats["center_bold"], value=prog.name)
                update_widths(widths, prog_col[prog.name], prog.name)
            current_row += 1

            applicable_covouts = {x.pop: x for x in self.covouts.values() if x.par == par_name}
            applicable_pops = [x for x, v in self.pops.items() if v["type"] == par_spec["type"]]  # All populations with matching type

            for pop_name in applicable_pops:

                if pop_name not in applicable_covouts:  # There is currently no covout
                    covout = None
                else:
                    covout = applicable_covouts[pop_name]

                sheet.write_formula(current_row, 0, self._references[self.pops[pop_name]["label"]], value=self.pops[pop_name]["label"])
                update_widths(widths, 0, self.pops[pop_name])

                if covout and covout.baseline is not None:
                    sheet.write(current_row, 1, covout.baseline, self._formats["not_required"])
                else:
                    sheet.write(current_row, 1, None, self._formats["unlocked"])

                if covout and covout.cov_interaction is not None:
                    sheet.write(current_row, 2, covout.cov_interaction.title(), self._formats["not_required"])
                else:
                    sheet.write(current_row, 2, "Additive", self._formats["unlocked"])
                sheet.data_validation(xlrc(current_row, 2), {"validate": "list", "source": ["Random", "Additive", "Nested"]})

                if covout and covout.imp_interaction is not None:
                    sheet.write(current_row, 3, covout.imp_interaction, self._formats["not_required"])
                else:
                    sheet.write(current_row, 3, None, self._formats["unlocked"])

                if covout and covout.sigma is not None:
                    sheet.write(current_row, 4, covout.sigma, self._formats["not_required"])
                else:
                    sheet.write(current_row, 4, None, self._formats["unlocked"])

                for prog in applicable_progs:
                    if covout and prog.name in covout.progs:
                        sheet.write(current_row, prog_col[prog.name], covout.progs[prog.name], self._formats["not_required"])
                    else:
                        sheet.write(current_row, prog_col[prog.name], None, self._formats["unlocked"])

                    fcn_pop_not_reached = '%s<>"Y"' % (self._references["reach_pop"][(prog.name, pop_name)])  # Excel formula returns FALSE if pop was 'N' (or blank)
                    sheet.conditional_format(xlrc(current_row, prog_col[prog.name]), {"type": "formula", "criteria": "=AND(%s,NOT(ISBLANK(%s)))" % (fcn_pop_not_reached, xlrc(current_row, prog_col[prog.name])), "format": self._formats["ignored_warning"]})
                    sheet.conditional_format(xlrc(current_row, prog_col[prog.name]), {"type": "formula", "criteria": "=" + fcn_pop_not_reached, "format": self._formats["ignored_not_required"]})

                # Conditional formatting for the impact interaction - hatched out if no single-program outcomes
                fcn_empty_outcomes = 'COUNTIF(%s:%s,"<>" & "")<2' % (xlrc(current_row, 5), xlrc(current_row, 5 + len(applicable_progs)))
                sheet.conditional_format(xlrc(current_row, 3), {"type": "formula", "criteria": "=" + fcn_empty_outcomes, "format": self._formats["ignored"]})
                sheet.conditional_format(xlrc(current_row, 3), {"type": "formula", "criteria": "=AND(%s,NOT(ISBLANK(%s)))" % (fcn_empty_outcomes, xlrc(current_row, 3)), "format": self._formats["ignored_warning"]})

                current_row += 1

            current_row += 1

        apply_widths(sheet, widths)

    @staticmethod
    def new(name=None, tvec=None, progs=None, project=None, framework=None, data=None):
        """
        Generate a new progset with blank data

        :param name: the name for the progset
        :param tvec: an np.array() with the time values to write
        :param progs: This can be
              - A number of progs
              - An odict of {code_name:display name} programs
        :param project: specify a project to use the project's framework and data to initialize the comps, pars, and pops
        :param framework: specify a framework to use the framework's comps and pars
        :param data: specify a data to use the data's pops
        :return: A new :class:`ProgramSet` instances

        """

        assert tvec is not None, "You must specify the time points where data will be entered"
        # Prepare programs
        if sc.isnumber(progs):
            nprogs = progs
            progs = sc.odict()
            for p in range(nprogs):
                progs["Prog %i" % (p + 1)] = "Program %i" % (p + 1)
        elif isinstance(progs, dict):  # will also match odict
            pass
        elif progs is None:
            errormsg = "When creating a ProgramSet, the programs cannot be None - it can either be a number of programs, or a dict with code names and full names"
            raise Exception(errormsg)
        else:
            errormsg = 'Please just supply a number of programs, not "%s"' % (type(progs))
            raise Exception(errormsg)

        framework, data = ProgramSet._normalize_inputs(framework, data, project)  # This step will fail if the framework and data cannot be resolved

        newps = ProgramSet(name=name, tvec=tvec, framework=framework, data=data)
        if not newps.pars:
            logger.warning('No parameters were marked as "Targetable" in the Framework, so no program effects were added')

        for k, v in progs.items():
            newps.add_program(code_name=k, full_name=v)

        return newps

    def validate(self) -> None:
        """
        Perform basic validation checks

        :raises: Exception if anything is invalid

        """

        for prog in self.programs.values():
            if not prog.target_comps and self.comps:
                # If there are no compartments, then it's fine not to target any compartments - it should be obvious that only coverage scenarios are possible
                # If there are compartments, then the same is true, but it's also possible (or even probable) that the user accidentally didn't target any compartments
                # Therefore, in this case, raise an error - if a user wants to just do coverage scenarios, then they can still target the compartments anyway
                raise Exception('Program "%s" does not target any compartments' % (prog.name))
            if not prog.target_pops:
                # If the user is using parameters only, they will still have to define a population. And that population must be targeted in order
                # to provide any program outcome values. Thus, the program should generally target the population even if there are no compartments,
                # so we raise an error if no populations are targeted
                raise Exception('Program "%s" does not target any populations' % (prog.name))

    #######################################################################################################
    # Methods for getting core response summaries: budget, allocations, coverages, outcomes, etc
    #######################################################################################################

    def get_alloc(self, tvec, instructions=None) -> dict:
        """
        Return the spending allocation for each program

        This method fuses the spending data entered in the program book with
        any overwrites that are present in the instructions. The spending values
        returned by this method thus reflect any budget scenarios that may be
        present.

        :param tvec: array of times (in years) - this is required to interpolate time-varying spending values
        :param instructions: optionally specify instructions, which can supply a spending overwrite
        :return: Dict like ``{prog_name: np.array()}`` with spending on each program (in units of '$/year' or currency equivalent)

        """

        tvec = sc.promotetoarray(tvec)

        alloc = sc.odict()
        for prog in self.programs.values():
            if instructions is None or prog.name not in instructions.alloc:
                alloc[prog.name] = prog.get_spend(tvec)
            else:
                alloc[prog.name] = instructions.alloc[prog.name].interpolate(tvec, method="previous")

        if instructions:
            for prog_name in set(instructions.alloc.keys()) - set(self.programs.keys()):
                logger.warning('The instructions contain an overwrite for a program called "%s" but as this is not in the ProgramSet, it will have no effect', prog_name)

        return alloc

    def get_capacities(self, tvec, dt, instructions=None) -> dict:
        """
        Return timestep capacity for all programs

        For convenience, this method automatically calls :meth:`ProgramSet.get_alloc()` to
        retrieve the spending values that are used to compute capacity. Thus, this method
        fuses the program capacity computed with the inclusion of any budget scenarios, with
        any capacity overwrites that are present in the instructions.

        :param tvec: array of times (in years) - this is required to interpolate time-varying unit costs and capacity_constraint constraints
        :param dt: scalar timestep size - this is required to adjust spending on incidence-type programs
        :param instructions: optionally specify instructions, which can supply a spending overwrite
        :return: Dict like ``{prog_name: np.array()}`` with program capacity at each timestep (in units of people)

        """

        # Validate inputs
        tvec = sc.promotetoarray(tvec)
        alloc = self.get_alloc(tvec, instructions)

        # Get number covered for each program
        capacities = sc.odict()  # Initialise outputs
        for prog in self.programs.values():
            if instructions is None or prog.name not in instructions.capacity:
                if prog.name in alloc:
                    spending = alloc[prog.name]
                else:
                    spending = None
                # Note that prog.get_capacity() returns capacity in units of people
                capacities[prog.name] = prog.get_capacity(tvec=tvec, dt=dt, spending=spending)
            else:
                capacities[prog.name] = instructions.capacity[prog.name].interpolate(tvec, method="previous")
                # Capacity overwrites are input in units of people/year so convert to units of people here
                if prog.is_one_off:
                    capacities[prog.name] *= dt

        return capacities

    def get_prop_coverage(self, tvec, dt, capacities: dict, num_eligible: dict, instructions=None) -> dict:
        """
        Return dimensionless (timestep) fractional coverage

        Note that this function is primarily for internal usage (i.e. during
        model integration or reconciliation). Since the proportion covered depends
        on the number of people eligible for the program (the coverage denominator),
        retrieving fractional coverage after running the model is best accomplished
        via ``Result.get_coverage('fraction')`` whereas this method is called automatically
        during integration.

        Evaluating the proportion coverage for a ProgramSet is not a straight division because

        - instructions can override the coverage (for coverage scenarios)
        - Programs can contain saturation constraints

        Note that while converage overwrites might be specified in '/year' units for one-off programs,
        *this function always returns dimensionless coverage* (i.e. not coverage/year). This coverage is also capped at 1.

        :param tvec: scalar year, or array of years - this is required to interpolate time-varying saturation values
        :param capacities: dict of program coverages, should match the available programs (typically the output of ``ProgramSet.get_capacities()``)
                           Note that since the capacity and eligible compartment sizes are being compared here,
                           the capacity needs to be in units of 'people' (not 'people/year') at this point
        :param num_eligible: dict of number of people covered by each program, computed externally and with one entry for each program
        :param instructions: optionally specify instructions, which can supply a coverage overwrite
        :return: Dict like ``{prog_name: np.array()}`` with fractional coverage values (dimensionless)

        """

        prop_coverage = sc.odict()  # Initialise outputs

        for prog in self.programs.values():
            if instructions is None or prog.name not in instructions.coverage:
                # The capacities have already been converted to timestep values, so no further transformation is necessary
                prop_coverage[prog.name] = prog.get_prop_covered(tvec, capacities[prog.name], num_eligible[prog.name])
            else:
                prop_coverage[prog.name] = instructions.coverage[prog.name].interpolate(tvec, method="previous")
                if prog.is_one_off:
                    # Coverage overwrites for one off programs are specified in /year units, therefore they get adjusted by dt here
                    prop_coverage[prog.name] *= dt

            prop_coverage[prog.name] = np.minimum(prop_coverage[prog.name], 1.0)

        return prop_coverage

    def get_outcomes(self, prop_coverage: dict) -> dict:
        """
        Get program outcomes given fractional coverage

        Since the modality interactions in Covout.get_outcome() assume that the coverage is scalar, this function
        will also only work for scalar coverage. Therefore, the prop coverage would normally come from
        ProgramSet.get_prop_coverage(tvec,...) where tvec was only one year.

        Note that this function is mainly aimed at internal usage. Typically, the program-provided
        parameter values would be best accessed by examining the appropriate output in the ``Result``.
        For example, if the programs system overwrites the screening rate ``screen`` then it would
        normally be easiest to run a simulation and then use ``Result.get_variable(popname,'screen')``

        For computational efficiency, this method returns a flat dictionary keyed by
        parameter-population pairs that then gets inserted into the appropriate integration objects
        by :meth:`Model.update_pars`.

        :param prop_coverage: dict with coverage values ``{prog_name:val}``
        :return: dict ``{(par,pop):val}`` containing parameter value overwrites

        """

        return {(covout.par, covout.pop): covout.get_outcome(prop_coverage) for covout in self.covouts.values()}

    def sample(self, constant: bool = True):
        """
        Perturb programs based on uncertainties

        The covout objects contained within the ProgramSet cache the program outcomes. At construction,
        the cache corresponds to the values entered in the databook. Calling this function will perturb
        the caches based on the sigma values. A simulation subsequently run using the ProgramSet will
        use the perturbed outcomes.

        :param constant: If True, time series will be perturbed by a single constant offset. If False,
                         an different perturbation will be applied to each time specific value independently.
        :return: A new ``ProgramSet`` with values perturbed by sampling

        """

        new = sc.dcp(self)
        for prog in new.programs.values():
            prog.sample(constant)
        for covout in new.covouts.values():
            covout.sample()
        return new


class Program(NamedItem):
    """
    Representation of a single program

    A :class:`Program` object is instantiated for every program listed on the 'Program Targeting'
    sheet in the program book. The :class:`Program` object contains

    - Collections of targeted populations and compartments from the targeting sheet in the program book
    - The time-dependent program properties on the spending data sheet (such as total spend and unit cost)

    :param name: Short name of the program
    :param label: Full name of the program
    :param target_pops: List of population code names for pops targeted by the program
    :param target_comps: List of compartment code names for compartments targeted by the program
    :param currency: The currency to use (for display purposes only) - normally this would be set to ``ProgramSet.currency`` by ``ProgramSet.add_program()``

    :param name: Short name of the program
    :param label: Full name of the program
    :param target_pops: List of population code names for pops targeted by the program
    :param target_comps: List of compartment code names for compartments targeted by the program
    :param currency: The currency to use (for display purposes only) - normally this would be set to ``ProgramSet.currency`` by ``ProgramSet.add_program()``

    """

    def __init__(self, name, label=None, target_pops=None, target_comps=None, currency="$"):
        NamedItem.__init__(self, name)
        self.name = name  #: Short name of program
        self.label = name if label is None else label  #: Full name of the program
        self.target_pops = [] if target_pops is None else target_pops  #: List of populations targeted by the program
        self.target_comps = [] if target_comps is None else target_comps  #: Compartments targeted by the program - used for calculating coverage denominators
        self.baseline_spend = TimeSeries(assumption=0.0, units=currency + "/year")  #: A TimeSeries with any baseline spending data - currently not exposed in progbook
        self.spend_data = TimeSeries(units=currency + "/year")  #: TimeSeries with spending data for the program
        self.unit_cost = TimeSeries(units=currency + "/person (one-off)")  #: TimeSeries with unit cost of the program
        self.capacity_constraint = TimeSeries(units="people/year")  #: TimeSeries with capacity constraint for the program
        self.saturation = TimeSeries(units=FS.DEFAULT_SYMBOL_INAPPLICABLE)  #: TimeSeries with saturation constraint that is applied to fractional coverage
        self.coverage = TimeSeries(units="people/year")  #: TimeSeries with capacity of program - optional - if not supplied, cost function is assumed to be linear

    @property
    def is_one_off(self) -> bool:
        """
        Flag for one-off programs

        A one-off program is a program where the cost is incurred once, per person impacted. For example, a treatment
        program where after treatment the person is no longer eligible for treatment. In contrast, a non-one-off program
        (a continuous program) is one where a person reached by the program remains eligible - for example, ART. In addition,
        one-off programs are typically linked to transition parameters, while continuous programs are typically linked to
        non-transition parameters.

        Whether a program is one-off or not depends on whether the unit cost is specified as
        - Cost per person (one-off)
        - Cost per person per year (continuous)

        :return: True if program is a one-off program

        """
        return "/year" not in self.unit_cost.units

    def sample(self, constant: bool) -> None:
        """
        Perturb program values based on uncertainties

        Calling this function will perturb the original values based on their uncertainties. The
        values will change in-place. Normally, this method would be called by
        :meth:`ProgramSet.sample()` which will copy the ``Program`` instance first.

        :param constant: If True, time series will be perturbed by a single constant offset. If False,
                         an different perturbation will be applied to each time specific value independently.
        """

        self.spend_data = self.spend_data.sample(constant)
        self.unit_cost = self.unit_cost.sample(constant)
        self.capacity_constraint = self.capacity_constraint.sample(constant)
        self.saturation = self.saturation.sample(constant)
        self.coverage = self.coverage.sample(constant)

    def __repr__(self):
        output = sc.prepr(self)
        output += "          Program name: %s\n" % self.name
        output += "         Program label: %s\n" % self.label
        output += "  Targeted populations: %s\n" % self.target_pops
        output += " Targeted compartments: %s\n" % self.target_comps
        output += "\n"
        return output

    def get_spend(self, year=None, total: bool = False) -> np.array:
        """
        Retrieve program spending

        :param year: Scalar, list, or array of years to retrieve spending in
        :param total: If True, the baseline spend will be added to the spending data
        :return: Array of spending values

        """

        if total:
            return self.spend_data.interpolate(year, method="previous") + self.baseline_spend.interpolate(year, method="previous")
        else:
            return self.spend_data.interpolate(year, method="previous")

    def get_capacity(self, tvec, spending, dt):
        """
        Return timestep capacity

        This method returns the number of people covered at each timestep. For one-off
        programs, this means the annual capacity is multiplied by the timestep size.
        Whether timestep scaling takes place or not is determined based on the units
        of the unit cost ($/person or $/person/year where the former is used for one-off programs).

        The method takes in the spending value to support overwrites in spending value by program
        instructions (in which case, spending should be drawn from the instructions rather than
        the program's spending data). This is handled in :meth:`ProgramSet.get_capacities`

        This method returns the program's timestep capacity - that is, the capacity of the program per
        timestep, at specified points in time. The spending and capacity constraint are automatically
        adjusted depending on the units of the unit cost and capacity constraint such that the
        calculation returns capacity in units of 'people' (*not* 'people/year')

        :param tvec: A scalar, list, or array of times
        :param spending: A vector of spending values (in units of '$/year'), the same size as ``tvec``
        :param dt: The time step size (required because the number covered at each time step potentially depends on the spending per-timestep)
        :return: Array the same size as ``tvec``, with capacity in units of 'people'

        """

        # Validate inputs
        spending = sc.promotetoarray(spending)

        unit_cost = self.unit_cost.interpolate(tvec, method="previous")
        if self.is_one_off:
            # The spending is $/year, and the /year gets eliminated if the unit cost is also per year. For one-off programs, the unit cost is not
            # /year, therefore we need to multiply the spending by the timestep to the capacity as people rather than people/year
            spending *= dt

        capacity = spending / unit_cost

        if self.capacity_constraint.has_data:
            capacity_constraint = self.capacity_constraint.interpolate(tvec, method="previous")
            if "/year" in self.capacity_constraint.units:
                # The capacity_constraint constraint is applied to a number of people. If it is /year, then it must be multiplied by the timestep first
                capacity_constraint *= dt
            capacity = np.minimum(capacity_constraint, capacity)

        return capacity

    def get_prop_covered(self, tvec, capacity, eligible):
        """
        Return proportion of people covered

        The time vector ``tvec`` is required to interpolate the saturation values. The
        ``capacity`` and ``eligible`` variables are assumed to correspond to the same time points
        and thus the array sizes should match the size of the time array.

        :param tvec:  An array of times
        :param capacity: An array of number of people covered (e.g. the output of ``Program.get_capacity()``)
                         This should be in units of 'people', rather than 'people/year' although it may be a
                         timestep-sensitive value if the capacity follows from a timestep-adjusted spend.
        :param eligible: The number of people eligible for the program (computed from a model object or a Result)
        :return: The fractional coverage (used to compute outcomes)

        """

        tvec = sc.promotetoarray(tvec)
        eligible = sc.promotetoarray(eligible)
        capacity = sc.promotetoarray(capacity)

        if self.saturation.has_data:
            # If the coverage denominator (eligible) is 0, then we need to use the saturation value
            prop_covered = np.divide(capacity, eligible, out=np.full(capacity.shape, np.inf), where=eligible != 0)
            saturation = self.saturation.interpolate(tvec, method="previous")
            prop_covered = 2 * saturation / (1 + exp(-2 * prop_covered / saturation)) - saturation
            prop_covered = np.minimum(prop_covered, 1.0)  # Ensure that coverage doesn't go above 1 (if saturation is < 1)
        else:
            # The division below means that 0/0 is treated as returning 1
            prop_covered = np.divide(capacity, eligible, out=np.ones_like(capacity), where=eligible > capacity)

        return prop_covered


class Covout:
    """
    Store and compute program outcomes

    The :class:`Covout` object is responsible for storing the


    :param par: string with the code name of the parameter being overwritten
    :param pop: string with the code name of the population being overwritten
    :param progs: a dict containing ``{prog_name:outcome}`` with the single program outcomes
    :param cov_interaction: one of 'additive', 'random', 'nested'
    :param imp_interaction: a parsable string like ``'Prog1+Prog2=10,Prog2+Prog3=20'`` with the interaction outcomes
    :param uncertainty: a scalar standard deviation for the outcomes
    :param baseline: the zero coverage baseline value

    """

    def __init__(self, par: str, pop: str, progs: dict, cov_interaction: str = None, imp_interaction: str = None, uncertainty=0.0, baseline=0.0):

        if cov_interaction is None:
            cov_interaction = "additive"
        else:
            assert cov_interaction in ["additive", "random", "nested"], 'Coverage interaction must be set to "additive", "random", or "nested"'

        self.par = par
        self.pop = pop
        self.cov_interaction = cov_interaction
        self.imp_interaction = imp_interaction
        self.progs = sc.dcp(progs)
        self.sigma = uncertainty
        self.baseline = baseline

        # Parse the interactions into a numeric representation
        self._interactions = dict()
        if self.imp_interaction and not self.imp_interaction.lower() in ["best", "synergistic"]:
            for interaction in self.imp_interaction.split(","):
                combo, val = interaction.split("=")
                combo = frozenset([x.strip() for x in combo.split("+")])
                for x in combo:
                    assert x in self.progs, 'The impact interaction refers to a program "%s" which does not appear in the available programs' % (x)
                self._interactions[combo] = float(val) - self.baseline

        self.update_outcomes()

    @property
    def n_progs(self) -> int:
        """
        Return the number of programs

        :return: The number of programs with defined outcomes (usually this is a subset of all available programs)

        """

        return len(self.progs)

    def sample(self) -> None:
        """
        Perturb the values entered in the databook

        The :class:`Covout` instance is modified in-place. Note that the program outcomes are scalars
        that do not vary over time - therefore, :meth:`Covout.sample()` does not have a ``constant``
        argument.

        """

        if self.sigma is None:
            return

        for k, v in self.progs.items():
            self.progs[k] = v + self.sigma * np.random.randn(1)[0]
        # Perturb the interactions
        if self._interactions:
            for k, v in self.interactions.items():
                self.interactions[k] = v + self.sigma * np.random.randn(1)[0]
            tokens = ["%s=%.4f" % ("+".join(k), v) for k, v in self.interactions.items()]
            self.imp_interaction = ",".join(tokens)

        self.update_outcomes()

    def update_outcomes(self) -> None:
        """
        Update cache when outcomes change

        This method should be called whenever the baseline, program outcomes, or interaction outcomes change.
        It updates the internal cache so that get_outcome() uses the correct values. It's responsible for

        1. Sorting the programs by outcome value
        2. Compute the deltas relative to baseline
        3. Pre-compute the outcomes associated with every possible combination of programs

        """

        # First, sort the program dict by the magnitude of the outcome
        prog_tuple = [(k, v) for k, v in self.progs.items()]
        prog_tuple = sorted(prog_tuple, key=lambda x: -abs(x[1] - self.baseline))
        self._cached_progs = sc.odict()  # This list contains the perturbed/sampled values, in order
        for item in prog_tuple:
            self._cached_progs[item[0]] = item[1]
        self._deltas = np.array([x[1] - self.baseline for x in prog_tuple])  # Internally cache the deltas which are used

        # Precompute the combinations and associated modality interaction outcomes - it's computationally expensive otherwise
        # We need to store it in two forms
        # - An (ordered) vector of outcomes, which is used by additive and random to do the modality interaction in vectorized form
        # - A dict of outcomes, which is used by nested to look up the outcome using a tupled key of program indices
        combination_strings = [bin(x)[2:].rjust(self.n_progs, "0") for x in range(2 ** self.n_progs)]  # ['00','01','10',...]
        self.combinations = np.array([list(int(y) for y in x) for x in combination_strings])
        _combination_outcomes = []
        for prog_combination in self.combinations.astype(bool):
            _combination_outcomes.append(self.compute_impact_interaction(progs=prog_combination))
        self._combination_outcomes = np.array(_combination_outcomes)  # Reshape to column vector, since that's the shape of combination_coverage

    def __repr__(self):
        output = sc.prepr(self)
        output = sc.indent("   Parameter: ", self.par)
        output += sc.indent("  Population: ", self.pop)
        output += sc.indent("Baseline val: ", self.baseline)
        output += sc.indent("    Programs: ", ", ".join(["%s: %s" % (key, val) for key, val in self.progs.items()]))
        output += "\n"
        return output

    def get_outcome(self, prop_covered):
        """Return parameter value given program coverages

        The :class:`Covout` object contains a set of programs and outcomes. The :meth:`Covout.get_outcome` method
        returns the outcome value associated for coverage of each program. Don't forget that any given Covout instance
        is already specific to a ``(par,pop)`` combination

        :param prop_covered: A dict with ``{prog_name:coverage}`` containing at least all of the
                             programs in `self.progs`. Note that `coverage` is expected to be a ``np.array``
                             (such that that generated by :meth:`ProgramSet.get_prop_coverage`). However,
                             because the modality calculations only work for scalars, only the first entry
                             in the array will be used. Note that the coverage in this dictionary should be
                             dimensionless.
        :return: A scalar outcome (of type `np.double` or similar i.e. _not_ an array)

        """

        # Put coverages and deltas into array form
        outcome = self.baseline  # Accumulate the outcome by adding the deltas onto this

        if self.n_progs == 0:
            return outcome  # If there are no programs active, return the baseline value immediately
        elif self.n_progs == 1:
            return outcome + prop_covered[self._cached_progs.keys()[0]][0] * self._deltas[0]

        cov = []
        for prog in self._cached_progs.keys():
            cov.append(prop_covered[prog][0])
        cov = np.array(cov)

        # ADDITIVE CALCULATION
        if self.cov_interaction == "additive":
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
                    contribution = np.ones((net_random.shape[0],))
                    for j in range(0, net_random.shape[1]):
                        if i == j:
                            contribution *= additive_portion_coverage[:, j]
                        else:
                            contribution *= net_random[:, j]
                    combination_coverage += contribution
                outcome += np.sum(combination_coverage * self._combination_outcomes.ravel())
            else:
                outcome += np.sum(cov * self._deltas)

        # NESTED CALCULATION
        elif self.cov_interaction == "nested":
            # Outcome += c3*max(delta_out1,delta_out2,delta_out3) + (c2-c3)*max(delta_out1,delta_out2) + (c1 -c2)*delta_out1, where c3<c2<c1.
            idx = np.argsort(cov)
            prog_mask = np.full(cov.shape, fill_value=True)
            combination_coverage = np.zeros((self.combinations.shape[0],))

            for i in range(0, len(cov)):
                combination_index = int("0b" + "".join(["1" if x else "0" for x in prog_mask]), 2)
                if i == 0:
                    combination_coverage[combination_index] = cov[idx[i]]
                else:
                    combination_coverage[combination_index] = cov[idx[i]] - cov[idx[i - 1]]
                prog_mask[idx[i]] = False  # Disable this program at the next iteration

            outcome += np.sum(combination_coverage * self._combination_outcomes.ravel())

        # RANDOM CALCULATION
        elif self.cov_interaction == "random":
            # Outcome += c1(1-c2)* delta_out1 + c2(1-c1)*delta_out2 + c1c2* max(delta_out1,delta_out2)
            combination_coverage = np.product(self.combinations * cov + (self.combinations ^ 1) * (1 - cov), axis=1)
            outcome += np.sum(combination_coverage.ravel() * self._combination_outcomes.ravel())
        else:
            raise Exception('Unknown reachability type "%s"', self.cov_interaction)

        return outcome

    def compute_impact_interaction(self, progs: np.array) -> float:
        """
        Return the output for a given combination of programs

        The outcome for various combinations of programs is cached prior to running the model.
        This function retrieves the appropriate delta given a boolean array flagging which
        programs are active

        :param progs: A numpy boolean array, with length equal to the number of programs
        :return: The delta value corresponding to the specified combination of programs

        """

        if not any(progs):
            return 0.0
        else:
            progs_active = frozenset(np.array(self._cached_progs.keys())[progs])

        if progs_active in self._interactions:
            # If the combination of programs has an explicitly specified outcome, then use it
            return self._interactions[progs_active]
        elif self.imp_interaction is not None and self.imp_interaction.lower() == "synergistic":
            raise NotImplementedError
        else:
            # Otherwise, do the 'best' interaction and return the delta with the largest magnitude
            tmp = self._deltas[progs]
            idx = np.argmax(abs(tmp))
            return tmp[idx]
