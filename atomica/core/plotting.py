# Imports

import itertools
import os
import textwrap
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

import sciris.core as sc
from .model import Compartment, Characteristic, Parameter, Link
from .results import Result
from .system import AtomicaException, NotFoundError, logger, NotAllowedError
from .parser_function import parse_function
from .interpolation import interpolate_func
from .structure import FrameworkSettings as FS
import scipy.interpolate
from six import string_types

settings = dict()
settings['legend_mode'] = 'together'  # Possible options are ['together','separate','none']
settings['bar_width'] = 1.0  # Width of bars in plot_bars()

def save_figs(figs, path='.', prefix='', fnames=None):
    # Take in array of figures, and save them to disk
    # Path and prefix are appended to the start
    # fnames - Optionally an array of file names. By default, each figure is named
    # using its 'label' property. If a figure has an empty 'label' string it is assumed to be
    # a legend and will be named based on the name of the figure immediately before it.
    # If you provide an empty string in the `fnames` argument this same operation will be carried
    # out. If the last figure name is omitted, an empty string will automatically be added. This allows
    # the separate-legend option to be turned on or off without changing the filename inputs to this function
    # (because the last legend figure may or may not be present depending on the legend mode)

    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno != os.errno.EEXIST:
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
    assert len(fnames) == len(figs), \
        "Number of figures must match number of specified filenames, or the last figure must be a legend with no label"
    assert fnames[0], 'The first figure name cannot be empty'

    for i, fig in enumerate(figs):
        if not fnames[i]:  # assert above means that i>0
            fnames[i] = fnames[i - 1] + '_legend'
        fname = prefix + fnames[i] + '.png'
        fig.savefig(os.path.join(path, fname), bbox_inches='tight')
        logger.info('Saved figure "%s"' % fname)


