"""
Functions for generating plots from model outputs

This module implements Atomica's plotting library, which is used to
generate various plots from model outputs.

"""

import itertools
import os
import errno
from collections import defaultdict

import matplotlib.cm as cmx
import matplotlib.colors as matplotlib_colors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Patch
from matplotlib.ticker import FuncFormatter

import sciris as sc
from .model import Compartment, Characteristic, Parameter, Link
from .results import Result
from .system import logger
from .function_parser import parse_function
from .interpolation import interpolate_func
from .system import FrameworkSettings as FS
import scipy.interpolate
import scipy.integrate

settings = dict()
settings['legend_mode'] = 'together'  # Possible options are ['together','separate','none']
settings['bar_width'] = 1.0  # Width of bars in plot_bars()
settings['line_width'] = 3.0  # Width of bars in plot_bars()


def save_figs(figs, path='.', prefix='', fnames=None) -> None:
    """
    Save figures to disk as PNG files

    Functions like `plot_series` and `plot_bars` can generate multiple figures, depending on
    the data and legend options. This function facilitates saving those figures together.
    The name for the file can be automatically selected when saving figures generated
    by `plot_series` and `plot_bars`. This function also deals with cases where the figure
    list may or may not contain a separate legend (so saving figures with this function means
    the legend mode can be changed freely without having to change the figure saving code).

    :param figs: A figure or list of figures
    :param path: Optionally append a path to the figure file name
    :param prefix: Optionally prepend a prefix to the file name
    :param fnames: Optionally an array of file names. By default, each figure is named
    using its 'label' property. If a figure has an empty 'label' string it is assumed to be
    a legend and will be named based on the name of the figure immediately before it.
    If you provide an empty string in the `fnames` argument this same operation will be carried
    out. If the last figure name is omitted, an empty string will automatically be added.

    """

    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise

    # Sanitize fig array input
    if not isinstance(figs, list):
        figs = [figs]

    # Sanitize and populate default fnames values
    if fnames is None:
        fnames = [fig.get_label() for fig in figs]
    elif not isinstance(fnames, list):
        fnames = [fnames]

    # Add legend figure to the end
    if len(fnames) < len(figs):
        fnames.append('')
    assert len(fnames) == len(figs), "Number of figures must match number of specified filenames, or the last figure must be a legend with no label"
    assert fnames[0], 'The first figure name cannot be empty'

    for i, fig in enumerate(figs):
        if not fnames[i]:  # assert above means that i>0
            fnames[i] = fnames[i - 1] + '_legend'
        fname = prefix + fnames[i] + '.png'
        fig.savefig(os.path.join(path, fname), bbox_inches='tight')
        logger.info('Saved figure "%s"', fname)


