"""
Functions for generating plots from model outputs

This module implements Atomica's plotting library, which is used to
generate various plots from model outputs.

"""

import itertools
import os
import errno
from collections import defaultdict
from pandas import isna

import numpy as np
import scipy.interpolate
import scipy.integrate
import matplotlib.cm as cmx
import matplotlib.colors as matplotlib_colors
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Patch
from matplotlib.ticker import FuncFormatter

import atomica
import sciris as sc
from .model import Compartment, Characteristic, Parameter, Link, SourceCompartment, JunctionCompartment, SinkCompartment
from .results import Result
from .system import logger, NotFoundError
from .function_parser import parse_function
from .system import FrameworkSettings as FS
from .utils import format_duration, nested_loop

__all__ = ["save_figs", "PlotData", "Series", "plot_bars", "plot_series", "plot_legend", "reorder_legend", "relabel_legend"]

settings = dict()
settings["legend_mode"] = "together"  # Possible options are ['together','separate','none']
settings["bar_width"] = 1.0  # Width of bars in plot_bars()
settings["line_width"] = 3.0  # Width of lines in plot_series()
settings["marker_edge_width"] = 3.0
settings["dpi"] = 150  # average quality
settings["transparent"] = False


def save_figs(figs, path=".", prefix="", fnames=None, file_format="png") -> None:
    """
    Save figures to disk as PNG or other graphics format files

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
    :param file_format: the file format to save as, default png, allowed formats {png, ps, pdf, svg}
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
        fnames.append("")
    assert len(fnames) == len(figs), "Number of figures must match number of specified filenames, or the last figure must be a legend with no label"
    assert fnames[0], "The first figure name cannot be empty"

    assert file_format in ["png", "ps", "pdf", "svg"], f'File format {file_format} invalid. Format must be one of "png", "ps", "pdf", or "svg"'

    for i, fig in enumerate(figs):
        if not fnames[i]:  # assert above means that i>0
            fnames[i] = fnames[i - 1] + "_legend"
            legend = fig.findobj(Legend)[0]
            renderer = fig.canvas.get_renderer()
            fig.draw(renderer=renderer)
            bbox = legend.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
        else:
            bbox = "tight"
        fname = prefix + fnames[i] + "." + file_format
        fname = sc.sanitizefilename(fname)  # parameters may have inappropriate characters
        fig.savefig(os.path.join(path, fname), bbox_inches=bbox, dpi=settings["dpi"], transparent=settings["transparent"])
        logger.info('Saved figure "%s"', fname)


class PlotData:
    """
    Process model outputs into plottable quantities

    This is what gets passed into a plotting function, which displays a View of the data
    Conceptually, we are applying visuals to the data.
    But we are performing an extraction step rather than doing it directly because things like
    labels, colours, groupings etc. only apply to plots, not to results, and there could be several
    different views of the same data.

    Operators for ``-`` and ``/`` are defined to faciliate looking at differences and relative
    differences of derived quantities (quantities computed using ``PlotData`` operations) across
    individual results. To keep the implementation tractable, they don't generalize further than that,
    and operators ``+`` and ``*`` are not implemented because these operations rarely make sense
    for the data being operated on.

    :param results: Specify which results to plot. Can be

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

    :param output_aggregation: If an output aggregation is requested, combine the outputs listed using one of

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

    :param project: Optionally provide a :class:`Project` object, which will be used to convert names to labels in the outputs for plotting.

    :param time_aggregation: Optionally specify time aggregation method. Supported methods are 'integrate' and 'average' (no weighting). When aggregating
                                times, *non-annualized* flow rates will be used.

    :param t_bins: Optionally specify time bins, which will enable time aggregation. Supported inputs are

                      - A vector of bin edges. Time points are included if the time
                        is >= the lower bin value and < upper bin value.
                      - A scalar bin size (e.g. 5) which will be expanded to a vector spanning the data
                      - The string 'all' will maps to bin edges ``[-inf, inf]`` aggregating over all time

    :param accumulate: Optionally accumulate outputs over time. Can be 'sum' or 'integrate' to either sum quantities or integrate by multiplying by the timestep. Accumulation happens *after* time aggregation.
                   The logic is extremely simple - the quantities in the Series pass through ``cumsum``. If 'integrate' is selected, then the quantities are multiplied
                   by ``dt`` and the units are multiplied by ``years``
    :return: A :class:`PlotData` instance that can be passed to :func:`plot_series` or :func:`plot_bars`

    .. automethod:: __getitem__

    """

    # TODO: Make sure to chuck a useful error when t_bins is greater than sim duration, rather than just crashing.
    def __init__(self, results, outputs=None, pops=None, output_aggregation=None, pop_aggregation=None, project=None, time_aggregation=None, t_bins=None, accumulate=None):
        # Validate inputs
        if isinstance(results, sc.odict):
            results = [result for _, result in results.items()]
        elif not isinstance(results, list):
            results = [results]

        result_names = [x.name for x in results]
        if len(set(result_names)) != len(result_names):
            raise Exception("Results must have different names (in their result.name property)")

        if pops in [None, "all"]:
            pops = [pop.name for pop in results[0].model.pops]
        elif pops == "total":
            pops = [{"Total": [pop.name for pop in results[0].model.pops]}]
        pops = sc.promotetolist(pops)

        if outputs is None:
            outputs = [comp.name for comp in results[0].model.pops[0].comps if not (isinstance(comp, SourceCompartment) or isinstance(comp, JunctionCompartment) or isinstance(comp, SinkCompartment))]
        elif not isinstance(outputs, list):
            outputs = [outputs]

        pops = _expand_dict(pops)
        outputs = _expand_dict(outputs)

        assert output_aggregation in [None, "sum", "average", "weighted"]
        assert pop_aggregation in [None, "sum", "average", "weighted"]

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
            aggregated_timescales = dict()
            output_units = dict()
            output_timescales = dict()
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

                    try:
                        vars = pop.get_variable(output_label)
                    except NotFoundError as e:
                        in_pops = [x.name for x in result.model.pops if output_label in x]
                        message = f'Variable "{output_label}" was requested in population "{pop.name}" but it is only defined in these populations: {in_pops}'
                        raise NotFoundError(message) from e

                    if vars[0].vals is None:
                        raise Exception('Requested output "%s" was not recorded because only partial results were saved' % (vars[0].name))

                    if isinstance(vars[0], Link):
                        data_dict[output_label] = np.zeros(tvecs[result_label].shape)
                        compsize[output_label] = np.zeros(tvecs[result_label].shape)

                        for link in vars:
                            data_dict[output_label] += link.vals
                            compsize[output_label] += link.source.vals if not isinstance(link.source, JunctionCompartment) else link.source.outflow

                        # Annualize the units, and record that they correspond to a flow per year
                        data_dict[output_label] /= dt
                        output_units[output_label] = vars[0].units
                        output_timescales[output_label] = 1.0
                        data_label[output_label] = vars[0].parameter.name if (vars[0].parameter and vars[0].parameter.units == FS.QUANTITY_TYPE_NUMBER) else None  # Only use parameter data points if the units match

                    elif isinstance(vars[0], Parameter):
                        data_dict[output_label] = vars[0].vals
                        output_units[output_label] = vars[0].units
                        output_timescales[output_label] = vars[0].timescale  # The timescale attribute for non-transition parameters will already be set to None
                        data_label[output_label] = vars[0].name

                        # If there are links, we can retrieve a compsize for the user to do a weighted average
                        if vars[0].links:
                            output_units[output_label] = vars[0].units
                            compsize[output_label] = np.zeros(tvecs[result_label].shape)
                            for link in vars[0].links:
                                compsize[output_label] += link.source.vals if not isinstance(link.source, JunctionCompartment) else link.source.outflow

                    elif isinstance(vars[0], Compartment) or isinstance(vars[0], Characteristic):
                        data_dict[output_label] = vars[0].vals
                        compsize[output_label] = vars[0].vals
                        output_units[output_label] = vars[0].units
                        output_timescales[output_label] = None
                        data_label[output_label] = vars[0].name

                    else:
                        raise Exception("Unknown type")

                # Second pass, add in any dynamically computed quantities
                # Using model. Parameter objects will automatically sum over Links and convert Links
                # to annualized rates
                for output in outputs:
                    if not isinstance(output, dict):
                        continue

                    output_label, f_stack_str = list(output.items())[0]  # _extract_labels has already ensured only one key is present

                    if not sc.isstring(f_stack_str):
                        continue

                    def placeholder_pop():
                        return None

                    placeholder_pop.name = "None"
                    par = Parameter(pop=placeholder_pop, name=output_label)
                    fcn, dep_labels = parse_function(f_stack_str)
                    deps = {}
                    displayed_annualization_warning = False
                    for dep_label in dep_labels:
                        vars = pop.get_variable(dep_label)
                        if t_bins is not None and (isinstance(vars[0], Link) or isinstance(vars[0], Parameter)) and time_aggregation == "sum" and not displayed_annualization_warning:
                            raise Exception("Function includes Parameter/Link so annualized rates are being used. Aggregation should therefore use 'average' rather than 'sum'.")
                        deps[dep_label] = vars
                    par._fcn = fcn
                    par.deps = deps
                    par.preallocate(tvecs[result_label], dt)
                    par.update()
                    data_dict[output_label] = par.vals
                    output_units[output_label] = par.units
                    output_timescales[output_label] = None

                # Third pass, aggregate them according to any aggregations present
                for output in outputs:  # For each final output
                    if isinstance(output, dict):
                        output_name = list(output.keys())[0]
                        labels = output[output_name]

                        # If this was a function, aggregation over outputs doesn't apply so just put it straight in.
                        if sc.isstring(labels):
                            aggregated_outputs[pop_label][output_name] = data_dict[output_name]
                            aggregated_units[output_name] = "unknown"  # Also, we don't know what the units of a function are
                            aggregated_timescales[output_name] = None  # Timescale is lost
                            continue

                        units = list(set([output_units[x] for x in labels]))
                        timescales = list(set([np.nan if isna(output_timescales[x]) else output_timescales[x] for x in labels]))  # Ensure that None and nan don't appear as different timescales

                        # Set default aggregation method depending on the units of the quantity
                        if output_aggregation is None:
                            if units[0] in ["", FS.QUANTITY_TYPE_FRACTION, FS.QUANTITY_TYPE_PROPORTION, FS.QUANTITY_TYPE_PROBABILITY, FS.QUANTITY_TYPE_RATE]:
                                output_aggregation = "average"
                            else:
                                output_aggregation = "sum"

                        if len(units) > 1:
                            logger.warning("Aggregation for output '%s' is mixing units, this is almost certainly not desired.", output_name)
                            aggregated_units[output_name] = "unknown"
                        else:
                            if units[0] in ["", FS.QUANTITY_TYPE_FRACTION, FS.QUANTITY_TYPE_PROPORTION, FS.QUANTITY_TYPE_PROBABILITY, FS.QUANTITY_TYPE_RATE] and output_aggregation == "sum" and len(labels) > 1:  # Dimensionless, like prevalance
                                logger.warning("Output '%s' is not in number units, so output aggregation probably should not be 'sum'.", output_name)
                            aggregated_units[output_name] = output_units[labels[0]]

                        if len(timescales) > 1:
                            logger.warning("Aggregation for output '%s' is mixing timescales, this is almost certainly not desired.", output_name)
                            aggregated_timescales[output_name] = None
                        else:
                            aggregated_timescales[output_name] = output_timescales[labels[0]]

                        if output_aggregation == "sum":
                            aggregated_outputs[pop_label][output_name] = sum(data_dict[x] for x in labels)  # Add together all the outputs
                        elif output_aggregation == "average":
                            aggregated_outputs[pop_label][output_name] = sum(data_dict[x] for x in labels)  # Add together all the outputs
                            aggregated_outputs[pop_label][output_name] /= len(labels)
                        elif output_aggregation == "weighted":
                            aggregated_outputs[pop_label][output_name] = sum(data_dict[x] * compsize[x] for x in labels)  # Add together all the outputs
                            aggregated_outputs[pop_label][output_name] /= sum([compsize[x] for x in labels])
                    else:
                        aggregated_outputs[pop_label][output] = data_dict[output]
                        aggregated_units[output] = output_units[output]
                        aggregated_timescales[output] = output_timescales[output]

            # Now aggregate over populations
            # If we have requested a reduction over populations, this is done for every output present
            for pop in pops:  # This is looping over the population entries
                for output_name in aggregated_outputs[list(aggregated_outputs.keys())[0]].keys():
                    if isinstance(pop, dict):
                        pop_name = list(pop.keys())[0]
                        pop_labels = pop[pop_name]

                        # Set population aggregation method depending on
                        if pop_aggregation is None:
                            if aggregated_units[output_name] in ["", FS.QUANTITY_TYPE_FRACTION, FS.QUANTITY_TYPE_PROPORTION, FS.QUANTITY_TYPE_PROBABILITY, FS.QUANTITY_TYPE_RATE]:
                                pop_aggregation = "average"
                            else:
                                pop_aggregation = "sum"

                        if pop_aggregation == "sum":
                            if aggregated_units[output_name] in ["", FS.QUANTITY_TYPE_FRACTION, FS.QUANTITY_TYPE_PROPORTION, FS.QUANTITY_TYPE_PROBABILITY, FS.QUANTITY_TYPE_RATE] and len(pop_labels) > 1:
                                logger.warning("Output '%s' is not in number units, so population aggregation probably should not be 'sum'", output_name)
                            vals = sum(aggregated_outputs[x][output_name] for x in pop_labels)  # Add together all the outputs
                        elif pop_aggregation == "average":
                            vals = sum(aggregated_outputs[x][output_name] for x in pop_labels)  # Add together all the outputs
                            vals /= len(pop_labels)
                        elif pop_aggregation == "weighted":
                            vals = sum(aggregated_outputs[x][output_name] * popsize[x] for x in pop_labels)  # Add together all the outputs
                            vals /= sum([popsize[x] for x in pop_labels])
                        else:
                            raise Exception("Unknown pop aggregation method")
                        self.series.append(Series(tvecs[result_label], vals, result_label, pop_name, output_name, data_label[output_name], units=aggregated_units[output_name], timescale=aggregated_timescales[output_name], data_pop=pop_name))
                    else:
                        vals = aggregated_outputs[pop][output_name]
                        self.series.append(Series(tvecs[result_label], vals, result_label, pop, output_name, data_label[output_name], units=aggregated_units[output_name], timescale=aggregated_timescales[output_name], data_pop=pop))

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
            self.time_aggregate(t_bins, time_aggregation)

        if accumulate is not None:
            self.accumulate(accumulate)

    def accumulate(self, accumulation_method) -> None:
        """
        Accumulate values over time

        Accumulation methods are

        :param accumulation_method: Select whether to add or integrate. Supported methods are:
                                    - 'sum' : runs `cumsum` on all quantities - should not be used if units are flow rates (so will check for a timescale).
                                              Summation should be used for compartment-based quantities, such as DALYs
                                    - 'integrate' : integrate using trapezoidal rule, assuming initial value of 0
                                            Note that here there is no concept of 'dt' because we might have non-uniform time aggregation bins
                                            Therefore, we need to use the time vector actually contained in the Series object (via `cumtrapz()`)

        """

        # Note, in general we need to be able to explicitly specify the method to use, because we don't
        # know how to deal with parameter functions that have unknown units
        assert accumulation_method in ["sum", "integrate"]

        for s in self.series:
            if accumulation_method == "sum":
                if not isna(s.timescale):
                    raise Exception('Quantity "%s" has timescale %g which means it should be accumulated by integration, not summation' % (s.output, s.timescale))
                s.vals = np.cumsum(s.vals)
            elif accumulation_method == "integrate":
                if s.timescale:
                    s.vals = scipy.integrate.cumtrapz(s.vals, s.tvec / s.timescale)
                else:
                    s.vals = scipy.integrate.cumtrapz(s.vals, s.tvec)
                s.vals = np.insert(s.vals, 0, 0.0)

                # If integrating a quantity with a timescale, then lose the timescale factor
                # Otherwise, the units pick up a factor of time
                if not isna(s.timescale):
                    s.timescale = None
                else:
                    if s.units == "Number of people":
                        s.units = "Number of person-years"
                    else:
                        s.units += " years"

            else:
                raise Exception("Unknown accumulation type")

            self.outputs[s.output] = "Cumulative " + self.outputs[s.output]

    def time_aggregate(self, t_bins, time_aggregation=None, interpolation_method=None):
        """
        Aggregate values over time

        Note that *accumulation* is a running total, whereas *aggregation* refers to binning. The two can be
        both be applied (aggregation should be performed prior to accumulation).

        Normally, aggregation is performed when constructing a `PlotData` instance and this method does not need
        to be manually called. However, in rare cases, it may be necessary to explicitly set the interpolation method.
        Specifically, the interpolation method needs to match the underlying assumption for parameter values. For
        parameter scenarios, this may require that the 'previous' method is used (to match the assumption in the parameter overwrite)
        rather than relying on the standard assumption that databook quantities can be interpolated directly.

        This method modifies the `PlotData` object in-place. However, the modified object is also returned, so that
        time aggregation can be chained with other operations, the same as `PlotData.interpolate()`.

        :param t_bins: Vector of bin edges OR a scalar bin size, which will be automatically expanded to a vector of bin edges
        :param time_aggregation: can be 'integrate' or 'average'. Note that for quantities that have a timescale, flow parameters
                                 in number units will be adjusted accordingly (e.g. a parameter in units of 'people/day'
                                 aggregated over a 1 year period will display as the equivalent number of people that year)
        :param interpolation_method: Assumption on how the quantity behaves in between timesteps - in general, 'linear' should be suitable for
                                     most dynamic quantities, while 'previous' should be used for spending and other program-related quantities.
        :return: The same modified `PlotData` instance

        """

        assert time_aggregation in [None, "integrate", "average"]
        assert interpolation_method in [None, "linear", "previous"]

        if interpolation_method is None:
            interpolation_method = "linear"

        if not hasattr(t_bins, "__len__"):
            # If a scalar bin is provided, then it is
            if t_bins > (self.series[0].tvec[-1] - self.series[0].tvec[0]):
                # If bin width is greater than the sim duration, treat it the same as aggregating over all times
                t_bins = "all"
            else:
                if not (self.series[0].tvec[-1] - self.series[0].tvec[0]) % t_bins:
                    upper = self.series[0].tvec[-1] + t_bins
                else:
                    upper = self.series[0].tvec[-1]
                t_bins = np.arange(self.series[0].tvec[0], upper, t_bins)
        elif len(t_bins) < 2:
            raise Exception("If passing in t_bins as a list of bin edges, at least two values must be provided")

        if sc.isstring(t_bins) and t_bins == "all":
            t_bins = self.series[0].tvec[[0, -1]].ravel()

        t_bins = sc.promotetoarray(t_bins)
        lower = t_bins[0:-1]
        upper = t_bins[1:]

        for s in self.series:

            # Decide automatic aggregation method if not specified - this is done on a per-quantity basis
            if time_aggregation is None:
                if s.units in {FS.QUANTITY_TYPE_DURATION, FS.QUANTITY_TYPE_PROBABILITY, FS.QUANTITY_TYPE_RATE, FS.QUANTITY_TYPE_PROPORTION, FS.QUANTITY_TYPE_FRACTION}:
                    method = "average"
                else:
                    method = "integrate"
            else:
                method = time_aggregation
                if method == "integrate" and s.units in {FS.QUANTITY_TYPE_DURATION, FS.QUANTITY_TYPE_PROBABILITY, FS.QUANTITY_TYPE_RATE, FS.QUANTITY_TYPE_PROPORTION, FS.QUANTITY_TYPE_FRACTION}:
                    logger.warning('Units for series "%s" are "%s" so time aggregation should probably be "average", not "integrate"', s, s.units)

            if not isna(s.timescale):
                scale = s.timescale
            else:
                scale = 1.0

            # We interpolate in time-aggregation because the time bins are independent of the step size. In contrast,
            # accumulation preserves the same time bins, so we don't need the interpolation step and instead go straight
            # to summation or trapezoidal integration
            max_step = 0.5 * min(np.diff(s.tvec))  # Subdivide for trapezoidal integration with at least 2 divisions per timestep. Could be a lot of memory for integrating daily timesteps over a full simulation, but unlikely to be prohibitive
            vals = np.full(lower.shape, fill_value=np.nan)
            for i, (l, u) in enumerate(zip(lower, upper)):
                n = np.ceil((u - l) / max_step) + 1  # Add 1 so that in most cases, we can use the actual timestep values
                t2 = np.linspace(l, u, int(n))
                if interpolation_method == "linear":
                    v2 = np.interp(t2, s.tvec, s.vals, left=np.nan, right=np.nan)  # Return NaN outside bounds - it should never be valid to use extrapolated output values in time aggregation
                    vals[i] = np.trapz(y=v2 / scale, x=t2)  # Note division by timescale here, which annualizes it
                elif interpolation_method == "previous":
                    v2 = scipy.interpolate.interp1d(s.tvec, s.vals, kind="previous", copy=False, assume_sorted=True, bounds_error=False, fill_value=(np.nan, np.nan))(t2)
                    vals[i] = sum(v2[:-1] / scale * np.diff(t2))

            s.tvec = (lower + upper) / 2.0

            if method == "integrate":
                s.vals = np.array(vals)

                # If integrating the units might change
                if not isna(s.timescale):
                    # Any flow rates get integrated over the bin width, so change the timescale to None
                    # If the units were 'duration', this doesn't make sense, but integrating a duration doesn't
                    # make sense either. This would only happen if the user explicitly requests it anyway. For example,
                    # a parameter might go from 'number of people per month' to 'number of people'
                    s.timescale = None
                else:
                    # For quantities that don't have a timescale and are being integrated, the scale is 1.0 and
                    # it picks up 'years' in the units. So for example, 'number of people' becomes 'number of person years'
                    # This would be the usage 99% of the time (esp. for DALYs that are interested in number of person-years)
                    if s.units == "Number of people":
                        s.units = "Number of person-years"
                    elif s.units is not None:
                        s.units += " years"
                    else:
                        # If the units are none, decide what to do. It probably makes sense just to do nothing and
                        # leave the units blank, on the assumption that the user knows what they are doing if they
                        # are working with dimensionless quantities. More commonly, the quantity wouldn't actually
                        # be dimensionless, but it might not have had units entered e.g. parameter functions
                        pass

            elif method == "average":
                s.vals = np.array(vals) / np.diff(t_bins / scale)  # Divide by bin width if averaging within the bins
                s.units = "Average %s" % (s.units)  # It will look odd to do 'Cumulative Average Number of people' but that's will accurately what the user has requested (combining aggregation and accumulation is permitted, but not likely to be necessary)
            else:
                raise Exception('Unknown time aggregation type "%s"' % (time_aggregation))

            if sc.isstring(t_bins) and t_bins == "all":
                s.t_labels = ["All"]
            else:
                s.t_labels = ["%d-%d" % (low, high) for low, high in zip(lower, upper)]

        return self

    def __repr__(self):
        s = "PlotData\n"
        s += "Results: {0}\n".format(self.results.keys())
        s += "Pops: {0}\n".format(self.pops.keys())
        s += "Outputs: {0}\n".format(self.outputs.keys())
        return s

    def __sub__(self, other):
        """
        Difference between two instances

        This function iterates over all Series and takes their difference.
        The intended functionality is when wanting to compute the difference
        of derived quantities between two results. It only functions clearly when
        the only difference between two PlotData instances is the result they were
        constructed on. For example, model usage would be

        >>> a = PlotData(result1, outputs, pops)
        >>> b = PlotData(result2, outputs, pops)
        >>> c = a-b

        Both PlotData instances must have

            - The same pops
            - The same outputs
            - The same units (i.e. the same aggregation steps)
            - The same time points

        This method also incorporates singleton expansion for results, which means that one or both
        of the PlotData instances can contain a single result instead of multiple results. The single
        result will be applied against all of the results in the other PlotData instance, so for example
        a single baseline result can be subtracted off a set of scenarios. Note that if both PlotData instances
        have more than one result, then an error will be raised (because the result names don't have to match,
        it is otherwise impossible to identify which pairs of results to subtract).

        Series will be copied either from the PlotData instance that has multiple Results, or from the left :class:`PlotData` instance
        if both instances have only one result. Thus, ensure that ordering, formatting, and
        labels are set in advance on the appropriate object, if preserving the formatting is important. In practice, it would be usually
        be best to operate on the :class:`PlotData` values first, before setting formatting etc.

        :param other: A :class:`PlotData` instance to subtract off
        :return: A new :class:`PlotData` instance
        """

        assert isinstance(other, self.__class__), "PlotData subtraction can only operate on another PlotData instance"
        assert set(self.pops) == set(other.pops), "PlotData subtraction requires both instances to have the same populations"
        assert set(self.outputs) == set(other.outputs), "PlotData subtraction requires both instances to have the same populations"
        assert np.array_equal(self.tvals()[0], other.tvals()[0])

        if len(self.results) > 1 and len(other.results) > 1:
            raise Exception("When subtracting PlotData instances, both of them cannot have more than one result")
        elif len(other.results) > 1:
            new = sc.dcp(other)
        else:
            new = sc.dcp(self)
        new.results = sc.odict()

        for s1 in new.series:

            if len(other.results) > 1:
                s2 = self[self.results[0], s1.pop, s1.output]
            else:
                s2 = other[other.results[0], s1.pop, s1.output]
            assert s1.units == s2.units
            assert s1.timescale == s2.timescale

            if len(other.results) > 1:
                # If `b` has more than one result, then `s1` is from `b` and `s2` is from `a`, so the values for `a-b` are `s2-s1`
                s1.vals = s2.vals - s1.vals
                s1.result = "%s-%s" % (s2.result, s1.result)
            else:
                s1.vals = s1.vals - s2.vals
                s1.result = "%s-%s" % (s1.result, s2.result)

            new.results[s1.result] = s1.result

        return new

    def __truediv__(self, other):
        """
        Divide two instances

        This function iterates over all Series and divides them. The original intention
        is to use this functionality when wanting to compute fractional differences between
        insteances. It only functions clearly when the only difference between two PlotData instances is the result they were
        constructed on. For example, model usage would be

        >>> a = PlotData(result1, outputs, pops)
        >>> b = PlotData(result2, outputs, pops)
        >>> c = (a-b)/a

        Both PlotData instances must have

            - The same pops
            - The same outputs
            - The same units (i.e. the same aggregation steps)
            - The same time points

        Series will be copied either from the PlotData instance that has multiple Results, or from the left :class:`PlotData` instance
        if both instances have only one result. Thus, ensure that ordering, formatting, and
        labels are set in advance on the appropriate object, if preserving the formatting is important. In practice, it would be usually
        be best to operate on the :class:`PlotData` values first, before setting formatting etc.

        :param other: A :class:`PlotData` instance to serve as denominator in division
        :return: A new :class:`PlotData` instance

        """

        assert isinstance(other, self.__class__), "PlotData subtraction can only operate on another PlotData instance"
        assert set(self.pops) == set(other.pops), "PlotData subtraction requires both instances to have the same populations"
        assert set(self.outputs) == set(other.outputs), "PlotData subtraction requires both instances to have the same populations"
        assert np.array_equal(self.tvals()[0], other.tvals()[0])

        if len(self.results) > 1 and len(other.results) > 1:
            raise Exception("When subtracting PlotData instances, both of them cannot have more than one result")
        elif len(other.results) > 1:
            new = sc.dcp(other)
        else:
            new = sc.dcp(self)
        new.results = sc.odict()

        for s1 in new.series:
            if len(other.results) > 1:
                s2 = self[self.results[0], s1.pop, s1.output]
            else:
                s2 = other[other.results[0], s1.pop, s1.output]
            assert s1.units == s2.units
            assert s1.timescale == s2.timescale

            if len(other.results) > 1:
                # If `b` has more than one result, then `s1` is from `b` and `s2` is from `a`, so the values for `a-b` are `s2-s1`
                s1.vals = s2.vals / s1.vals
                s1.result = "%s/%s" % (s2.result, s1.result)
            else:
                s1.vals = s1.vals / s2.vals
                s1.result = "%s/%s" % (s1.result, s2.result)
            s1.units = ""
            new.results[s1.result] = s1.result

        return new

    @staticmethod
    def programs(results, outputs=None, t_bins=None, quantity="spending", accumulate=None, nan_outside=False):
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
        :param quantity: can be 'spending', 'coverage_number', 'coverage_eligible', or 'coverage_fraction'. The 'coverage_eligible' is
                        the sum of compartments reached by a program, such that coverage_fraction = coverage_number/coverage_eligible
        :param accumulate: can be 'sum' or 'integrate'
        :param nan_outside: If True, then values will be NaN outside the program start/stop year
        :return: A new :class:`PlotData` instance

        """

        # Sanitize the results input
        if isinstance(results, sc.odict):
            results = [result for _, result in results.items()]
        elif isinstance(results, Result):
            results = [results]

        result_names = [x.name for x in results]
        if len(set(result_names)) != len(result_names):
            raise Exception("Results must have different names (in their result.name property)")
        for result in results:
            if result.model.progset is None:
                raise Exception('Tried to plot program outputs for result "%s", but that result did not use programs' % result.name)

        if outputs is None:
            outputs = results[0].model.progset.programs.keys()
        elif not isinstance(outputs, list):
            outputs = [outputs]

        outputs = _expand_dict(outputs)

        assert quantity in ["spending", "equivalent_spending", "coverage_number", "coverage_eligible", "coverage_fraction", "coverage_capacity"]
        # Make a new PlotData instance
        # We are using __new__ because this method is to be formally considered an alternate constructor and
        # thus bears responsibility for ensuring this new instance is initialized correctly
        plotdata = PlotData.__new__(PlotData)
        plotdata.series = []

        # Because aggregations always occur within a Result object, loop over results
        for result in results:

            if quantity == "spending":
                all_vals = result.get_alloc()
                units = result.model.progset.currency
                timescales = dict.fromkeys(all_vals, 1.0)
            elif quantity == "equivalent_spending":
                all_vals = result.get_equivalent_alloc()
                units = result.model.progset.currency
                timescales = dict.fromkeys(all_vals, 1.0)
            elif quantity in {"coverage_capacity", "coverage_number"}:
                if quantity == "coverage_capacity":
                    all_vals = result.get_coverage("capacity")
                else:
                    all_vals = result.get_coverage("number")
                units = "Number of people"
                timescales = dict.fromkeys(all_vals, 1.0)
            elif quantity == "coverage_eligible":
                all_vals = result.get_coverage("eligible")
                units = "Number of people"
                timescales = dict.fromkeys(all_vals, None)
            elif quantity == "coverage_fraction":
                all_vals = result.get_coverage("fraction")
                units = "Fraction covered"
                timescales = dict.fromkeys(all_vals, None)
            else:
                raise Exception("Unknown quantity")

            for output in outputs:  # For each final output
                if isinstance(output, dict):  # If this is an aggregation over programs
                    if quantity in ["spending", "equivalent_spending"]:
                        output_name = list(output.keys())[0]  # This is the aggregated name
                        labels = output[output_name]  # These are the quantities being aggregated

                        # We only support summation for combining program spending, not averaging
                        vals = sum(all_vals[x] for x in labels)
                        output_name = output_name
                        data_label = None  # No data present for aggregations
                        timescale = timescales[labels[0]]
                    else:
                        raise Exception("Cannot use program aggregation for anything other than spending yet")
                else:
                    vals = all_vals[output]
                    output_name = output
                    data_label = output  # Can look up program spending by the program name
                    timescale = timescales[output]

                if nan_outside:
                    vals[(result.t < result.model.program_instructions.start_year) | (result.t > result.model.program_instructions.stop_year)] = np.nan

                plotdata.series.append(Series(result.t, vals, result=result.name, pop=FS.DEFAULT_SYMBOL_INAPPLICABLE, output=output_name, data_label=data_label, units=units, timescale=timescale))  # The program should specify the units for its unit cost

        plotdata.results = sc.odict()
        for result in results:
            plotdata.results[result.name] = result.name

        plotdata.pops = sc.odict({FS.DEFAULT_SYMBOL_INAPPLICABLE: FS.DEFAULT_SYMBOL_INAPPLICABLE})

        plotdata.outputs = sc.odict()
        for output in outputs:
            key = list(output.keys())[0] if isinstance(output, dict) else output
            plotdata.outputs[key] = results[0].model.progset.programs[key].label if key in results[0].model.progset.programs else key

        if t_bins is not None:
            # TODO - time aggregation of coverage_number by integration should only be applied to one-off programs
            # TODO - confirm time aggregation of spending is correct for the units entered in databook or in overwrites
            if quantity in {"spending", "equivalent_spending", "coverage_number"}:
                plotdata.time_aggregate(t_bins, "integrate", interpolation_method="previous")
            elif quantity in {"coverage_eligible", "coverage_fraction"}:
                plotdata.time_aggregate(t_bins, "average", interpolation_method="previous")
            else:
                raise Exception("Unknown quantity type for aggregation")

        if accumulate is not None:
            plotdata.accumulate(accumulate)

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
            assert all(np.equal(self.series[i].tvec, tvec)), "All series must have the same time points"
        return tvec, t_labels

    def interpolate(self, new_tvec):
        """
        Interpolate all ``Series`` onto new time values

        This will modify all of the contained ``Series`` objects in-place.
        The modified ``PlotData`` instance is also returned, so that interpolation and
        construction can be performed in one line. i.e. both

        >>> d = PlotData(result)
        ... d.interpolate(tvals)

        and

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

        The :class:`Series` objects stored within :class:`PlotData` are each bound to a single
        result, population, and output. This operator makes it possible to easily retrieve
        a particular :class:`Series` instance. For example,

        >>> d = PlotData(results)
        ... d['default','0-4','sus']

        :param key: A tuple of (result,pop,output)
        :return: A :class:`Series` instance

        """

        for s in self.series:
            if s.result == key[0] and s.pop == key[1] and s.output == key[2]:
                return s
        raise Exception("Series %s-%s-%s not found" % (key[0], key[1], key[2]))

    def set_colors(self, colors=None, results="all", pops="all", outputs="all", overwrite=False):
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
            assert len(colors) == len(targets), "Number of colors must either be a string, or a list with as many elements as colors to set"
            colors = colors
        elif colors.startswith("#") or colors not in [m for m in plt.cm.datad if not m.endswith("_r")]:
            colors = [colors for _ in range(len(targets))]  # Apply color to all requested outputs
        else:
            color_norm = matplotlib_colors.Normalize(vmin=-1, vmax=len(targets))
            scalar_map = cmx.ScalarMappable(norm=color_norm, cmap=colors)
            colors = [scalar_map.to_rgba(index) for index in range(len(targets))]

        # Now each of these colors gets assigned
        for color, target in zip(colors, targets):
            series = self.series
            series = [x for x in series if (x.result == target[0] or target[0] == "all")]
            series = [x for x in series if (x.pop == target[1] or target[1] == "all")]
            series = [x for x in series if (x.output == target[2] or target[2] == "all")]
            for s in series:
                s.color = color if (s.color is None or overwrite) else s.color

        return self


