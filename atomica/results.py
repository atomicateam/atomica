"""
Implements interface for working with model outputs

The :class:`Result` class is a wrapper for a :class:`Model` instance,
providing methods to conveniently access, plot, and export model outputs.

"""
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import tqdm
import logging
from pathlib import Path

import sciris as sc
from .excel import standard_formats
from .system import FrameworkSettings as FS
from .system import logger, NotFoundError
from .utils import NamedItem, evaluate_plot_string, nested_loop
from .function_parser import parse_function
from .version import version, gitinfo

__all__ = ["Result", "export_results", "Ensemble"]


class Result(NamedItem):
    """
    Storage for single simulation result

    A Result object (similar to the ``raw_result`` in Optima HIV) stores a complete simulation run.
    In Atomica, a Result is a lightweight wrapper around a :class:`Model` object. During a simulation,
    the :class:`Model` object contains integration objects like compartments, links, and parameters, which
    store values for each quantity at every time step. The methods in the :class:`Model` class are oriented
    at performing the calculations required to simulate the model. A :class:`Result` object contains within
    it a single :class:`Model` object, which in turn contains all of the integration objects together with
    the data they contain and the relationships between them, as well as the :class:`programs.ProgramSet` and
    :class:`programs.ProgramInstructions` that were used to perform the simulation. The methods of the :class:`Result`
    class are oriented at plotting and exporting.

    :param model: A single :class:`model.Model` instance (after integration
    :param parset: A :class:`parameters.ParameterSet` instance
    :param name: The name to use for the new :class:`Result` object

    """

    # A Result stores a single model run
    def __init__(self, model, parset=None, name=None):
        if name is None:
            if parset is None:
                name = None
            else:
                name = parset.name
        NamedItem.__init__(self, name)

        self.uid = sc.uuid()
        self.version = version  # Track versioning information for the result. This might change due to migration (whereas by convention, the model version does not)
        self.gitinfo = gitinfo

        # The Result constructor is called in model.run_model and the Model is no longer returned.
        # The following should be the only reference to that instance so no need to dcp.
        self.model = model  # : A completed model run that serves as primary storage for the underlying values
        self.parset_name = parset.name if parset is not None else None  # : The name of the ParameterSet that was used for the simulation
        self.pop_names = [x.name for x in self.model.pops]  # : A list of the population names present. This gets frequently used, so it is saved as an actual output

    def __setstate__(self, d):
        from .migration import migrate

        self.__dict__ = d
        result = migrate(self)
        self.__dict__ = result.__dict__

    @property
    def used_programs(self) -> bool:
        """
        Flag whether programs were used or not

        :return: ``True`` if a progset and program instructions were present. Note that programs will be considered active even if the
               start/stop years in the instructions don't overlap the simulation years (so no overwrite actually took place).
        """

        return self.model.programs_active

    @property
    def framework(self):
        """
        Return framework from Result

        :return: A :class:`ProjectFramework` instance

        """

        return self.model.framework

    @property
    def t(self) -> np.array:
        """
        Return simulation time vector

        :return: Array of all time points available in the result

        """
        return self.model.t

    @property
    def dt(self) -> float:
        """
        Return simulation timestep

        :return: The simulation timestep (scalar)
        """
        return self.model.dt

    @property
    def pop_labels(self):
        """
        Return all population full names

        The full names/labels are returned in the same order as the names
        in ``Result.pop_names``

        :return: List of population full names

        """

        return [x.label for x in self.model.pops]

    def check_for_nans(self, verbose=True) -> bool:
        """
        Check if any NaNs/Infs are present

        :param verbose: Print NaN/Inf quantities
        :return: True if any quantities contain NaNs/Infs
        """

        nans_present = False

        for pop in self.model.pops:
            for var in pop.pars + pop.comps + pop.characs + pop.links:
                if not np.all(np.isfinite(var.vals)):
                    nans_present = True
                    if verbose:
                        print(f"NaNs detected in {var.name} ({pop.name})")
        return nans_present

    def get_alloc(self, year=None) -> dict:
        """
        Return spending allocation

        If the result was generated using programs, this method will return the spending
        on all programs in the requested years.

        :param year: Optionally specify a scalar or list/array of years to return budget values
                     for. Otherwise, uses all simulation times
        :return: Dictionary keyed by program name with arrays of spending values
        """

        if self.model.progset is None:
            return None

        if year is None:
            year = self.t

        return self.model.progset.get_alloc(year, self.model.program_instructions)

    def get_equivalent_alloc(self, year=None) -> dict:
        """
        Return minimal spending allocation for a given year based on the coverage

        If the result was generated using programs, this method will return the spending
        on all programs in the requested years.

        :param year: Optionally specify a scalar or list/array of years to return budget values
                     for. Otherwise, uses all simulation times
        :return: Dictionary keyed by program name with arrays of spending values
        """

        if self.model.progset is None:
            return None

        if year is None:
            year = self.t

        prop_coverage = self.get_coverage(quantity="fraction", year=year)
        num_eligible = self.get_coverage(quantity="eligible", year=year)

        equivalent_alloc = sc.odict()
        for prog in prop_coverage.keys():
            uc = self.model.progset.programs[prog].unit_cost.interpolate(year)
            pc = sc.dcp(prop_coverage[prog])

            if self.model.progset.programs[prog].saturation.has_data:
                sat = self.model.progset.programs[prog].saturation.interpolate(year)

                # If prop_covered is higher than the saturation then set it to nan (without the error that would happen from np.log)
                pc[pc >= sat] = np.nan

                # invert the calculation on the proportional coverage to determine the necessary "costed" coverage
                pc = -sat * np.log((sat - pc) / (sat + pc)) / 2.0

            # Calculating the program coverage, capacity constraint is applied first, then saturation, so it needs to happen second when reversing the calculation
            if self.model.progset.programs[prog].capacity_constraint.has_data:
                cap = self.model.progset.programs[prog].capacity_constraint.interpolate(year)
                # If prop_covered is higher than the capacity constraint then set it to nan as it wouldn't be possible to reach that coverage
                pc[pc * num_eligible[prog] > cap] = np.nan

            # multiply the proportion of naively costed coverage by the number of actually eligible people (catching the case where number covered would be higher than the number eligible)
            num_costed_coverage = pc * num_eligible[prog]

            equivalent_alloc[prog] = uc * num_costed_coverage

            if "/year" in self.model.progset.programs[prog].coverage.units:  # it's a one-off program, need to multiply by the time step to annualize spending
                equivalent_alloc[prog] /= self.dt

        return equivalent_alloc

    def get_coverage(self, quantity: str = "fraction", year=None) -> dict:
        """
        Return program coverage

        This function is the primary function to use when wanting to query coverage
        values. All coverage quantities are accessible via the :class:`Result` object
        because the compartment sizes and thus eligible people are known.

        **Caution** - capacity and number covered are returned in units of 'people/year'. They need to be
        accumulated by integration rather than summation.

        :param quantity: One of
            - 'capacity' - Program capacity in units of 'people/year' (for all types of programs)
            - 'eligible' - The number of people eligible for the program (coverage denominator) in units of 'people'
            - 'fraction' - ``capacity/eligible``, the fraction coverage (maximum value is 1.0) - this quantity is dimensionless
            - 'number' - The number of people covered (``fraction*eligible``) returned in units of 'people/year'

        :param year: Optionally specify a scalar or list/array of years to return budget values
                     for. Otherwise, uses all simulation times
        :return: Requested values in dictionary ``{prog_name:value}`` in requested years

        """

        from .model import JunctionCompartment

        if self.model.progset is None:
            return None

        capacities = self.model.progset.get_capacities(tvec=self.t, dt=self.dt, instructions=self.model.program_instructions)

        if quantity == "capacity":
            output = capacities
        else:
            # Get the program coverage denominator
            num_eligible = dict()  # This is the coverage denominator, number of people covered by the program
            for prog in self.model.progset.programs.values():  # For each program
                for pop_name in prog.target_pops:
                    for comp_name in prog.target_comps:
                        comp = self.get_variable(comp_name, pop_name)[0]

                        if isinstance(comp, JunctionCompartment):
                            vals = comp.outflow
                        else:
                            vals = comp.vals

                        if prog.name not in num_eligible:
                            num_eligible[prog.name] = vals.copy()
                        else:
                            num_eligible[prog.name] += vals

            # Note that `ProgramSet.get_prop_coverage()` takes in capacity in units of 'people' which matches
            # the units of 'num_eligible' so we therefore use the returned value from `ProgramSet.get_capacities()`
            # as-is without doing any annualization
            prop_coverage = self.model.progset.get_prop_coverage(tvec=self.t, dt=self.dt, capacities=capacities, num_eligible=num_eligible, instructions=self.model.program_instructions)

            if quantity in {"fraction", "annual_fraction"}:
                output = prop_coverage
            elif quantity == "eligible":
                output = num_eligible
            elif quantity == "number":
                output = {x: num_eligible[x] * prop_coverage[x] for x in prop_coverage.keys()}
            else:
                raise Exception("Unknown coverage type requested")

        if quantity in {"capacity", "number", "annual_fraction"}:
            # Return capacity and number coverage as 'people/year' rather than 'people'
            for prog in output.keys():
                if self.model.progset.programs[prog].is_one_off:
                    output[prog] /= self.dt

        if year is not None:
            for k in output.keys():
                output[k] = np.interp(sc.promotetoarray(year), self.t, output[k], left=np.nan, right=np.nan)  # Linear output interpolation

        return output

    # Convenience methods to list available comps, characs, pars, and links
    # The population name is required because different populations could have
    # different contents
    def comp_names(self, pop_name: str) -> list:
        """
        Return compartment names within a population

        :param pop_name: The code name of one of the populations
        :return: List of code names of all compartments within that population

        """

        return sorted(self.model.get_pop(pop_name).comp_lookup.keys())

    def charac_names(self, pop_name: str) -> list:
        """
        Return list of characteristic names

        This method returns all of the characteristic names available within a specified
        population

        :param pop_name: The name of one of the populations in the :class:`Result`
        :return: List of characteristic code names

        """

        return sorted(self.model.get_pop(pop_name).charac_lookup.keys())

    def par_names(self, pop_name: str) -> list:
        """
        Return list of parameter names

        This method returns all of the parameter names available within a specified
        population

        :param pop_name: The name of one of the populations in the :class:`Result`
        :return: List of parameter code names

        """

        return sorted(self.model.get_pop(pop_name).par_lookup.keys())

    def link_names(self, pop_name: str) -> list:
        """
        Return list of link names

        This method returns all of the link names available within a specified
        population. The names will be unique (so duplicate links will only appear
        once in the list of names)

        :param pop_name: The name of one of the populations in the :class:`Result`
        :return: List of link code names

        """

        names = set()
        pop = self.model.get_pop(pop_name)
        for link in pop.links:
            names.add(link.name)
        return sorted(names)

    def __repr__(self):
        output = sc.prepr(self)
        return output

    def get_variable(self, name: str, pops: str = None) -> list:
        """
        Retrieve integration objects

        This method retrieves an integration object from the model for a given
        population. It serves as a shortcut for ``model.Population.get_variable()`
        by incorporating the population lookup in the same step.

        :param pops: The name of a population
        :param name: The name of a variable
        :return: A list of matching variables (integration objects)

        """

        if pops is not None:
            return self.model.get_pop(pops).get_variable(name)
        else:
            vars = []
            for pop in self.model.pops:
                try:
                    vars += pop.get_variable(name)
                except NotFoundError:
                    pass
            if not vars:
                raise NotFoundError(f"Variable '{name}' was not found in any populations")
            return vars

    def export_raw(self, filename=None) -> pd.DataFrame:
        """
        Save raw outputs

        This method produces a single Pandas DataFrame with all of the raw model
        values, and then optionally saves it to an Excel file.

        :param filename: The file name of the Excel file to write. If not provided, no file will be written
        :return: A DataFrame with all model outputs

        """

        # Assemble the outputs into a dict
        d = dict()

        def gl(name):
            # Local helper to get name and gracefully deal with transfer parameters that don't appear in the framework
            try:
                return self.framework.get_label(name)
            except NotFoundError:
                return "-"

        for pop in self.model.pops:
            for comp in pop.comps:
                d[("Compartments", pop.name, comp.name, gl(comp.name))] = comp.vals
            for charac in pop.characs:
                d[("Characteristics", pop.name, charac.name, gl(charac.name))] = charac.vals
            for par in pop.pars:
                if par.vals is not None:
                    d[("Parameters", pop.name, par.name, gl(par.name))] = par.vals
            for link in pop.links:
                # Sum over duplicate links and annualize flow rate
                if link.parameter is None:
                    par_label = "-"
                else:
                    par_label = gl(link.parameter.name)

                if par_label == "-":
                    link_label = par_label
                else:
                    link_label = "%s (flow)" % (par_label)

                key = ("Flow rates", pop.name, link.name, link_label)
                if key not in d:
                    d[key] = np.zeros(self.t.shape)
                d[key] += link.vals / self.dt

        # Create DataFrame from dict
        df = pd.DataFrame(d, index=self.t)
        df.index.name = "Time"

        # Optionally save it
        if filename is not None:
            output_fname = Path(filename).with_suffix(".xlsx").resolve()
            df.T.to_excel(output_fname)

        return df

    def plot(self, plot_name=None, plot_group=None, pops=None, project=None):
        """
        Produce framework-defined plot

        This method plots a single Result instance using the plots defined in the framework.

        If plot_group is not None, then plot_name is ignored
        If plot_name and plot_group are both None, then all plots will be displayed

        :param plot_name: The name of a single plot in the Framework
        :param plot_group: The name of a plot group
        :param pops: A population aggregation supposed by PlotData (e.g. 'all')
        :param project: A Project instance used to plot data and full names
        :return: List of figure objects

        """

        from .plotting import PlotData, plot_series

        assert not (plot_name and plot_group), "When plotting a Result, you can specify the plot name or plot group, but not both"

        df = self.framework.sheets["plots"][0]
        df = df.dropna(subset=["name", "quantities"])  # Remove any plots that are missing names or quantities

        if plot_group is None and plot_name is None:
            for plot_name in df["name"]:
                self.plot(plot_name, pops=pops, project=project)
            return
        elif plot_group is not None:
            for plot_name in df.loc[df["plot group"] == plot_group, "name"]:
                self.plot(plot_name=plot_name, pops=pops, project=project)
            return

        this_plot = df.loc[df["name"] == plot_name, :].iloc[0]  # A Series with the row of the 'Plots' sheet corresponding to the plot we want to render

        quantities = evaluate_plot_string(this_plot["quantities"])

        # Work out which populations these are defined in
        # Going via Result.get_variable() means that it will automatically
        # work correctly for flow rate syntax as well
        if not pops:
            pops = _filter_pops_by_output(self, quantities)

        d = PlotData(self, outputs=quantities, pops=pops, project=project)
        h = plot_series(d, axis="pops", data=(project.data if project is not None else None))
        plt.title(this_plot["name"])
        return h


