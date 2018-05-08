# %% Imports
import logging
logger = logging.getLogger(__name__)

import numpy as np
import pylab as pl
from random import shuffle
import numbers
import os
import itertools
import textwrap

from collections import defaultdict

from copy import deepcopy as dcp

from sciris.utils import odict

from atomica.system import AtomicaException
from atomica.results import Result
from atomica.model import Compartment, Characteristic, Parameter, Link
from atomica.parser_function import FunctionParser

import matplotlib
from matplotlib.pyplot import plot
import matplotlib.cm as cmx
import matplotlib.colors as matplotlib_colors
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Rectangle, Patch
from matplotlib.collections import PatchCollection
from matplotlib.legend import Legend
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

parser = FunctionParser(debug=False)  # Decomposes and evaluates functions written as strings, in accordance with a grammar defined within the parser object.

settings = dict()
settings['legend_mode'] = 'together' # Possible options are ['together','separate','none'] 
settings['bar_width'] = 1.0 # Width of bars in plotBars()

def save_figs(figs,path = '.',prefix = '',fnames=None):
    #
    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno!=os.errno.EEXIST:
            raise

    if not isinstance(figs,list):
        figs = [figs]

    if fnames is not None:
        if not isinstance(fnames,list):
            fnames = [fnames]
        if len(fnames) == len(figs)-1 and not figs[-1].get_label():
            fnames.append('')
        else:
            assert len(fnames) == len(figs), 'Number of figures must match number of specified filenames, or the last figure must be a legend with no label'

    for i,fig in enumerate(figs):
        if fnames is not None and fnames[i]: # Use the specified filename
            fname = prefix+fnames[i] + '.png'
        else:
            if not fig.get_label() and i == len(figs)-1: # If the figure has no label (e.g. it is a legend)
                fname = fname[0:-4] + '_legend.png'
            elif not fig.get_label():
                raise AtomicaException('Only the last figure passed to save_figs is allowed to have an empty label if the filenames are not explicitly specified')
            else:
                fname = prefix+fig.get_label() + '.png'
        fig.savefig(os.path.join(path,fname),bbox_inches='tight')
        logger.info('Saved figure "%s"' % fname)