class PlotData():
    """
    Process model outputs into plottable quantities

    This is what gets passed into a plotting function, which displays a View of the data
    Conceptually, we are applying visuals to the data.
    But we are performing an extraction step rather than doing it directly because things like
    labels, colours, groupings etc. only apply to plots, not to results, and there could be several
    different views of the same data.

    :param results: which results to plot. Can be
                  - a Result,
                  - a list of Results,
                  - a dict/odict of results (the name of the result is taken from the Result, not the dict)
    :param outputs: The name of an output compartment, characteristic, or
                      parameter, or list of names. Inside a list, a dict can be given to
                      specify an aggregation e.g. ``outputs=['sus',{'total':['sus','vac']}]``
                      where the key is the new name. Or, a formula can be given which will
                      be evaluated by looking up labels within the model object. Links will
                      automatically be summed over
    :param pops: The name of an output population, or list of names. Like
                 outputs, can specify a dict with a list of pops to aggregate over them
    :param output_aggregation: If an output aggregation is requested, combine
                                the outputs listed using one of
                                  - 'sum' - just add values together
                                  - 'average' - unweighted average of quantities
                                  - 'weighted' - weighted average where the weight is the
                                    compartment size, characteristic value, or link source
                                    compartment size (summed over duplicate links). 'weighted'
                                    method cannot be used with non-transition parameters and a
                                    KeyError will result in that case
    :param pop_aggregation: Same as output_aggregation, except that 'weighted'
                              uses population sizes. Note that output aggregation is performed
                              before population aggregation. This also means that population
                              aggregation can be used to combine already aggregated outputs (e.g.
                              can first sum 'sus'+'vac' within populations, and then take weighted
                              average across populations)
    :param project: Optionally provide a :py:class:`Project` object, which will be used to convert names to labels in the outputs for plotting.
    :param time_aggregation: Optionally specify time aggregation method. Supported methods are 'sum' and 'average' (no weighting). When aggregating
                                times, *non-annualized* flow rates will be used.
    :param t_bins: Optionally specify time bins, which will enable time aggregation. Supported inputs are
                      - A vector of bin edges. Time points are included if the time
                        is >= the lower bin value and < upper bin value.
                      - A scalar bin size (e.g. 5) which will be expanded to a vector spanning the data
                      - The string 'all' will maps to bin edges `[-inf, inf]` aggregating over all time
    :param accumulate: Optionally accumulate outputs over time. Can be 'sum' or 'integrate' to either sum quantities or integrate by multiplying by the timestep. Accumulation happens *after* time aggregation.
                   The logic is extremely simple - the quantities in the Series pass through `cumsum`. If 'integrate' is selected, then the quantities are multiplied
                   by `dt` and the units are multiplied by `years`
    :return: A `PlotData` instance that can be passed to :py:func:`plot_series` or :py:func:`plot_bars`

    .. automethod:: __getitem__

    """

    # TODO: Make sure to chuck a useful error when t_bins is greater than sim duration, rather than just crashing.
    def __init__(self, results, outputs=None, pops=None, output_aggregation=None, pop_aggregation=None, project=None, time_aggregation='sum', t_bins=None, accumulate=None):
        # Validate inputs
        if isinstance(results, sc.odict):
            results = [result for _, result in results.items()]
        elif not isinstance(results, list):
            results = [results]

        result_names = [x.name for x in results]
        if len(set(result_names)) != len(result_names):
            raise Exception('Results must have different names (in their result.name property)')

        if pops in [None, 'all']:
            pops = [pop.name for pop in results[0].model.pops]
        elif pops == 'total':
            pops = [{'Total': [pop.name for pop in results[0].model.pops]}]
        pops = sc.promotetolist(pops)

        if outputs is None:
            outputs = [comp.name for comp in results[0].model.pops[0].comps if
                       not (comp.tag_birth or comp.tag_dead or comp.is_junction)]
        elif not isinstance(outputs, list):
            outputs = [outputs]

        pops = _expand_dict(pops)
        outputs = _expand_dict(outputs)

        assert output_aggregation in [None, 'sum', 'average', 'weighted']
        assert pop_aggregation in [None, 'sum', 'average', 'weighted']

        # First, get all of the pops and outputs requested by flattening the lists
        pops_required = _extract_labels(pops)
        outputs_required = _extract_labels(outputs)

        self.series = []
        tvecs = dict()

        # Because aggregations always occur within a Result object, loop over results
        for result in results:

            result_label = result.name
            tvecs[result_label] = result.model.t
            dt = result.model.dt

            aggregated_outputs = defaultdict(dict)  # Dict with aggregated_outputs[pop_label][aggregated_output_label]
            aggregated_units = dict()  # Dict with aggregated_units[aggregated_output_label]
            output_units = dict()
            compsize = dict()
            popsize = dict()
            # Defaultdict won't throw key error when checking outputs.
            data_label = defaultdict(str)  # Label used to identify which data to plot, maps output label to data label.

            # Aggregation over outputs takes place first, so loop over pops
            for pop_label in pops_required:
                pop = result.model.get_pop(pop_label)
                popsize[pop_label] = pop.popsize()
                data_dict = dict()  # Temporary storage for raw outputs

                # First pass, extract the original output quantities, summing links and annualizing as required
                for output_label in outputs_required:
                    vars = pop.get_variable(output_label)

                    if vars[0].vals is None:
                        raise Exception(
                            'Requested output "%s" was not recorded because only partial results were saved' % (
                                vars[0].name))

                    if isinstance(vars[0], Link):
                        data_dict[output_label] = np.zeros(tvecs[result_label].shape)
                        compsize[output_label] = np.zeros(tvecs[result_label].shape)

                        for link in vars:
                            data_dict[output_label] += link.vals
                            compsize[output_label] += (link.source.vals if not link.source.is_junction else link.source.outflow)

                        if t_bins is None:  # Annualize if not time aggregating
                            data_dict[output_label] /= dt
                            output_units[output_label] = vars[0].units + '/year'
                        else:
                            output_units[output_label] = vars[0].units  # If we sum links in a bin, we get a number of people
                        data_label[output_label] = vars[0].parameter.name if vars[0].parameter.units == FS.QUANTITY_TYPE_NUMBER else None  # Only use parameter data points if the units match

                    elif isinstance(vars[0], Parameter):
                        data_dict[output_label] = vars[0].vals
                        output_units[output_label] = vars[0].units
                        data_label[output_label] = vars[0].name

                        # If there are links, we can retrieve a compsize for the user to do a weighted average
                        if vars[0].links:
                            output_units[output_label] = vars[0].units
                            compsize[output_label] = np.zeros(tvecs[result_label].shape)
                            for link in vars[0].links:
                                compsize[output_label] += (link.source.vals if not link.source.is_junction else link.source.outflow)

                    elif isinstance(vars[0], Compartment) or isinstance(vars[0], Characteristic):
                        data_dict[output_label] = vars[0].vals
                        compsize[output_label] = vars[0].vals
                        output_units[output_label] = vars[0].units
                        data_label[output_label] = vars[0].name

                    else:
                        raise Exception('Unknown type')

                # Second pass, add in any dynamically computed quantities
                # Using model. Parameter objects will automatically sum over Links and convert Links
                # to annualized rates
                for l in outputs:
                    if not isinstance(l, dict):
                        continue

                    output_label, f_stack_str = list(l.items())[0]  # _extract_labels has already ensured only one key is present

                    if not sc.isstring(f_stack_str):
                        continue

                    def placeholder_pop(): return None
                    placeholder_pop.name = 'None'
                    par = Parameter(pop=placeholder_pop, name=output_label)
                    fcn, dep_labels = parse_function(f_stack_str)
                    deps = {}
                    displayed_annualization_warning = False
                    for dep_label in dep_labels:
                        vars = pop.get_variable(dep_label)
                        if t_bins is not None and (isinstance(vars[0], Link) or isinstance(vars[0], Parameter)) and time_aggregation == "sum" and not displayed_annualization_warning:
                            raise Exception("Function includes Parameter/Link so annualized rates are being "
                                            "used. Aggregation should use 'average' rather than 'sum'.")
                        deps[dep_label] = vars
                    par._fcn = fcn
                    par.deps = deps
                    par.preallocate(tvecs[result_label], dt)
                    par.update()
                    data_dict[output_label] = par.vals
                    output_units[output_label] = par.units

                # Third pass, aggregate them according to any aggregations present
                for output in outputs:  # For each final output
                    if isinstance(output, dict):
                        output_name = list(output.keys())[0]
                        labels = output[output_name]

                        # If this was a function, aggregation over outputs doesn't apply so just put it straight in.
                        if sc.isstring(labels):
                            aggregated_outputs[pop_label][output_name] = data_dict[output_name]
                            aggregated_units[output_name] = 'unknown'  # Also, we don't know what the units of a function are
                            continue

                        units = list(set([output_units[x] for x in labels]))

                        # Set default aggregation method depending on the units of the quantity
                        if output_aggregation is None:
                            if units[0] in ['', FS.QUANTITY_TYPE_FRACTION, FS.QUANTITY_TYPE_PROPORTION, FS.QUANTITY_TYPE_PROBABILITY]:
                                output_aggregation = 'average'
                            else:
                                output_aggregation = 'sum'

                        if len(units) > 1:
                            logger.warning("Aggregation for output '%s' is mixing units, this is almost certainly not desired.", output_name)
                            aggregated_units[output_name] = 'unknown'
                        else:
                            if units[0] in ['', FS.QUANTITY_TYPE_FRACTION, FS.QUANTITY_TYPE_PROPORTION, FS.QUANTITY_TYPE_PROBABILITY] and output_aggregation == 'sum' and len(labels) > 1:  # Dimensionless, like prevalance
                                logger.warning("Output '%s' is not in number units, so output aggregation probably should not be 'sum'.", output_name)
                            aggregated_units[output_name] = output_units[labels[0]]

                        if output_aggregation == 'sum':
                            aggregated_outputs[pop_label][output_name] = sum(data_dict[x] for x in labels)  # Add together all the outputs
                        elif output_aggregation == 'average':
                            aggregated_outputs[pop_label][output_name] = sum(data_dict[x] for x in labels)  # Add together all the outputs
                            aggregated_outputs[pop_label][output_name] /= len(labels)
                        elif output_aggregation == 'weighted':
                            aggregated_outputs[pop_label][output_name] = sum(data_dict[x] * compsize[x] for x in labels)  # Add together all the outputs
                            aggregated_outputs[pop_label][output_name] /= sum([compsize[x] for x in labels])
                    else:
                        aggregated_outputs[pop_label][output] = data_dict[output]
                        aggregated_units[output] = output_units[output]

            # Now aggregate over populations
            # If we have requested a reduction over populations, this is done for every output present
            for pop in pops:  # This is looping over the population entries
                for output_name in aggregated_outputs[list(aggregated_outputs.keys())[0]].keys():
                    if isinstance(pop, dict):
                        pop_name = list(pop.keys())[0]
                        pop_labels = pop[pop_name]

                        # Set population aggregation method depending on
                        if pop_aggregation is None:
                            if aggregated_units[output_name] in ['', FS.QUANTITY_TYPE_FRACTION, FS.QUANTITY_TYPE_PROPORTION, FS.QUANTITY_TYPE_PROBABILITY]:
                                pop_aggregation = 'average'
                            else:
                                pop_aggregation = 'sum'

                        if pop_aggregation == 'sum':
                            if aggregated_units[output_name] in ['', FS.QUANTITY_TYPE_FRACTION, FS.QUANTITY_TYPE_PROPORTION, FS.QUANTITY_TYPE_PROBABILITY] and len(pop_labels) > 1:
                                logger.warning("Output '%s' is not in number units, so population aggregation probably should not be 'sum'", output_name)
                            vals = sum(aggregated_outputs[x][output_name] for x in pop_labels)  # Add together all the outputs
                        elif pop_aggregation == 'average':
                            vals = sum(aggregated_outputs[x][output_name] for x in pop_labels)  # Add together all the outputs
                            vals /= len(pop_labels)
                        elif pop_aggregation == 'weighted':
                            vals = sum(aggregated_outputs[x][output_name] * popsize[x] for x in pop_labels)  # Add together all the outputs
                            vals /= sum([popsize[x] for x in pop_labels])
                        else:
                            raise Exception('Unknown pop aggregation method')
                        self.series.append(Series(tvecs[result_label], vals, result_label, pop_name, output_name, data_label[output_name], units=aggregated_units[output_name]))
                    else:
                        vals = aggregated_outputs[pop][output_name]
                        self.series.append(Series(tvecs[result_label], vals, result_label, pop, output_name, data_label[output_name], units=aggregated_units[output_name]))

        self.results = sc.odict()
        for result in results:
            self.results[result.name] = result.name

        self.pops = sc.odict()
        for pop in pops:
            key = list(pop.keys())[0] if isinstance(pop, dict) else pop
            self.pops[key] = _get_full_name(key, project) if project is not None else key

        self.outputs = sc.odict()
        for output in outputs:
            key = list(output.keys())[0] if isinstance(output, dict) else output
            self.outputs[key] = _get_full_name(key, project) if project is not None else key

        # Handle time aggregation
        if t_bins is not None:
            self._time_aggregate(t_bins, time_aggregation)

        if accumulate is not None:
            self._accumulate(accumulate)

    def _accumulate(self, accumulation_method) -> None:
        """
        Internal method to accumulate values over time

        Accumulation methods are

        :param accumulation_method: Select whether to add or integrate. Supported methods are:
                                    - 'sum' : runs `cumsum` on all quantities - should not be used if units are flow rates (so will check for '/year')
                                    - 'integrate' : integrate using trapezoidal rule, assuming initial value of 0
                                            Note that here there is no concept of 'dt' because we might have non-uniform time aggregation bins
                                            Therefore, we need to use the time vector actually contained in the Series object (via `cumtrapz()`)

        """

        assert accumulation_method in ['sum', 'integrate']

        for s in self.series:
            if accumulation_method == 'sum':
                if '/year' in s.units:
                    raise Exception('Quantity "%s" has units "%s" which means it should be accumulated by integration, not summation' % (s.output, s.units))
                s.vals = np.cumsum(s.vals)
            elif accumulation_method == 'integrate':
                s.vals = scipy.integrate.cumtrapz(s.vals, s.tvec)
                s.vals = np.insert(s.vals, 0, 0.0)
                if '/year' in s.units:
                    s.units = s.units.replace('/year', '')
                else:
                    s.units += ' years'
            else:
                raise Exception('Unknown accumulation type')

            s.units = 'Cumulative ' + s.units

    def _time_aggregate(self, t_bins, time_aggregation) -> None:
        """
        Internal method for time aggregation

        Note that accumulation is effectively a running total, whereas aggregation refers to binning

        :param t_bins: Vector of bin edges OR a scalar bin size, which will be automatically expanded to a vector of bin edges
        :param time_aggregation: can be 'sum' or 'average'

        """

        assert time_aggregation in ['sum', 'average']

        if not hasattr(t_bins, '__len__'):
            # TODO - here is where the code to handle t_bins > sim duration goes
            if not (self.series[0].tvec[-1] - self.series[0].tvec[0]) % t_bins:
                upper = self.series[0].tvec[-1] + t_bins
            else:
                upper = self.series[0].tvec[-1]
            t_bins = np.arange(self.series[0].tvec[0], upper, t_bins)

        if sc.isstring(t_bins) and t_bins == 'all':
            t_out = np.zeros((1,))
            lower = [-np.inf]
            upper = [np.inf]
        else:
            lower = t_bins[0:-1]
            upper = t_bins[1:]
            if time_aggregation == 'sum':
                t_out = upper
            elif time_aggregation == 'average':
                t_out = (lower + upper) / 2.0
            else:
                raise Exception('Unknown time aggregation type')

        for s in self.series:
            tvec = []
            vals = []
            for i, low, high, t in zip(range(len(lower)), lower, upper, t_out):
                tvec.append(t)
                if (not np.isinf(low) and low < s.tvec[0]) or (not np.isinf(high) and high > s.tvec[-1]):
                    vals.append(np.nan)
                else:
                    if low == high:
                        flt = s.tvec == low
                    else:
                        flt = (s.tvec >= low) & (s.tvec < high)

                    if time_aggregation == 'sum':
                        if s.units in ['', 'fraction', 'proportion', 'probability']:
                            logger.warning("'{0}' is not in number units, so time aggregation probably should not "
                                           "be 'sum'.".format(s))
                        vals.append(np.sum(s.vals[flt]))
                    elif time_aggregation == 'average':
                        vals.append(np.average(s.vals[flt]))

            s.tvec = np.array(tvec)
            s.vals = np.array(vals)
            if sc.isstring(t_bins) and t_bins == 'all':
                s.t_labels = ['All']
            else:
                s.t_labels = ['%d-%d' % (l, h) for l, h in zip(lower, upper)]

    def __repr__(self):
        s = "PlotData\n"
        s += "Results: {0}\n".format(self.results.keys())
        s += "Pops: {0}\n".format(self.pops.keys())
        s += "Outputs: {0}\n".format(self.outputs.keys())
        return s

    @staticmethod
    def programs(results, outputs=None, t_bins=None, quantity='spending', accumulate=None):
        """
        Constructs a PlotData instance from program values

        This alternate constructor can be used to plot program-related quantities such as spending or coverage.

        :param results: single Result, or list of Results
        :param outputs: specification of which programs to plot spending for. Can be:
                        - the name of a single program
                        - a list of program names
                        - aggregation dict e.g. {'treatment':['tx-1','tx-2']} or list of such dicts. Output aggregation type is automatically 'sum' for
                          program spending, and aggregation is NOT permitted for coverages (due to modality interactions)
        :param t_bins: aggregate over time, using summation for spending and number coverage, and average for fraction/proportion coverage. Notice that
                        unlike the `PlotData()` constructor, this function does _not_ allow the time aggregation method to be manually set.
        :param quantity: can be 'spending', 'coverage_number', 'coverage_denominator', or 'coverage_fraction'. The 'coverage_denominator' is
                        the sum of compartments reached by a program, such that coverage_fraction = coverage_number/coverage_denominator
        :param accumulate: can be 'sum' or 'integrate'
        :return: A new :py:class:`PlotData` instance

        """

        # Sanitize the results input
        if isinstance(results, sc.odict):
            results = [result for _, result in results.items()]
        elif isinstance(results, Result):
            results = [results]

        result_names = [x.name for x in results]
        if len(set(result_names)) != len(result_names):
            raise Exception('Results must have different names (in their result.name property)')
        for result in results:
            if result.model.progset is None:
                raise Exception('Tried to plot program spending for result "%s" that did not use programs', result.name)

        if outputs is None:
            outputs = results[0].model.progset.programs.keys()
        elif not isinstance(outputs, list):
            outputs = [outputs]

        outputs = _expand_dict(outputs)