def _filter_pops_by_output(result, output) -> list:
    """
    Helper function for plotting quantities

    With population types, a given output/output aggregation may only be defined
    in a subset of populations. To deal with this when plotting Result objects,
    it's necessary to work out which population the requested output aggregation can be
    plotted in. This function takes in an output definition and returns a list of populations
    matching this.

    :param output: An output aggregation string e.g. 'alive' or ':ddis' or {['lt_inf','lteu']} (supported by PlotData/get_variable)
    :return: A list of population code names

    """

    if sc.isstring(output):
        vars = result.get_variable(output)
    elif isinstance(output, list):
        vars = result.get_variable(output[0])
    elif isinstance(output, dict):
        v = list(output.values())[0]
        if isinstance(v, list):
            vars = result.get_variable(v[0])
        elif sc.isstring(v):
            # It could be a function aggregation or it could be a single one
            _, deps = parse_function(v)
            vars = result.get_variable(deps[0])
    else:
        raise Exception("Could not determine population type")

    matching_pops = {x.pop.name for x in vars}
    return [x for x in result.pop_names if x in matching_pops]  # Maintain original population order


def export_results(results, filename=None, output_ordering=("output", "result", "pop"), cascade_ordering=("pop", "result", "stage"), program_ordering=("program", "result", "quantity")):
    """Export Result outputs to a file

    This function writes an XLSX file with the data corresponding to any Cascades or Plots
    that are present. Note that results are exported for every year by selecting integer years.
    Flow rates are annualized instantaneously. So for example, the flow will have values from
    2014, 2015, 2016, but the 2015 flow rate is the actual flow at 2015.0 divided by dt, not the
    time-aggregated flow rate. Time-aggregation isn't appropriate here because many of the quantities
    plotted are probabilities. Selecting the annualized value at a particular year also means that the
    data being exported will match up with whatever plots are generated from within Atomica.

    Optionally can specify a list/set of names of the plots/cascades to include in the export
    Set to an empty list to omit that category e.g.

    >>> plot_names = None # export all plots in framework
    >>> plot_names = ['a','b'] # export only plots 'a' and 'b'
    >>> plot_names = [] # don't export any plots e.g. to only export cascades

    :param results: A :class:`Result`, or list of `Results`. Results must all have different names. Outputs are drawn from the first result, normally
                    all results would have the same framework and populations.
    :param filename: Write an excel file. If 'None', no file will be written (but dataframes will be returned)
    :param output_ordering: A tuple specifying the grouping of outputs, results, and pops for the Plots and targetable parameters sheet.
                            The first item in the tuple will split the dataframes into separate tables. Then within the tables, rows
                            will be grouped by the second item
    :param cascade_ordering: A similar tuple specifying the groupings for the cascade sheets. The cascade tables are always split by cascade first,
                             so the order in this tuple only affects the column ordering
    :param program_ordering: A similar tuple specifying the groupings for the program sheets
    :return: The name of the file that was written

    """

    # Check all results have unique names
    if isinstance(results, dict):
        results = list(results.values())
    else:
        results = sc.promotetolist(results)

    result_names = [x.name for x in results]
    if len(set(result_names)) != len(result_names):
        raise Exception("Results must have different names (in their result.name property)")

    # Check all results have the same time range
    for result in results:
        if result.t[0] != results[0].t[0] or result.t[-1] != results[0].t[-1]:
            raise Exception("All results must have the same start and finish years")

        if set(result.pop_names) != set(results[0].pop_names):
            raise Exception("All results must have the same populations")

    # Interpolate all outputs onto these years
    new_tvals = np.arange(np.ceil(results[0].t[0]), np.floor(results[0].t[-1]) + 1)

    # Open the output file
    output_fname = Path(filename).with_suffix(".xlsx").resolve()
    writer = pd.ExcelWriter(output_fname, engine="xlsxwriter")
    formats = standard_formats(writer.book)

    # Write the plots sheet if any plots are available
    if "plots" in results[0].framework.sheets:
        plots_available = results[0].framework.sheets["plots"][0]

        if not plots_available.empty:
            plot_df = []
            for _, spec in plots_available.iterrows():
                if "type" in spec and spec["type"] == "bar":
                    continue  # For now, don't do bars - not implemented yet
                plot_df.append(_output_to_df(results, output_name=spec["name"], output=evaluate_plot_string(spec["quantities"]), tvals=new_tvals, time_aggregate=False))
            _write_df(writer, formats, "Plot data annualized", pd.concat(plot_df), output_ordering)

            plot_df = []
            for _, spec in plots_available.iterrows():
                if "type" in spec and spec["type"] == "bar":
                    continue  # For now, don't do bars - not implemented yet
                plot_df.append(_output_to_df(results, output_name=spec["name"], output=evaluate_plot_string(spec["quantities"]), tvals=new_tvals, time_aggregate=True))
            _write_df(writer, formats, "Plot data annual aggregated", pd.concat(plot_df), output_ordering)

    # Write cascades into separate sheets
    cascade_df = []
    for name in results[0].framework.cascades.keys():
        cascade_df.append(_cascade_to_df(results, name, new_tvals))
    if cascade_df:
        # always split tables by cascade, since different cascades can have different stages or the same stages with different definitions
        # it's thus potentially very confusing if the tables are split by something other than the cascade
        _write_df(writer, formats, "Cascade", pd.concat(cascade_df), ("cascade",) + cascade_ordering)

    # If there are targetable parameters, output them
    targetable_code_names = list(results[0].framework.pars.index[results[0].framework.pars["targetable"] == "y"])
    if targetable_code_names:
        par_df = []
        for par_name in targetable_code_names:
            par_df.append(_output_to_df(results, output_name=par_name, output=par_name, tvals=new_tvals))
        _write_df(writer, formats, "Target parameters annualized", pd.concat(par_df), output_ordering)

    # If any of the results used programs, output them
    if any([x.used_programs for x in results]):

        # Work out which programs are present
        prog_names = list()
        for result in results:
            if result.used_programs:
                prog_names += list(result.model.progset.programs.keys())
        prog_names = list(dict.fromkeys(prog_names))

        prog_df = []
        for prog_name in prog_names:
            prog_df.append(_programs_to_df(results, prog_name, new_tvals, time_aggregate=False))
        _write_df(writer, formats, "Programs annualized", pd.concat(prog_df), program_ordering)

        prog_df = []
        for prog_name in prog_names:
            prog_df.append(_programs_to_df(results, prog_name, new_tvals, time_aggregate=True))
        _write_df(writer, formats, "Programs annual aggregated", pd.concat(prog_df), program_ordering)

    writer.close()

    return output_fname


