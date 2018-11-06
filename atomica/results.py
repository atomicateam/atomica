"""
Implements interface for working with model outputs

The :py:class:`Result` class is a wrapper for a :py:class:`Model` instance,
providing methods to conveniently access, plot, and export model outputs.

"""

import numpy as np
import pandas as pd
import sciris as sc
from .utils import NamedItem
import matplotlib.pyplot as plt
import ast
from .excel import standard_formats
from .system import logger, AtomicaException
from zipfile import ZipFile
import os


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
            prop_coverage = self.model.progset.get_prop_coverage(tvec=self.t, num_coverage=num_coverage, denominator=num_eligible, instructions=self.model.program_instructions, sample=False)

            if quantity == 'fraction':
                return prop_coverage
            elif quantity == 'denominator':
                return num_eligible
            else:
                raise AtomicaException('Unknown coverage type requested')

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

    def export(self, filename=None, plot_names=None, cascade_names=None, include_target_pars=True, include_programs=True):
        # This function writes an XLSX file with the data corresponding to any Cascades or Plots
        # that are present. Note that results are exported for every year by selecting integer years.
        # Flow rates are annualized instantaneously. So for example, the flow will have values from
        # 2014, 2015, 2016, but the 2015 flow rate is the actual flow at 2015.0 divided by dt, not the
        # time-aggregated flow rate. Time-aggregation isn't appropriate here because many of the quantities
        # plotted are probabilities. Selecting the annualized value at a particular year also means that the
        # data being exported will match up with whatever plots are generated from within Atomica
        #
        # Optionally can specify a list/set of names of the plots/cascades to include in the export
        # Set to an empty list to omit that category e.g.
        #
        #   plot_names = None # export all plots in framework
        #   plot_names = ['a','b'] # export only plots 'a' and 'b'
        #   plot_names = [] # don't export any plots e.g. to only export cascades
        #
        # First, make a dataframe for all the plot data, if plots are specified in the cascade
        # Imports here to avoid circular references
        #
        # INPUTS
        # - filename : Write an excel file. If 'None', no file will be written (but dataframes will be returned)
        # - plot_names : Optional list of plot names to export. If 'None', all plots. If '[]', then no plots
        # - cascade_names : Names of which cascades to plot. If 'None', all cascades
        # - include_target_pars : If True, include values for impact parameters
        # - include_programs : If True, programs sheet will be written if result contains programs

        from .plotting import PlotData
        from .cascade import get_cascade_vals

        pop_names = sc.odict()
        pop_names['all'] = 'Entire population'
        for pop_name, pop_label in zip(self.pop_names, self.pop_labels):
            pop_names[pop_name] = pop_label

        new_tvals = np.arange(np.ceil(self.t[0]), np.floor(self.t[-1]) + 1)

        if 'plots' not in self.framework.sheets:
            plot_df = None
        else:
            plots_required = self.framework.sheets['plots'][0]
            if plot_names is not None:
                plots_required = plots_required[plots_required['name'].isin(plot_names)]
            plot_df = []

            # Now for each plot, we have one output and several populations
            # We will have one dataframe for each output
            for _, spec in plots_required.iterrows():
                if 'type' in spec and spec['type'] == 'bar':
                    continue  # For now, don't do bars - not implemented yet
                data = sc.odict()
                popdata = PlotData(self, outputs=evaluate_plot_string(spec['quantities']))
                assert len(popdata.outputs) == 1, 'Framework plot specification should evaluate to exactly one output series - there were %d' % (len(popdata.outputs))
                popdata.interpolate(new_tvals)
                for pop in popdata.pops:
                    data[pop_names[pop]] = popdata[self.name, pop, popdata.outputs[0]].vals
                df = pd.DataFrame(data, index=new_tvals)
                df = df.T
                df.name = spec['name']
                plot_df.append(df)

        cascade_df = list()

        for name in self.framework.cascades.keys():
            if cascade_names is None or name in cascade_names:
                for pop, label in pop_names.items():
                    data = sc.odict()
                    cascade_vals, _ = get_cascade_vals(self, name, pops=pop, year=new_tvals)
                    for stage, vals in cascade_vals.items():
                        data[stage] = vals
                    df = pd.DataFrame(data, index=new_tvals)
                    df = df.T
                    df.name = '%s - %s' % (name, label)
                    cascade_df.append(df)

        output_fname = filename + '.xlsx' if not filename.endswith('.xlsx') else filename
        writer = pd.ExcelWriter(output_fname, engine='xlsxwriter')
        formats = standard_formats(writer.book)

        # WRITE THE PLOTS
        def write_df_list(df_list, sheet_name):
            i = 0
            for n, df in enumerate(df_list):
                df.to_excel(writer, sheet_name, startcol=0, startrow=i)
                worksheet = writer.sheets[sheet_name]
                worksheet.write_string(i, 0, df.name, formats['center_bold'])
                i += df.shape[0] + 2
            worksheet = writer.sheets[sheet_name]

            required_width = 0.0
            for df in df_list:
                required_width = max(required_width, len(df.name))
                if not isinstance(df.index, pd.MultiIndex):
                    required_width = max(required_width, max(df.index.str.len()))
            worksheet.set_column(0, 0, required_width * 1.1 + 1)

        if plot_df:
            write_df_list(plot_df, 'Plot data')

        if cascade_df:
            write_df_list(cascade_df, 'Cascades')

        if include_target_pars:
            targetable_code_names = list(self.framework.pars.index[self.framework.pars['targetable'] == 'y'])
            if targetable_code_names:
                par_df = []

                for par_name in targetable_code_names:
                    data = sc.odict()
                    popdata = PlotData(self, outputs=par_name)
                    popdata.interpolate(new_tvals)
                    for pop in popdata.pops:
                        data[pop_names[pop]] = popdata[self.name, pop, popdata.outputs[0]].vals
                    df = pd.DataFrame(data, index=new_tvals)
                    df = df.T
                    df.name = self.framework.pars.loc[par_name]['display name']
                    par_df.append(df)

                write_df_list(par_df, 'Target parameters')

        if include_programs:
            if self.model.programs_active:
                prog_df = []
                programs_active = (self.model.program_instructions.start_year <= new_tvals) & (new_tvals <= self.model.program_instructions.stop_year)
                for prog_name in self.model.progset.programs:
                    data = sc.odict()

                    spending = PlotData.programs(self, outputs=prog_name, quantity='spending').interpolate(new_tvals)
                    data['Spending ($/year)'] = spending.series[0].vals

                    spending = PlotData.programs(self, outputs=prog_name, quantity='coverage_number').interpolate(new_tvals)
                    data['People covered'] = spending.series[0].vals

                    spending = PlotData.programs(self, outputs=prog_name, quantity='coverage_denominator').interpolate(new_tvals)
                    data['People eligible'] = spending.series[0].vals

                    spending = PlotData.programs(self, outputs=prog_name, quantity='coverage_fraction').interpolate(new_tvals)
                    data['Proportion covered'] = spending.series[0].vals

                    df = pd.DataFrame(data, index=new_tvals)
                    df[~programs_active] = np.nan

                    df = df.T
                    df.name = prog_name
                    prog_df.append(df)

                write_df_list(prog_df, 'Programs')

        writer.save()
        writer.close()

        return output_fname

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