#        progs_required = _extract_labels(outputs)

        assert quantity in ['spending', 'coverage_number', 'coverage_denominator', 'coverage_fraction']
        # Make a new PlotData instance
        # We are using __new__ because this method is to be formally considered an alternate constructor and
        # thus bears responsibility for ensuring this new instance is initialized correctly
        plotdata = PlotData.__new__(PlotData)
        plotdata.series = []

        # Because aggregations always occur within a Result object, loop over results
        for result in results:

            if quantity == 'spending':
                all_vals = result.get_alloc()
                units = '$/year'
            elif quantity == 'coverage_number':
                all_vals = result.get_coverage('number')
                units = 'Number of people/year'
            elif quantity == 'coverage_denominator':
                all_vals = result.get_coverage('denominator')
                units = 'Number of people'
            elif quantity == 'coverage_fraction':
                all_vals = result.get_coverage('fraction')
                units = 'Fraction covered/year'
            else:
                raise Exception('Unknown quantity')

            for output in outputs:  # For each final output
                if isinstance(output, dict):  # If this is an aggregation over programs
                    if quantity == 'spending':
                        output_name = list(output.keys())[0]  # This is the aggregated name
                        labels = output[output_name]  # These are the quantities being aggregated

                        # We only support summation for combining program spending, not averaging
                        # TODO - if/when we track which currency, then should check here that all of the programs have the same currency
                        vals = sum(all_vals[x] for x in labels)
                        output_name = output_name
                        data_label = None  # No data present for aggregations
                    else:
                        raise Exception('Cannot use program aggregation for anything other than spending yet')
                else:
                    vals = all_vals[output]
                    output_name = output
                    data_label = output  # Can look up program spending by the program name

                if quantity in ['spending', 'coverage_number'] and t_bins is not None:
                    # If we are time-aggregating, then the annual quantities which are going to be summed need to be
                    # converted back to timestep values - for both spending and number coverage, this is simply multiplicative
                    vals *= result.dt
                    units = units.replace('/year', '')

                # Accumulate the Series
                plotdata.series.append(Series(result.t, vals, result=result.name, pop=FS.DEFAULT_SYMBOL_INAPPLICABLE, output=output_name, data_label=data_label, units=units))  # The program should specify the units for its unit cost

        plotdata.results = sc.odict()
        for result in results:
            plotdata.results[result.name] = result.name

        plotdata.pops = sc.odict({FS.DEFAULT_SYMBOL_INAPPLICABLE: FS.DEFAULT_SYMBOL_INAPPLICABLE})

        plotdata.outputs = sc.odict()
        for output in outputs:
            key = list(output.keys())[0] if isinstance(output, dict) else output
            plotdata.outputs[key] = results[0].model.progset.programs[key].label if key in results[0].model.progset.programs else key

        if t_bins is not None:
            if quantity in ['spending', 'coverage_number']:
                plotdata._time_aggregate(t_bins, 'sum')
            elif quantity in ['coverage_denominator', 'coverage_fraction']:
                plotdata._time_aggregate(t_bins, 'average')
            else:
                raise Exception('Unknown quantity')

        if accumulate is not None:
            plotdata._accumulate(accumulate)

        return plotdata

    def tvals(self):
        """
        Return vector of time values

        This method returns a vector of time values for the ``PlotData`` object, if all of the series have the
        same time axis (otherwise it will throw an error). All series must have the same number of timepoints.
        This will always be the case for a ``PlotData`` object unless the instance has been manually modified after construction.

        :return: Tuple with (array of time values, array of time labels)

        """

        assert len(set([len(x.tvec) for x in self.series])) == 1, "All series must have the same number of time points."
        tvec = self.series[0].tvec
        t_labels = self.series[0].t_labels
        for i in range(1, len(self.series)):
            assert (all(np.equal(self.series[i].tvec, tvec))), 'All series must have the same time points'
        return tvec, t_labels

    def interpolate(self, new_tvec):
        """
        Interpolate all ``Series`` onto new time values

        This will modify all of the contained ``Series`` objects in-place.
        The modified ``PlotData`` instance is also returned, so that interpolation and
        construction can be performed in one line. i.e. both

        >>> d = PlotData(result)
        ... d.interpolate(tvals)

        >>> vals = PlotData(result).interpolate(tvals)

        will work as intended.

        :param new_tvec: Vector of new time values
        :return: The modified `PlotData` instance

        """

        new_tvec = sc.promotetoarray(new_tvec)
        for series in self.series:
            series.vals = series.interpolate(new_tvec)
            series.tvec = np.copy(new_tvec)
            series.t_labels = np.copy(new_tvec)
        return self

    def __getitem__(self, key: tuple):
        """
        Implement custom indexing

        The :py:class:`Series` objects stored within :py:class:`PlotData` are each bound to a single
        result, population, and output. This operator makes it possible to easily retrieve
        a particular :py:class:`Series` instance. For example,

        >>> d = PlotData(results)
        ... d['default','0-4','sus']

        :param key: A tuple of (result,pop,output)
        :return: A :py:class:`Series` instance

        """

        for s in self.series:
            if s.result == key[0] and s.pop == key[1] and s.output == key[2]:
                return s
        raise Exception('Series %s-%s-%s not found' % (key[0], key[1], key[2]))

    def set_colors(self, colors=None, results='all', pops='all', outputs='all', overwrite=False):
        """
        Assign colors to quantities

        This function facilitates assigned colors to the ``Series`` objects contained in this
        ``PlotData`` instance.

        :param colors: Specify the colours to use. This can be
                    - A list of colours that applies to the list of all matching items
                    - A single colour to use for all matching items
                    - The name of a colormap to use (e.g., 'Blues')
        :param results: A list of results to set colors for, or a dict of results where the key names the results (e.g. ``PlotData.results``)
        :param pops: A list of pops to set colors for, or a dict of pops where the key names the pops (e.g. ``PlotData.pops``
        :param outputs:A list of outputs to set colors for, or a dict of outputs where the key names the outputs (e.g. ``PlotData.outputs``)
        :param overwrite: False (default) or True. If True, then any existing manually set colours will be overwritten
        :return: The `PlotData` instance (also modified in-place)

        Essentially, the lists of results, pops, and outputs are used to filter the ``Series`` resulting in a list of ``Series`` to operate on.
        Then, the colors argument is applied to that list.

        """

        if isinstance(results, dict):
            results = results.keys()
        else:
            results = sc.promotetolist(results)

        if isinstance(pops, dict):
            pops = pops.keys()
        else:
            pops = sc.promotetolist(pops)

        if isinstance(outputs, dict):
            outputs = outputs.keys()
        else:
            outputs = sc.promotetolist(outputs)

        targets = list(itertools.product(results, pops, outputs))

        if colors is None:
            colors = sc.gridcolors(len(targets))  # Default colors
        elif isinstance(colors, list):
            assert len(colors) == len(targets), 'Number of colors must either be a string, or a list with as many elements as colors to set'
            colors = colors
        elif colors.startswith('#') or colors not in [m for m in plt.cm.datad if not m.endswith("_r")]:
            colors = [colors for _ in range(len(targets))]  # Apply color to all requested outputs
        else:
            color_norm = matplotlib_colors.Normalize(vmin=-1, vmax=len(targets))
            scalar_map = cmx.ScalarMappable(norm=color_norm, cmap=colors)
            colors = [scalar_map.to_rgba(index) for index in range(len(targets))]

        # Now each of these colors gets assigned
        for color, target in zip(colors, targets):
            series = self.series
            series = [x for x in series if (x.result == target[0] or target[0] == 'all')]
            series = [x for x in series if (x.pop == target[1] or target[1] == 'all')]
            series = [x for x in series if (x.output == target[2] or target[2] == 'all')]
            for s in series:
                s.color = color if (s.color is None or overwrite) else s.color

        return self