class Series:
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
    :param timescale: For Number, Probability and Duration units, there are timescales associated with them

    """

    def __init__(self, tvec, vals, result="default", pop="default", output="default", data_label="", color=None, units="", timescale=None, data_pop=""):
        self.tvec = np.copy(tvec)  # : array of time values
        self.t_labels = np.copy(self.tvec)  # : Iterable array of time labels - could be set to strings like [2010-2014]
        self.vals = np.copy(vals)  # : array of values
        self.result = result  # : name of the result associated with ths data
        self.pop = pop  # : name of the pop associated with the data
        self.output = output  # : name of the output associated with the data
        self.color = color  # : the color to render the `Series` with
        self.data_label = data_label  #: Used to identify data for plotting - should match the name of a data TDVE
        self.data_pop = data_pop  #: Used to identify which population in the TDVE (specified by ``data_label``) to look up
        self.units = units  #: The units for the quantity to display on the plot

        #: If the quantity has a time-like denominator (e.g. number/year, probability/day) then the denominator is stored here (in units of years)
        #: This enables quantities to be time-aggregated correctly (e.g. number/day must be converted to number/timestep prior to summation or integration)
        #: For links, the timescale is normally just ``dt``. This also enables more rigorous checking for quantities with time denominators than checking
        #: for a string like ``'/year'`` because users may not set this specifically.
        self.timescale = timescale

        if np.any(np.isnan(vals)):
            logger.warning("%s contains NaNs", self)

    @property
    def unit_string(self) -> str:
        """
        Return the units for the quantity including timescale

        When making plots, it is useful for the axis label to have the units of the quantity. The units should
        also include the time scale e.g. "Death rate (probability per day)". However, if the timescale changes
        due to aggregation or accumulation, then the value might be different. In that case,
        The unit of the quantity is interpreted as a numerator if the Timescale is not None. For example,
        Compartments have units of 'number', while Links have units of 'number/timestep' which is stored as
        ``Series.units='number'`` and ``Series.timescale=0.25`` (if ``dt=0.25``). The `unit_string` attribute
        returns a string that is suitable to use for plots e.g. 'number per week'.

        :return: A string representation of the units for use in plotting

        """

        if not isna(self.timescale):
            if self.units == FS.QUANTITY_TYPE_DURATION:
                return "%s" % (format_duration(self.timescale, True))
            else:
                return "%s per %s" % (self.units, format_duration(self.timescale))
        else:
            return self.units

    def __repr__(self):
        return "Series(%s,%s,%s)" % (self.result, self.pop, self.output)

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

        out_of_bounds = (new_tvec < self.tvec[0]) | (new_tvec > self.tvec[-1])
        if np.any(out_of_bounds):
            logger.warning("Series has values from %.2f to %.2f so requested time points %s are out of bounds", self.tvec[0], self.tvec[-1], new_tvec[out_of_bounds])
        return np.interp(sc.promotetoarray(new_tvec), self.tvec, self.vals, left=np.nan, right=np.nan)


def plot_bars(plotdata, stack_pops=None, stack_outputs=None, outer=None, legend_mode=None, show_all_labels=False, orientation="vertical") -> list:
    """
    Produce a bar plot

    :param plotdata: a :class:`PlotData` instance to plot
    :param stack_pops: A list of lists with populations to stack. A bar is rendered for each item in the list.
                       For example, `[['0-4','5-14'],['15-64']]` will render two bars, with two populations stacked
                       in the first bar, and only one population in the second bar. Items not appearing in this list
                       will be rendered unstacked.
    :param stack_outputs: Same as `stack_pops`, but for outputs.
    :param outer: Optionally select whether the outermost/highest level of grouping is by `'times'` or by `'results'`
    :param legend_mode: override the default legend mode in settings
    :param show_all_labels: If True, then inner/outer labels will be shown even if there is only one label
    :param orientation: 'vertical' (default) or 'horizontal'
    :return: A list of newly created Figures

    """

    global settings
    if legend_mode is None:
        legend_mode = settings["legend_mode"]

    assert outer in [None, "times", "results"], 'Supported outer groups are "times" or "results"'
    assert orientation in ["vertical", "horizontal"], 'Supported orientations are "vertical" or "horizontal"'

    if outer is None:
        if len(plotdata.results) == 1:
            # If there is only one Result, then use 'outer=results' so that times can be promoted to axis labels
            outer = "results"
        else:
            outer = "times"

    plotdata = sc.dcp(plotdata)

    # Note - all of the tvecs must be the same
    tvals, t_labels = plotdata.tvals()  # We have to iterate over these, with offsets, if there is more than one

    # If quantities are stacked, then they need to be coloured differently.
    if stack_pops is None:
        color_by = "outputs"
        plotdata.set_colors(outputs=plotdata.outputs.keys())
    elif stack_outputs is None:
        color_by = "pops"
        plotdata.set_colors(pops=plotdata.pops.keys())
    else:
        color_by = "both"
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
            return [(x, "", [x]) for x in available_items]
        elif input_stacks == "all":
            # Put all available items into a single stack
            return process_input_stacks([available_items], available_items)

        items = set()
        output_stacks = []
        if isinstance(input_stacks, list):
            for x in input_stacks:
                if isinstance(x, list):
                    output_stacks.append(("", "", x) if len(x) > 1 else (x[0], "", x))
                    items.update(x)
                elif sc.isstring(x):
                    output_stacks.append((x, "", [x]))
                    items.add(x)
                else:
                    raise Exception("Unsupported input")

        elif isinstance(input_stacks, dict):
            for k, x in input_stacks.items():
                if isinstance(x, list):
                    output_stacks.append(("", k, x) if len(x) > 1 else (x[0], k, x))
                    items.update(x)
                elif sc.isstring(x):
                    output_stacks.append((x, k, [x]))
                    items.add(x)
                else:
                    raise Exception("Unsupported input")

        # Add missing items
        missing = list(set(available_items) - items)
        output_stacks += [(x, "", [x]) for x in missing]
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

    width = settings["bar_width"]
    gaps = [0.1, 0.4, 0.8]  # Spacing within blocks, between inner groups, and between outer groups

    block_width = len(bar_pops) * (width + gaps[0])

    # If there is only one bar group, then increase spacing between bars
    if len(tvals) == 1 and len(plotdata.results) == 1:
        gaps[0] = 0.3

    if outer == "times":
        if len(plotdata.results) == 1:  # If there is only one inner group
            gaps[2] = gaps[1]
            gaps[1] = 0
        result_offset = block_width + gaps[1]
        tval_offset = len(plotdata.results) * (block_width + gaps[1]) + gaps[2]
        iterator = nested_loop([range(len(plotdata.results)), range(len(tvals))], [0, 1])
    elif outer == "results":
        if len(tvals) == 1:  # If there is only one inner group
            gaps[2] = gaps[1]
            gaps[1] = 0
        result_offset = len(tvals) * (block_width + gaps[1]) + gaps[2]
        tval_offset = block_width + gaps[1]
        iterator = nested_loop([range(len(plotdata.results)), range(len(tvals))], [1, 0])
    else:
        raise Exception('outer option must be either "times" or "results"')

    figs = []
    fig, ax = plt.subplots()
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    fig.set_label("bars")
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
    negative_present = False  # If True, it means negative quantities were present

    # Iterate over the inner and outer groups, rendering blocks at a time
    for r_idx, t_idx in iterator:
        base_offset = r_idx * result_offset + t_idx * tval_offset  # Offset between outer groups
        block_offset = 0.0  # Offset between inner groups

        if outer == "results":
            inner_labels.append((base_offset + block_width / 2.0, t_labels[t_idx]))
        elif outer == "times":
            inner_labels.append((base_offset + block_width / 2.0, plotdata.results[r_idx]))

        for idx, bar_pop, bar_output in zip(range(len(bar_pops)), bar_pops, bar_outputs):
            # pop is something like ['0-4','5-14'] or ['0-4']
            # output is something like ['sus','vac'] or ['0-4'] depending on the stack

            y0 = [0, 0]  # Baselines for positive and negative bars, respectively

            # Set the name of the bar
            # If the user provided a label, it will always be displayed
            # In addition, if there is more than one label of the other (output/pop) type,
            # then that label will also be shown, otherwise it will be suppressed
            if bar_pop[1] or bar_output[1]:
                if bar_pop[1]:
                    if bar_output[1]:
                        bar_label = "%s\n%s" % (bar_pop[1], bar_output[1])
                    elif len(output_stacks) > 1 and len(set([x[0] for x in output_stacks])) > 1 and bar_output[0]:
                        bar_label = "%s\n%s" % (bar_pop[1], bar_output[0])
                    else:
                        bar_label = bar_pop[1]
                else:
                    if len(pop_stacks) > 1 and len(set([x[0] for x in pop_stacks])) > 1 and bar_pop[0]:
                        bar_label = "%s\n%s" % (bar_pop[0], bar_output[1])
                    else:
                        bar_label = bar_output[1]
            else:
                if color_by == "outputs" and len(pop_stacks) > 1 and len(set([x[0] for x in pop_stacks])) > 1:
                    bar_label = plotdata.pops[bar_pop[0]]
                elif color_by == "pops" and len(output_stacks) > 1 and len(set([x[0] for x in output_stacks])) > 1:
                    bar_label = plotdata.outputs[bar_output[0]]
                else:
                    bar_label = ""

            for pop in bar_pop[2]:
                for output in bar_output[2]:
                    series = plotdata[plotdata.results[r_idx], pop, output]
                    y = series.vals[t_idx]
                    if y >= 0:
                        baseline = y0[0]
                        y0[0] += y
                        height = y
                    else:
                        baseline = y0[1] + y
                        y0[1] += y
                        height = -y
                        negative_present = True

                    if orientation == "horizontal":
                        rectangles[series.color].append(Rectangle((baseline, base_offset + block_offset), height, width))
                    else:
                        rectangles[series.color].append(Rectangle((base_offset + block_offset, baseline), width, height))

                    if series.color in color_legend and (pop, output) not in color_legend[series.color]:
                        color_legend[series.color].append((pop, output))
                    elif series.color not in color_legend:
                        color_legend[series.color] = [(pop, output)]

            block_labels.append((base_offset + block_offset + width / 2.0, bar_label))

            block_offset += width + gaps[0]

    # Add the patches to the figure and assemble the legend patches
    legend_patches = []

    for color, items in color_legend.items():
        pc = PatchCollection(rectangles[color], facecolor=color, edgecolor="none")
        ax.add_collection(pc)
        pops = set([x[0] for x in items])
        outputs = set([x[1] for x in items])

        if pops == set(plotdata.pops.keys()) and len(outputs) == 1:  # If the same color is used for all pops and always the same output
            label = plotdata.outputs[items[0][1]]  # Use the output name
        elif outputs == set(plotdata.outputs.keys()) and len(pops) == 1:  # Same color for all outputs and always same pop
            label = plotdata.pops[items[0][0]]  # Use the pop name
        else:
            label = ""
            for x in items:
                label += "%s-%s,\n" % (plotdata.pops[x[0]], plotdata.outputs[x[1]])
            label = label.strip()[:-1]  # Replace trailing newline and comma
        legend_patches.append(Patch(facecolor=color, label=label))

    # Set axes now, because we need block_offset and base_offset after the loop
    ax.autoscale()
    _turn_off_border(ax)
    block_labels = sorted(block_labels, key=lambda x: x[0])

    if orientation == "horizontal":
        ax.set_ylim(bottom=-2 * gaps[0], top=block_offset + base_offset)
        fig.set_figheight(0.75 + 0.75 * (block_offset + base_offset))
        if not negative_present:
            ax.set_xlim(left=0)
        else:
            ax.spines["right"].set_color("k")
            ax.spines["right"].set_position("zero")
        ax.set_yticks([x[0] for x in block_labels])
        ax.set_yticklabels([x[1] for x in block_labels])
        ax.invert_yaxis()
        sc.SIticks(ax=ax, axis="x")
    else:
        ax.set_xlim(left=-2 * gaps[0], right=block_offset + base_offset)
        fig.set_figwidth(1.1 + 1.1 * (block_offset + base_offset))
        if not negative_present:
            ax.set_ylim(bottom=0)
        else:
            ax.spines["top"].set_color("k")
            ax.spines["top"].set_position("zero")
        ax.set_xticks([x[0] for x in block_labels])
        ax.set_xticklabels([x[1] for x in block_labels])
        sc.SIticks(ax=ax, axis="y")

    # Calculate the units. As all bar patches are shown on the same axis, they are all expected to have the
    # same units. If they do not, the plot could be misleading
    units = list(set([x.unit_string for x in plotdata.series]))
    if len(units) == 1 and units[0] is not None:
        if orientation == "horizontal":
            ax.set_xlabel(units[0].capitalize())
        else:
            ax.set_ylabel(units[0].capitalize())
    elif len(units) > 1:
        logger.warning("Warning - bar plot quantities mix units, double check that output selection is correct")

    # Outer group labels are only displayed if there is more than one group
    if outer == "times" and (show_all_labels or len(tvals) > 1):
        offset = 0.0
        for t in t_labels:
            # Can't use title() here, there are usually more than one of these labels and they need to be positioned
            # at the particular axis value where the block of bars appear. Also, it would be common that the plot still
            # needs a title in addition to these (these outer labels are essentially tertiary axis ticks, not a title for the plot)
            if orientation == "horizontal":
                ax.text(1, offset + (tval_offset - gaps[1] - gaps[2]) / 2, t, transform=ax.get_yaxis_transform(), verticalalignment="center", horizontalalignment="left")
            else:
                ax.text(offset + (tval_offset - gaps[1] - gaps[2]) / 2, 1, t, transform=ax.get_xaxis_transform(), verticalalignment="bottom", horizontalalignment="center")
            offset += tval_offset

    elif outer == "results" and (show_all_labels or len(plotdata.results) > 1):
        offset = 0.0
        for r in plotdata.results:
            if orientation == "horizontal":
                ax.text(1, offset + (result_offset - gaps[1] - gaps[2]) / 2, plotdata.results[r], transform=ax.get_yaxis_transform(), verticalalignment="center", horizontalalignment="left")
            else:
                ax.text(offset + (result_offset - gaps[1] - gaps[2]) / 2, 1, plotdata.results[r], transform=ax.get_xaxis_transform(), verticalalignment="bottom", horizontalalignment="center")
            offset += result_offset

    # If there are no block labels (e.g. due to stacking) and the number of inner labels matches the number of bars, then promote the inner group
    # labels and use them as bar labels
    if not any([x[1] for x in block_labels]) and len(block_labels) == len(inner_labels):
        if orientation == "horizontal":
            ax.set_yticks([x[0] for x in inner_labels])
            ax.set_yticklabels([x[1] for x in inner_labels])
        else:
            ax.set_xticks([x[0] for x in inner_labels])
            ax.set_xticklabels([x[1] for x in inner_labels])
    elif show_all_labels or (len(inner_labels) > 1 and len(set([x for _, x in inner_labels])) > 1):
        # Otherwise, if there is only one inner group AND there are bar labels, don't show the inner group labels unless show_all_labels is True
        if orientation == "horizontal":
            ax2 = ax.twinx()  # instantiate a second axes that shares the same y-axis
            ax2.set_yticks([x[0] for x in inner_labels])
            # TODO - At the moment there is a chance these labels will overlap, need to increase the offset somehow e.g. padding with spaces
            # Best to leave this until a specific test case arises
            # Simply rotating doesn't work because the vertical labels also overlap with the original axis labels
            # So would be necessary to apply some offset as well (perhaps from YAxis.get_text_widths)
            ax2.set_yticklabels([str(x[1]) for x in inner_labels])
            ax2.yaxis.set_ticks_position("left")
            ax2.set_ylim(ax.get_ylim())
        else:
            ax2 = ax.twiny()  # instantiate a second axes that shares the same x-axis
            ax2.set_xticks([x[0] for x in inner_labels])
            ax2.set_xticklabels(["\n\n" + str(x[1]) for x in inner_labels])
            ax2.xaxis.set_ticks_position("bottom")
            ax2.set_xlim(ax.get_xlim())
        ax2.tick_params(axis="both", which="both", length=0)
        ax2.spines["right"].set_visible(False)
        ax2.spines["top"].set_visible(False)
        ax2.spines["left"].set_visible(False)
        ax2.spines["bottom"].set_visible(False)

    fig.tight_layout()  # Do a final resizing

    # Do the legend last, so repositioning the axes works properly
    if legend_mode == "together":
        _render_legend(ax, plot_type="bar", handles=legend_patches)
    elif legend_mode == "separate":
        figs.append(sc.separatelegend(handles=legend_patches, reverse=True))

    return figs


def plot_series(plotdata, plot_type="line", axis=None, data=None, legend_mode=None, lw=None) -> list:
    """
    Produce a time series plot

    :param plotdata: a :class:`PlotData` instance to plot
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
        legend_mode = settings["legend_mode"]

    if lw is None:
        lw = settings["line_width"]

    if axis is None:
        axis = "outputs"
    assert axis in ["outputs", "results", "pops"]

    figs = []
    ax = None

    plotdata = sc.dcp(plotdata)
    if min([len(s.vals) for s in plotdata.series]) == 1:
        logger.warning("At least one Series has only one timepoint. Series must have at least 2 time points to be rendered as a line - `plot_bars` may be more suitable for such data")

    if axis == "results":
        plotdata.set_colors(results=plotdata.results.keys())

        for pop in plotdata.pops.keys():
            for output in plotdata.outputs.keys():
                fig, ax = plt.subplots()
                fig.patch.set_alpha(0)
                ax.patch.set_alpha(0)
                fig.set_label("%s_%s" % (pop, output))
                figs.append(fig)

                units = list(set([plotdata[result, pop, output].unit_string for result in plotdata.results]))
                if len(units) == 1 and units[0]:
                    ax.set_ylabel("%s (%s)" % (plotdata.outputs[output], units[0]))
                else:
                    ax.set_ylabel("%s" % (plotdata.outputs[output]))

                if plotdata.pops[pop] != FS.DEFAULT_SYMBOL_INAPPLICABLE:
                    ax.set_title("%s" % (plotdata.pops[pop]))

                if plot_type in ["stacked", "proportion"]:
                    y = np.stack([plotdata[result, pop, output].vals for result in plotdata.results])
                    y = y / np.sum(y, axis=0) if plot_type == "proportion" else y
                    ax.stackplot(plotdata[plotdata.results.keys()[0], pop, output].tvec, y, labels=[plotdata.results[x] for x in plotdata.results], colors=[plotdata[result, pop, output].color for result in plotdata.results])
                    if plot_type == "stacked" and data is not None:
                        _stack_data(ax, data, [plotdata[result, pop, output] for result in plotdata.results])
                else:
                    for i, result in enumerate(plotdata.results):
                        ax.plot(plotdata[result, pop, output].tvec, plotdata[result, pop, output].vals, color=plotdata[result, pop, output].color, label=plotdata.results[result], lw=lw)
                        if data is not None and i == 0:
                            _render_data(ax, data, plotdata[result, pop, output])
                _apply_series_formatting(ax, plot_type)
                if legend_mode == "together":
                    _render_legend(ax, plot_type)

    elif axis == "pops":
        plotdata.set_colors(pops=plotdata.pops.keys())

        for result in plotdata.results:
            for output in plotdata.outputs:
                fig, ax = plt.subplots()
                fig.patch.set_alpha(0)
                ax.patch.set_alpha(0)
                fig.set_label("%s_%s" % (result, output))
                figs.append(fig)

                units = list(set([plotdata[result, pop, output].unit_string for pop in plotdata.pops]))
                if len(units) == 1 and units[0]:
                    ax.set_ylabel("%s (%s)" % (plotdata.outputs[output], units[0]))
                else:
                    ax.set_ylabel("%s" % (plotdata.outputs[output]))

                ax.set_title("%s" % (plotdata.results[result]))
                if plot_type in ["stacked", "proportion"]:
                    y = np.stack([plotdata[result, pop, output].vals for pop in plotdata.pops])
                    y = y / np.sum(y, axis=0) if plot_type == "proportion" else y
                    ax.stackplot(plotdata[result, plotdata.pops.keys()[0], output].tvec, y, labels=[plotdata.pops[x] for x in plotdata.pops], colors=[plotdata[result, pop, output].color for pop in plotdata.pops])
                    if plot_type == "stacked" and data is not None:
                        _stack_data(ax, data, [plotdata[result, pop, output] for pop in plotdata.pops])
                else:
                    for pop in plotdata.pops:
                        ax.plot(plotdata[result, pop, output].tvec, plotdata[result, pop, output].vals, color=plotdata[result, pop, output].color, label=plotdata.pops[pop], lw=lw)
                        if data is not None:
                            _render_data(ax, data, plotdata[result, pop, output])
                _apply_series_formatting(ax, plot_type)
                if legend_mode == "together":
                    _render_legend(ax, plot_type)

    elif axis == "outputs":
        plotdata.set_colors(outputs=plotdata.outputs.keys())

        for result in plotdata.results:
            for pop in plotdata.pops:
                fig, ax = plt.subplots()
                fig.patch.set_alpha(0)
                ax.patch.set_alpha(0)
                fig.set_label("%s_%s" % (result, pop))
                figs.append(fig)

                units = list(set([plotdata[result, pop, output].unit_string for output in plotdata.outputs]))
                if len(units) == 1 and units[0]:
                    ax.set_ylabel(units[0][0].upper() + units[0][1:])

                if plotdata.pops[pop] != FS.DEFAULT_SYMBOL_INAPPLICABLE:
                    ax.set_title("%s-%s" % (plotdata.results[result], plotdata.pops[pop]))
                else:
                    ax.set_title("%s" % (plotdata.results[result]))

                if plot_type in ["stacked", "proportion"]:
                    y = np.stack([plotdata[result, pop, output].vals for output in plotdata.outputs])
                    y = y / np.sum(y, axis=0) if plot_type == "proportion" else y
                    ax.stackplot(plotdata[result, pop, plotdata.outputs.keys()[0]].tvec, y, labels=[plotdata.outputs[x] for x in plotdata.outputs], colors=[plotdata[result, pop, output].color for output in plotdata.outputs])
                    if plot_type == "stacked" and data is not None:
                        _stack_data(ax, data, [plotdata[result, pop, output] for output in plotdata.outputs])
                else:
                    for output in plotdata.outputs:
                        ax.plot(plotdata[result, pop, output].tvec, plotdata[result, pop, output].vals, color=plotdata[result, pop, output].color, label=plotdata.outputs[output], lw=lw)
                        if data is not None:
                            _render_data(ax, data, plotdata[result, pop, output])
                _apply_series_formatting(ax, plot_type)
                if legend_mode == "together":
                    _render_legend(ax, plot_type)
    else:
        raise Exception('axis option must be one of "results", "pops" or "outputs"')

    if legend_mode == "separate":
        reverse_legend = True if plot_type in ["stacked", "proportion"] else False
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

    ts = data.get_ts(series.data_label, series.data_pop)
    if ts is None:
        return

    if not ts.has_time_data:
        return

    t, y = ts.get_arrays()

    if baseline is not None:
        y_data = np.interp(sc.promotetoarray(t), series.tvec, baseline, left=np.nan, right=np.nan)
        y = y + y_data

    if filled:
        ax.scatter(t, y, marker="o", s=40, linewidths=1, facecolors=series.color, color="k")  # label='Data %s %s' % (name(pop,proj),name(output,proj)))
    else:
        ax.scatter(t, y, marker="o", s=40, linewidths=settings["marker_edge_width"], facecolors="none", color=series.color)  # label='Data %s %s' % (name(pop,proj),name(output,proj)))