def evaluate_plot_string(plot_string):
    # The plots in the framework are specified as strings - for example,
    #
    # plot_string = "{'New active DS-TB':['pd_div:flow','nd_div:flow']}"
    #
    # This needs to be (safely) evaluated so that the actual dict can be
    # used. This function evaluates a string like this and returns a
    # variable accordingly. For example
    #
    # x = evaluate_plot_string("{'New active DS-TB':['pd_div:flow','nd_div:flow']}")
    #
    # is the same as
    #
    # x = {'New active DS-TB':['pd_div:flow','nd_div:flow']}
    #
    # This will only happen if tokens associated with dicts and lists are present -
    # otherwise the original string will just be returned directly

    if '{' in plot_string or '[' in plot_string:
        # Evaluate the string to set lists and dicts - do at least a little validation
        assert '__' not in plot_string, 'Cannot use double underscores in functions'
        assert len(plot_string) < 1800  # Function string must be less than 1800 characters
        fcn_ast = ast.parse(plot_string, mode='eval')
        for node in ast.walk(fcn_ast):
            if not (node is fcn_ast):
                assert isinstance(node, ast.Dict) or isinstance(node, ast.Str) or isinstance(node, ast.List) or isinstance(node, ast.Load), 'Only allowed to initialize lists and dicts of strings here'
        compiled_code = compile(fcn_ast, filename="<ast>", mode="eval")
        return eval(compiled_code)
    else:
        return plot_string


