"""
Implements interface for working with model outputs

The :class:`Result` class is a wrapper for a :class:`Model` instance,
providing methods to conveniently access, plot, and export model outputs.

"""

import numpy as np
import pandas as pd
import sciris as sc
from .utils import NamedItem
import matplotlib.pyplot as plt
import ast
from .excel import standard_formats
from .system import logger
from .system import FrameworkSettings as FS
from .utils import evaluate_plot_string


class Result(NamedItem):
    # A Result stores a single model run
    def __init__(self, model, parset=None, name=None):
        if name is None:
            if parset is None:
                name = None
            else:
                name = parset.name
        NamedItem.__init__(self, name)

        self.uid = sc.uuid()

        # The Result constructor is called in model.run_model and the Model is no longer returned.
        # The following should be the only reference to that instance so no need to dcp.
        self.model = model
        self.parset_name = parset.name if parset is not None else None
        self.pop_names = [x.name for x in self.model.pops]  # This gets frequently used, so save it as an actual output

    # Property methods trade off storage space against computation time. The property methods below
    # are cheap to compute or used less frequently, are read-only, and can always be changed to actual
    # later without needing changes in other code that uses Result objects
    @property
    def framework(self):
        return self.model.framework

    @property
    def t(self):
        return self.model.t

    @property
    def dt(self):
        return self.model.dt

    @property
    def indices_observed_data(self):
        return np.where(self.t % 1.0 == 0)

    @property
    def t_observed_data(self):
        return self.t[self.indices_observed_data]

    @property
    def pop_labels(self):
        return [x.label for x in self.model.pops]

    def get_alloc(self):
        # Return a dict with time-varying funding allocation at every time point in the simulation
        if self.model.progset is None:
            return None
        else:
            return self.model.progset.get_alloc(self.t, self.model.program_instructions)

    def get_coverage(self, quantity='fraction'):
        # Return program coverage
        #
        # INPUTS
        # - quantity : one of ['number','fraction','denominator']
        # OUTPUTS
        # - {prog_name:value}

        if self.model.progset is None:
            return None

        num_coverage = self.model.progset.get_num_coverage(tvec=self.t, dt=self.dt, instructions=self.model.program_instructions)

        if quantity == 'number':
            return num_coverage
        else:
            # Get the program coverage denominator
            num_eligible = dict()  # This is the coverage denominator, number of people covered by the program
            for prog in self.model.progset.programs.values():  # For each program
                for pop_name in prog.target_pops:
                    for comp_name in prog.target_comps:
                        if prog.name not in num_eligible:
                            num_eligible[prog.name] = self.get_variable(pop_name, comp_name)[0].vals.copy()
                        else:
                            num_eligible[prog.name] += self.get_variable(pop_name, comp_name)[0].vals
            prop_coverage = self.model.progset.get_prop_coverage(tvec=self.t, num_coverage=num_coverage, denominator=num_eligible, instructions=self.model.program_instructions)

            if quantity == 'fraction':
                return prop_coverage
            elif quantity == 'denominator':
                return num_eligible
            else:
                raise Exception('Unknown coverage type requested')

    # Methods to list available comps, characs, pars, and links
    # pop_name is required because different populations could have
    # different contents
    def comp_names(self, pop_name):
        # Return compartment names for a given population
        return sorted(self.model.get_pop(pop_name).comp_lookup.keys())

    def charac_names(self, pop_name):
        # Return characteristic names for a given population
        return sorted(self.model.get_pop(pop_name).charac_lookup.keys())

    def par_names(self, pop_name):
        # Return parteristic names for a given population
        return sorted(self.model.get_pop(pop_name).par_lookup.keys())

    def link_names(self, pop_name):
        # Return link names for a given population
        names = set()
        pop = self.model.get_pop(pop_name)
        for link in pop.links:
            names.add(link.name)
        return sorted(names)

    def __repr__(self):
        """ Print out useful information when called"""
        output = sc.prepr(self)
        return output

    def get_variable(self, pops, name):
        # Retrieve a list of variables from a population
        return self.model.get_pop(pops).get_variable(name)

    def export_raw(self, filename=None):
        """Convert raw outputs to a single DataFrame and optionally write it to a file"""

        # Assemble the outputs into a dict
        d = dict()

        for pop in self.model.pops:
            for comp in pop.comps:
                d[('Compartments', pop.name, comp.name)] = comp.vals
            for charac in pop.characs:
                d[('Characteristics', pop.name, charac.name)] = charac.vals
            for par in pop.pars:
                if par.vals is not None:
                    d[('Parameters', pop.name, par.name)] = par.vals
            for link in pop.links:
                # Sum over duplicate links and annualize flow rate
                key = ('Flow rates', pop.name, link.name)
                if key not in d:
                    d[key] = np.zeros(self.t.shape)
                d[key] += link.vals / self.dt

        # Create DataFrame from dict
        df = pd.DataFrame(d, index=self.t)
        df.index.name = 'Time'

        # Optionally save it
        if filename is not None:
            df.T.to_excel(filename + '.xlsx' if not filename.endswith('.xlsx') else filename)

        return df

    def plot(self, plot_name=None, plot_group=None, pops=None, project=None):
        # Plot a single Result instance using the plots defined in the framework
        # INPUTS
        # - plot_name : The name of a single plot in the Framework
        # - plot_group : The name of a plot group
        # - pops : A population aggregation supposed by PlotData (e.g. 'all')
        # - project : A Project instance used to plot data and full names
        #
        # If plot_group is not None, then plot_name is ignored
        # If plot_name and plot_group are both None, then all plots will be displayed
        from .plotting import PlotData, plot_series

        df = self.framework.sheets['plots'][0]

        if plot_group is None and plot_name is None:
            for plot_name in df['name']:
                self.plot(plot_name, pops=pops, project=project)
            return
        elif plot_group is not None:
            for plot_name in df.loc[df['plot group'] == plot_group, 'name']:
                self.plot(plot_name=plot_name, pops=pops, project=project)
            return

        this_plot = df.loc[df['name'] == plot_name, :].iloc[0]  # A Series with the row of the 'Plots' sheet corresponding to the plot we want to render

        quantities = evaluate_plot_string(this_plot['quantities'])

        d = PlotData(self, outputs=quantities, pops=pops, project=project)
        h = plot_series(d, axis='pops', data=(project.data if project is not None else None))
        plt.title(this_plot['name'])
        return h

    def budget(self, year=None):
        # Return budget at given year
        # year - a time, or array of times. Returns budget at these times. If `None` then
        #        it will use all simulation times
        if self.model.progset is None:
            return None
        else:
            if year is None:
                year = self.t
            return self.model.progset.get_alloc(year, self.model.program_instructions)

    def coverage(self, year=None, quantity='coverage_fraction'):
        # Other supported quantities - 'coverage_number' or 'coverage_denominator'
        from .plotting import PlotData  # return

        if self.model.progset is None:
            return None
        else:
            if year is None:
                year = self.t
        d = PlotData.programs(self, quantity=quantity)
        d.interpolate(year)
        return sc.odict([(s.data_label, s.vals) for s in d.series])