def _programs_to_df(results, prog_name, tvals, time_aggregate=False):
    """
    Return a DataFrame for program outputs for a group of results

    The dataframe will have a three-level MultiIndex for the program, result, and program quantity
    (e.g. spending, coverage fraction)

    :param results: List of Results
    :param prog_name: The name of a program
    :param tvals: Outputs will be interpolated onto the times in this array (typically would be annual)
    :param time_aggregate: False means output annualized Jan 1 values, True means use time_aggregation to sum or average the timestep values over the year for each parameter.
    :return: A DataFrame

    """

    from .plotting import PlotData

    data = dict()

    for result in results:
        if result.used_programs and prog_name in result.model.progset.programs:
            programs_active = (result.model.program_instructions.start_year <= tvals) & (tvals <= result.model.program_instructions.stop_year)

            out_quantities = {
                "spending": "Spending ($)" if time_aggregate else "Spending ($/year)",
                "equivalent_spending": "Equivalent spending ($)" if time_aggregate else "Equivalent spending ($/year)",
                "coverage_number": "People covered" if time_aggregate else "People covered (people/year)",
                "coverage_eligible": "People eligible",
                "coverage_fraction": "Proportion covered",
            }

            for quantity, label in out_quantities.items():
                plot_data = PlotData.programs(result, outputs=prog_name, quantity=quantity)
                vals = plot_data.time_aggregate(_extend_tvals(tvals)) if time_aggregate else plot_data.interpolate(tvals)
                vals.series[0].vals[~programs_active] = np.nan
                data[(prog_name, result.name, label)] = vals.series[0].vals

    df = pd.DataFrame(data, index=tvals)
    df = df.T
    df.index = df.index.set_names(["program", "result", "quantity"])  # Set the index names correctly so they can be reordered easily

    return df