def _apply_series_formatting(ax, plot_type) -> None:
    # This function applies formatting that is common to all Series plots
    # (irrespective of the 'axis' setting)
    ax.autoscale(enable=True, axis="x", tight=True)
    ax.set_xlabel("Year")
    ax.set_ylim(bottom=0)
    _turn_off_border(ax)
    if plot_type == "proportion":
        ax.set_ylim(top=1)
        ax.set_ylabel("Proportion " + ax.get_ylabel())
    else:
        ax.set_ylim(top=ax.get_ylim()[1] * 1.05)
    sc.SIticks(ax=ax, axis="y")


def _turn_off_border(ax) -> None:
    """
    Turns off top and right borders.

    Note that this function will leave the bottom and left borders on.

    :param ax: An axis object
    :return: None
    """
    ax.spines["right"].set_color("none")
    ax.spines["top"].set_color("none")
    ax.xaxis.set_ticks_position("bottom")
    ax.yaxis.set_ticks_position("left")


def plot_legend(entries: dict, plot_type=None, fig=None, legendsettings: dict = None):
    """
    Render a new legend

    :param entries: Dict where key is the label and value is the colour e.g. `{'sus':'blue','vac':'red'}`
    :param plot_type: Optionally specify 'patch', 'line', 'circle', or a list the same length as param_entries containing these values
    :param fig: Optionally takes in the figure to render the legend in. If not provided, a new figure will be created
    :param legendsettings: settings for the layout of the legend. If not provided will default to appropriate values depending on whether the legend is separate or together with a plot
    :return: The matplotlib `Figure` object containing the legend

    """

    if plot_type is None:
        plot_type = "line"

    plot_type = sc.promotetolist(plot_type)
    if len(plot_type) == 1:
        plot_type = plot_type * len(entries)
    assert len(plot_type) == len(entries), "If plot_type is a list, it must have the same number of values as there are entries in the legend (%s vs %s)" % (plot_type, entries)

    h = []
    for (label, color), p_type in zip(entries.items(), plot_type):
        if p_type == "patch":
            h.append(Patch(color=color, label=label))
        elif p_type == "line":
            h.append(Line2D([0], [0], linewidth=settings["line_width"], color=color, label=label))
        elif p_type == "circle":
            h.append(Line2D([0], [0], marker="o", linewidth=0, markeredgewidth=settings["marker_edge_width"], fillstyle="none", color=color, label=label))
        else:
            raise Exception(f'Unknown plot type "{p_type}"')

    if fig is None:  # Draw in a new figure
        fig = sc.separatelegend(handles=h, legendsettings=legendsettings)
    else:
        existing_legend = fig.findobj(Legend)
        if existing_legend and existing_legend[0].parent is fig:  # If existing legend and this is a separate legend fig
            existing_legend[0].remove()  # Delete the old legend
            if legendsettings is None:
                legendsettings = {"loc": "center", "bbox_to_anchor": None, "frameon": False}  # Settings for separate legend
            fig.legend(handles=h, **legendsettings)
        else:  # Drawing into an existing figure
            ax = fig.axes[0]
            if legendsettings is None:
                legendsettings = {"loc": "center left", "bbox_to_anchor": (1.05, 0.5), "ncol": 1}
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

    legendsettings = {"loc": "center left", "bbox_to_anchor": (1.05, 0.5), "ncol": 1, "framealpha": 0}
    #    labels = [textwrap.fill(label, 16) for label in labels]

    if plot_type in ["stacked", "proportion", "bar"]:
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
    assert len(legend._legend_handle_box._children) == 1, "Only single-column legends are supported"
    vpacker = legend._legend_handle_box._children[0]

    if order is None:
        return
    elif order == "reverse":
        order = range(len(legend.legendHandles) - 1, -1, -1)
    else:
        assert max(order) < len(vpacker._children), "Requested index greater than number of legend entries"

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
    assert len(legend._legend_handle_box._children) == 1, "Only single-column legends are supported"
    vpacker = legend._legend_handle_box._children[0]

    if isinstance(labels, list):
        assert len(labels) == len(vpacker._children), "If specifying list of labels, length must match number of legend entries"
        labels = {i: l for i, l in enumerate(labels)}
    elif isinstance(labels, dict):
        idx = labels.keys()
        assert max(idx) < len(vpacker._children), "Requested index greater than number of legend entries"
    else:
        raise Exception("Labels must be a list or a dict")

    for idx, label in labels.items():
        text = vpacker._children[idx]._children[1]._text
        text.set_text(label)