def export_results(results, filename=None, output_ordering=('output', 'result', 'pop'), cascade_ordering=('pop', 'result', 'stage'), program_ordering=('program', 'result', 'quantity')):
    """ Export Result outputs to a file

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
        raise Exception('Results must have different names (in their result.name property)')

    # Check all results have the same time range
    for result in results:
        if result.t[0] != results[0].t[0] or result.t[-1] != results[0].t[-1]:
            raise Exception('All results must have the same start and finish years')

        if set(result.pop_names) != set(results[0].pop_names):
            raise Exception('All results must have the same populations')

    # Interpolate all outputs onto these years
    new_tvals = np.arange(np.ceil(results[0].t[0]), np.floor(results[0].t[-1]) + 1)

    # Open the output file
    output_fname = filename + '.xlsx' if not filename.endswith('.xlsx') else filename
    writer = pd.ExcelWriter(output_fname, engine='xlsxwriter')
    formats = standard_formats(writer.book)

    # Write the plots sheet if any plots are available
    if 'plots' in results[0].framework.sheets:
        plot_df = []
        plots_available = results[0].framework.sheets['plots'][0]
        for _, spec in plots_available.iterrows():
            if 'type' in spec and spec['type'] == 'bar':
                continue  # For now, don't do bars - not implemented yet
            plot_df.append(_output_to_df(results, output_name=spec['name'], output=evaluate_plot_string(spec['quantities']), tvals=new_tvals))
        _write_df(writer, formats, 'Plot data', pd.concat(plot_df), output_ordering)

    # Write cascades into separate sheets
    cascade_df = []
    for name in results[0].framework.cascades.keys():
        cascade_df.append(_cascade_to_df(results, name, new_tvals))
    if cascade_df:
        # always split tables by cascade, since different cascades can have different stages or the same stages with different definitions
        # it's thus potentially very confusing if the tables are split by something other than the cascade
        _write_df(writer, formats, 'Cascade', pd.concat(cascade_df), ('cascade',) + cascade_ordering)

    # If there are targetable parameters, output them
    targetable_code_names = list(results[0].framework.pars.index[results[0].framework.pars['targetable'] == 'y'])
    if targetable_code_names:
        par_df = []
        for par_name in targetable_code_names:
            par_df.append(_output_to_df(results, output_name=par_name, output=par_name, tvals=new_tvals))
        _write_df(writer, formats, 'Target parameters', pd.concat(par_df), output_ordering)

    # If any of the results used programs, output them
    if any([x.model.programs_active for x in results]):

        # Work out which programs are present
        prog_names = list()
        for result in results:
            if result.model.programs_active:
                prog_names += list(result.model.progset.programs.keys())
        prog_names = list(dict.fromkeys(prog_names))

        prog_df = []
        for prog_name in prog_names:
            prog_df.append(_programs_to_df(results, prog_name, new_tvals))
        _write_df(writer, formats, 'Programs', pd.concat(prog_df), program_ordering)

    writer.save()
    writer.close()

    return output_fname


def _programs_to_df(results, prog_name, tvals):
    """
    Return a DataFrame for program outputs for a group of results

    The dataframe will have a three-level MultiIndex for the program, result, and program quantity
    (e.g. spending, coverage fraction)

    :param results: List of Results
    :param prog_name: The name of a program
    :param tvals: Outputs will be interpolated onto the times in this array (typically would be annual)
    :return: A DataFrame

    """

    from .plotting import PlotData

    data = dict()

    for result in results:
        if result.model.programs_active and prog_name in result.model.progset.programs:
            programs_active = (result.model.program_instructions.start_year <= tvals) & (tvals <= result.model.program_instructions.stop_year)

            vals = PlotData.programs(result, outputs=prog_name, quantity='spending').interpolate(tvals)
            vals.series[0].vals[~programs_active] = np.nan
            data[(prog_name, result.name, 'Spending ($/year)')] = vals.series[0].vals

            vals = PlotData.programs(result, outputs=prog_name, quantity='coverage_number').interpolate(tvals)
            vals.series[0].vals[~programs_active] = np.nan
            data[(prog_name, result.name, 'People covered')] = vals.series[0].vals

            vals = PlotData.programs(result, outputs=prog_name, quantity='coverage_denominator').interpolate(tvals)
            vals.series[0].vals[~programs_active] = np.nan
            data[(prog_name, result.name, 'People eligible')] = vals.series[0].vals

            vals = PlotData.programs(result, outputs=prog_name, quantity='coverage_fraction').interpolate(tvals)
            vals.series[0].vals[~programs_active] = np.nan
            data[(prog_name, result.name, 'Proportion covered')] = vals.series[0].vals

    df = pd.DataFrame(data, index=tvals)
    df = df.T
    df.index = df.index.set_names(['program', 'result', 'quantity'])  # Set the index names correctly so they can be reordered easily

    return df


def _cascade_to_df(results, cascade_name, tvals):
    """
    Return a DataFrame for a cascade for a group of results

    The dataframe will have a three-level MultiIndex for the result, population, and cascade stage
    :param results: List of Results
    :param cascade_name: The name or index of a cascade stage (interpretable by get_cascade_vals)
    :param tvals: Outputs will be interpolated onto the times in this array (typically would be annual)
    :return: A DataFrame

    """

    from .cascade import get_cascade_vals

    # Prepare the population names and time values
    pop_names = dict()
    pop_names['all'] = 'Entire population'
    for pop_name, pop_label in zip(results[0].pop_names, results[0].pop_labels):
        pop_names[pop_name] = pop_label

    cascade_df = []
    for pop, label in pop_names.items():
        data = sc.odict()
        for result in results:
            cascade_vals, _ = get_cascade_vals(result, cascade_name, pops=pop, year=tvals)
            for stage, vals in cascade_vals.items():
                data[(cascade_name, pop_names[pop], result.name, stage)] = vals
        df = pd.DataFrame(data, index=tvals)
        df = df.T
        df.index = df.index.set_names(['cascade', 'pop', 'result', 'stage'])  # Set the index names correctly so they can be reordered easily
        cascade_df.append(df)

    return pd.concat(cascade_df)


def _output_to_df(results, output_name, output, tvals):
    """
    Convert an output to a DataFrame for a group of results

    This function takes in a list of results, and an output specification recognised by :class:`PlotData`.
    It extracts the outputs from all results and stores them in a 3-level MultiIndexed dataframe, which is
    returned. The index levels are the name of the output, the name of the results, and the populations.

    In addition, this function attempts to aggregate the outputs, if the units of the outputs matches
    known units. If the units lead to an obvious use of summation or weighted averating, it will be used.
    Otherwise, the output will contain NaNs for the population-aggregated results, which will appear as empty
    cells in the Excel spreadsheet so the user is able to fill them in themselves.

    :param results: List of Results
    :param outputs: An output aggregation that evaluates to a single output
    :param group_results: True/false flag for whether results should be grouped in the DataFrame
    :param tvals: Outputs will be interpolated onto the times in this array (typically would be annual)
    :return: A DataFrame

    """

    from .plotting import PlotData

    pop_labels = {x: y for x, y in zip(results[0].pop_names, results[0].pop_labels)}
    data = dict()
    popdata = PlotData(results, outputs=output)
    assert len(popdata.outputs) == 1, 'Framework plot specification should evaluate to exactly one output series - there were %d' % (len(popdata.outputs))
    popdata.interpolate(tvals)
    for result in popdata.results:
        for pop_name in popdata.pops:
            data[(output_name, popdata.results[result], pop_labels[pop_name])] = popdata[result, pop_name, popdata.outputs[0]].vals

    # Now do a population total. Need to check the units after any aggregations
    # Check results[0].model.pops[0].comps[0].units just in case someone changes it later on
    if popdata.series[0].units in {FS.QUANTITY_TYPE_NUMBER, results[0].model.pops[0].comps[0].units}:
        # Number units, can use summation
        popdata = PlotData(results, outputs=output, pops='total', pop_aggregation='sum')
        popdata.interpolate(tvals)
        for result in popdata.results:
            data[(output_name, popdata.results[result], 'Total (sum)')] = popdata[result, popdata.pops[0], popdata.outputs[0]].vals
    elif popdata.series[0].units in {FS.QUANTITY_TYPE_FRACTION, FS.QUANTITY_TYPE_PROPORTION, FS.QUANTITY_TYPE_PROBABILITY}:
        popdata = PlotData(results, outputs=output, pops='total', pop_aggregation='weighted')
        popdata.interpolate(tvals)
        for result in popdata.results:
            data[(output_name, popdata.results[result], 'Total (weighted average)')] = popdata[result, popdata.pops[0], popdata.outputs[0]].vals
    else:
        for result in popdata.results:
            data[(output_name, popdata.results[result], 'Total (unknown units)')] = np.full(tvals.shape, np.nan)

    df = pd.DataFrame(data, index=tvals)
    df = df.T
    df.index = df.index.set_names(['output', 'result', 'pop'])  # Set the index names correctly so they can be reordered easily
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

    level_substitutions = {'pop': 'Population', 'stage': 'Cascade stage'}

    # Remember the ordering of each index level
    order = {}
    for level in level_ordering:
        order[level] = list(dict.fromkeys(df.index.get_level_values(level)))

    required_width = [0] * (len(level_ordering) - 1)

    row = 0

    worksheet = writer.book.add_worksheet(sheet_name)
    writer.sheets[sheet_name] = worksheet  # Need to add it to the ExcelWriter for it to behave properly

    for title, table in df.groupby(level=level_ordering[0], sort=False):
        worksheet.write_string(row, 0, title, formats['center_bold'])
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

from scipy import stats

class Ensemble():
    """
    Class for working with sampled Results

    This class facilitates working with results and sampling.
    It manages the mapping of sets of results onto a scalar, which is
    then accumulated over samples. For example, we might sample from
    a ParameterSet and then run simulations with 2 different allocations to
    compare their expected difference. The Ensemble contains

    - A reduction function that maps from Results^N => R^M where typically M would
      index


    """

    def __init__(self, mapping_function):
        self.mapping_function = mapping_function
        self.samples = []
        self.baseline = None

    def set_baseline(self,results) -> None:
        self.baseline = self.mapping_function(results)

    def add_sample(self,results) -> None:
        self.samples.append(self.mapping_function(results))

    def plot_distribution(self, ti=None, fig=None):
        if fig is None:
            fig = plt.figure()

        if not self.samples:
            raise Exception('No samples added')


        for i in range(len(self.samples[0])):

        # Get the distribution over outcomes
        fn = lambda x: x.get_variable('m_rural', 'con')[0].vals[-1]
        kernel = stats.gaussian_kde(np.array([fn(x) for x in res]).ravel())

        x = np.linspace(105, 115, 500)
        plt.figure()
        plt.plot(x, kernel(x), label='With uncertainty')
        plt.axvline(fn(self.baseline), color='r', label='Baseline values')
        plt.legend()

    def plot_series(self):
        if not self.samples:
            raise Exception('No samples added')

        n_vars = len(self.samples[0])
        n_times =