def _extend_tvals(tvals):
    """
    Given a list of time values, add an extra time value to the end to allow these time values to be used with time_integration instead of interpolate
    :param tvals: array or list of time values (ints)
    """
    assert isinstance(tvals, (list, np.ndarray)), "Time values must be an array or list "
    if len(tvals) == 0:
        return tvals  # no time values to add to, return as is (empty list or array)
    else:
        for tv in range(1, len(tvals)):
            assert tvals[tv] == tvals[tv - 1] + 1, "Time values should be one year apart, otherwise time integration may produce inconsistent results, use interpolation instead"

        return np.append(tvals, [tvals[-1] + 1])  # return the list or array with one more year added on to the end


def _cascade_to_df(results, cascade_name, tvals):
    """
    Return a DataFrame for a cascade for a group of results

    The dataframe will have a three-level MultiIndex for the result, population, and cascade stage
    :param results: List of Results
    :param cascade_name: The name or index of a cascade stage (interpretable by get_cascade_vals)
    :param tvals: Outputs will be interpolated onto the times in this array (typically would be annual)
    :return: A DataFrame

    """

    from .cascade import get_cascade_vals, sanitize_cascade

    # Find the cascade pop type
    _, cascade_dict, pop_type = sanitize_cascade(results[0].framework, cascade_name)

    # Prepare the population names and time values
    pop_names = dict()
    pop_names["all"] = "Entire population"
    for pop in results[0].model.pops:
        if pop.type == pop_type:
            pop_names[pop.name] = pop.label

    cascade_df = []
    for pop, label in pop_names.items():
        data = sc.odict()
        for result in results:
            cascade_vals, _ = get_cascade_vals(result, cascade_name, pops=pop, year=tvals)
            for stage, vals in cascade_vals.items():
                data[(cascade_name, pop_names[pop], result.name, stage)] = vals
        df = pd.DataFrame(data, index=tvals)
        df = df.T
        df.index = df.index.set_names(["cascade", "pop", "result", "stage"])  # Set the index names correctly so they can be reordered easily
        cascade_df.append(df)

    return pd.concat(cascade_df)


def _output_to_df(results, output_name: str, output, tvals, time_aggregate=False) -> pd.DataFrame:
    """
    Convert an output to a DataFrame for a group of results

    This function takes in a list of results, and an output specification recognised by :class:`PlotData`.
    It extracts the outputs from all results and stores them in a 3-level MultiIndexed dataframe, which is
    returned. The index levels are the name of the output, the name of the results, and the populations.

    In addition, this function attempts to aggregate the outputs, if the units of the outputs matches
    known units. If the units lead to anver obvious use of summation or weighted averating, it will be used.
    Otherwise, the output will contain NaNs for the population-aggregated results, which will appear as empty
    cells in the Excel spreadsheet so the user is able to fill them in themselves.

    :param results: List of Results
    :param output_name: The name to use for the output quantity
    :param output: An output specification/aggregation supported by :class:`PlotData`
    :param tvals: Outputs will be interpolated onto the times in this array (typically would be annual)
    :param time_aggregate: False means output annualized Jan 1 values, True means use time_aggregation to sum or average the timestep values over the year for each parameter.
    :return: A DataFrame

    """

    from .plotting import PlotData

    pops = _filter_pops_by_output(results[0], output)
    pop_labels = {x: y for x, y in zip(results[0].pop_names, results[0].pop_labels) if x in pops}
    data = dict()

    popdata = PlotData(results, pops=pops, outputs=output)
    assert len(popdata.outputs) == 1, "Framework plot specification should evaluate to exactly one output series - there were %d" % (len(popdata.outputs))
    if time_aggregate:
        popdata.time_aggregate(_extend_tvals(tvals))
    else:
        popdata.interpolate(tvals)
    for result in popdata.results:
        for pop_name in popdata.pops:
            data[(output_name, popdata.results[result], pop_labels[pop_name])] = popdata[result, pop_name, popdata.outputs[0]].vals

    # Now do a population total. Need to check the units after any aggregations
    # Check results[0].model.pops[0].comps[0].units just in case someone changes it later on
    if popdata.series[0].units in {FS.QUANTITY_TYPE_NUMBER, results[0].model.pops[0].comps[0].units}:
        # Number units, can use summation
        popdata = PlotData(results, outputs=output, pops={"total": pops}, pop_aggregation="sum")
        if time_aggregate:
            popdata.time_aggregate(_extend_tvals(tvals))
        else:
            popdata.interpolate(tvals)
        for result in popdata.results:
            data[(output_name, popdata.results[result], "Total (sum)")] = popdata[result, popdata.pops[0], popdata.outputs[0]].vals
    elif popdata.series[0].units in {FS.QUANTITY_TYPE_FRACTION, FS.QUANTITY_TYPE_PROPORTION, FS.QUANTITY_TYPE_PROBABILITY}:
        popdata = PlotData(results, outputs=output, pops={"total": pops}, pop_aggregation="weighted")
        if time_aggregate:
            popdata.time_aggregate(_extend_tvals(tvals))
        else:
            popdata.interpolate(tvals)
        for result in popdata.results:
            data[(output_name, popdata.results[result], "Total (weighted average)")] = popdata[result, popdata.pops[0], popdata.outputs[0]].vals
    else:
        for result in popdata.results:
            data[(output_name, popdata.results[result], "Total (unknown units)")] = np.full(tvals.shape, np.nan)

    df = pd.DataFrame(data, index=tvals)
    df = df.T
    df.index = df.index.set_names(["output", "result", "pop"])  # Set the index names correctly so they can be reordered easily
    return df


