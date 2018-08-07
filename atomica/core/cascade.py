from .plotting import grid_color_map, plot_legend
import matplotlib.pyplot as plt
import numpy as np
import textwrap
import sciris.core as sc
import matplotlib
from .utils import NDict
from .results import Result
from six import string_types
import logging
logger = logging.getLogger(__name__)

def plot_multi_cascade(results,cascade,pops='all',year=None,data=None):
    # This is a cascade plot that handles multiple results and times
    # Results are grouped by stage/output, which is not possible to do with plot_bars()

    # First, process the cascade into an odict of outputs for PlotData
    if isinstance(results, sc.odict):
        results = [result for _, result in results.items()]
    elif isinstance(results, Result):
        results = [results]
    elif isinstance(results, NDict):
        results = list(results)

    if year is None:
        year = results[0].t[0] # Draw cascade for first year
    else:
        year = sc.promotetoarray(year)

    if (len(results)>1 and len(year)>1):
        label_fcn = lambda result,t: '%s (%s)' % (result.name,t)
    elif len(results) > 1:
        label_fcn = lambda result,t: '%s' % (result.name)
    else:
        label_fcn = lambda result,t: '%s' % (t)

    # Gather all of the cascade outputs and years
    cascade_vals = sc.odict()
    for result in results:
        for t in year:
            cascade_vals[label_fcn(result,t)] = get_cascade_vals(result,cascade,pops=pops,year=t)[0]

    # Determine the number of bars, per stage - based either on result or time point
    n_bars = len(cascade_vals)
    bar_width = 1. # This is the width of the bars
    bar_gap = 0.15 # This is the width of the bars
    block_gap = 1. # This is the gap between blocks
    block_size = n_bars*(bar_width+bar_gap)
    x = np.arange(0,len(cascade_vals[0].keys()))*(block_size+block_gap) # One block for each cascade stage
    colors = grid_color_map(n_bars)  # Default colors
    legend_entries = sc.odict()

    fig = plt.figure()
    fig.set_figwidth(fig.get_figwidth()*1.5)

    for offset,(bar_label,data) in enumerate(cascade_vals.items()):
        legend_entries[bar_label] = colors[offset]
        vals = np.hstack(data.values())
        plt.bar(x+offset*(bar_width+bar_gap),vals,color=colors[offset],width=bar_width)

    plot_legend(legend_entries,fig=fig)
    ax = fig.axes[0]
    ax.set_xticks(x+(block_size-bar_gap-bar_width)/2)
    ax.set_xticklabels(['\n'.join(textwrap.wrap(k, 15)) for k in cascade_vals[0].keys()])
    ax.get_xaxis().set_ticks_position('top')

    # Make the loss table
    cell_text = []
    for data in cascade_vals.values():
        cascade_array = np.hstack(data.values())
        loss = np.diff(cascade_array)
        loss_str = ['%s' % sc.sigfig(-val, sigfigs=3, sep=True) for val in loss]
        loss_str.append('-') # No loss for final stage
        cell_text.append(loss_str)

    # Clean up formatting
    yticks = ax.get_yticks()
    ax.set_yticks(yticks[1:]) # Remove the first tick at 0 so it doesn't clash with table - TODO: improve table spacing so this isn't needed
    plt.ylabel('Number of people')
    plt.subplots_adjust(top=0.8,right=0.75,left=0.2)

    # Add a table at the bottom of the axes
    table = plt.table(cellText=cell_text,rowLabels=list(cascade_vals.keys()),rowColours=None,colLabels=None,loc='bottom',cellLoc='center')