class PlotData(object):
    # This is what gets passed into a plotting function, which displays a View of the data
    # Conceptually, we are applying visuals to the data.
    # But we are performing an extraction step rather than doing it directly because things like
    # labels, colours, groupings etc. only apply to plots, not to results, and there could be several
    # different views of the same data.

    # TODO: Make sure to chuck a useful error when t_bins is greater than sim duration, rather than just crashing.
    def __init__(self, results, outputs=None, pops=None, output_aggregation='sum', pop_aggregation='sum', project=None,time_aggregation='sum', t_bins=None):
        # Construct a PlotData instance from model outputs
        #
        # final_outputs[result][pop][output] = vals
        # where the keys are the aggregated labels (if specified)
        # Aggregation computation is performed here
        # Input must be a list either containing a list of raw output labels or a dict with a single
        # key where the value is a list of raw output labels e.g.
        # outputs = ['vac',{'total':['vac','sus']}]
        #
        #
        # - results - which results to plot. Can be
        #               - a Result,
        #               - a list of Results,
        #               - a dict/odict of results (the name of the result is taken from the Result, not the dict)
        # - outputs - The name of an output compartment, characteristic, or
        #   parameter, or list of names. Inside a list, a dict can be given to
        #   specify an aggregation e.g. outputs=['sus',{'total':['sus','vac']}]
        #   where the key is the new name. Or, a formula can be given which will
        #   be evaluated by looking up labels within the model object. Links will
        #   automatically be summed over
        # - pops - The name of an output population, or list of names. Like
        #   outputs, can specify a dict with a list of pops to aggregate over them
        # - axis - Display one of results, outputs, or pops as different coloured
        #   lines on the plot. A new figure will be generated for all other
        #   combinations of the remaining quantities
        # - output_aggregation - If an output aggregation is requested, combine
        #   the outputs listed using one of
        #       - 'sum' - just add values together
        #       - 'average' - unweighted average of quantities
        #       - 'weighted' - weighted average where the weight is the
        #         compartment size, characteristic value, or link source
        #         compartment size (summed over duplicate links). 'weighted'
        #         method cannot be used with non-transition parameters and a
        #         KeyError will result in that case
        # - pop_aggregation - Same as output_aggregation, except that 'weighted'
        #   uses population sizes. Note that output aggregation is performed
        #   before population aggregation. This also means that population
        #   aggregation can be used to combine already aggregated outputs (e.g.
        #   can first sum 'sus'+'vac' within populations, and then take weighted
        #   average across populations)
        # - time_aggregation - Supported methods are 'sum' and 'average' (no weighting). When aggregating
        #   times, *non-annualized* flow rates will be used. 
        # - t_bins can be
        #       - A vector of bin edges. Time points are included if the time
        #         is >= the lower bin value and < upper bin value.
        #       - A scalar bin size (e.g. 5) which will be expanded to a vector spanning the data
        #       - The string 'all' will maps to bin edges [-inf inf] aggregating over all time

        # Validate inputs
        if isinstance(results, sc.odict):
            results = [result for _, result in results.items()]
        elif not isinstance(results, list):
            results = [results]


        result_names = [x.name for x in results]
        if len(set(result_names)) != len(result_names):
            raise AtomicaException('Results must have different names (in their result.name property)')

        if pops is None:
            pops = [pop.name for pop in results[0].model.pops]
        elif pops == 'all':
            pops = [{'All': [pop.name for pop in results[0].model.pops]}]
        elif not isinstance(pops, list):
            pops = [pops]

        if outputs is None:
            outputs = [comp.name for comp in results[0].model.pops[0].comps if
                       not (comp.tag_birth or comp.tag_dead or comp.is_junction)]
        elif not isinstance(outputs, list):
            outputs = [outputs]

        pops = expand_dict(pops)
        outputs = expand_dict(outputs)

        assert isinstance(results, list), 'Results should be specified as a Result, list, or odict'

        assert output_aggregation in ['sum', 'average', 'weighted']
        assert pop_aggregation in ['sum', 'average', 'weighted']
        assert time_aggregation in ['sum', 'average']

        # First, get all of the pops and outputs requested by flattening the lists
        pops_required = extract_labels(pops)
        outputs_required = extract_labels(outputs)

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
                        raise AtomicaException(
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
                        data_label[output_label] = vars[0].parameter.name if vars[0].parameter.units == FS.QUANTITY_TYPE_NUMBER else None # Only use parameter data points if the units match

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
                        raise AtomicaException('Unknown type')

                # Second pass, add in any dynamically computed quantities
                # Using model. Parameter objects will automatically sum over Links and convert Links
                # to annualized rates
                for l in outputs:
                    if not isinstance(l, dict):
                        continue

                    output_label, f_stack_str = list(l.items())[0]  # extract_labels has already ensured only one key is present

                    if not isinstance(f_stack_str, string_types):
                        continue

                    placeholder_pop = lambda: None
                    placeholder_pop.name = 'None'
                    par = Parameter(pop=placeholder_pop, name=output_label)
                    fcn, dep_labels = parse_function(f_stack_str)
                    deps = {}
                    displayed_annualization_warning = False
                    for dep_label in dep_labels:
                        vars = pop.get_variable(dep_label)
                        if t_bins is not None and (isinstance(vars[0], Link) or isinstance(vars[0], Parameter)) and time_aggregation == "sum" and not displayed_annualization_warning:
                            raise AtomicaException("Function includes Parameter/Link so annualized rates are being "
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
                        if isinstance(labels, string_types):
                            aggregated_outputs[pop_label][output_name] = data_dict[output_name]
                            aggregated_units[output_name] = 'unknown'  # Also, we don't know what the units of a function are
                            continue

                        units = list(set([output_units[x] for x in labels]))
                        if len(units) > 1:
                            logger.warning("Aggregation for output '{0}' is mixing units, this is almost certainly not desired.".format(output_name))
                            aggregated_units[output_name] = 'unknown'
                        else:
                            if units[0] in ['', 'fraction', 'proportion', 'probability'] and output_aggregation == 'sum' and len(labels) > 1:  # Dimensionless, like prevalance
                                logger.warning("Output '{0}' is not in number units, so output aggregation probably should not be 'sum'.".format(output_name))
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
                        if pop_aggregation == 'sum':
                            if aggregated_units[output_name] in ['', 'fraction', 'proportion', 'probability'] and len(pop_labels) > 1:
                                logger.warning("Output '{0}' is not in number units, so population aggregation probably should not be 'sum'".format(output_name))
                            vals = sum(aggregated_outputs[x][output_name] for x in pop_labels)  # Add together all the outputs
                        elif pop_aggregation == 'average':
                            vals = sum(aggregated_outputs[x][output_name] for x in pop_labels)  # Add together all the outputs
                            vals /= len(pop_labels)
                        elif pop_aggregation == 'weighted':
                            vals = sum(aggregated_outputs[x][output_name] * popsize[x] for x in pop_labels)  # Add together all the outputs
                            vals /= sum([popsize[x] for x in pop_labels])
                        else:
                            raise AtomicaException('Unknown pop aggregation method')
                        self.series.append(Series(tvecs[result_label], vals, result_label, pop_name, output_name,data_label[output_name], units=aggregated_units[output_name]))
                    else:
                        vals = aggregated_outputs[pop][output_name]
                        self.series.append(Series(tvecs[result_label], vals, result_label, pop, output_name, data_label[output_name],units=aggregated_units[output_name]))

        self.results = [x.name for x in
                        results]  # NB. These are lists that thus specify the order in which plotting takes place
        self.pops = [list(x.keys())[0] if isinstance(x, dict) else x for x in pops]
        self.outputs = [list(x.keys())[0] if isinstance(x, dict) else x for x in outputs]

        # Names will be substituted with these at the last minute when plotting for titles/legends
        self.result_names = {x: x for x in self.results}  # At least for now, no Result name mapping
        self.pop_names = {x: (get_full_name(x, project) if project is not None else x) for x in self.pops}
        self.output_names = {x: (get_full_name(x, project) if project is not None else x) for x in self.outputs}

        # Handle time aggregation
        if t_bins is not None:
            self._time_aggregate(t_bins,time_aggregation)

    def _time_aggregate(self, t_bins, time_aggregation):
        # This is an internal method used for time aggregation
        # It is called by __init__() to time-aggregate model outputs, and by
        # `.programs()` to time-aggregate spending values

        # If t_bins is a scalar, expand it into a vector of bin edges
        if not hasattr(t_bins, '__len__'):
            # TODO - here is where the code to handle t_bins > sim duration goes
            if not (self.series[0].tvec[-1] - self.series[0].tvec[0]) % t_bins:
                upper = self.series[0].tvec[-1] + t_bins
            else:
                upper = self.series[0].tvec[-1]
            t_bins = np.arange(self.series[0].tvec[0], upper, t_bins)

        if isinstance(t_bins, string_types) and t_bins == 'all':
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
                raise AtomicaException('Unknown time aggregation type')

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
            if isinstance(t_bins, string_types) and t_bins == 'all':
                s.t_labels = ['All']
            else:
                s.t_labels = ['%d-%d' % (l, h) for l, h in zip(lower, upper)]

    def __repr__(self):
        s = "PlotData\n"
        s += "Results: {0}\n".format(self.results)
        s += "Pops: {0}\n".format(self.pops)
        s += "Outputs: {0}\n".format(self.outputs)
        return s

    @staticmethod
    def programs(results,outputs=None,t_bins=None,quantity='spending'):
        # This constructs a PlotData instance from spending values
        #
        # INPUTS
        # - results - single Result, or list of Results. Technically could plot spending given just a progset and instructions, but
        #           passing in Results makes it parsimonious with the other plotting functions. This could be relaxed in future, where the 'Result'
        #           name is actually the name of a progset etc. but unless that's necessary, doing it this way is clearer and more consistent
        #           otherwise it's too easy to pass in the wrong combination of progset+instructions
        # - prognames - specification of which programs to plot spending for
        #     - the name of a single program
        #     - a list of program names
        #     - aggregation dict e.g. {'treatment':['tx-1','tx-2']} or list of such dicts. Output aggregation type is automatically 'sum' for
        #                              program spending, and NOT permitted for coverages (due to modality interactions)
        # - t_bins - aggregate over time, using summation for spending and number coverage, and average for fraction/proportion coverage
        # - quantity - can be 'spending', 'coverage_number', 'coverage_denominator', or 'coverage_fraction'. The 'coverage_denominator' is
        #              the sum of compartments reached by a program, such that coverage_fraction = coverage_number/coverage_denominator

        # Sanitize the results input
        if isinstance(results, sc.odict):
            results = [result for _, result in results.items()]
        elif isinstance(results, Result):
            results = [results]

        result_names = [x.name for x in results]
        if len(set(result_names)) != len(result_names):
            raise AtomicaException('Results must have different names (in their result.name property)')
        for result in results:
            if result.model.progset is None:
                raise AtomicaException('Tried to plot program spending for result "%s" that did not use programs', result.name)

        if outputs is None:
            outputs = results[0].model.progset.programs.keys()
        elif not isinstance(outputs, list):
            outputs = [outputs]

        outputs = expand_dict(outputs)
        progs_required = extract_labels(outputs)

        assert quantity in ['spending','coverage_number','coverage_denominator','coverage_fraction']
        # Make a new PlotData instance
        # We are using __new__ because this method is to be formally considered an alternate constructor and
        # thus bears responsibility for ensuring this new instance is initialized correctly
        plotdata = PlotData.__new__(PlotData)
        plotdata.series = []

        # Because aggregations always occur within a Result object, loop over results
        for result in results:

            alloc = result.model.progset.get_alloc(result.model.program_instructions, tvec=result.t)

            if quantity == 'spending':
                units = '$/year'
            elif quantity == 'coverage_number':
                num_covered = result.model.progset.get_num_covered(year=result.t, alloc=alloc) # program coverage based on unit cost and spending
                units = 'Number of people/year'
            elif quantity in ['coverage_fraction','coverage_denominator']:
                num_covered = result.model.progset.get_num_covered(year=result.t, alloc=alloc)  # program coverage based on unit cost and spending
                # Get the program coverage denominator
                prop_covered = dict()
                num_eligible = dict() # This is the coverage denominator, number of people covered by the program
                for prog in result.model.progset.programs.values(): # For each program
                    for pop_name in prog.target_pops:
                        for comp_name in prog.target_comps:
                            if prog.short not in num_eligible:
                                num_eligible[prog.short] = result.get_variable(pop_name,comp_name)[0].vals.copy()
                            else:
                                num_eligible[prog.short] += result.get_variable(pop_name,comp_name)[0].vals
                    prop_covered[prog.short] = np.minimum(num_covered[prog.short]/num_eligible[prog.short],np.ones(result.t.shape))
                if quantity == 'coverage_denominator':
                    units = 'Number of people'
                elif quantity == 'coverage_fraction':
                    units = 'Fraction covered/year'
            else:
                raise AtomicaException('Unknown quantity')

            for output in outputs:  # For each final output
                if isinstance(output, dict): # If this is an aggregation over programs
                    if quantity == 'spending':
                        output_name = list(output.keys())[0] # This is the aggregated name
                        labels = output[output_name] # These are the quantities being aggregated

                        # We only support summation for combining program spending, not averaging
                        # TODO - if/when we track which currency, then should check here that all of the programs have the same currency
                        vals = sum(alloc[x] for x in labels)*result.dt  # Add together all the outputs
                        output_name = output_name
                        data_label = None # No data present for aggregations
                    else:
                        raise NotAllowedError('Cannot use program aggregation for anything other than spending yet')
                else:
                    if quantity == 'spending':
                        vals = alloc[output]
                    elif quantity == 'coverage_number':
                        vals = num_covered[output]
                    elif quantity == 'coverage_fraction':
                        vals = prop_covered[output]
                    elif quantity == 'coverage_denominator':
                        vals = num_eligible[output]
                    else:
                        raise AtomicaException('Unknown quantity')
                    output_name = output
                    data_label = output # Can look up program spending by the program name

                if quantity in ['spending','coverage_number'] and t_bins is not None:
                    # If we are time-aggregating, then the annual quantities which are going to be summed need to be
                    # converted back to timestep values - for both spending and number coverage, this is simply multiplicative
                    vals *= result.dt
                    units = units.replace('/year','')

                # Accumulate the Series
                plotdata.series.append(Series(result.t, vals, result=result.name, pop=FS.DEFAULT_SYMBOL_INAPPLICABLE, output=output_name, data_label=data_label, units=units)) # The program should specify the units for its unit cost

        plotdata.results = [x.name for x in results]  # NB. These are lists that thus specify the order in which plotting takes place
        plotdata.pops = [FS.DEFAULT_SYMBOL_INAPPLICABLE]
        plotdata.outputs = [list(x.keys())[0] if isinstance(x, dict) else x for x in outputs]

        # Names will be substituted with these at the last minute when plotting for titles/legends
        plotdata.result_names = {x: x for x in plotdata.results}  # At least for now, no Result name mapping
        plotdata.pop_names = {FS.DEFAULT_SYMBOL_INAPPLICABLE:FS.DEFAULT_SYMBOL_INAPPLICABLE}
        plotdata.output_names = {x: (results[0].model.progset.programs[x].label if x in results[0].model.progset.programs else x) for x in plotdata.outputs}

        if t_bins is not None:
            if quantity in ['spending','coverage_number']:
                plotdata._time_aggregate(t_bins,'sum')
            elif quantity in ['coverage_denominator','coverage_fraction']:
                plotdata._time_aggregate(t_bins,'average')
            else:
                raise AtomicaException('Unknown quantity')

        return plotdata

    def tvals(self):
        # Return a vector of time values for the PlotData object, if all of the series have the
        # same time axis (otherwise throw an error)
        # All series must have the same number of timepoints.
        assert len(set([len(x.tvec) for x in self.series])) == 1, "All series must have the same number of time points."
        tvec = self.series[0].tvec
        t_labels = self.series[0].t_labels
        for i in range(1, len(self.series)):
            assert (all(np.equal(self.series[i].tvec, tvec))), 'All series must have the same time points'
        return tvec, t_labels

    def interpolate(self,t2):
        # This will interpolate all Series onto a new time axis
        # Note that NaNs will be set anywhere that extrapolation is needed
        t2 = sc.promotetoarray(t2)
        for series in self.series:
            series.vals = series.interpolate(t2)
            series.tvec = np.copy(t2)
            series.t_labels = np.copy(t2)

    def __getitem__(self, key):
        # key is a tuple of (result,pop,output)
        # retrive a single Series e.g. plotdata['default','0-4','sus']
        for s in self.series:
            if s.result == key[0] and s.pop == key[1] and s.output == key[2]:
                return s
        raise AtomicaException('Series %s-%s-%s not found' % (key[0], key[1], key[2]))

    def set_colors(self, colors=None, results='all', pops='all', outputs='all', overwrite=False):
        # What are the different ways we might want to set colours?
        # - Assign a set of colours to results/pops/outputs to distinguish on a line plot
        # - Assign a colour scheme to a bunch of outputs
        #
        # There are two usage scenarios
        # - Colour filling, where we want to assign colours to a number of outputs
        # What if we want to assign *across* pops? Then, we need something a bit more 
        # sophisticated
        #
        # set_colors() - Assign a colour to every output
        # set_colors(outputs=[a,b,c]) - Assign a colour to every output of type a,b,c irrespective of pop
        # set_colors(pops=[a,b,c]) - Assign a colour to each pop irrespective of result/output
        # What if we want to assign a particular one?
        # 
        # Or keep the others fixed? 
        #
        # - Specific colour assignment
        # 
        # colors can be
        # - None, in which case colours will automatically be added
        # - a colour string that will be applied to filtered things
        #
        # Then results, pop, outputs corresponds to a series filter

        # Usage scenarios
        # - Colours are shared across any dimensions that are 'None'
        # - So for instance, 'output=[a,b,c]' would give the same colour to all of those outputs,
        # across all results and pops
        # - If multiple ones are specified, combinations get the unique colours
        # - At least one of them must not be none
        # - It is a bad idea to manually set colors for more than one dimension because the order is unclear!

        results = [results] if not isinstance(results, list) else results
        pops = [pops] if not isinstance(pops, list) else pops
        outputs = [outputs] if not isinstance(outputs, list) else outputs

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


class Series(object):
    def __init__(self, tvec, vals, result='default', pop='default', output='default', data_label='', color=None,units=''):
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
            logger.warning('%s contains NaNs' % (self))

    def __repr__(self):
        return 'Series(%s,%s,%s)' % (self.result, self.pop, self.output)

    def interpolate(self,t2):
        # Return an np.array() with the values of this series interpolated onto the requested
        # time array t2. To ensure results are not misleading, extrapolation is disabled
        # and will return NaN if t2 contains values outside the original time range
        f = scipy.interpolate.PchipInterpolator(self.tvec, self.vals, axis=0, extrapolate=False)
        out_of_bounds = (t2 < self.tvec[0]) | (t2 > self.tvec[-1])
        if np.any(out_of_bounds):
            logger.warning('Series has values from %.2f to %.2f so requested time points %s are out of bounds',self.tvec[0],self.tvec[-1],t2[out_of_bounds])
        return f(sc.promotetoarray(t2))

def plot_bars(plotdata, stack_pops=None, stack_outputs=None, outer='times'):
    # We have a collection of bars - one for each Result, Pop, Output, and Timepoint.
    # Any aggregations have already been done. But _groupings_ have not. Let's say that we can group
    # pops and outputs but we never want to stack results. At least for now. 
    # But, the quantities could still vary over time. So we will have
    # - A set of arrays where the number of arrays is the number of things being stacked and
    #   the number of values is the number of bars - could be time, or could be results?
    # - As many sets as there are ungrouped bars
    # xlabels refers to labels within a block (i.e. they will be repeated for multiple times and results)
    global settings

    assert outer in ['times', 'results'], 'Supported outer groups are "times" or "results"'

    plotdata = sc.dcp(plotdata)

    # Note - all of the tvecs must be the same
    tvals, t_labels = plotdata.tvals()  # We have to iterate over these, with offsets, if there is more than one

    # If quantities are stacked, then they need to be coloured differently.
    if stack_pops is None:
        color_by = 'outputs'
        plotdata.set_colors(outputs=plotdata.outputs)
    elif stack_outputs is None:
        color_by = 'pops'
        plotdata.set_colors(pops=plotdata.pops)
    else:
        color_by = 'both'
        plotdata.set_colors(pops=plotdata.pops, outputs=plotdata.outputs)

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
                elif isinstance(x, string_types):
                    output_stacks.append((x, '', [x]))
                    items.add(x)
                else:
                    raise AtomicaException('Unsupported input')

        elif isinstance(input_stacks, dict):
            for k, x in input_stacks.items():
                if isinstance(x, list):
                    output_stacks.append(('', k, x) if len(x) > 1 else (x[0], k, x))
                    items.update(x)
                elif isinstance(x, string_types):
                    output_stacks.append((x, k, [x]))
                    items.add(x)
                else:
                    raise AtomicaException('Unsupported input')

        # Add missing items
        missing = list(set(available_items) - items)
        output_stacks += [(x, '', [x]) for x in missing]
        return output_stacks

    pop_stacks = process_input_stacks(stack_pops, plotdata.pops)
    output_stacks = process_input_stacks(stack_outputs, plotdata.outputs)

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
        iterator = nested_loop([range(len(plotdata.results)), range(len(tvals))], [0, 1])
    elif outer == 'results':
        if len(tvals) == 1:  # If there is only one inner group
            gaps[2] = gaps[1]
            gaps[1] = 0
        result_offset = len(tvals) * (block_width + gaps[1]) + gaps[2]
        tval_offset = block_width + gaps[1]
        iterator = nested_loop([range(len(plotdata.results)), range(len(tvals))], [1, 0])
    else:
        raise AtomicaException('outer option must be either "times" or "results"')

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

    # Iterate over the inner and outer groups, rendering blocks at a time
    for r_idx, t_idx in iterator:
        base_offset = r_idx * result_offset + t_idx * tval_offset  # Offset between outer groups
        block_offset = 0.0  # Offset between inner groups

        if outer == 'results':
            inner_labels.append((base_offset + block_width / 2.0, t_labels[t_idx]))
        elif outer == 'times':
            inner_labels.append((base_offset + block_width / 2.0, plotdata.result_names[plotdata.results[r_idx]]))

        for idx, bar_pop, bar_output in zip(range(len(bar_pops)), bar_pops, bar_outputs):
            # pop is something like ['0-4','5-14'] or ['0-4']
            # output is something like ['sus','vac'] or ['0-4'] depending on the stack
            y0 = 0

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
                    rectangles[series.color].append(Rectangle((base_offset + block_offset, y0), width, y))
                    if series.color in color_legend and (pop, output) not in color_legend[series.color]:
                        color_legend[series.color].append((pop, output))
                    elif series.color not in color_legend:
                        color_legend[series.color] = [(pop, output)]
                    y0 += y

            block_labels.append((base_offset + block_offset + width / 2, bar_label))

            block_offset += width + gaps[0]

    # Add the patches to the figure and assemble the legend patches
    legend_patches = []

    for color, items in color_legend.items():
        pc = PatchCollection(rectangles[color], facecolor=color, edgecolor='none')
        ax.add_collection(pc)
        pops = set([x[0] for x in items])
        outputs = set([x[1] for x in items])

        if pops == set(plotdata.pops) and len(outputs) == 1:  # If the same color is used for all pops and always the same output
            label = plotdata.output_names[items[0][1]]  # Use the output name
        elif outputs == set(plotdata.outputs) and len(pops) == 1:  # Same color for all outputs and always same pop
            label = plotdata.pop_names[items[0][0]]  # Use the pop name
        else:
            label = ''
            for x in items:
                label += '%s-%s,\n' % (plotdata.pop_names[x[0]], plotdata.output_names[x[1]])
            label = label.strip()[:-1]  # Replace trailing newline and comma
        legend_patches.append(Patch(facecolor=color, label=label))

    # Set axes now, because we need block_offset and base_offset after the loop
    ax.autoscale()
    ax.set_xlim(xmin=-2 * gaps[0], xmax=block_offset + base_offset)
    fig.set_figwidth(1.75 * (block_offset + base_offset))
    ax.set_ylim(ymin=0)
    _turn_off_border(ax)
    set_ytick_format(ax, "km")
    block_labels = sorted(block_labels, key=lambda x: x[0])
    ax.set_xticks([x[0] for x in block_labels])
    ax.set_xticklabels([x[1] for x in block_labels])

    # Calculate the units. As all bar patches are shown on the same axis, they are all expected to have the
    # same units. If they do not, the plot could be misleading
    units = list(set([x.units for x in plotdata.series]))
    if len(units) == 1:
        ax.set_ylabel(units[0])
    else:
        logger.warning('Warning - bar plot quantities mix units, double check that output selection is correct')

    # Outer group labels are only displayed if there is more than one group
    if outer == 'times' and len(tvals) > 1:
        offset = 0.0
        for t in t_labels:
            ax.text(offset + (tval_offset - gaps[1] - gaps[2]) / 2, 1, t, transform=ax.get_xaxis_transform(),
                    verticalalignment='bottom', horizontalalignment='center')
            offset += tval_offset
    elif outer == 'results' and len(plotdata.results) > 1:
        offset = 0.0
        for r in plotdata.results:
            ax.text(offset + (result_offset - gaps[1] - gaps[2]) / 2, 1, plotdata.result_names[r],
                    transform=ax.get_xaxis_transform(), verticalalignment='bottom', horizontalalignment='center')
            offset += result_offset

    # If there is only one block per inner group, then use the inner group string as the bar label
    if not any([x[1] for x in block_labels]) and len(block_labels) == len(inner_labels) and len(set([x for _, x in inner_labels])) > 1:
        ax.set_xticks([x[0] for x in inner_labels])
        ax.set_xticklabels([x[1] for x in inner_labels])
    elif len(inner_labels) > 1 and len(set([x for _, x in inner_labels])) > 1:  # Inner group labels are only displayed if there is more than one label
        ax2 = ax.twiny()  # instantiate a second axes that shares the same x-axis
        ax2.set_xticks([x[0] for x in inner_labels])
        ax2.set_xticklabels(['\n\n' + str(x[1]) for x in inner_labels])
        ax2.xaxis.set_ticks_position('bottom')
        ax2.set_xlim(ax.get_xlim())
        ax2.spines['right'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        ax2.spines['bottom'].set_visible(False)
        ax2.tick_params(axis=u'both', which=u'both', length=0)

    # Do the legend last, so repositioning the axes works properly
    if settings['legend_mode'] == 'separate':
        figs.append(render_separate_legend(ax, plot_type='bar', handles=legend_patches))
    elif settings['legend_mode'] == 'together':
        render_legend(ax, plot_type='bar', handles=legend_patches)

    return figs


def plot_series(plotdata, plot_type='line', axis=None, data=None, legend_mode=None):
    # This function plots a time series for a model output quantities
    #
    # INPUTS
    # - plotdata - a PlotData instance to plot
    # - plot_type - 'line', 'stacked', or 'proportion' (stacked, normalized to 1)
    # - data - Draw scatter points for data wherever the output label matches
    #   a data label. Only draws data if the plot_type is 'line'

    global settings
    if legend_mode is not None: 
        settings['legend_mode'] = legend_mode
    
    if axis is None: axis = 'outputs'

    assert axis in ['outputs', 'results', 'pops']

    figs = []
    ax = None

    plotdata = sc.dcp(plotdata)

    if axis == 'results':
        plotdata.set_colors(results=plotdata.results)

        for pop in plotdata.pops:
            for output in plotdata.outputs:
                fig, ax = plt.subplots()
                fig.set_label('%s_%s' % (pop, output))
                figs.append(fig)

                units = list(set([plotdata[result, pop, output].units for result in plotdata.results]))
                if len(units) == 1 and units[0]:
                    ax.set_ylabel('%s (%s)' % (plotdata.output_names[output], units[0]))
                else:
                    ax.set_ylabel('%s' % (plotdata.output_names[output]))

                if plotdata.pop_names[pop] != FS.DEFAULT_SYMBOL_INAPPLICABLE:
                    ax.set_title('%s' % (plotdata.pop_names[pop]))

                if plot_type in ['stacked', 'proportion']:
                    y = np.stack([plotdata[result, pop, output].vals for result in plotdata.results])
                    y = y / np.sum(y, axis=0) if plot_type == 'proportion' else y
                    ax.stackplot(plotdata[plotdata.results[0], pop, output].tvec, y,
                                 labels=[plotdata.result_names[x] for x in plotdata.results],
                                 colors=[plotdata[result, pop, output].color for result in plotdata.results])
                    if plot_type == 'stacked' and data is not None:
                        stack_data(ax, data, [plotdata[result, pop, output] for result in plotdata.results])
                else:
                    for i,result in enumerate(plotdata.results):
                        ax.plot(plotdata[result, pop, output].tvec, plotdata[result, pop, output].vals,
                                color=plotdata[result, pop, output].color, label=plotdata.result_names[result])
                        if data is not None and i == 0:
                            render_data(ax, data, plotdata[result, pop, output])
                apply_series_formatting(ax, plot_type)
                if settings['legend_mode'] == 'together':
                    render_legend(ax, plot_type)

    elif axis == 'pops':
        plotdata.set_colors(pops=plotdata.pops)

        for result in plotdata.results:
            for output in plotdata.outputs:
                fig, ax = plt.subplots()
                fig.set_label('%s_%s' % (result, output))
                figs.append(fig)

                units = list(set([plotdata[result, pop, output].units for pop in plotdata.pops]))
                if len(units) == 1 and units[0]:
                    ax.set_ylabel('%s (%s)' % (plotdata.output_names[output], units[0]))
                else:
                    ax.set_ylabel('%s' % (plotdata.output_names[output]))

                ax.set_title('%s' % (plotdata.result_names[result]))
                if plot_type in ['stacked', 'proportion']:
                    y = np.stack([plotdata[result, pop, output].vals for pop in plotdata.pops])
                    y = y / np.sum(y, axis=0) if plot_type == 'proportion' else y
                    ax.stackplot(plotdata[result, plotdata.pops[0], output].tvec, y,
                                 labels=[plotdata.pop_names[x] for x in plotdata.pops],
                                 colors=[plotdata[result, pop, output].color for pop in plotdata.pops])
                    if plot_type == 'stacked' and data is not None:
                        stack_data(ax, data, [plotdata[result, pop, output] for pop in plotdata.pops])
                else:
                    for pop in plotdata.pops:
                        ax.plot(plotdata[result, pop, output].tvec, plotdata[result, pop, output].vals,
                                color=plotdata[result, pop, output].color, label=plotdata.pop_names[pop])
                        if data is not None:
                            render_data(ax, data, plotdata[result, pop, output])
                apply_series_formatting(ax, plot_type)
                if settings['legend_mode'] == 'together':
                    render_legend(ax, plot_type)

    elif axis == 'outputs':
        plotdata.set_colors(outputs=plotdata.outputs)

        for result in plotdata.results:
            for pop in plotdata.pops:
                fig, ax = plt.subplots()
                fig.set_label('%s_%s' % (result, pop))
                figs.append(fig)

                units = list(set([plotdata[result, pop, output].units for output in plotdata.outputs]))
                if len(units) == 1 and units[0]:
                    ax.set_ylabel(units[0])

                if plotdata.pop_names[pop] != FS.DEFAULT_SYMBOL_INAPPLICABLE:
                    ax.set_title('%s-%s' % (plotdata.result_names[result], plotdata.pop_names[pop]))
                else:
                    ax.set_title('%s' % (plotdata.result_names[result]))

                if plot_type in ['stacked', 'proportion']:
                    y = np.stack([plotdata[result, pop, output].vals for output in plotdata.outputs])
                    y = y / np.sum(y, axis=0) if plot_type == 'proportion' else y
                    ax.stackplot(plotdata[result, pop, plotdata.outputs[0]].tvec, y,
                                 labels=[plotdata.output_names[x] for x in plotdata.outputs],
                                 colors=[plotdata[result, pop, output].color for output in plotdata.outputs])
                    if plot_type == 'stacked' and data is not None:
                        stack_data(ax,data,[plotdata[result, pop, output] for output in plotdata.outputs])
                else:
                    for output in plotdata.outputs:
                        ax.plot(plotdata[result, pop, output].tvec, plotdata[result, pop, output].vals,
                                color=plotdata[result, pop, output].color, label=plotdata.output_names[output])
                        if data is not None:
                            render_data(ax, data, plotdata[result, pop, output])
                apply_series_formatting(ax, plot_type)
                if settings['legend_mode'] == 'together':
                    render_legend(ax, plot_type)
    else:
        raise AtomicaException('axis option must be one of "results", "pops" or "outputs"')

    if settings['legend_mode'] == 'separate':
        figs.append(render_separate_legend(ax, plot_type))

    return figs

def stack_data(ax,data,series):
    # Stack a list of series in order
    baselines = np.cumsum(np.stack([s.vals for s in series]),axis=0)
    baselines = np.vstack([np.zeros((1,baselines.shape[1])),baselines]) # Insert row of zeros for first data row
    for i,s in enumerate(series):
        render_data(ax,data,s,baselines[i,:],True)
            
def render_data(ax, data, series,baseline=None,filled=False):
    # This function renders a scatter plot for a single variable in a single population
    #
    # INPUTS
    # ax - axis object that data will be rendered in
    # data - a ProjectData instance containing the data to render
    # series - a Series object, the 'pop' and 'data_label' attributes are used to extract the TimeSeries from the data
    # baseline - adds an offset to the data e.g. for stacked plots
    # filled - fill the marker with a solid fill e.g. for stacked plots

    ts = data.get_ts(series.data_label,series.pop)
    if ts is None:
        return

    if not ts.has_time_data:
        return

    t, y = ts.get_arrays()

    if baseline is not None:
        y_data = interpolate_func(series.tvec, baseline, t, method='pchip', extrapolate_nan=False)
        y = y + y_data

    if filled:
        ax.scatter(t,y,marker='o', s=40, linewidths=1, facecolors=series.color,color='k')#label='Data %s %s' % (name(pop,proj),name(output,proj)))
    else:
        ax.scatter(t,y,marker='o', s=40, linewidths=3, facecolors='none',color=series.color)#label='Data %s %s' % (name(pop,proj),name(output,proj)))


def set_ytick_format(ax, formatter):
    def km(x, pos):
        # 
        if x >= 1e6:
            return '%1.1fM' % (x * 1e-6)
        elif x >= 1e3:
            return '%1.1fK' % (x * 1e-3)
        else:
            return '%g' % x

    def percent(x, pos):
        return '%g%%' % (x * 100)

    fcn = locals()[formatter]
    ax.yaxis.set_major_formatter(FuncFormatter(fcn))


def apply_series_formatting(ax, plot_type):
    # This function applies formatting that is common to all Series plots
    # (irrespective of the 'axis' setting)
    ax.autoscale(enable=True, axis='x', tight=True)
    ax.set_xlabel('Year')
    ax.set_ylim(ymin=0)
    _turn_off_border(ax)
    if plot_type == 'proportion':
        ax.set_ylim(ymax=1)
        ax.set_ylabel('Proportion ' + ax.get_ylabel())
    else:
        ax.set_ylim(ymax=ax.get_ylim()[1] * 1.05)

    set_ytick_format(ax, "km")


def _turn_off_border(ax):
    """
    Turns off top and right borders, leaving only bottom and left borders on.
    """
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')


def plot_legend(entries, plot_type='patch', fig=None):
    # plot type - can be 'patch' or 'line'
    # The legend items are a dict keyed with the label e.g.
    # entries = {'sus':'blue','vac':'red'}
    # If a figure is passed in, the legend will be drawn in that figure, overwriting
    # a previous legend if one was already there

    h = []
    for label, color in entries.items():
        if plot_type == 'patch':
            h.append(Patch(color=color, label=label))
        else:
            h.append(Line2D([0], [0], color=color, label=label))

    legendsettings = {'loc': 'center', 'bbox_to_anchor': None, 'frameon': False}  # Settings for separate legend

    if fig is None:  # Draw in a new figure
        render_separate_legend(None, None, h)
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


def render_separate_legend(ax, plot_type=None, handles=None):
    if handles is None:
        handles, labels = ax.get_legend_handles_labels()
    else:
        labels = [h.get_label() for h in handles]

    fig, ax = plt.subplots()
    ax.set_position([0.5, 0.5, 0.01, 0.01])
    ax.set_axis_off()  # This allows the figure to be shown in jupyter notebook

    legendsettings = {'loc': 'center', 'bbox_to_anchor': None, 'frameon': False}

    # A legend renders the line/patch based on the object handle. However, an object
    # can only appear in one figure. Thus, if the legend is in a different figure, the
    # object cannot be shown in both the original figure and in the legend. Thus we need
    # to copy the handles, and use the copies to render the legend
    from copy import copy
    handles = [copy(x) for x in handles]

    # Stop the figures from being rendered in the original figure, which will allow them to
    # then be rendered in the legend figure
    for h in handles:
        h.figure = None

    if plot_type in ['stacked', 'proportion', 'bar']:
        fig.legend(handles=handles[::-1], labels=labels[::-1], **legendsettings)
    else:
        fig.legend(handles=handles, labels=labels, **legendsettings)

    return fig


def render_legend(ax, plot_type=None, handles=None, ):
    # This function renders a legend
    # INPUTS
    # - plot_type - Used to decide whether to reverse the legend order for stackplots
    if handles is None:
        handles, labels = ax.get_legend_handles_labels()
    else:
        labels = [h.get_label() for h in handles]

    legendsettings = {'loc': 'center left', 'bbox_to_anchor': (1.05, 0.5), 'ncol': 1}
    labels = [textwrap.fill(label, 16) for label in labels]

    if plot_type in ['stacked', 'proportion', 'bar']:
        ax.legend(handles=handles[::-1], labels=labels[::-1], **legendsettings)
    else:
        ax.legend(handles=handles, labels=labels, **legendsettings)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])


def reorder_legend(figs, order=None):
    # This helper function lets you reorder a legend after figure creation
    # Order can be
    # - A string 'reverse' to reverse the order of the legend
    # - A list of indices mapping old position to new position. For example, if the
    #   original label order was ['a,'b','c'], then order=[1,0,2] would result in ['b','a','c']

    if isinstance(figs, list):
        if not figs[-1].get_label():  # If the last figure is a legend figure
            fig = figs[-1]
        else:
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


def relabel_legend(figs, labels):
    if isinstance(figs, list):
        if not figs[-1].get_label():  # If the last figure is a legend figure
            fig = figs[-1]
        else:
            for fig in figs:  # Apply order operation to all figures passed in
                relabel_legend(fig, labels=labels)
            return
    else:
        fig = figs

    legend = fig.findobj(Legend)[0]
    assert len(legend._legend_handle_box._children) == 1, 'Only single-column legends are supported'
    vpacker = legend._legend_handle_box._children[0]

    if isinstance(labels, list):
        assert len(labels) == len(
            vpacker._children), 'If specifying list of labels, length must match number of legend entries'
        labels = {i: l for i, l in enumerate(labels)}
    elif isinstance(labels, dict):
        idx = labels.keys()
        assert max(idx) < len(vpacker._children), 'Requested index greater than number of legend entries'
    else:
        raise AtomicaException('Labels must be a list or a dict')

    for idx, label in labels.items():
        text = vpacker._children[idx]._children[1]._text
        text.set_text(label)


def get_full_name(output_id, proj):
    """
    For a given output_id, returns the user-friendly version of the name. 
    """

    # Note that an output_id could be a Compartment, Characteristic, Parameter, Population, or Link Expression
    if proj is None:
        return output_id

    if output_id in proj.data.pops:
        return proj.data.pops[output_id]['label'] # Convert population

    full_name = lambda x: proj.framework.get_variable(x)[0]['display name']

    if ':' in output_id: # We are parsing a link
        # Handle Links specified with colon syntax
        output_tokens = output_id.split(':')
        if len(output_tokens) == 2:
            output_tokens.append('')
        src, dest, par = output_tokens

        # If 'par_name:flow' syntax was used
        if dest == 'flow':
            if src in proj.framework:
                return "{0} (flow)".format(full_name(src))
            else:
                return "{0} (flow)".format(src)

        if src and src in proj.framework:
            src = full_name(src)

        if dest and dest in proj.framework:
            dest = full_name(dest)

        if par and par in proj.framework:
            par = full_name(par)

        full = 'Flow'
        if src:
            full += ' from {}'.format(src)
        if dest:
            full += ' to {}'.format(dest)
        if par:
            full += ' ({})'.format(par)
        return full
    else:
        if output_id in proj.framework:
            return full_name(output_id)
        else:
            return output_id


def nested_loop(inputs, loop_order):
    # Take in a list of lists to iterate over, and their nesting order
    # Return items in the order of the original lists
    # e.g
    # inputs = [['a','b','c'],[1,2,3]]
    # for l,n in nested_loop([['a','b','c'],[1,2,3]],[0,1]):
    # This would yield in order (a,1),(a,2),(a,3),(b,1)...
    # but if loop_order = [1,0], then it would be (a,1),(b,1),(c,1),(a,2)...
    inputs = [inputs[i] for i in loop_order]
    iterator = itertools.product(*inputs)  # This is in the loop order
    for item in iterator:
        out = [None] * len(loop_order)
        for i in range(len(item)):
            out[loop_order[i]] = item[i]
        yield out

def expand_dict(x):
    # If a list contains a dict with multiple keys, expand it into multiple dicts each
    # with a single key
    y = list()
    for v in x:
        if isinstance(v, dict):
            y += [{a: b} for a, b in v.items()]
        else:
            y.append(v)
    return y


def extract_labels(input_arrays):
    # Flatten the input arrays to extract all requested pops and outputs
    # e.g. ['vac',{'a':['vac','sus']}] -> ['vac','vac','sus'] -> set(['vac','sus'])
    # This is because the workflow for aggregation is
    #   1 - retrieve all quantities required
    #   2 - perform all aggregations

    out = []
    for x in input_arrays:
        if isinstance(x, dict):
            k = list(x.keys())
            assert len(k) == 1, 'Aggregation dict can only have one key'
            if isinstance(x[k[0]], string_types):
                continue
            else:
                out += x[k[0]]
        else:
            out.append(x)
    return set(out)