def export_results(results, filename=None, plot_names=None, cascade_names=None, include_target_pars=True, include_programs=True,group_results=True):
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

      plot_names = None # export all plots in framework
      plot_names = ['a','b'] # export only plots 'a' and 'b'
      plot_names = [] # don't export any plots e.g. to only export cascades

    :param results: A :py:class:`Result`, or list of `Results`. Results must all have different names. Outputs are drawn from the first result, normally
                    all results would have the same framework and populations.
    :param filename: Write an excel file. If 'None', no file will be written (but dataframes will be returned)
    :param plot_names: Optional list of plot names to export. If 'None', all plots. If '[]', then no plots
    :param cascade_names: Names of which cascades to plot. If 'None', all cascades
    :param include_target_pars: If True, include values for impact parameters
    :param include_programs: If True, programs sheet will be written if any results contains programs
    :param group_results: If True, results will be grouped by result instead of by pop or cascade stage
    :return: The name of the file that was written

    """

    # Local imports to avoid circular dependencies
    from .plotting import PlotData
    from .cascade import get_cascade_vals


    # Check all results have unique names
    if isinstance(results, dict):
        results = list(results.values())
    else:
        results = sc.promotetolist(results)

    result_names = [x.name for x in results]
    if len(set(result_names)) != len(result_names):
        raise AtomicaException('Results must have different names (in their result.name property)')

    # Check all results have the same time range
    for result in results:
        if result.t[0] != results[0].t[0] or result.t[-1] != results[0].t[-1]:
            raise AtomicaException('All results must have the same start and finish years')

        if set(result.pop_names) != set(results[0].pop_names):
            raise AtomicaException('All results must have the same populations')

    # Open the output file
    output_fname = filename + '.xlsx' if not filename.endswith('.xlsx') else filename
    writer = pd.ExcelWriter(output_fname, engine='xlsxwriter')
    formats = standard_formats(writer.book)

    # Prepare the population names and time values
    pop_names = sc.odict()
    pop_names['all'] = 'Entire population'
    for pop_name, pop_label in zip(results[0].pop_names, results[0].pop_labels):
        pop_names[pop_name] = pop_label
    new_tvals = np.arange(np.ceil(results[0].t[0]), np.floor(results[0].t[-1]) + 1)

    # Write the plots sheet
    if 'plots' in results[0].framework.sheets:

        # Figure out which plots are required
        plots_required = results[0].framework.sheets['plots'][0]
        if plot_names is not None:
            plots_required = plots_required[plots_required['name'].isin(plot_names)]
        plot_df = []

        # Now for each plot, we have one output and several populations
        # We will have one dataframe for each output, eventually with a multi-index for each result
        # The strategy will be to first assemble the dataframe, and then set the index appropriately
        for _, spec in plots_required.iterrows():
            if 'type' in spec and spec['type'] == 'bar':
                continue  # For now, don't do bars - not implemented yet
            data = sc.odict()
            popdata = PlotData(results, outputs=evaluate_plot_string(spec['quantities']))
            assert len(popdata.outputs) == 1, 'Framework plot specification should evaluate to exactly one output series - there were %d' % (len(popdata.outputs))
            popdata.interpolate(new_tvals)
            for result in popdata.results:
                for pop in popdata.pops:
                    data[(popdata.results[result],pop_names[pop])] = popdata[result, pop, popdata.outputs[0]].vals

            df = pd.DataFrame(data, index=new_tvals)
            df = df.T
            if not group_results:
                df = df.swaplevel().reindex([pop_names[pop] for pop in popdata.pops],level=0)
            df.name = spec['name']
            plot_df.append(df)

        _write_df_list(writer, formats, 'Plot data', plot_df)

    cascade_df = list()
    for name in results[0].framework.cascades.keys():
        if cascade_names is None or name in cascade_names:
            for pop, label in pop_names.items():
                data = sc.odict()
                for result in results:
                    cascade_vals, _ = get_cascade_vals(result, name, pops=pop, year=new_tvals)
                    for stage, vals in cascade_vals.items():
                        data[(result.name,stage)] = vals
                df = pd.DataFrame(data, index=new_tvals)
                df = df.T
                if not group_results:
                    df = df.swaplevel().reindex(list(cascade_vals.keys()), level=0)
                df.name = '%s - %s' % (name, label)
                cascade_df.append(df)
    _write_df_list(writer, formats, 'Cascades', cascade_df)

    if include_target_pars:
        targetable_code_names = list(results[0].framework.pars.index[results[0].framework.pars['targetable'] == 'y'])
        if targetable_code_names:
            par_df = []
            for par_name in targetable_code_names:
                data = sc.odict()
                popdata = PlotData(results, outputs=par_name)
                popdata.interpolate(new_tvals)
                for result in popdata.results:
                    for pop in popdata.pops:
                        data[(popdata.results[result], pop_names[pop])] = popdata[result, pop, popdata.outputs[0]].vals
                df = pd.DataFrame(data, index=new_tvals)
                df = df.T
                if not group_results:
                    df = df.swaplevel().reindex([pop_names[pop] for pop in popdata.pops], level=0)
                df.name = results[0].framework.pars.loc[par_name]['display name']
                par_df.append(df)

            _write_df_list(writer, formats, 'Target parameters', par_df)

    if include_programs and any([x.model.programs_active for x in results]):

        prog_df = []

        # Work out which programs are present
        prog_names = list()
        for result in results:
            if result.model.programs_active:
                prog_names += list(result.model.progset.programs.keys())
        prog_names = list(dict.fromkeys(prog_names))

        for prog_name in prog_names:
            data = sc.odict()

            for result in results:
                if result.model.programs_active and prog_name in result.model.progset.programs:
                    programs_active = (result.model.program_instructions.start_year <= new_tvals) & (new_tvals <= result.model.program_instructions.stop_year)

                    vals = PlotData.programs(result, outputs=prog_name, quantity='spending').interpolate(new_tvals)
                    vals.series[0].vals[~programs_active] = np.nan
                    data[(result.name,'Spending ($/year)')] = vals.series[0].vals

                    vals = PlotData.programs(result, outputs=prog_name, quantity='coverage_number').interpolate(new_tvals)
                    vals.series[0].vals[~programs_active] = np.nan
                    data[(result.name,'People covered')] = vals.series[0].vals

                    vals = PlotData.programs(result, outputs=prog_name, quantity='coverage_denominator').interpolate(new_tvals)
                    vals.series[0].vals[~programs_active] = np.nan
                    data[(result.name,'People eligible')] = vals.series[0].vals

                    vals = PlotData.programs(result, outputs=prog_name, quantity='coverage_fraction').interpolate(new_tvals)
                    vals.series[0].vals[~programs_active] = np.nan
                    data[(result.name,'Proportion covered')] = vals.series[0].vals


            df = pd.DataFrame(data, index=new_tvals)
            df = df.T
            if not group_results:
                df = df.swaplevel().reindex(['Spending ($/year)','People covered','People eligible','Proportion covered'], level=0)
            df.name = prog_name
            prog_df.append(df)

        _write_df_list(writer, formats, 'Programs', prog_df)

    writer.save()
    writer.close()

    return output_fname

def _write_df_list(writer, formats, sheet_name, df_list):
    """
    Write a list of DataFrames into a worksheet

    :param writer: A Pandas ExcelWriter instance specifying the file to write into
    :param formats: The output of `standard_formats(workbook)` specifying the styles embedded in the workbook
    :param sheet_name: The name of the sheet to create. It is assumed that this sheet will be generated entirely by
                       this function call (i.e. the sheet is not already present)
    :param df_list: A list of DataFrames to write. Each dataframe will be written sequentially, separated by empty rows
    :return: None

    """

    if not df_list:
        return

    i = 0
    for n, df in enumerate(df_list):
        df.to_excel(writer, sheet_name, startcol=0, startrow=i)
        worksheet = writer.sheets[sheet_name]
        worksheet.write_string(i, 0, df.name, formats['center_bold'])
        i += df.shape[0] + 2

    required_width = [0.0,0.0]
    for df in df_list:
        required_width[0] = max(required_width[0], len(df.name))
        if isinstance(df.index,pd.MultiIndex):
            required_width[0] = max(required_width[0], max(df.index.get_level_values(0).str.len()))
            required_width[1] = max(required_width[1], max(df.index.get_level_values(1).str.len()))
        else:
            required_width[0] = max(required_width[0], max(df.index.str.len()))
    if required_width[0] > 0:
        worksheet.set_column(0, 0, required_width[0] * 1.1 + 1)
    if required_width[1] > 0:
        worksheet.set_column(1, 1, required_width[1] * 1.1 + 1)