def plot_cascade(result, cascade, pops=None, year=None):
    # This is the fancy cascade plot, which only applies to a single result at a single time
    # For inputs, see `Result.get_cascade_vals`

    if pops is None: pops = 'all'

    fontsize=14
    if year is None:
        year = result.t[0] # Draw cascade for first year
    else:
        year = sc.promotetoarray(year)
        assert len(year) == 1

    assert isinstance(result,Result), 'Input must be a single Result object'
    cascade_vals,t = get_cascade_vals(result,cascade,pops,year)
    if data is not None:
        cascade_data,_ = get_cascade_data(data,result.framework,cascade,pops,year)
        cascade_data_array = np.hstack(cascade_data.values())

    assert len(t) == 1, 'Plot cascade requires time aggregation'
    cascade_array = np.hstack(cascade_vals.values())

    fig = plt.figure()
    fig.set_figwidth(fig.get_figwidth()*1.5)
    ax = plt.gca()
    h = plt.bar(np.arange(len(cascade_vals)),cascade_array, width=0.5)
    if data is not None:
        h_scatter = plt.scatter(np.arange(len(cascade_vals)), cascade_data_array,s=40,c='#ff9900',marker='s',zorder=100)

    ax.set_xticks(np.arange(len(cascade_vals)))
    ax.set_xticklabels([ '\n'.join(textwrap.wrap(x, 15)) for x in cascade_vals.keys()])

    ylim = ax.get_ylim()
    yticks = ax.get_yticks()
    data_yrange = np.diff(ylim)
    ax.set_ylim(-data_yrange*0.2,data_yrange*1.1)
    ax.set_yticks(yticks)
    for i,val in enumerate(cascade_array):
        plt.text(i, val*1.01, '%s' % sc.sigfig(val, sigfigs=3, sep=True), verticalalignment='bottom',horizontalalignment='center',size=fontsize,zorder=200)

    bars = h.get_children()
    conversion = cascade_array[1:]/cascade_array[0:-1] # Fraction not lost
    conversion_text_height = cascade_array[-1]/2

    for i in range(len(bars)-1):
        left_bar = bars[i]
        right_bar = bars[i+1]

        xy = np.array([
        (left_bar.get_x() + left_bar.get_width(), 0), # Bottom left corner
        (left_bar.get_x() + left_bar.get_width(), left_bar.get_y() + left_bar.get_height()), # Top left corner
        (right_bar.get_x(), right_bar.get_y() + right_bar.get_height()),  # Top right corner
        (right_bar.get_x(), 0),  # Bottom right corner
        ])

        p = matplotlib.patches.Polygon(xy, closed=True,facecolor=(0.93,0.93,0.93))
        ax.add_patch(p)

        bbox_props = dict(boxstyle="rarrow", fc=(0.7, 0.7, 0.7),lw=1)

        t = ax.text(np.average(xy[1:3,0]), conversion_text_height, '%s%%' % sc.sigfig(conversion[i]*100, sigfigs=3, sep=True), ha="center", va="center", rotation=0,size=fontsize,bbox=bbox_props)


    loss = np.diff(cascade_array)
    for i,val in enumerate(loss):

        plt.text(i, -data_yrange[0]*0.02, 'Loss\n%s' % sc.sigfig(-val, sigfigs=3, sep=True), verticalalignment='top',horizontalalignment='center',color=(0.8,0.2,0.2),size=fontsize)

    pop_label = 'entire population' if pops=='all' else pops
    plt.ylabel('Number of people')
    plt.title('Cascade for %s in %d' % (pop_label,year))
    plt.tight_layout()

    return fig

def get_cascade_outputs(framework,cascade_name):
    # Given a cascade name, return an outputs dicts corresponding to the cascade stages
    # suitable for use in PlotData
    # INPUTS
    # - framework : a ProjectFramework
    # - cascade_name : one of framework.cascade.keys()
    #
    # OUTPUTS
    # - outputs : A odict suitable for PlotData(outputs=outputs)
    #
    # Example
    # a = get_cascade(framework,'main')
    # Suppose the spreadsheet had stages
    # Stage 1 - sus,vac,inf
    # Stage 2 - vac,inf
    #
    # Then the output of this function would be
    # output = {'Stage 1':['sus','vac','inf'],'Stage 2':['vac','inf']
    df = framework.cascades[cascade_name]
    outputs = sc.odict()
    for _, stage in df.iterrows():
        outputs[stage[0]] = [x.strip() for x in stage[1].split(',')]  # Split the name of the stage and the constituents
    return outputs