class Series():
    """
    Represent a plottable time series

    A Series represents a quantity available for plotting. It is like a `TimeSeries` but contains
    additional information only used for plotting, such as color.

    :param tvec: array of time values
    :param vals: array of values
    :param result: name of the result associated with ths data
    :param pop: name of the pop associated with the data
    :param output: name of the output associated with the data
    :param data_label: name of a quantity in project data to plot in conjunction with this `Series`
    :param color: the color to render the `Series` with
    :param units: the units for the values

    """

    def __init__(self, tvec, vals, result='default', pop='default', output='default', data_label='', color=None, units=''):
        self.tvec = np.copy(tvec)
        self.t_labels = np.copy(self.tvec)  # Iterable array of time labels - could become strings like [2010-2014]
        self.vals = np.copy(vals)
        self.result = result
        self.pop = pop
        self.output = output
        self.color = color
        self.data_label = data_label  # Used to identify data for plotting
        self.units = units

        if np.any(np.isnan(vals)):
            logger.warning('%s contains NaNs', self)

    def __repr__(self):
        return 'Series(%s,%s,%s)' % (self.result, self.pop, self.output)

    def interpolate(self, new_tvec):
        """
        Return interpolated vector of values

        This function returns an `np.array()` with the values of this series interpolated onto the requested
        time array new_tvec. To ensure results are not misleading, extrapolation is disabled
        and will return `NaN` if `new_tvec` contains values outside the original time range.

        Note that unlike `PlotData.interpolate()`, `Series.interpolate()` does not modify the object but instead
        returns the interpolated values. This makes the `Series` object more versatile (`PlotData` is generally
        used only for plotting, but the `Series` object can be a convenient way to work with values computed using
        the sophisticated aggregations within `PlotData`).

        :param new_tvec: array of new time values
        :return: array with interpolated values (same size as `new_tvec`)

        """

        f = scipy.interpolate.PchipInterpolator(self.tvec, self.vals, axis=0, extrapolate=False)
        out_of_bounds = (new_tvec < self.tvec[0]) | (new_tvec > self.tvec[-1])
        if np.any(out_of_bounds):
            logger.warning('Series has values from %.2f to %.2f so requested time points %s are out of bounds', self.tvec[0], self.tvec[-1], new_tvec[out_of_bounds])
        return f(sc.promotetoarray(new_tvec))