def _write_df(writer, formats, sheet_name, df, level_ordering):
    """
    Write a list of DataFrames into a worksheet

    :param writer: A Pandas ExcelWriter instance specifying the file to write into
    :param formats: The output of `standard_formats(workbook)` specifying the styles embedded in the workbook
    :param sheet_name: The name of the sheet to create. It is assumed that this sheet will be generated entirely by
                       this function call (i.e. the sheet is not already present)
    :param df: A DataFrame that has a MultiIndex
    :param level_ordering: Tuple of index level names. Split the dataframe such that a separate table is
                           generated for the first level, and then the rows are reordered by the remaining levels and the
                           original sort order is preserved. The contents of this tuple need to match the levels
                           present in the dataframe
    :return: None

    """

    # Substitute full names for short names after re-ordering the levels but before
    # writing the dataframe
    level_substitutions = {"pop": "Population", "stage": "Cascade stage", "quantity": "Quantity (on Jan 1)"}

    # Remember the ordering of each index level
    order = {}
    for level in level_ordering:
        order[level] = list(dict.fromkeys(df.index.get_level_values(level)))

    required_width = [0] * (len(level_ordering) - 1)

    row = 0

    worksheet = writer.book.add_worksheet(sheet_name)
    writer.sheets[sheet_name] = worksheet  # Need to add it to the ExcelWriter for it to behave properly

    for title, table in df.groupby(level=level_ordering[0], sort=False):
        worksheet.write_string(row, 0, title, formats["center_bold"])
        row += 1

        table.reset_index(level=level_ordering[0], drop=True, inplace=True)  # Drop the title column
        table = table.reorder_levels(level_ordering[1:])
        for i in range(1, len(level_ordering)):
            table = table.reindex(order[level_ordering[i]], level=i - 1)
        table.index = table.index.set_names([level_substitutions[x] if x in level_substitutions else x.title() for x in table.index.names])
        table.to_excel(writer, sheet_name, startcol=0, startrow=row)
        row += table.shape[0] + 2

        required_width[0] = max(required_width[0], len(title))
        for i in range(0, len(required_width)):
            required_width[i] = max(required_width[i], max(table.index.get_level_values(i).str.len()))

    for i in range(0, len(required_width)):
        if required_width[i] > 0:
            worksheet.set_column(i, i, required_width[i] * 1.1 + 1)