def get_cascade_vals(result,cascade,pops='all',year=None):
    '''
    Gets values for populating a cascade plot
    '''
    # INPUTS
    # - result is a single result object
    # - cascade can be a list of cascade entries, or the name of a cascade in a Framework
    # - pops should map to a single population output (a single pop name, or a single aggregation)
    # - year controls which time points appear in the output. Possible values are
    #   - None : all time points in the Result
    #   - scalar or np.array : one entry for each time specified e.g. `year=2020` or `year=[2020,2025,2030]`
    #
    # OUTPUTS
    # - cascade_output : odict with {stage_name:vals} where vals is an ndarray the same shape as the 't' output
    # - t : ndarray of time values

    from .plotting import PlotData # Import here to avoid circular dependencies

    assert isinstance(pops,string_types), 'At this stage, get_cascade_vals only intended to retrieve one population at a time, or to aggregate over all pops'

    if isinstance(cascade,string_types):
        outputs = get_cascade_outputs(result.framework,cascade)
    else:
        outputs = cascade

    if year is None:
        d = PlotData(result, outputs=outputs, pops=pops)
    else:
        year = sc.promotetoarray(year)
        d = PlotData(result, outputs=outputs, pops=pops)
        d.interpolate(year)

    assert len(d.pops) == 1, 'get_cascade_vals() cannot get results for multiple populations or population aggregations, only a single pop or single aggregation'
    cascade_vals = sc.odict()
    for result in d.results:
        for pop in d.pops:
            for output in d.outputs:
                cascade_vals[output] = d[(result,pop,output)].vals # NB. Might want to return the Series here to retain formatting, units etc.
    t = d.tvals()[0] # nb. first entry in d.tvals() is time values, second entry is time labels

    return cascade_vals,t

def get_cascade_data(data,framework,cascade,pops='all',year=None):
    # This function is the counterpart to get_cascade_vals but it returns data
    # instead. Note that the inputs and outputs are slightly different
    # - If year is specified, the output is guaranteed to be the same size as the input year array, the same as get_cascade_vals
    #   However, the get_cascade_vals defaults to all time points in the simulation output, whereas get_cascade_data defaults to
    #   all data years. To make a plot superimposing data and model output, the year should be specified to ensure that the years
    #   match up
    # pops - can be 'all', or a pop name, or a list of pop names
    #
    # NB - In general, data probably will NOT exist
    # Set the logging level to 'DEBUG' to have messages regarding this printed out

    if isinstance(cascade,string_types):
        outputs = get_cascade_outputs(framework,cascade)
    else:
        outputs = cascade

    if pops == 'all':
        pops = list(data.pops.keys())
    elif isinstance(pops,string_types):
        pops = [pops]

    if year is not None:
        t = sc.promotetoarray(year) # Output times are guaranteed to be
    else:
        t = data.tvec # Defaults to data's time vector

    # Now, get the outputs in the given years
    data_values = dict()
    for stage_constituents in outputs.values():
        for code_name in stage_constituents:
            if code_name not in data_values:
                data_values[code_name] = np.zeros(t.shape)* np.nan # data values start out as NaN - this is a fallback in case for some reason pops is empty (the data will be all NaNs then)

                for pop_idx,pop in enumerate(pops):
                    ts = data.get_ts(code_name,pop) # The TimeSeries data for the required variable and population
                    vals = np.ones(t.shape) * np.nan # preallocate output values coming from this TimeSeries object

                    # Now populate this array
                    if ts is not None:
                        for i,tval in enumerate(ts.t):
                            match = np.where(t==tval)[0]
                            if len(match): # If a time point in the TimeSeries matches the requested time - then match[0] is the index in t
                                vals[match[0]] = ts.vals[i]
                        if np.any(np.isnan(vals)):
                            logger.debug('Data for %s (%s) did not contain values for some of the requested years' % (code_name, pop))
                    else:
                        logger.debug('Data not present for %s (%s)' % (code_name,pop))


                    if pop_idx == 0:
                        data_values[code_name] = vals  # If at least one TimeSeries was found, use the first one as the data values (it could still be NaN if no times match)
                    else:
                        data_values[code_name] += vals

    # Now, data values contains all of the required quantities in all of the required years. Last step is to aggregate them
    cascade_data = sc.odict()
    for stage_name,stage_constituents in outputs.items():
        for code_name in stage_constituents:
            if stage_name not in cascade_data:
                cascade_data[stage_name] = data_values[code_name]
            else:
                cascade_data[stage_name] += data_values[code_name]

    return cascade_data,t