def plot_bars(plotdata, stack_pops=None, stack_outputs=None, outer='times', legend_mode=None, show_all_labels=False, orientation='vertical') -> list:
    """
    Produce a bar plot

    :param plotdata: a :py:class:`PlotData` instance to plot
    :param stack_pops: A list of lists with populations to stack. A bar is rendered for each item in the list.
                       For example, `[['0-4','5-14'],['15-64']]` will render two bars, with two populations stacked
                       in the first bar, and only one population in the second bar. Items not appearing in this list
                       will be rendered unstacked.
    :param stack_outputs: Same as `stack_pops`, but for outputs.
    :param outer: Select whether the outermost/highest level of grouping is by `'times'` or by `'results'`
    :param legend_mode: override the default legend mode in settings
    :param show_all_labels: If True, then inner/outer labels will be shown even if there is only one label
    :param orientation: 'vertical' (default) or 'horizontal'
    :return: A list of newly created Figures

    """

    global settings
    if legend_mode is None:
        legend_mode = settings['legend_mode']

    assert outer in ['times', 'results'], 'Supported outer groups are "times" or "results"'
    assert orientation in ['vertical', 'horizontal'], 'Supported orientations are "vertical" or "horizontal"'

    plotdata = sc.dcp(plotdata)

    # Note - all of the tvecs must be the same
    tvals, t_labels = plotdata.tvals()  # We have to iterate over these, with offsets, if there is more than one

    # If quantities are stacked, then they need to be coloured differently.
    if stack_pops is None:
        color_by = 'outputs'
        plotdata.set_colors(outputs=plotdata.outputs.keys())
    elif stack_outputs is None:
        color_by = 'pops'
        plotdata.set_colors(pops=plotdata.pops.keys())
    else:
        color_by = 'both'
        plotdata.set_colors(pops=plotdata.pops.keys(), outputs=plotdata.outputs.keys())

    def process_input_stacks(input_stacks, available_items):
        # Sanitize the input. input stack could be
        # - A list of stacks, where a stack is a list of pops or a string with a single pop
        # - A dict of stacks, where the key is the name, and the value is a list of pops or a string with a single pop
        # - None, in which case all available items are used
        # - 'all' in which case all of the items appear in a single stack
        #
        # The return value `output_stacks` is a list of tuples where
        # (a,b,c)
        # a - The automatic name
        # b - User provided manual name
        # c - List of pop labels
        # Same for outputs

        if input_stacks is None:
            return [(x, '', [x]) for x in available_items]
        elif input_stacks == 'all':
            # Put all available items into a single stack
            return process_input_stacks([available_items], available_items)

        items = set()
        output_stacks = []
        if isinstance(input_stacks, list):
            for x in input_stacks:
                if isinstance(x, list):
                    output_stacks.append(('', '', x) if len(x) > 1 else (x[0], '', x))
                    items.update(x)
                elif sc.isstring(x):
                    output_stacks.append((x, '', [x]))
                    items.add(x)
                else:
                    raise Exception('Unsupported input')

        elif isinstance(input_stacks, dict):
            for k, x in input_stacks.items():
                if isinstance(x, list):
                    output_stacks.append(('', k, x) if len(x) > 1 else (x[0], k, x))
                    items.update(x)
                elif sc.isstring(x):
                    output_stacks.append((x, k, [x]))
                    items.add(x)
                else:
                    raise Exception('Unsupported input')

        # Add missing items
        missing = list(set(available_items) - items)
        output_stacks += [(x, '', [x]) for x in missing]
        return output_stacks

    pop_stacks = process_input_stacks(stack_pops, plotdata.pops.keys())
    output_stacks = process_input_stacks(stack_outputs, plotdata.outputs.keys())

    # Now work out which pops and outputs appear in each bar (a bar is a pop-output combo)
    bar_pops = []
    bar_outputs = []
    for pop in pop_stacks:
        for output in output_stacks:
            bar_pops.append(pop)
            bar_outputs.append(output)

    width = settings['bar_width']
    gaps = [0.1, 0.4, 0.8]  # Spacing within blocks, between inner groups, and between outer groups

    block_width = len(bar_pops) * (width + gaps[0])

    # If there is only one bar group, then increase spacing between bars
    if len(tvals) == 1 and len(plotdata.results) == 1:
        gaps[0] = 0.3

    if outer == 'times':
        if len(plotdata.results) == 1:  # If there is only one inner group
            gaps[2] = gaps[1]
            gaps[1] = 0
        result_offset = block_width + gaps[1]
        tval_offset = len(plotdata.results) * (block_width + gaps[1]) + gaps[2]
        iterator = _nested_loop([range(len(plotdata.results)), range(len(tvals))], [0, 1])
    elif outer == 'results':
        if len(tvals) == 1:  # If there is only one inner group
            gaps[2] = gaps[1]
            gaps[1] = 0
        result_offset = len(tvals) * (block_width + gaps[1]) + gaps[2]
        tval_offset = block_width + gaps[1]
        iterator = _nested_loop([range(len(plotdata.results)), range(len(tvals))], [1, 0])
    else:
        raise Exception('outer option must be either "times" or "results"')

    figs = []
    fig, ax = plt.subplots()
    fig.set_label('bars')
    figs.append(fig)

    rectangles = defaultdict(list)  # Accumulate the list of rectangles for each colour
    color_legend = sc.odict()

    # NOTE
    # pops, output - colour separates them. To merge colours, aggregate the data first
    # results, time - spacing separates them. Can choose to group by one or the other

    # Now, there are three levels of ticks
    # There is the within-block level, the inner group, and the outer group
    block_labels = []  # Labels for individual bars (tick labels)
    inner_labels = []  # Labels for bar groups below axis
    block_offset = None
    base_offset = None
    negative_present = False # If True, it means negative quantities were present

    # Iterate over the inner and outer groups, rendering blocks at a time
    for r_idx, t_idx in iterator:
        base_offset = r_idx * result_offset + t_idx * tval_offset  # Offset between outer groups
        block_offset = 0.0  # Offset between inner groups

        if outer == 'results':
            inner_labels.append((base_offset + block_width / 2.0, t_labels[t_idx]))
        elif outer == 'times':
            inner_labels.append((base_offset + block_width / 2.0, plotdata.results[r_idx]))

        for idx, bar_pop, bar_output in zip(range(len(bar_pops)), bar_pops, bar_outputs):
            # pop is something like ['0-4','5-14'] or ['0-4']
            # output is something like ['sus','vac'] or ['0-4'] depending on the stack

            y0 = [0,0] # Baselines for positive and negative bars, respectively

            # Set the name of the bar
            # If the user provided a label, it will always be displayed
            # In addition, if there is more than one label of the other (output/pop) type,
            # then that label will also be shown, otherwise it will be suppressed
            if bar_pop[1] or bar_output[1]:
                if bar_pop[1]:
                    if bar_output[1]:
                        bar_label = '%s\n%s' % (bar_pop[1], bar_output[1])
                    elif len(output_stacks) > 1 and len(set([x[0] for x in output_stacks])) > 1 and bar_output[0]:
                        bar_label = '%s\n%s' % (bar_pop[1], bar_output[0])
                    else:
                        bar_label = bar_pop[1]
                else:
                    if len(pop_stacks) > 1 and len(set([x[0] for x in pop_stacks])) > 1 and bar_pop[0]:
                        bar_label = '%s\n%s' % (bar_pop[0], bar_output[1])
                    else:
                        bar_label = bar_output[1]
            else:
                if color_by == 'outputs' and len(pop_stacks) > 1 and len(set([x[0] for x in pop_stacks])) > 1:
                    bar_label = bar_pop[0]
                elif color_by == 'pops' and len(output_stacks) > 1 and len(set([x[0] for x in output_stacks])) > 1:
                    bar_label = bar_output[0]
                else:
                    bar_label = ''

            for pop in bar_pop[2]:
                for output in bar_output[2]:
                    series = plotdata[plotdata.results[r_idx], pop, output]
                    y = series.vals[t_idx]
                    if y >= 0:
                        baseline = y0[0]
                        y0[0] += y
                        height = y
                    else:
                        baseline = y0[1]+y
                        y0[1] += y
                        height = -y
                        negative_present = True

                    if orientation == 'horizontal':
                        rectangles[series.color].append(Rectangle((baseline, base_offset + block_offset), height, width))
                    else:
                        rectangles[series.color].append(Rectangle((base_offset + block_offset, baseline), width, height))

                    if series.color in color_legend and (pop, output) not in color_legend[series.color]:
                        color_legend[series.color].append((pop, output))
                    elif series.color not in color_legend:
                        color_legend[series.color] = [(pop, output)]

            block_labels.append((base_offset + block_offset + width / 2., bar_label))

            block_offset += width + gaps[0]

    # Add the patches to the figure and assemble the legend patches
    legend_patches = []

    for color, items in color_legend.items():
        pc = PatchCollection(rectangles[color], facecolor=color, edgecolor='none')
        ax.add_collection(pc)
        pops = set([x[0] for x in items])
        outputs = set([x[1] for x in items])

        if pops == set(plotdata.pops.keys()) and len(outputs) == 1:  # If the same color is used for all pops and always the same output
            label = plotdata.outputs[items[0][1]]  # Use the output name
        elif outputs == set(plotdata.outputs.keys()) and len(pops) == 1:  # Same color for all outputs and always same pop
            label = plotdata.pops[items[0][0]]  # Use the pop name
        else:
            label = ''
            for x in items:
                label += '%s-%s,\n' % (plotdata.pops[x[0]], plotdata.outputs[x[1]])
            label = label.strip()[:-1]  # Replace trailing newline and comma
        legend_patches.append(Patch(facecolor=color, label=label))

    # Set axes now, because we need block_offset and base_offset after the loop
    ax.autoscale()
    _turn_off_border(ax)
    block_labels = sorted(block_labels, key=lambda x: x[0])

    if orientation == 'horizontal':
        ax.set_ylim(bottom=-2 * gaps[0], top=block_offset + base_offset)
        fig.set_figheight(0.75 + 0.75 * (block_offset + base_offset))
        if not negative_present:
            ax.set_xlim(left=0)
        else:
            ax.spines['right'].set_color('k')
            ax.spines['right'].set_position('zero')
        ax.set_yticks([x[0] for x in block_labels])
        ax.set_yticklabels([x[1] for x in block_labels])
        ax.invert_yaxis()
        ax.xaxis.set_major_formatter(FuncFormatter(sc.SItickformatter))
    else:
        ax.set_xlim(left=-2 * gaps[0], right=block_offset + base_offset)
        fig.set_figwidth(1.1 + 1.1 * (block_offset + base_offset))
        if not negative_present:
            ax.set_ylim(bottom=0)
        else:
            ax.spines['top'].set_color('k')
            ax.spines['top'].set_position('zero')
        ax.set_xticks([x[0] for x in block_labels])
        ax.set_xticklabels([x[1] for x in block_labels])
        ax.yaxis.set_major_formatter(FuncFormatter(sc.SItickformatter))

    # Calculate the units. As all bar patches are shown on the same axis, they are all expected to have the
    # same units. If they do not, the plot could be misleading
    units = list(set([x.units for x in plotdata.series]))
    if len(units) == 1:
        if orientation == 'horizontal':
            ax.set_xlabel(units[0].title())
        else:
            ax.set_ylabel(units[0].title())
    else:
        logger.warning('Warning - bar plot quantities mix units, double check that output selection is correct')

    # Outer group labels are only displayed if there is more than one group
    if outer == 'times' and (show_all_labels or len(tvals) > 1):
        offset = 0.0
        for t in t_labels:
            # Can't use title() here, there are usually more than one of these labels and they need to be positioned
            # at the particular axis value where the block of bars appear. Also, it would be common that the plot still
            # needs a title in addition to these (these outer labels are essentially tertiary axis ticks, not a title for the plot)
            if orientation == 'horizontal':
                ax.text(1, offset + (tval_offset - gaps[1] - gaps[2]) / 2, t, transform=ax.get_yaxis_transform(),
                        verticalalignment='center', horizontalalignment='left')
            else:
                ax.text(offset + (tval_offset - gaps[1] - gaps[2]) / 2, 1, t, transform=ax.get_xaxis_transform(),
                        verticalalignment='bottom', horizontalalignment='center')
            offset += tval_offset

    elif outer == 'results' and (show_all_labels or len(plotdata.results) > 1):
        offset = 0.0
        for r in plotdata.results:
            if orientation == 'horizontal':
                ax.text(1, offset + (result_offset - gaps[1] - gaps[2]) / 2, plotdata.results[r],
                        transform=ax.get_yaxis_transform(), verticalalignment='center', horizontalalignment='left')
            else:
                ax.text(offset + (result_offset - gaps[1] - gaps[2]) / 2, 1, plotdata.results[r],
                        transform=ax.get_xaxis_transform(), verticalalignment='bottom', horizontalalignment='center')
            offset += result_offset

    # If there are no block labels (e.g. due to stacking) and the number of inner labels matches the number of bars, then promote the inner group
    # labels and use them as bar labels
    if not any([x[1] for x in block_labels]) and len(block_labels) == len(inner_labels):
        if orientation == 'horizontal':
            ax.set_yticks([x[0] for x in inner_labels])
            ax.set_yticklabels([x[1] for x in inner_labels])
        else:
            ax.set_xticks([x[0] for x in inner_labels])
            ax.set_xticklabels([x[1] for x in inner_labels])
    elif show_all_labels or (len(inner_labels) > 1 and len(set([x for _, x in inner_labels])) > 1):
        # Otherwise, if there is only one inner group AND there are bar labels, don't show the inner group labels unless show_all_labels is True
        if orientation == 'horizontal':
            ax2 = ax.twinx()  # instantiate a second axes that shares the same y-axis
            ax2.set_yticks([x[0] for x in inner_labels])
            # TODO - At the moment there is a chance these labels will overlap, need to increase the offset somehow e.g. padding with spaces
            # Best to leave this until a specific test case arises
            # Simply rotating doesn't work because the vertical labels also overlap with the original axis labels
            # So would be necessary to apply some offset as well (perhaps from YAxis.get_text_widths)
            ax2.set_yticklabels([str(x[1]) for x in inner_labels])
            ax2.yaxis.set_ticks_position('left')
            ax2.set_ylim(ax.get_ylim())
        else:
            ax2 = ax.twiny()  # instantiate a second axes that shares the same x-axis
            ax2.set_xticks([x[0] for x in inner_labels])
            ax2.set_xticklabels(['\n\n' + str(x[1]) for x in inner_labels])
            ax2.xaxis.set_ticks_position('bottom')
            ax2.set_xlim(ax.get_xlim())
        ax2.tick_params(axis=u'both', which=u'both', length=0)
        ax2.spines['right'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        ax2.spines['bottom'].set_visible(False)

    fig.tight_layout()  # Do a final resizing

    # Do the legend last, so repositioning the axes works properly
    if legend_mode == 'together':
        _render_legend(ax, plot_type='bar', handles=legend_patches)
    elif legend_mode == 'separate':
        figs.append(sc.separatelegend(handles=legend_patches, reverse=True))

    return figs


def plot_series(plotdata, plot_type='line', axis=None, data=None, legend_mode=None, lw=None) -> list:
    """
    Produce a time series plot

    :param plotdata: a :py:class:`PlotData` instance to plot
    :param plot_type: 'line', 'stacked', or 'proportion' (stacked, normalized to 1)
    :param axis: Specify which quantity to group outputs on plots by - can be 'outputs', 'results', or 'pops'. A line will
                 be drawn for each of the selected quantity, and any other quantities will appear as separate figures.
    :param data:  Draw scatter points for data wherever the output label matches a data label. Only draws data if the plot_type is 'line'
    :param legend_mode: override the default legend mode in settings
    :param lw: override the default line width
    :return: A list of newly created Figures

    """


    global settings
    if legend_mode is None:
        legend_mode = settings['legend_mode']

    if lw is None:
        lw = settings['line_width']

    if axis is None:
        axis = 'outputs'
    assert axis in ['outputs', 'results', 'pops']

    figs = []
    ax = None

    plotdata = sc.dcp(plotdata)

    if axis == 'results':
        plotdata.set_colors(results=plotdata.results.keys())

        for pop in plotdata.pops.keys():
            for output in plotdata.outputs.keys():
                fig, ax = plt.subplots()
                fig.set_label('%s_%s' % (pop, output))
                figs.append(fig)

                units = list(set([plotdata[result, pop, output].units for result in plotdata.results]))
                if len(units) == 1 and units[0]:
                    ax.set_ylabel('%s (%s)' % (plotdata.outputs[output], units[0].title()))
                else:
                    ax.set_ylabel('%s' % (plotdata.outputs[output]))

                if plotdata.pops[pop] != FS.DEFAULT_SYMBOL_INAPPLICABLE:
                    ax.set_title('%s' % (plotdata.pops[pop]))

                if plot_type in ['stacked', 'proportion']:
                    y = np.stack([plotdata[result, pop, output].vals for result in plotdata.results])
                    y = y / np.sum(y, axis=0) if plot_type == 'proportion' else y
                    ax.stackplot(plotdata[plotdata.results.keys()[0], pop, output].tvec, y,
                                 labels=[plotdata.results[x] for x in plotdata.results],
                                 colors=[plotdata[result, pop, output].color for result in plotdata.results])
                    if plot_type == 'stacked' and data is not None:
                        _stack_data(ax, data, [plotdata[result, pop, output] for result in plotdata.results])
                else:
                    for i, result in enumerate(plotdata.results):
                        ax.plot(plotdata[result, pop, output].tvec, plotdata[result, pop, output].vals,
                                color=plotdata[result, pop, output].color, label=plotdata.results[result], lw=lw)
                        if data is not None and i == 0:
                            _render_data(ax, data, plotdata[result, pop, output])
                _apply_series_formatting(ax, plot_type)
                if legend_mode == 'together':
                    _render_legend(ax, plot_type)

    elif axis == 'pops':
        plotdata.set_colors(pops=plotdata.pops.keys())

        for result in plotdata.results:
            for output in plotdata.outputs:
                fig, ax = plt.subplots()
                fig.set_label('%s_%s' % (result, output))
                figs.append(fig)

                units = list(set([plotdata[result, pop, output].units for pop in plotdata.pops]))
                if len(units) == 1 and units[0]:
                    ax.set_ylabel('%s (%s)' % (plotdata.outputs[output], units[0].title()))
                else:
                    ax.set_ylabel('%s' % (plotdata.outputs[output]))

                ax.set_title('%s' % (plotdata.results[result]))
                if plot_type in ['stacked', 'proportion']:
                    y = np.stack([plotdata[result, pop, output].vals for pop in plotdata.pops])
                    y = y / np.sum(y, axis=0) if plot_type == 'proportion' else y
                    ax.stackplot(plotdata[result, plotdata.pops.keys()[0], output].tvec, y,
                                 labels=[plotdata.pops[x] for x in plotdata.pops],
                                 colors=[plotdata[result, pop, output].color for pop in plotdata.pops])
                    if plot_type == 'stacked' and data is not None:
                        _stack_data(ax, data, [plotdata[result, pop, output] for pop in plotdata.pops])
                else:
                    for pop in plotdata.pops:
                        ax.plot(plotdata[result, pop, output].tvec, plotdata[result, pop, output].vals,
                                color=plotdata[result, pop, output].color, label=plotdata.pops[pop], lw=lw)
                        if data is not None:
                            _render_data(ax, data, plotdata[result, pop, output])
                _apply_series_formatting(ax, plot_type)
                if legend_mode == 'together':
                    _render_legend(ax, plot_type)

    elif axis == 'outputs':
        plotdata.set_colors(outputs=plotdata.outputs.keys())

        for result in plotdata.results:
            for pop in plotdata.pops:
                fig, ax = plt.subplots()
                fig.set_label('%s_%s' % (result, pop))
                figs.append(fig)

                units = list(set([plotdata[result, pop, output].units for output in plotdata.outputs]))
                if len(units) == 1 and units[0]:
                    ax.set_ylabel(units[0].title())

                if plotdata.pops[pop] != FS.DEFAULT_SYMBOL_INAPPLICABLE:
                    ax.set_title('%s-%s' % (plotdata.results[result], plotdata.pops[pop]))
                else:
                    ax.set_title('%s' % (plotdata.results[result]))

                if plot_type in ['stacked', 'proportion']:
                    y = np.stack([plotdata[result, pop, output].vals for output in plotdata.outputs])
                    y = y / np.sum(y, axis=0) if plot_type == 'proportion' else y
                    ax.stackplot(plotdata[result, pop, plotdata.outputs.keys()[0]].tvec, y,
                                 labels=[plotdata.outputs[x] for x in plotdata.outputs],
                                 colors=[plotdata[result, pop, output].color for output in plotdata.outputs])
                    if plot_type == 'stacked' and data is not None:
                        _stack_data(ax, data, [plotdata[result, pop, output] for output in plotdata.outputs])
                else:
                    for output in plotdata.outputs:
                        ax.plot(plotdata[result, pop, output].tvec, plotdata[result, pop, output].vals,
                                color=plotdata[result, pop, output].color, label=plotdata.outputs[output], lw=lw)
                        if data is not None:
                            _render_data(ax, data, plotdata[result, pop, output])
                _apply_series_formatting(ax, plot_type)
                if legend_mode == 'together':
                    _render_legend(ax, plot_type)
    else:
        raise Exception('axis option must be one of "results", "pops" or "outputs"')

    if legend_mode == 'separate':
        reverse_legend = True if plot_type in ['stacked', 'proportion'] else False
        figs.append(sc.separatelegend(ax, reverse=reverse_legend))

    return figs


def _stack_data(ax, data, series) -> None:
    """
    Internal function to stack series data

    Used by `plot_series` when rendering stacked plots and also showing data.

    """

    baselines = np.cumsum(np.stack([s.vals for s in series]), axis=0)
    baselines = np.vstack([np.zeros((1, baselines.shape[1])), baselines])  # Insert row of zeros for first data row
    for i, s in enumerate(series):
        _render_data(ax, data, s, baselines[i, :], True)


def _render_data(ax, data, series, baseline=None, filled=False) -> None:
    """
    Renders a scatter plot for a single variable in a single population

    :param ax: axis object that data will be rendered in
    :param data: a ProjectData instance containing the data to render
    :param series: a `Series` object, the 'pop' and 'data_label' attributes are used to extract the TimeSeries from the data
    :param baseline: adds an offset to the data e.g. for stacked plots
    :param filled: fill the marker with a solid fill e.g. for stacked plots

    """

    ts = data.get_ts(series.data_label, series.pop)
    if ts is None:
        return

    if not ts.has_time_data:
        return

    t, y = ts.get_arrays()

    if baseline is not None:
        y_data = interpolate_func(series.tvec, baseline, t, method='pchip', extrapolate_nan=False)
        y = y + y_data

    if filled:
        ax.scatter(t, y, marker='o', s=40, linewidths=1, facecolors=series.color, color='k')  # label='Data %s %s' % (name(pop,proj),name(output,proj)))
    else:
        ax.scatter(t, y, marker='o', s=40, linewidths=3, facecolors='none', color=series.color)  # label='Data %s %s' % (name(pop,proj),name(output,proj)))


def _apply_series_formatting(ax, plot_type) -> None:
    # This function applies formatting that is common to all Series plots
    # (irrespective of the 'axis' setting)
    ax.autoscale(enable=True, axis='x', tight=True)
    ax.set_xlabel('Year')
    ax.set_ylim(bottom=0)
    _turn_off_border(ax)
    if plot_type == 'proportion':
        ax.set_ylim(top=1)
        ax.set_ylabel('Proportion ' + ax.get_ylabel())
    else:
        ax.set_ylim(top=ax.get_ylim()[1] * 1.05)
    ax.yaxis.set_major_formatter(FuncFormatter(sc.SItickformatter))


def _turn_off_border(ax) -> None:
    """
    Turns off top and right borders.

    Note that this function will leave the bottom and left borders on.

    :param ax: An axis object
    :return: None
    """
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')


def plot_legend(entries: dict, plot_type='patch', fig=None):
    """
    Render a new legend

    :param entries: Dict where key is the label and value is the colour e.g. `{'sus':'blue','vac':'red'}`
    :param plot_type: can be 'patch' or 'line'
    :param fig: Optionally takes in the figure to render the legend in. If not provided, a new figure will be created
    :return: The matplotlib `Figure` object containing the legend

    """

    h = []
    for label, color in entries.items():
        if plot_type == 'patch':
            h.append(Patch(color=color, label=label))
        else:
            h.append(Line2D([0], [0], color=color, label=label))

    legendsettings = {'loc': 'center', 'bbox_to_anchor': None, 'frameon': False}  # Settings for separate legend

    if fig is None:  # Draw in a new figure
        fig = sc.separatelegend(handles=h)
    else:
        existing_legend = fig.findobj(Legend)
        if existing_legend and existing_legend[0].parent is fig:  # If existing legend and this is a separate legend fig
            existing_legend[0].remove()  # Delete the old legend
            fig.legend(handles=h, **legendsettings)
        else:  # Drawing into an existing figure
            ax = fig.axes[0]
            legendsettings = {'loc': 'center left', 'bbox_to_anchor': (1.05, 0.5), 'ncol': 1}
            if existing_legend:
                existing_legend[0].remove()  # Delete the old legend
                ax.legend(handles=h, **legendsettings)
            else:
                ax.legend(handles=h, **legendsettings)
                box = ax.get_position()
                ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

    return fig


def _render_legend(ax, plot_type=None, handles=None) -> None:
    """
    Internal function to render a legend

    :param ax: Axis in which to create the legend
    :param plot_type: Used to decide whether to reverse the legend order for stackplots
    :param handles: The handles of the objects to enter in the legend. Labels should be stored in the handles

    """

    if handles is None:
        handles, labels = ax.get_legend_handles_labels()
    else:
        labels = [h.get_label() for h in handles]

    legendsettings = {'loc': 'center left', 'bbox_to_anchor': (1.05, 0.5), 'ncol': 1}
#    labels = [textwrap.fill(label, 16) for label in labels]

    if plot_type in ['stacked', 'proportion', 'bar']:
        ax.legend(handles=handles[::-1], labels=labels[::-1], **legendsettings)
    else:
        ax.legend(handles=handles, labels=labels, **legendsettings)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])