def _get_full_name(code_name: str, proj=None) -> str:
    """
    Return the label of an object retrieved by name

    If a :class:`Project` has been provided, code names can be converted into
    labels for plotting. This function is different to `framework.get_label()` though,
    because it supports converting population names to labels as well (this information is
    in the project's data, not in the framework), and it also supports converting
    link syntax (e.g. `sus:vac`) into full names as well. Note also that this means that the strings
    returned by `_get_full_name` can be as specific as necessary for plotting.

    :param code_name: The code name for a variable (e.g. `'sus'`, `'pris'`, `'sus:vac'`)
    :param proj: Optionally specify a :class:`Project` instance
    :return: If a project was provided, returns the full name. Otherwise, just returns the code name
    """

    if proj is None:
        return code_name

    if code_name in proj.data.pops:
        return proj.data.pops[code_name]["label"]  # Convert population

    if ":" in code_name:  # We are parsing a link
        # Handle Links specified with colon syntax
        output_tokens = code_name.split(":")
        if len(output_tokens) == 2:
            output_tokens.append("")
        src, dest, par = output_tokens

        # If 'par_name:flow' syntax was used
        if dest == "flow":
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

        full = "Flow"
        if src:
            full += " from {}".format(src)
        if dest:
            full += " to {}".format(dest)
        if par:
            full += " ({})".format(par)
        return full
    else:
        if code_name in proj.framework:
            return proj.framework.get_label(code_name)
        else:
            return code_name


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
            raise Exception("Unknown type")
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
            assert len(k) == 1, "Aggregation dict can only have one key"
            if sc.isstring(x[k[0]]):
                continue
            else:
                out += x[k[0]]
        else:
            out.append(x)
    return set(out)