class Ensemble(NamedItem):
    """
    Class for working with sampled Results

    This class facilitates working with results and sampling.
    It manages the mapping of sets of results onto a scalar, which is
    then accumulated over samples. For example, we might sample from
    a ParameterSet and then run simulations with 2 different allocations to
    compare their expected difference. The Ensemble contains

    - A reduction function that maps from Results^N => R^M where typically M would
      index

    :param mapping_function: A function that takes in a Result, or a list/dict of Results, and returns a single PlotData instance
    :param name: Name for the Ensemble (will appear on plots)
    :param baseline: Optionally provide the non-sampled results at instantiation
    :param kwargs: Additional arguments to pass to the mapping function

    """

    def __init__(self, mapping_function=None, name: str = None, baseline_results=None, **kwargs):

        NamedItem.__init__(self, name)
        self.mapping_function = mapping_function  #: This function gets called by :meth:`Ensemble.add_sample`
        self.samples = []  #: A list of :class:`PlotData` instances, one for each sample
        self.baseline = None  #: A single PlotData instance with reference values (i.e. outcome without sampling)

        if baseline_results:
            self.set_baseline(baseline_results, **kwargs)

    def run_sims(self, proj, parset, progset=None, progset_instructions=None, result_names=None, n_samples: int = 1, parallel=False, max_attempts=None) -> None:
        """
        Run and store sampled simulations

        Use this method to perform sampling if there is insufficient memory available to store
        all simulations prior to inserting into the Ensemble. This method adds Results to the
        Ensemble one at a time, so the memory required is never more than the number of Results
        taken in by the mapping function (typically this would either be 1, or the number of
        budget scenarios being compared).

        Note that a separate function, `_sample_and_map` is used, which does the conversion to
        ``PlotData``. This is so that the data reduction is performed on the parallel workers
        so that ``Multiprocessing`` only accumulates ``PlotData`` rather than ``Result`` instances.

        :param proj: A :class:`Project` instance
        :param n_samples: An integer number of samples
        :param parset: A :class:`ParameterSet` instance
        :param progset: Optionally a :class:`ProgramSet` instance
        :param progset_instructions: This can be a list of instructions
        :param result_names: Optionally specify names for each result. The most common usage would be when passing in a list of program instructions
                             corresponding to different budget scenarios. The result names should be a list the same length as the instructions, or
                             containing a single element if not using programs.
        :param parallel: If True, run simulations in parallel (on Windows, must have ``if __name__ == '__main__'`` gating the calling code)
        :param max_attempts: Number of retry attempts for bad initializations

        """

        self.samples = []  # Drop the old samples

        if parallel:
            # NB. The calling code must be wrapped in a 'if __name__ == '__main__'
            # Currently not passing in any extra kwargs but that should be easy to add if/when required
            # (main reason for deferring implementation is so as to have suitable test code when developing)
            self.samples = sc.parallelize(_sample_and_map, iterarg=n_samples, kwargs={"mapping_function": self.mapping_function, "max_attempts": max_attempts, "proj": proj, "parset": parset, "progset": progset, "progset_instructions": progset_instructions, "result_names": result_names})
        else:
            original_level = logger.getEffectiveLevel()
            logger.setLevel(logging.WARNING)  # Never print debug messages inside the sampling loop - note that depending on the platform, this may apply within `sc.parallelize`

            if original_level <= logging.INFO:
                range_iterator = tqdm.trange(n_samples)
            else:
                range_iterator = range(n_samples)

            for _ in range_iterator:
                sample = _sample_and_map(mapping_function=self.mapping_function, proj=proj, parset=parset, progset=progset, progset_instructions=progset_instructions, result_names=result_names, max_attempts=max_attempts)
                self.samples.append(sample)

            logger.setLevel(original_level)  # Reset the logger

        # Finally, set the colours for the first sample
        self.samples[0].set_colors(pops=self.samples[0].pops, outputs=self.samples[0].outputs)

    @property
    def n_samples(self) -> int:
        """
        Return number of samples present

        :return: Number of samples contained in the :class:`Ensemble`

        """

        return len(self.samples)

    @property
    def outputs(self) -> list:
        """
        Return a list of outputs

        The outputs are retrieved from the first sample, or the baseline
        if no samples are present yet, or an empty list if no samples present.

        It is generally assumed that the baseline and all samples should have the
        same outputs and populations, because they should have all been generated
        with the same mapping function

        :return: A list of outputs (strings)

        """
        if self.samples:
            return list(self.samples[0].outputs.keys())
        elif self.baseline:
            return list(self.baseline.outputs.keys())
        else:
            return list()

    @property
    def tvec(self) -> np.array:
        """
        Return time vector

        The time vector are retrieved from the first sample, or the baseline
        if no samples are present yet, or an empty list if no samples present.

        :return: A time array from one of the stores :class:`PlotData` instances

        """

        if self.samples:
            return self.samples[0].series[0].tvec
        elif self.baseline:
            return self.baseline[0].series[0].tvec
        else:
            return np.empty(0)

    @property
    def pops(self) -> list:
        """
        Return a list of populations

        The pops are retrieved from the first sample, or the baseline
        if no samples are present yet, or an empty list if no samples present.

        It is generally assumed that the baseline and all samples should have the
        same outputs and populations, because they should have all been generated
        with the same mapping function

        :return: A list of population names (strings)

        """
        if self.samples:
            return list(self.samples[0].pops.keys())
        elif self.baseline:
            return list(self.baseline.pops.keys())
        else:
            return list()

    @property
    def results(self) -> list:
        """
        Return a list of result names

        The result names are retrieved from the first sample, or the baseline
        if no samples are present yet, or an empty list if no samples present.

        It is generally assumed that the results will all have the same name in the
        case that this Ensemble contains multiple PlotData samples. Otherwise, a key
        error may occur.

        :return: A list of population names (strings)

        """
        if self.samples:
            return list(self.samples[0].results.keys())
        elif self.baseline:
            return list(self.baseline.results.keys())
        else:
            return list()

    def _get_series(self) -> dict:
        """
        Flatten the series in samples

        The Ensemble contains a list of `PlotData` containing a list of `Series`. Computing
        uncertainty requires iterating over the Series for a a particular result, pop, and output.
        This function returns a dict keyed by a ``(result,pop,output)`` tuple with a list of
        references to the underlying series. Thus, the series are organized either by `self.samples`
        which facilitates adding new samples, and `self._get_series` which facilitates computing
        uncertainties after the fact.

        :return: A dict keyed by result-pop-output containing lists of sampled Series

        """

        series_lookup = defaultdict(list)
        for sample in self.samples:
            for series in sample.series:
                series_lookup[(series.result, series.pop, series.output)].append(series)
        return sc.odict(series_lookup)

    def set_baseline(self, results, **kwargs) -> None:
        """
        Add a baseline to the Ensemble

        This function assigns a special result corresponding to the unsampled case
        as a reference. This result can be rendered in a different way on plots - for
        example, as a vertical line on density estimates, or a solid line on a time series plot.

        :param results: A Result, or list/dict of Results, as supported by the mapping function
        :param kwargs: Any additional keyword arguments to pass to the mapping function

        """

        from .plotting import PlotData

        plotdata = self.mapping_function(results, **kwargs)
        assert isinstance(plotdata, PlotData)  # Make sure the mapping function returns the correct type
        # assert len(plotdata.results) == 1, 'The mapping function must return a PlotData instance with only one Result'
        self.baseline = plotdata.set_colors(pops=plotdata.pops, outputs=plotdata.outputs)

    def add(self, results, **kwargs) -> None:
        """
        Add a sample to the Ensemble

        This function takes in Results and optionally any other arguments needed
        by the Ensemble's mapping function. It calls the mapping function and adds
        the resulting PlotData instance to the list of samples.

        :param results: A Result, or list/dict of Results, as supported by the mapping function
        :param kwargs: Any additional keyword arguments to pass to the mapping function

        """

        from .plotting import PlotData

        plotdata = self.mapping_function(results, **kwargs)
        assert isinstance(plotdata, PlotData)  # Make sure the mapping function returns the correct type
        # assert len(plotdata.results) == 1, 'The mapping function must return a PlotData instance with only one Result'
        if not self.samples:
            # Set the colors on the first PlotData to be added - for performance, only do this for the first sample
            plotdata.set_colors(pops=plotdata.pops, outputs=plotdata.outputs)
        self.samples.append(plotdata)

    def update(self, result_list, **kwargs) -> None:
        """
        Add multiple samples to the Ensemble

        The implementation of :meth:`add` vs :meth`update` parallels the behaviour of
        Python built-in sets, where :meth:`set.add` is used to add a single item, and
        :meth:`set.update` is used to add multiple items. This function is intended for
        cases where the user has stores multiple samples in memory and wants to dynamically
        construct Ensembles after the fact.

        The input list here is an iterable, and :meth:`Ensemble.add` gets called on every
        item in the list. It is up to the mapping function then to handle whether the items
        in `result_list` are single :class:`Result` instances or lists/tuples/dicts of Results.

        :param result_list: A list of samples, as supported by the mapping function (i.e.
                            the individual items would work with :meth:`Ensemble.add`)
        :param kwargs: Any additional keyword arguments to pass to the mapping function

        """

        for sample in result_list:
            self.add(sample, **kwargs)

    def plot_distribution(self, year: float = None, fig=None, results=None, outputs=None, pops=None):
        """
        Plot a kernel density distribution

        This method will plot kernel density estimates for all outputs and populations in
        the Ensemble.

        The :class:`PlotData` instances stored in the Ensemble could contain more than one
        output/population. To facilitate superimposing Ensembles, by default they will all be plotted
        into the figure. Specifying a string or list of strings for the outputs and pops will select
        a subset of the quantities to plot. Most of the time, an Ensemble would only have one output/pop,
        so it probably wouldn't matter.

        :param year: If ``None``, plots the first time index, otherwise, interpolate to the target year
        :param fig: Optionally specify a figure handle to plot into
        :param results: Optionally specify list of result names
        :param outputs: Optionally specify list of outputs
        :param pops: Optionally specify list of pops
        :return: A matplotlib figure (note that this method will only ever return a single figure)

        """

        if not self.samples:
            raise Exception("Cannot plot samples because no samples have been added yet")
        results = sc.promotetolist(results) if results is not None else self.results
        outputs = sc.promotetolist(outputs) if outputs is not None else self.outputs
        pops = sc.promotetolist(pops) if pops is not None else self.pops

        if fig is None:
            fig = plt.figure()
        ax = plt.gca()

        series_lookup = self._get_series()

        for result in results:
            for output in outputs:
                for pop in pops:
                    # Assemble the outputs
                    if year is None:
                        vals = np.array([x.vals[0] for x in series_lookup[result, pop, output]])
                    else:
                        vals = np.array([x.interpolate(year) for x in series_lookup[result, pop, output]])

                    # color = series_lookup[output,pop][0].color
                    value_range = (vals.min(), vals.max())

                    if value_range[0] == value_range[1]:
                        color = None
                        logger.warning("All values for %s-%s are the same, so no distribution will be visible" % (output, pop))
                    else:
                        kernel = stats.gaussian_kde(vals.ravel())
                        scale_up_range = 1.5  # Increase kernel density x range
                        span = np.average(value_range) + np.diff(value_range) * [-1, 1] / 2 * scale_up_range
                        x = np.linspace(*span, 100)
                        # TODO - expand this range a bit
                        h = plt.plot(x, kernel(x), label="%s: %s-%s-%s" % (self.name, result, pop, output))[0]
                        color = h.get_color()

                    if self.baseline:
                        series = self.baseline[result, pop, output]
                        val = series.vals[0] if year is None else series.interpolate(year)
                        plt.axvline(val, color=color, linestyle="dashed")

                    proposed_label = "%s (%s)" % (output, series_lookup[result, pop, output][0].unit_string)
                    if ax.xaxis.get_label().get_text():
                        assert proposed_label == ax.xaxis.get_label().get_text(), "The outputs being superimposed have different units"
                    else:
                        plt.xlabel(proposed_label)

        plt.legend()
        plt.ylabel("Probability density")

        return fig

    def plot_series(self, fig=None, style="quartile", results=None, outputs=None, pops=None, legend=True):
        """
        Plot a time series with uncertainty

        :param fig: Optionally specify the figure to render into
        :param style: Specify whether to plot transparent lines ('samples'), or shaded areas for uncertainty. For shaded areas,
                      the style can be 'std', 'ci', or 'quartile' depending on how the size of the area should be computed
        :param results: Select specific results to display
        :param outputs: Select specific outputs to display
        :param pops: Select specific populations to display
        :return: The figure object that was rendered into

        """

        assert style in {"samples", "quartile", "ci", "std"}

        if not self.samples:
            raise Exception("Cannot plot samples because no samples have been added yet")
        results = sc.promotetolist(results) if results is not None else self.results
        outputs = sc.promotetolist(outputs) if outputs is not None else self.outputs
        pops = sc.promotetolist(pops) if pops is not None else self.pops

        if fig is None:
            fig = plt.figure()
        ax = plt.gca()

        series_lookup = self._get_series()

        for result in results:
            for output in outputs:
                for pop in pops:

                    these_series = series_lookup[result, pop, output]
                    vals = np.vstack([x.vals.ravel() for x in these_series])  # Turn samples into a matrix

                    if self.baseline:
                        baseline_series = self.baseline[result, pop, output]
                        plt.plot(baseline_series.tvec, baseline_series.vals, color=baseline_series.color, label="%s: %s-%s-%s (baseline)" % (self.name, result, pop, output))[0]
                    else:
                        plt.plot(these_series[0].tvec, np.mean(vals, axis=0), color=these_series[0].color, linestyle="dashed", label="%s: %s-%s-%s (mean)" % (self.name, result, pop, output))[0]

                    if style == "samples":
                        for series in these_series:
                            plt.plot(series.tvec, series.vals, color=series.color, alpha=0.05)

                    elif style == "quartile":
                        ax.fill_between(these_series[0].tvec, np.quantile(vals, 0.25, axis=0), np.quantile(vals, 0.75, axis=0), alpha=0.15, color=these_series[0].color)
                    elif style == "ci":
                        ax.fill_between(these_series[0].tvec, np.quantile(vals, 0.025, axis=0), np.quantile(vals, 0.975, axis=0), alpha=0.15, color=these_series[0].color)
                    elif style == "std":
                        if self.baseline:
                            ax.fill_between(baseline_series.tvec, baseline_series.vals - np.std(vals, axis=0), baseline_series.vals + np.std(vals, axis=0), alpha=0.15, color=baseline_series.color)
                        else:
                            ax.fill_between(these_series[0].tvec, np.mean(vals, axis=0) - np.std(vals, axis=0), np.mean(vals, axis=0) + np.std(vals, axis=0), alpha=0.15, color=these_series[0].color)
                    else:
                        raise Exception("Unknown style")

            proposed_label = "%s (%s)" % (output, these_series[0].unit_string)
            if ax.yaxis.get_label().get_text():
                assert proposed_label == ax.yaxis.get_label().get_text(), "The outputs being superimposed have different units"
            else:
                ax.set_ylabel(proposed_label)

        ax.set_xlabel("Year")
        if legend:
            ax.legend()
        return fig

    def plot_bars(self, fig=None, years=None, results=None, outputs=None, pops=None, order=("years", "results", "outputs", "pops"), horizontal=False, offset: float = None):
        """
        Render a bar plot

        Very similar to a boxplot, the bar plot with error bars doesn't support stacking
        (because it can be misleading when stacking bars with errors, since the errors
        apply cumulatively within the bar).

        If an existing figure is provided, this function will attempt to add to the existing
        figure by offsetting the new bars relative to the current axis limits. This is intended
        to facilitate comparing bar plots across multiple Ensembles.

        :param fig: Optionally specify an existing figure to plot into
        :param years: Optionally specify years - otherwise, first time point will be used. Data is interpolated onto this year
        :param results: Optionally specify list of result names
        :param outputs: Optionally specify list of outputs
        :param pops: Optionally specify list of pops
        :param order: An iterable specifying the order in which bars appear - should be a permutation of ``('years','results','outputs','pops')``
        :param horizontal: If True, bar plot will be horizontal
        :param offset: Offset value to apply to the position of the bar. If ``None``, will be automatically determined based
                       on existing plot contents.
        :return: A matplotlib figure (note that this method will only ever return a single figure)

        """

        if not self.samples:
            raise Exception("Cannot plot samples because no samples have been added yet")
        results = sc.promotetolist(results) if results is not None else self.results
        outputs = sc.promotetolist(outputs) if outputs is not None else self.outputs
        pops = sc.promotetolist(pops) if pops is not None else self.pops
        if years is None:
            years = [None]
        else:
            years = sc.promotetolist(years)

        if fig is None:
            fig, ax = plt.subplots()
            offset = 0
        else:
            ax = fig.axes[0]
            if horizontal:
                offset = np.floor(max(ax.get_ylim())) + 1
            else:
                offset = np.floor(max(ax.get_xlim())) + 1

        series_lookup = self._get_series()

        x = []
        baselines = []
        labels = []

        base_order = ("years", "results", "outputs", "pops")
        for year, result, output, pop in nested_loop([years, results, outputs, pops], map(base_order.index, order)):

            if year is None:
                vals = np.array([x.vals[0] for x in series_lookup[result, pop, output]])
                year_val = series_lookup[result, pop, output][0].tvec[0]
                labels.append("%s: %s-%s-%s (%g)" % (self.name, result, pop, output, year_val))
            else:
                vals = np.array([x.interpolate(year) for x in series_lookup[result, pop, output]])
                labels.append("%s: %s-%s-%s (%g)" % (self.name, result, pop, output, year))

            if self.baseline:
                if year is None:
                    baselines.append(self.baseline[result, pop, output].vals[0])
                else:
                    baselines.append(self.baseline[result, pop, output].interpolate(year)[0])
            else:
                baselines.append(np.mean(vals))

            x.append(vals.ravel())

        locations = offset + np.arange(len(x))
        sample_array = np.vstack(x).T
        sample_errors = np.std(sample_array, axis=0)

        for location, baseline, error, label in zip(locations, baselines, sample_errors, labels):
            if horizontal:
                ax.barh(location, baseline, xerr=error, capsize=10, label=label, height=0.5)
            else:
                ax.bar(location, baseline, yerr=error, capsize=10, label=label, width=0.5)

        ax.legend()

        proposed_label = "%s (%s)" % (output, series_lookup[result, pop, output][0].unit_string)

        if horizontal:
            ax.set_ylim(-0.5, locations[-1] + 0.5)
            if ax.xaxis.get_label().get_text():
                assert proposed_label == ax.xaxis.get_label().get_text(), "The outputs being superimposed have different units"
            else:
                plt.xlabel(proposed_label)
            ax.set_yticks([])
        else:
            ax.set_xlim(-0.5, locations[-1] + 0.5)
            if ax.yaxis.get_label().get_text():
                assert proposed_label == ax.yaxis.get_label().get_text(), "The outputs being superimposed have different units"
            else:
                plt.ylabel(proposed_label)
            ax.set_xticks([])

        return fig

    def boxplot(self, fig=None, years=None, results=None, outputs=None, pops=None):
        """
        Render a box plot

        This is effectively an alternate approach to rendering the
        kernel density estimates for the distributions. The figure
        will have a box plot showing quantiles as whiskers for each
        quantity selected, filtered by the results, outputs, and pops
        arguments.

        :param fig: Optionally specify an existing figure to plot into
        :param years: Optionally specify years - otherwise, first time point will be used
        :param results: Optionally specify list of result names
        :param outputs: Optionally specify list of outputs
        :param pops: Optionally specify list of pops
        :return: A matplotlib figure (note that this method will only ever return a single figure)

        """

        if not self.samples:
            raise Exception("Cannot plot samples because no samples have been added yet")
        results = sc.promotetolist(results) if results is not None else self.results
        outputs = sc.promotetolist(outputs) if outputs is not None else self.outputs
        pops = sc.promotetolist(pops) if pops is not None else self.pops
        if years is None:
            years = [None]
        else:
            years = sc.promotetolist(years)

        if fig is None:
            fig, ax = plt.subplots()
            offset = 0
        else:
            ax = fig.axes[0]
            offset = len(ax.get_xticks())

        series_lookup = self._get_series()

        x = []
        baseline = []
        labels = []
        for year in years:
            for result in results:
                for output in outputs:
                    for pop in pops:

                        if self.baseline:
                            if year is None:
                                baseline.append(self.baseline[result, pop, output].vals[0])
                            else:
                                baseline.append(self.baseline[result, pop, output].interpolate(year)[0])

                        if year is None:
                            vals = np.array([x.vals[0] for x in series_lookup[result, pop, output]])
                            year_val = series_lookup[result, pop, output][0].tvec[0]
                            labels.append("%s: %s-%s-%s (%g)" % (self.name, result, pop, output, year_val))
                        else:
                            vals = np.array([x.interpolate(year) for x in series_lookup[result, pop, output]])
                            labels.append("%s: %s-%s-%s (%g)" % (self.name, result, pop, output, year))
                        x.append(vals.ravel())

        locations = offset + np.arange(len(x))

        # TODO - force matplotlib>=3.1 to address this
        import matplotlib

        if sc.compareversions(matplotlib.__version__, "3.1") < 0:
            plt.boxplot(np.vstack(x).T, positions=locations, manage_xticks=False)
        else:
            plt.boxplot(np.vstack(x).T, positions=locations, manage_ticks=False)

        ax.set_xlim(-0.5, locations[-1] + 0.5)
        if offset == 0:
            ax.set_xticks(np.arange(locations[-1] + 1))
            ax.set_xticklabels(labels)
        else:
            new_labels = [x.get_text() for x in ax.get_xticklabels()] + labels
            ax.set_xticks(np.arange(locations[-1] + 1))
            ax.set_xticklabels(new_labels)

        proposed_label = "%s (%s)" % (output, series_lookup[result, pop, output][0].unit_string)
        if ax.yaxis.get_label().get_text():
            assert proposed_label == ax.yaxis.get_label().get_text(), "The outputs being superimposed have different units"
        else:
            plt.ylabel(proposed_label)

        return fig

    def summary_statistics(self, years=None, results=None, outputs=None, pops=None):
        if not self.samples:
            raise Exception("Cannot plot samples because no samples have been added yet")
        results = sc.promotetolist(results) if results is not None else self.results
        outputs = sc.promotetolist(outputs) if outputs is not None else self.outputs
        pops = sc.promotetolist(pops) if pops is not None else self.pops
        if years is None:
            years = [None]
        else:
            years = sc.promotetolist(years)

        series_lookup = self._get_series()
        records = list()

        for year in years:
            for result in results:
                for output in outputs:
                    for pop in pops:

                        if self.baseline:
                            if year is None:
                                baseline = self.baseline[result, pop, output].vals[0]
                            else:
                                baseline = self.baseline[result, pop, output].interpolate(year)[0]
                            records.append((year, result, output, pop, "baseline", baseline))

                        if year is None:
                            vals = np.array([x.vals[0] for x in series_lookup[result, pop, output]])
                        else:
                            vals = np.array([x.interpolate(year) for x in series_lookup[result, pop, output]])

                        records.append((year, result, output, pop, "mean", np.mean(vals)))
                        records.append((year, result, output, pop, "median", np.median(vals)))
                        records.append((year, result, output, pop, "max", np.max(vals)))
                        records.append((year, result, output, pop, "min", np.min(vals)))
                        records.append((year, result, output, pop, "Q1", np.quantile(vals, 0.25)))
                        records.append((year, result, output, pop, "Q3", np.quantile(vals, 0.75)))

                df = pd.DataFrame.from_records(records, columns=["year", "result", "output", "pop", "quantity", "value"])
                df = df.set_index(["year", "result", "output", "pop", "quantity"])
                return df

    def pairplot(self, year=None, outputs=None, pops=None):
        # Paired plot for different outputs
        # See https://stackoverflow.com/questions/42592493/displaying-pair-plot-in-pandas-data-frame
        # General

        # Paired plot
        # One plot for each population
        # Different colours for each result

        if not self.samples:
            raise Exception("Cannot plot samples because no samples have been added yet")
        outputs = sc.promotetolist(outputs) if outputs is not None else self.outputs
        pops = sc.promotetolist(pops) if pops is not None else self.pops

        series_lookup = self._get_series()

        figs = []

        # Put all the values in a DataFrame
        for pop in self.pops:
            dfs = []
            for result in self.results:
                df_dict = dict()
                # Construct a dataframe with all of the outputs, with categorical results
                for output in self.outputs:
                    df_dict[output] = [x.vals[0] for x in series_lookup[result, pop, output]]
                df = pd.DataFrame.from_dict(df_dict)
                df["result"] = result
                dfs.append(df)
            df = pd.concat(dfs)

            colors = sc.gridcolors(len(self.results))
            colormap = {x: y for x, y in zip(self.results, colors)}
            fig = plt.figure()
            ax = plt.gca()
            pd.plotting.scatter_matrix(df, ax=ax, c=[colormap[x] for x in df["result"].values], diagonal="kde")
            plt.suptitle(pop)

            figs.append(fig)
        return figs


def _sample_and_map(proj, parset, progset, progset_instructions, result_names, mapping_function, max_attempts, **kwargs):
    """
    Helper function to sample

    This function runs a sampled simulation and also calls an Ensemble's mapping
    function prior to returning. This means that the Result goes out of scope and
    is discarded. Used when performing parallel simulations via `Ensemble.run_sims()`
    (which is used for memory-constrained simulations)

    """

    # First, get a single sample (could have multiple results if multiple instructions)
    results = proj.run_sampled_sims(n_samples=1, parset=parset, progset=progset, progset_instructions=progset_instructions, result_names=result_names, max_attempts=max_attempts)

    # Then convert it to a plotdata via the mapping function
    plotdata = mapping_function(results[0], **kwargs)

    # Finally, return the plotdata instead of the result
    return plotdata