def reorder_legend(figs, order=None) -> None:
    """
    Change the order of an existing legend

    :param figs: Figure, or list of figures, containing legends for which the order should be changed
    :param order: Specification of the order in which to render the legend entries. This can be
                    - The string `'reverse'` which will reverse the order of the legend
                    - A list of indices mapping old position to new position. For example, if the
                        original label order was ['a,'b','c'], then order=[1,0,2] would result in ['b','a','c'].
                        If a partial list is provided, then only a subset of the legend entries will appear. This
                        allows this function to be used to remove legend entries as well.

    """

    if isinstance(figs, list):
        for fig in figs:  # Apply order operation to all figures passed in
            reorder_legend(fig, order=order)
        return
    else:
        fig = figs

    legend = fig.findobj(Legend)[0]
    assert len(legend._legend_handle_box._children) == 1, 'Only single-column legends are supported'
    vpacker = legend._legend_handle_box._children[0]

    if order is None:
        return
    elif order == 'reverse':
        order = range(len(legend.legendHandles) - 1, -1, -1)
    else:
        assert max(order) < len(vpacker._children), 'Requested index greater than number of legend entries'

    new_children = []
    for i in range(0, len(order)):
        new_children.append(vpacker._children[order[i]])
    vpacker._children = new_children


def relabel_legend(figs, labels) -> None:
    """
    Change the labels on an existing legend

    :param figs: Figure, or list of figures, to change labels in
    :param labels: `list` of labels the same length as the number of legend labels OR a `dict` of labels where the key is the index
    of the labels to change. The `dict` input option makes it possible to change only a subset of the labels.

    """

    if isinstance(figs, list):
        for fig in figs:
            relabel_legend(fig, labels=labels)
        return
    else:
        fig = figs

    legend = fig.findobj(Legend)[0]
    assert len(legend._legend_handle_box._children) == 1, 'Only single-column legends are supported'
    vpacker = legend._legend_handle_box._children[0]

    if isinstance(labels, list):
        assert len(labels) == len(vpacker._children), 'If specifying list of labels, length must match number of legend entries'
        labels = {i: l for i, l in enumerate(labels)}
    elif isinstance(labels, dict):
        idx = labels.keys()
        assert max(idx) < len(vpacker._children), 'Requested index greater than number of legend entries'
    else:
        raise Exception('Labels must be a list or a dict')

    for idx, label in labels.items():
        text = vpacker._children[idx]._children[1]._text
        text.set_text(label)