class PlotData(object):
    # This is what gets passed into a plotting function, which displays a View of the data
    # Conceptually, we are applying visuals to the data.
    # But we are performing an extraction step rather than doing it directly because things like
    # labels, colours, groupings etc. only apply to plots, not to results, and there could be several
    # different views of the same data.

    # TODO: Make sure to chuck a useful error when t_bins is greater than sim duration, rather than just crashing.
    def __init__(self,results,outputs=None,pops=None,output_aggregation='sum',pop_aggregation='sum',project=None,time_aggregation='sum',t_bins=None):
        # Construct a PlotData instance from a Results object by selecting data and optionally
        # specifying desired aggregations
        #
        # final_outputs[result][pop][output] = vals
        # where the keys are the aggregated labels (if specified)
        # Aggregation computation is performed here
        # Input must be a list either containing a list of raw output labels or a dict with a single
        # key where the value is a list of raw output labels e.g.
        # outputs = ['vac',{'total':['vac','sus']}]
        #
        #
        # - results - A Result or a dict of Results with key corresponding
        #   to name
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
        if isinstance(results,odict):
            results = [result for _,result in results.items()]
        elif isinstance(results,Result):
            results = [results]

        result_names = [x.name for x in results]
        if len(set(result_names)) != len(result_names):
            raise AtomicaException('Results must have different names (in their result.name property)')

        if pops is None:
            pops = [pop.name for pop in results[0].model.pops]
        elif pops == 'all':
            pops = [{'All':[pop.name for pop in results[0].model.pops]}]
        elif not isinstance(pops,list):
            pops = [pops]

        if outputs is None:
            outputs = [comp.name for comp in results[0].model.pops[0].comps if not (comp.tag_birth or comp.tag_dead or comp.is_junction)]
        elif not isinstance(outputs,list):
            outputs = [outputs]

        def expand_dict(x):
            # If a list contains a dict with multiple keys, expand it into multiple dicts each
            # with a single key
            y = list()
            for v in x:
                if isinstance(v,dict):
                    y += [{a:b} for a,b in v.items()]
                else:
                    y.append(v)
            return y

        pops = expand_dict(pops)
        outputs = expand_dict(outputs)

        assert isinstance(results,list), 'Results should be specified as a Result, list, or odict'

        assert output_aggregation in ['sum','average','weighted']
        assert pop_aggregation in ['sum','average','weighted']
        assert time_aggregation in ['sum','average']

        def extract_labels(l):
            # Flatten the input arrays to extract all requested pops and outputs
            # e.g. ['vac',{'a':['vac','sus']}] -> ['vac','vac','sus'] -> set(['vac','sus'])
            # Also returns the labels for legends etc. i.e. ['vac','a']
            out = []
            for x in l:
                if isinstance(x,dict):
                    k = list(x.keys())
                    assert len(k) == 1, 'Aggregation dict can only have one key'
                    if isinstance(x[k[0]],str):
                        continue
                    else:
                        out += x[k[0]]
                else:
                    out.append(x)
            return set(out)

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

            aggregated_outputs = defaultdict(dict) # Dict with aggregated_outputs[pop_label][aggregated_output_label]
            aggregated_units = dict() # Dict with aggregated_units[aggregated_output_label]
            output_units = dict()
            compsize = dict()
            popsize = dict()
            data_label = defaultdict(str) # Label used to identify which data to plot, maps output label to data label. Defaultdict won't throw key error when checking outputs

            # Aggregation over outputs takes place first, so loop over pops
            for pop_label in pops_required:
                pop = result.model.get_pop(pop_label)
                popsize[pop_label] = pop.popsize()
                data_dict = dict()  # Temporary storage for raw outputs

                # First pass, extract the original output quantities, summing links and annualizing as required
                for output_label in outputs_required:
                    vars = pop.get_variable(output_label)

                    if vars[0].vals is None:
                        raise AtomicaException('Requested output "%s" was not recorded because only partial results were saved' % (vars[0].name))

                    if isinstance(vars[0],Link):
                        data_dict[output_label] = np.zeros(tvecs[result_label].shape)
                        compsize[output_label] = np.zeros(tvecs[result_label].shape)
                        
                        for link in vars:
                            data_dict[output_label] += link.vals
                            compsize[output_label] += (link.source.vals if not link.source.is_junction else link.source.outflow)

                        if t_bins is None: # Annualize if not time aggregating
                            data_dict[output_label] /= dt
                            output_units[output_label] = link.units + '/year'
                        else:    
                            output_units[output_label] = link.units # If we sum links in a bin, we get a number of people
                        data_label[output_label] = vars[0].parameter.name

                    elif isinstance(vars[0],Parameter):
                        data_dict[output_label] = vars[0].vals
                        output_units[output_label] = vars[0].units
                        data_label[output_label] = vars[0].name

                        # If there are links, we can retrieve a compsize for the user to do a weighted average
                        if vars[0].links:
                            output_units[output_label] = vars[0].units
                            compsize[output_label] = np.zeros(tvecs[result_label].shape)
                            for link in vars[0].links:
                                compsize[output_label] += (link.source.vals if not link.source.is_junction else link.source.outflow)

                    elif isinstance(vars[0],Compartment) or isinstance(vars[0],Characteristic): # Compartment or Characteristic
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
                    if not isinstance(l,dict):
                        continue

                    output_label,f_stack_str = list(l.items())[0] # extract_labels has already ensured only one key is present

                    if not isinstance(f_stack_str,str):
                        continue

                    par = Parameter(pop=None,name=output_label)
                    f_stack, dep_labels = parser.produceStack(f_stack_str)
                    deps = []
                    displayed_annualization_warning = False
                    for dep_label in dep_labels:
                        var = pop.get_variable(dep_label)
                        if t_bins is not None and (isinstance(var,Link) or isinstance(var,Parameter)) and time_aggregation == "sum" and not displayed_annualization_warning:
                            raise AtomicaException('Function includes Parameter/Link so annualized rates are being used. Aggregation may need to use "average" rather than "sum"')
                        deps += pop.get_variable(dep_label)
                    par.f_stack = f_stack
                    par.deps = deps
                    par.preallocate(tvecs[result_label], dt)
                    par.update()
                    data_dict[output_label] = par.vals
                    output_units[output_label] = par.units

                # Third pass, aggregate them according to any aggregations present
                for output in outputs: # For each final output
                    if isinstance(output,dict):
                        output_name = list(output.keys())[0]
                        labels = output[output_name]

                        if isinstance(labels,str): # If this was a function, aggregation over outputs doesn't apply so just put it straight in
                            aggregated_outputs[pop_label][output_name] = data_dict[output_name]
                            aggregated_units[output_name] = 'unknown' # Also, we don't know what the units of a function are
                            continue

                        units = list(set([output_units[x] for x in labels]))
                        if len(units) > 1:
                            logger.warning('Warning - aggregation for output "%s" is mixing units, this is almost certainly not desired' % (output_name))
                            aggregated_units[output_name] = 'unknown'
                        else:
                            if units[0] in ['','fraction','proportion','probability'] and output_aggregation == 'sum' and len(labels) > 1: # Dimensionless quantity, like a prevalance
                                logger.warning('Warning - output "%s" is not in number units, so output aggregation probably should not be "sum"' % (output_name))
                            aggregated_units[output_name] = output_units[labels[0]]
                            
                        if output_aggregation == 'sum': 
                            aggregated_outputs[pop_label][output_name] = sum(data_dict[x] for x in labels) # Add together all the outputs
                        elif output_aggregation == 'average': 
                            aggregated_outputs[pop_label][output_name] = sum(data_dict[x] for x in labels) # Add together all the outputs
                            aggregated_outputs[pop_label][output_name] /= len(labels)
                        elif output_aggregation == 'weighted':
                            aggregated_outputs[pop_label][output_name] = sum(data_dict[x]*compsize[x] for x in labels) # Add together all the outputs
                            aggregated_outputs[pop_label][output_name] /= sum([compsize[x] for x in labels])
                    else:
                        aggregated_outputs[pop_label][output] = data_dict[output]
                        aggregated_units[output] = output_units[output]

            # Now aggregate over populations
            # If we have requested a reduction over populations, this is done for every output present
            for pop in pops: # This is looping over the population entries
                for output_name in aggregated_outputs[list(aggregated_outputs.keys())[0]].keys():
                    if isinstance(pop,dict):
                        pop_name = list(pop.keys())[0]
                        pop_labels = pop[pop_name]
                        if pop_aggregation == 'sum':
                            if aggregated_units[output_name] in ['','fraction','proportion','probability'] and len(pop_labels) > 1:
                                logger.warning('Warning - output "%s" is not in number units, so population aggregation probably should not be "sum"' % (output_name))
                            vals = sum(aggregated_outputs[x][output_name] for x in pop_labels) # Add together all the outputs
                        elif pop_aggregation == 'average': 
                            vals = sum(aggregated_outputs[x][output_name] for x in pop_labels) # Add together all the outputs
                            vals /= len(labels)
                        elif pop_aggregation == 'weighted':
                            vals = sum(aggregated_outputs[x][output_name]*popsize[x] for x in pop_labels) # Add together all the outputs
                            vals /= sum([popsize[x] for x in pop_labels])
                        self.series.append(Series(tvecs[result_label],vals,result_label,pop_name,output_name,data_label[output_name],units=aggregated_units[output_name]))
                    else:
                        vals = aggregated_outputs[pop][output_name]
                        self.series.append(Series(tvecs[result_label],vals,result_label,pop,output_name,data_label[output_name],units=aggregated_units[output_name]))

        self.results = [x.name for x in results] # NB. These are lists that thus specify the order in which plotting takes place
        self.pops = [list(x.keys())[0] if isinstance(x,dict) else x for x in pops]
        self.outputs = [list(x.keys())[0] if isinstance(x,dict) else x for x in outputs]

        # Names will be substituted with these at the last minute when plotting for titles/legends
        self.result_names = {x:x for x in self.results} # At least for now, no Result name mapping
        self.pop_names = {x:(get_full_name(x, project) if project is not None else x) for x in self.pops}
        self.output_names = {x:(get_full_name(x, project) if project is not None else x) for x in self.outputs}

        if t_bins is not None:

            # If t_bins is a scalar, expand it into a vector of bin edges
            if not hasattr(t_bins,'__len__'):
                if not (self.series[0].tvec[-1]-self.series[0].tvec[0])%t_bins:
                    upper = self.series[0].tvec[-1]+t_bins
                else:
                    upper = self.series[0].tvec[-1]
                t_bins = np.arange(self.series[0].tvec[0],upper,t_bins)
            
            if isinstance(t_bins,str) and t_bins == 'all':
                t_out = np.zeros((1,))
                lower = [-np.inf]
                upper = [np.inf]
            else:
                lower = t_bins[0:-1]
                upper = t_bins[1:]
                if time_aggregation == 'sum':
                    t_out = upper
                elif time_aggregation == 'average':
                    t_out = (lower+upper)/2.0

            for s in self.series:
                tvec = []
                vals = []
                for i,low,high,t in zip(range(len(lower)),lower,upper,t_out):
                    tvec.append(t)
                    if (not np.isinf(low) and low < s.tvec[0]) or (not np.isinf(high) and high > s.tvec[-1]):
                        vals.append(np.nan)
                    else:
                        flt = (s.tvec >= low) & (s.tvec < high)
                        if time_aggregation == 'sum':
                            if s.units in ['','fraction','proportion','probability']:
                                logger.warning('Warning - %s is not in number units, so time aggregation probably should not be "sum"' % (s))
                            vals.append(np.sum(s.vals[flt]))
                        elif time_aggregation == 'average':
                            vals.append(np.average(s.vals[flt]))

                s.tvec = np.array(tvec)
                s.vals = np.array(vals)
                if isinstance(t_bins,str) and t_bins == 'all':
                    s.t_labels = ['All']
                else:
                    s.t_labels = ['%d-%d' % (l,h) for l,h in zip(lower,upper)]
                
    def __repr__(self):
        s = 'PlotData\n'
        s += 'Results: %s\n' % (self.results)
        s += 'Pops: %s\n' % (self.pops)
        s += 'Outputs: %s\n' % (self.outputs)
        return s

    def tvals(self):
        # Return a vector of time values for the PlotData object, if all of the series have the
        # same time axis (otherwise throw an error)
        assert len(set([len(x.tvec) for x in self.series])) == 1, 'All series must have the same number of time points' # All series must have the same number of timepoints
        tvec = self.series[0].tvec
        t_labels = self.series[0].t_labels
        for i in range(1,len(self.series)):
            assert(all(self.series[i].tvec == tvec)), 'All series must have the same time points'
        return tvec,t_labels

    def __getitem__(self,key):
        # key is a tuple of (result,pop,output)
        # retrive a single Series e.g. plotdata['default','0-4','sus']
        for s in self.series:
            if s.result == key[0] and s.pop == key[1] and s.output == key[2]:
                return s
        raise AtomicaException('Series %s-%s-%s not found' % (key[0],key[1],key[2]))

    def set_colors(self,colors=None,results=['all'],pops=['all'],outputs=['all'],overwrite=False):
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
        # - So for instance, 'output=[a,b,c]' would give the same colour to all of those outputs, across all results and pops
        # - If multiple ones are specified, combinations get the unique colours
        # - At least one of them must not be none
        # - It is a bad idea to manually set colors for more than one dimension because the order is unclear!

        results = [results] if not isinstance(results,list) else results
        pops = [pops] if not isinstance(pops,list) else pops
        outputs = [outputs] if not isinstance(outputs,list) else outputs

        targets = list(itertools.product(results,pops,outputs))

        if colors is None:
            colors = gridColorMap(len(targets)) # Default colors
        elif isinstance(colors,list):
            assert len(colors) == len(targets), 'Number of colors must either be a string, or a list with as many elements as colors to set'
            colors = colors
        elif colors.startswith('#') or colors not in [m for m in plt.cm.datad if not m.endswith("_r")]:
            colors = [colors for x in range(len(targets))] # Apply color to all requested outputs
        else:
            color_norm = matplotlib_colors.Normalize(vmin=-1, vmax=len(targets))
            scalar_map = cmx.ScalarMappable(norm=color_norm, cmap=colors)
            colors = [scalar_map.to_rgba(index) for index in range(len(targets))]

        # Now each of these colors gets assigned 
        for color,target in zip(colors,targets):
            series = self.series
            series = [x for x in series if (x.result == target[0] or target[0] == 'all')]
            series = [x for x in series if (x.pop == target[1] or target[1] == 'all')]
            series = [x for x in series if (x.output == target[2] or target[2] == 'all')]
            for s in series:
                s.color = color if (s.color is None or overwrite==True) else s.color