def _get_full_name(code_name: str, proj=None) -> str:
    """
    Return the label of an object retrieved by name

    If a :py:class:`Project` has been provided, code names can be converted into
    labels for plotting. This function is different to `framework.get_label()` though,
    because it supports converting population names to labels as well (this information is
    in the project's data, not in the framework), and it also supports converting
    link syntax (e.g. `sus:vac`) into full names as well. Note also that this means that the strings
    returned by `_get_full_name` can be as specific as necessary for plotting.

    :param code_name: The code name for a variable (e.g. `'sus'`, `'pris'`, `'sus:vac'`)
    :param proj: Optionally specify a :py:class:`Project` instance
    :return: If a project was provided, returns the full name. Otherwise, just returns the code name
    """

    if proj is None:
        return code_name

    if code_name in proj.data.pops:
        return proj.data.pops[code_name]['label']  # Convert population

    if ':' in code_name:  # We are parsing a link
        # Handle Links specified with colon syntax
        output_tokens = code_name.split(':')
        if len(output_tokens) == 2:
            output_tokens.append('')
        src, dest, par = output_tokens

        # If 'par_name:flow' syntax was used
        if dest == 'flow':
            if src in proj.framework:
                return "{0} (flow)".format(proj.framework.get_label(src))
            else:
                return "{0} (flow)".format(src)

        if src and src in proj.framework:
            src = proj.framework.get_label(src)

        if dest and dest in proj.framework:
            dest = proj.framework.get_label(dest)

        if par and par in proj.framework:
            par = proj.framework.get_label(par)

        full = 'Flow'
        if src:
            full += ' from {}'.format(src)
        if dest:
            full += ' to {}'.format(dest)
        if par:
            full += ' ({})'.format(par)
        return full
    else:
        if code_name in proj.framework:
            return proj.framework.get_label(code_name)
        else:
            return code_name


def _nested_loop(inputs, loop_order):
    """
    Zip list of lists in order

    This is used in :py:func:`plot_bars` to control whether 'times' or 'results' are the
    outer grouping. This function takes in a list of lists to iterate over, and their
    nesting order. It then yields tuples of items in the given order. Only tested
    for two levels (which are all that get used in :py:func:`plot_bars` but in theory
    supports an arbitrary number of items.

    :param inputs: List of lists. All lists should have the same length
    :param loop_order: Nesting order for the lists
    :return: Generator yielding tuples of items, one for each list

    Example usage:

    >>> list(_nested_loop([['a','b'],[1,2]],[0,1]))
    [['a', 1], ['a', 2], ['b', 1], ['b', 2]]

    Notice how the first two items have the same value for the first list
    while the items from the second list vary. If the `loop_order` is
    reversed, then:

    >>> list(_nested_loop([['a','b'],[1,2]],[1,0]))
    [['a', 1], ['b', 1], ['a', 2], ['b', 2]]

    Notice now how now the first two items have different values from the
    first list but the same items from the second list.

    """

    inputs = [inputs[i] for i in loop_order]
    iterator = itertools.product(*inputs)  # This is in the loop order
    for item in iterator:
        out = [None] * len(loop_order)
        for i in range(len(item)):
            out[loop_order[i]] = item[i]
        yield out


def _expand_dict(x: list) -> list:
    """
    Expand a dict with multiple keys into a list of single-key dicts

    An aggregation is defined as a mapping of multiple outputs into a single
    variable with a single label. This is represented by a dict with a single key,
    where the key is the label of the new quantity, and the value represents the instructions
    for how to compute the quantity. Sometimes outputs and pops are used directly, without
    renaming, so in this case, only the string representing the name of the quantity is required.
    Therefore, the format used internally by `PlotData` is that outputs/pops are represented
    as lists with length equal to the total number of quantities being returned/computed, and
    that list can contain dictionaries with single keys whenever an aggregation is required.

    For ease of use, it is convenient for users to enter multiple aggregations as a single dict
    with multiple keys. This function processes such a dict into the format used internally
    by PlotData.


    :param x: A list of inputs, containing strings or dicts that might have multiple keys
    :return: A list containing strings or dicts where any dicts have only one key

    Example usage:

    >>> _expand_dict(['a',{'b':1,'c':2}])
    ['a', {'b': 1}, {'c': 2}]

    """
    # If a list contains a dict with multiple keys, expand it into multiple dicts each
    # with a single key
    y = list()
    for v in x:
        if isinstance(v, dict):
            y += [{a: b} for a, b in v.items()]
        elif sc.isstring(v):
            y.append(v)
        else:
            raise Exception('Unknown type')
    return y


def _extract_labels(input_arrays) -> set:
    """
    Extract all quantities from list of dicts

    The inputs supported by `outputs` and `pops` can contain lists of optional
    aggregations. The first step in `PlotData` is to extract all of the quantities
    in the `Model` object that are required to compute the requested aggregations.

    :param input_arrays: Input string, list, or dict specifying aggregations
    :return: Set of unique string values that correspond to model quantities

    Example usage:

    >>> _extract_labels(['vac',{'a':['vac','sus']}])
    set(['vac','sus'])

    The main workflow is:

    ['vac',{'a':['vac','sus']}] -> ['vac','vac','sus'] -> set(['vac','sus'])

    i.e. first a flat list is constructed by replacing any dicts with their values
    and concatenating, then the list is converted into a set

    """

    out = []
    for x in input_arrays:
        if isinstance(x, dict):
            k = list(x.keys())
            assert len(k) == 1, 'Aggregation dict can only have one key'
            if sc.isstring(x[k[0]]):
                continue
            else:
                out += x[k[0]]
        else:
            out.append(x)
    return set(out)