class Series(object):
    def __init__(self,tvec,vals,result='default',pop='default',output='default',data_label='',color=None, units = ''):
        self.tvec = np.copy(tvec)
        self.t_labels = np.copy(self.tvec) # Iterable array of time labels - could become strings like [2010-2014]
        self.vals = np.copy(vals)
        self.result = result
        self.pop = pop
        self.output = output
        self.color = color
        self.data_label = data_label # Used to identify data for plotting
        self.units = units

    def __repr__(self):
        return 'Series(%s,%s,%s)' % (self.result,self.pop,self.output)


def plotBars(plotdata,stack_pops=None,stack_outputs=None,outer='times'):
    # We have a collection of bars - one for each Result, Pop, Output, and Timepoint.
    # Any aggregations have already been done. But _groupings_ have not. Let's say that we can group
    # pops and outputs but we never want to stack results. At least for now. 
    # But, the quantities could still vary over time. So we will have
    # - A set of arrays where the number of arrays is the number of things being stacked and
    #   the number of values is the number of bars - could be time, or could be results?
    # - As many sets as there are ungrouped bars
    # xlabels refers to labels within a block (i.e. they will be repeated for multiple times and results)
    global settings

    assert outer in ['times','results'], 'Supported outer groups are "times" or "results"'

    plotdata = dcp(plotdata)

    # Note - all of the tvecs must be the same
    tvals,t_labels = plotdata.tvals() # We have to iterate over these, with offsets, if there is more than one

    # If quantities are stacked, then they need to be coloured differently.
    if stack_pops is None:
        color_by = 'outputs'
        plotdata.set_colors(outputs=plotdata.outputs)
    elif stack_outputs is None:
        color_by = 'pops'
        plotdata.set_colors(pops=plotdata.pops)
    else:
        color_by = 'both'
        plotdata.set_colors(pops=plotdata.pops,outputs=plotdata.outputs)

    def process_input_stacks(input_stacks,available_items):
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
            return process_input_stacks([available_items],available_items)

        items = set()
        output_stacks = []
        if isinstance(input_stacks, list):
            for x in input_stacks:
                if isinstance(x,list):
                    output_stacks.append( ('','',x) if len(x) > 1 else (x[0],'',x))
                    items.update(x)
                elif isinstance(x,str):
                    output_stacks.append((x, '', [x]))
                    items.add(x)
                else:
                    raise AtomicaException('Unsupported input')

        elif isinstance(input_stacks, dict):
            for k, x in input_stacks.items():
                if isinstance(x,list):
                    output_stacks.append( ('',k,x) if len(x) > 1 else (x[0],k,x))
                    items.update(x)
                elif isinstance(x,str):
                    output_stacks.append((x, k, [x]))
                    items.add(x)
                else:
                    raise AtomicaException('Unsupported input')

        # Add missing items
        missing = list(set(available_items) - items)
        output_stacks += [(x, '', [x]) for x in missing]
        return output_stacks

    pop_stacks = process_input_stacks(stack_pops,plotdata.pops)
    output_stacks = process_input_stacks(stack_outputs,plotdata.outputs)

    # Now work out which pops and outputs appear in each bar (a bar is a pop-output combo)
    bar_pops = []
    bar_outputs = []
    for pop in pop_stacks:
        for output in output_stacks:
            bar_pops.append(pop)
            bar_outputs.append(output)

    width = settings['bar_width']
    gaps = [0.1,0.4,0.8] # Spacing within blocks, between inner groups, and between outer groups

    block_width = len(bar_pops)*(width+gaps[0])

    # If there is only one bar group, then increase spacing between bars
    if len(tvals) == 1 and len(plotdata.results) == 1:
        gaps[0] = 0.3

    if outer == 'times':
        if len(plotdata.results) == 1: # If there is only one inner group
            gaps[2] = gaps[1]
            gaps[1] = 0
        result_offset = block_width+gaps[1]
        tval_offset = len(plotdata.results)*(block_width+gaps[1])+gaps[2]
        iterator = nestedLoop([range(len(plotdata.results)),range(len(tvals))],[0,1])
    elif outer == 'results':
        if len(tvals) == 1: # If there is only one inner group
            gaps[2] = gaps[1]
            gaps[1] = 0
        result_offset = len(tvals)*(block_width+gaps[1])+gaps[2]
        tval_offset = block_width+gaps[1]
        iterator = nestedLoop([range(len(plotdata.results)),range(len(tvals))],[1,0])

    figs = []
    fig,ax = plt.subplots()
    fig.set_label('bars')
    figs.append(fig)

    rectangles = defaultdict(list) # Accumulate the list of rectangles for each colour
    color_legend = odict()

    # NOTE
    # pops, output - colour separates them. To merge colours, aggregate the data first
    # results, time - spacing separates them. Can choose to group by one or the other

    # Now, there are three levels of ticks
    # There is the within-block level, the inner group, and the outer group
    block_labels = [] # Labels for individual bars (tick labels)
    inner_labels = [] # Labels for bar groups below axis

    # Iterate over the inner and outer groups, rendering blocks at a time
    for r_idx,t_idx in iterator:
        base_offset = r_idx*result_offset + t_idx*tval_offset # Offset between outer groups
        block_offset = 0.0 # Offset between inner groups
        
        if outer == 'results':
            inner_labels.append((base_offset+block_width/2.0,t_labels[t_idx]))
        elif outer == 'times':
            inner_labels.append((base_offset+block_width/2.0,plotdata.result_names[plotdata.results[r_idx]]))

        for idx,bar_pop,bar_output in zip(range(len(bar_pops)),bar_pops,bar_outputs):
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
                    series = plotdata[plotdata.results[r_idx],pop,output]
                    y = series.vals[t_idx]
                    rectangles[series.color].append(Rectangle((base_offset+block_offset,y0), width, y))
                    if series.color in color_legend and (pop,output) not in color_legend[series.color]:
                        color_legend[series.color].append((pop,output))
                    elif series.color not in color_legend:
                        color_legend[series.color] = [(pop,output)]
                    y0 += y

            block_labels.append((base_offset+block_offset+width/2,bar_label))

            block_offset += width + gaps[0]

    # Add the patches to the figure and assemble the legend patches
    legend_patches = []

    for color,items in color_legend.items():
        pc = PatchCollection(rectangles[color], facecolor=color,edgecolor='none')
        ax.add_collection(pc)
        pops = set([x[0] for x in items])
        outputs = set([x[1] for x in items])

        if pops == set(plotdata.pops) and len(outputs) == 1: # If the same color is used for all pops and always the same output
            label = plotdata.output_names[items[0][1]] # Use the output name
        elif outputs == set(plotdata.outputs) and len(pops) == 1: # Same color for all outputs and always same pop
            label = plotdata.pop_names[items[0][0]] # Use the pop name
        else:
            label = ''
            for x in items:
                label += '%s-%s,\n' % (plotdata.pop_names[x[0]],plotdata.output_names[x[1]])
            label = label.strip()[:-1] # Replace trailing newline and comma
        legend_patches.append(Patch(facecolor=color,label=label))

    # Set axes now, because we need block_offset and base_offset after the loop
    ax.autoscale()
    ax.set_xlim(xmin=-2*gaps[0],xmax=block_offset+base_offset)
    fig.set_figwidth(1.75*(block_offset+base_offset))
    ax.set_ylim(ymin=0)
    _turnOffBorder(ax)
    set_ytick_format(ax,'KM')
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
            ax.text(offset + (tval_offset - gaps[1] - gaps[2])/2, 1,t,transform=ax.get_xaxis_transform(),verticalalignment='bottom', horizontalalignment='center')
            offset += tval_offset
    elif outer == 'results' and len(plotdata.results) > 1:
        offset = 0.0
        for r in plotdata.results:
            ax.text(offset + (result_offset - gaps[1] - gaps[2])/2, 1,plotdata.result_names[r],transform=ax.get_xaxis_transform(),verticalalignment='bottom', horizontalalignment='center')
            offset += result_offset

    # If there is only one block per inner group, then use the inner group string as the bar label
    if not any([x[1] for x in block_labels]) and len(block_labels) == len(inner_labels) and len(set([x for _,x in inner_labels])) > 1:
        ax.set_xticklabels([x[1] for x in inner_labels])
    elif len(inner_labels) > 1 and len(set([x for _,x in inner_labels])) > 1: # Inner group labels are only displayed if there is more than one label
        ax2 = ax.twiny()  # instantiate a second axes that shares the same x-axis
        ax2.set_xticks([x[0] for x in inner_labels])
        ax2.set_xticklabels(['\n\n'+x[1] for x in inner_labels])
        ax2.xaxis.set_ticks_position('bottom')
        ax2.set_xlim(ax.get_xlim())
        ax2.spines['right'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        ax2.spines['bottom'].set_visible(False)
        ax2.tick_params(axis=u'both', which=u'both',length=0)

    # Do the legend last, so repositioning the axes works properly
    if settings['legend_mode'] == 'separate':
        figs.append(render_separate_legend(ax,plot_type='bar',handles=legend_patches))
    elif settings['legend_mode'] == 'together':
        render_legend(ax,plot_type='bar',handles=legend_patches)

    return figs


def plotSeries(plotdata,plot_type='line',axis='outputs',data=None):
    # TODO -
    # - Clean up doing aggregation separately
    # - Implement separate figures as everything starting out on the same plot and then
    #   distributing them across figures if requested? But does this still have those problems associated
    #   with colours? Maybe the colours should be specified in a dict the same as the data?
    # This function plots a time series for a model output quantities
    #
    # INPUTS
    # - plotdata - a PlotData instance to plot
    # - plot_type - 'line', 'stacked', or 'proportion' (stacked, normalized to 1)
    # - data - Draw scatter points for data wherever the output label matches
    #   a data label. Only draws data if the plot_type is 'line'
    global settings

    assert axis in ['outputs','results','pops']

    figs = []

    plotdata = dcp(plotdata)

    # Update colours with defaults, if they were not set

    if axis == 'results':
        plotdata.set_colors(results=plotdata.results)
    elif axis == 'pops':
        plotdata.set_colors(pops=plotdata.pops)
    elif axis == 'outputs':
        plotdata.set_colors(outputs=plotdata.outputs)

    if axis == 'results':
        for pop in plotdata.pops:
            for output in plotdata.outputs:
                fig,ax = plt.subplots()
                fig.set_label('%s_%s' % (pop,output))
                figs.append(fig)

                units = list(set([plotdata[result,pop,output].units for result in plotdata.results]))
                if len(units) == 1 and units[0]:
                    ax.set_ylabel('%s (%s)' % (plotdata.output_names[output],units[0]))
                else:
                    ax.set_ylabel('%s' % (plotdata.output_names[output]))

                ax.set_title('%s' % (plotdata.pop_names[pop]))
                if plot_type in ['stacked','proportion']:
                    y = np.stack([plotdata[result,pop,output].vals for result in plotdata.results])
                    y = y/np.sum(y,axis=0) if plot_type == 'proportion' else y
                    ax.stackplot(plotdata[plotdata.results[0],pop,output].tvec,y,labels=[plotdata.result_names[x] for x in plotdata.results],colors=[plotdata[result,pop,output].color for result in plotdata.results])
                else:
                    for result in plotdata.results:
                        ax.plot(plotdata[result,pop,output].tvec,plotdata[result,pop,output].vals,color=plotdata[result,pop,output].color,label=plotdata.result_names[result])
                        if data is not None:
                            render_data(ax,data,plotdata[result,pop,output])
                apply_series_formatting(ax,plot_type)
                if settings['legend_mode'] == 'together':
                    render_legend(ax,plot_type)

    elif axis == 'pops':
        for result in plotdata.results:
            for output in plotdata.outputs:
                fig,ax = plt.subplots()
                fig.set_label('%s_%s' % (result,output))
                figs.append(fig)

                units = list(set([plotdata[result,pop,output].units for pop in plotdata.pops]))
                if len(units) == 1 and units[0]:
                    ax.set_ylabel('%s (%s)' % (plotdata.output_names[output],units[0]))
                else:
                    ax.set_ylabel('%s' % (plotdata.output_names[output]))

                ax.set_title('%s' % (plotdata.result_names[result]))
                if plot_type in ['stacked','proportion']:
                    y = np.stack([plotdata[result,pop,output].vals for pop in plotdata.pops])
                    y = y/np.sum(y,axis=0) if plot_type == 'proportion' else y
                    ax.stackplot(plotdata[result,plotdata.pops[0],output].tvec,y,labels=[plotdata.pop_names[x] for x in plotdata.pops],colors=[plotdata[result,pop,output].color for pop in plotdata.pops])
                else:
                    for pop in plotdata.pops:
                        ax.plot(plotdata[result,pop,output].tvec,plotdata[result,pop,output].vals,color=plotdata[result,pop,output].color,label=plotdata.pop_names[pop])
                        if data is not None:
                            render_data(ax,data,plotdata[result,pop,output])
                apply_series_formatting(ax,plot_type)
                if settings['legend_mode'] == 'together':
                    render_legend(ax,plot_type)

    elif axis == 'outputs':
        for result in plotdata.results:
            for pop in plotdata.pops:
                fig,ax = plt.subplots()
                fig.set_label('%s_%s' % (result,pop))
                figs.append(fig)

                units = list(set([plotdata[result,pop,output].units for output in plotdata.outputs]))
                if len(units) == 1 and units[0]:
                    ax.set_ylabel(units[0])

                ax.set_title('%s-%s' % (plotdata.result_names[result],plotdata.pop_names[pop]))
                if plot_type in ['stacked','proportion']:
                    y = np.stack([plotdata[result,pop,output].vals for output in plotdata.outputs])
                    y = y/np.sum(y,axis=0) if plot_type == 'proportion' else y
                    ax.stackplot(plotdata[result,pop,plotdata.outputs[0]].tvec,y,labels=[plotdata.output_names[x] for x in plotdata.outputs],colors=[plotdata[result,pop,output].color for output in plotdata.outputs])
                else:
                    for output in plotdata.outputs:
                        ax.plot(plotdata[result,pop,output].tvec,plotdata[result,pop,output].vals,color=plotdata[result,pop,output].color,label=plotdata.output_names[output])
                        if data is not None:
                            render_data(ax,data,plotdata[result,pop,output])
                apply_series_formatting(ax,plot_type)
                if settings['legend_mode'] == 'together':
                    render_legend(ax,plot_type)

    if settings['legend_mode'] == 'separate':
        figs.append(render_separate_legend(ax,plot_type))

    return figs

def render_data(ax,data,series):
    # This function renders a scatter plot for a single variable (in a single population)
    # The scatter plot is drawn in the current axis
    # INPUTS
    # proj - Project object
    # pop - name of a population (str)
    # output - name of an output (str)
    # name - The name-formatting function to retrieve full names (currently unused)
    # color - The color of the data points to use

    if series.data_label in data.filter['datapar']:
        d = data.get_spec(series.data_label)
    else:
        return

    if series.pop in d['data'].keys():
        t,y = d['data'].get_arrays(series.pop)
        if len(t) == 0:
            return
    else:
        return

    ax.scatter(t,y,marker='o', s=40, linewidths=3, facecolors='none',color=series.color)#label='Data %s %s' % (name(pop,proj),name(output,proj)))

def set_ytick_format(ax,formatter):

    def KM(x, pos):
        # 
        if x >= 1e6:
            return '%1.1fM' % (x * 1e-6)
        elif x >= 1e3:
            return '%1.1fK' % (x * 1e-3)
        else:
            return '%g' % x

    def percent(x,pos):
        return '%g%%' % (x*100)

    fcn = locals()[formatter]
    ax.yaxis.set_major_formatter(FuncFormatter(fcn))

def apply_series_formatting(ax,plot_type):
    # This function applies formatting that is common to all Series plots
    # (irrespective of the 'axis' setting)
    ax.autoscale(enable=True, axis='x', tight=True)
    ax.set_xlabel('Year')
    ax.set_ylim(ymin=0)
    _turnOffBorder(ax)
    if plot_type == 'proportion':
        ax.set_ylim(ymax=1)
        ax.set_ylabel('Proportion ' + ax.get_ylabel())
    else:
        ax.set_ylim(ymax=ax.get_ylim()[1] * 1.05)

    set_ytick_format(ax,'KM')

def _turnOffBorder(ax):
    """
    Turns off top and right borders, leaving only bottom and left borders on.
    """
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')

def plotLegend(entries,plot_type='patch',fig=None):
    # plot type - can be 'patch' or 'line'
    # The legend items are a dict keyed with the label e.g.
    # entries = {'sus':'blue','vac':'red'}
    # If a figure is passed in, the legend will be drawn in that figure, overwriting
    # a previous legend if one was already there

    h = []
    for label,color in entries.items():
        if plot_type == 'patch':
            h.append(Patch(color=color,label=label))
        else:
            h.append(Line2D([0],[0],color=color,label=label))

    legendsettings = {'loc': 'center', 'bbox_to_anchor': None,'frameon':False} # Settings for separate legend

    if fig is None: # Draw in a new figure
        render_separate_legend(None,None,h)
    else:
        existing_legend = fig.findobj(Legend)
        if existing_legend and existing_legend[0].parent is fig: # If existing legend and this is a separate legend fig
                existing_legend[0].remove() # Delete the old legend
                fig.legend(handles=h, **legendsettings)
        else: # Drawing into an existing figure
            ax = fig.axes[0]
            legendsettings = {'loc': 'center left', 'bbox_to_anchor': (1.05, 0.5), 'ncol': 1}
            if existing_legend:
                existing_legend[0].remove() # Delete the old legend
                ax.legend(handles=h,**legendsettings)
            else:
                ax.legend(handles=h,**legendsettings)
                box = ax.get_position()
                ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    return fig

def render_separate_legend(ax,plot_type=None,handles=None):
    if handles is None:
        handles, labels = ax.get_legend_handles_labels()
    else:
        labels = [h.get_label() for h in handles]

    fig,ax = plt.subplots()
    ax.set_position([0.5,0.5,0.01,0.01])
    ax.set_axis_off() # This allows the figure to be shown in jupyter notebook

    legendsettings = {'loc': 'center', 'bbox_to_anchor': None,'frameon':False}

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

    if plot_type in ['stacked', 'proportion','bar']:
        fig.legend(handles=handles[::-1], labels=labels[::-1], **legendsettings)
    else:
        fig.legend(handles=handles, labels=labels, **legendsettings)

    return fig

def render_legend(ax,plot_type=None,handles=None,):
    # This function renders a legend
    # INPUTS
    # - plot_type - Used to decide whether to reverse the legend order for stackplots
    if handles is None:
        handles, labels = ax.get_legend_handles_labels()
    else:
        labels = [h.get_label() for h in handles]

    legendsettings = {'loc': 'center left', 'bbox_to_anchor': (1.05, 0.5), 'ncol': 1}
    labels = [textwrap.fill(label, 16) for label in labels]

    if plot_type in ['stacked', 'proportion','bar']:
        ax.legend(handles=handles[::-1], labels=labels[::-1], **legendsettings)
    else:
        ax.legend(handles=handles, labels=labels,**legendsettings)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

def reorder_legend(figs,order=None):
    # This helper function lets you reorder a legend after figure creation
    # Order can be
    # - A string 'reverse' to reverse the order of the legend
    # - A list of indices mapping old position to new position. For example, if the
    #   original label order was ['a,'b','c'], then order=[1,0,2] would result in ['b','a','c']

    if isinstance(figs,list):
        if not figs[-1].get_label(): # If the last figure is a legend figure
            fig = figs[-1]
        else:
            for fig in figs: # Apply order operation to all figures passed in
                reorder_legend(fig,order=order)
    else:
        fig = figs

    legend = fig.findobj(Legend)[0]
    assert len(legend._legend_handle_box._children) == 1, 'Only single-column legends are supported'
    vpacker = legend._legend_handle_box._children[0]

    if order is None:
        return
    elif order == 'reverse':
        order = range(len(legend.legendHandles)-1,-1,-1)
    else:
        assert max(order) < len(vpacker._children), 'Requested index greater than number of legend entries'

    new_children = []
    for i in range(0,len(order)):
        new_children.append(vpacker._children[order[i]])
    vpacker._children = new_children

def relabel_legend(figs,labels):

    if isinstance(figs,list):
        if not figs[-1].get_label(): # If the last figure is a legend figure
            fig = figs[-1]
        else:
            for fig in figs: # Apply order operation to all figures passed in
                relabel_legend(fig,labels=labels)
    else:
        fig = figs

    legend = fig.findobj(Legend)[0]
    assert len(legend._legend_handle_box._children) == 1, 'Only single-column legends are supported'
    vpacker = legend._legend_handle_box._children[0]

    if isinstance(labels,list):
        assert len(labels) == len(vpacker._children), 'If specifying list of labels, length must match number of legend entries'
        labels = {i:l for i,l in enumerate(labels)}
    elif isinstance(labels,dict):
        idx = labels.keys()
        assert max(idx) < len(vpacker._children), 'Requested index greater than number of legend entries'
    else:
        raise AtomicaException('Labels must be a list or a dict')

    for idx,label in labels.items():
        text=vpacker._children[idx]._children[1]._text
        text.set_text(label)


def get_full_name(output_id, proj):
    """
    For a given output_id, returns the user-friendly version of the name. 
    """

    if proj is None:
        return output_id

    labels = {y['name']:x for x,y in proj.framework.semantics.items() if y['attribute']=='label'}

    # Handle Links specified with colon syntax
    if ':' in output_id:
        src,dest = output_id.split(':')

        if dest == 'flow':
            if src in labels:
                return f'{labels[src]} (flow)'
            else:
                return f'{src} (flow)'

        if src and src in labels:
            src = labels[src]

        if dest and dest in labels:
            dest = labels[dest]

        full = 'Flow'
        if src:
            full += f' from {src}'
        if dest:
            full += f' to {dest}'
        return full
    else:
        if output_id in labels:
            return labels[output_id]
        else:
            return output_id

def gridColorMap(ncolors=10, limits=None, nsteps=10, asarray=False, doplot=False, newwindow=True):
    '''
    Create a qualitative colormap by assigning points according to the maximum pairwise distance in the
    color cube. Basically, the algorithm generates n points that are maximally uniformly spaced in the
    [R, G, B] color cube.
    
    Arguments:
        ncolors: the number of colors to create
        limits: how close to the edges of the cube to make colors (to avoid white and black)
        nsteps: the discretization of the color cube (e.g. 10 = 10 units per side = 1000 points total)
        asarray: whether to return the colors as an array instead of as a list of tuples
        doplot: whether or not to plot the color cube itself
        newwindow: if doplot=True, whether to use a new window

    Usage example:
        from pylab import *
        from colortools import gridcolormap
        ncolors = 10
        piedata = rand(ncolors)
        colors = gridcolormap(ncolors)
        figure()
        pie(piedata, colors=colors)
        gridcolormap(ncolors, doplot=True)
        show()

    Version: 2015dec29 (cliffk)
    '''

    # # Imports
    from numpy import linspace, meshgrid, array, transpose, inf, zeros, argmax, minimum
    from numpy.linalg import norm

    # Steal colorbrewer colors for small numbers of colors
    colorbrewercolors = array([
    [27, 158, 119],
    [217, 95, 2],
    [117, 112, 179],
    [231, 41, 138],
    [255, 127, 0],
    [200, 200, 51],  # Was too bright yellow
    [166, 86, 40],
    [247, 129, 191],
    [153, 153, 153],
    ]) / 255.

    if ncolors <= len(colorbrewercolors):
        colors = colorbrewercolors[:ncolors]

    else:  # Too many colors, calculate instead
        # # Calculate sliding limits if none provided
        if limits is None:
            colorrange = 1 - 1 / float(ncolors ** 0.5)
            limits = [0.5 - colorrange / 2, 0.5 + colorrange / 2]

        # # Calculate primitives and dot locations
        primitive = linspace(limits[0], limits[1], nsteps)  # Define primitive color vector
        x, y, z = meshgrid(primitive, primitive, primitive)  # Create grid of all possible points
        dots = transpose(array([x.flatten(), y.flatten(), z.flatten()]))  # Flatten into an array of dots
        ndots = nsteps ** 3  # Calculate the number of dots
        indices = [0]  # Initialize the array

        # # Calculate the distances
        for pt in range(ncolors - 1):  # Loop over each point
            totaldistances = inf + zeros(ndots)  # Initialize distances
            for ind in indices:  # Loop over each existing point
                rgbdistances = dots - dots[ind]  # Calculate the distance in RGB space
                totaldistances = minimum(totaldistances, norm(rgbdistances, axis=1))  # Calculate the minimum Euclidean distance
            maxindex = argmax(totaldistances)  # Find the point that maximizes the minimum distance
            indices.append(maxindex)  # Append this index

        colors = dots[indices, :]

    # # Wrap up: optionally turn into a list of tuples
    if asarray:
        output = colors
    else:
        output = []
        for i in range(ncolors): output.append(tuple(colors[i, :]))  # Gather output

    # # For plotting
    if doplot:
        from mpl_toolkits.mplot3d import Axes3D  # analysis:ignore
        from pylab import figure, gca
        if newwindow:
            fig = figure()
            ax = fig.add_subplot(111, projection='3d')
        else:
            ax = gca(projection='3d')
        ax.scatter(colors[:, 0], colors[:, 1], colors[:, 2], c=output, s=200, depthshade=False)
        ax.set_xlabel('R')
        ax.set_ylabel('G')
        ax.set_zlabel('B')
        ax.set_xlim((0, 1))
        ax.set_ylim((0, 1))
        ax.set_zlim((0, 1))
        ax.grid(False)

    return output

def nestedLoop(inputs,loop_order):
    # Take in a list of lists to iterate over, and their nesting order
    # Return items in the order of the original lists
    # e.g
    # inputs = [['a','b','c'],[1,2,3]]
    # for l,n in nested_loop([['a','b','c'],[1,2,3]],[0,1]):
    # This would yield in order (a,1),(a,2),(a,3),(b,1)...
    # but if loop_order = [1,0], then it would be (a,1),(b,1),(c,1),(a,2)...
    inputs = [inputs[i] for i in loop_order] 
    iterator = itertools.product(*inputs) # This is in the loop order
    for item in iterator:
        out = [None for x in loop_order]
        for i in range(len(item)):
            out[loop_order[i]] = item[i]
        yield out