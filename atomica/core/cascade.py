from .plotting import grid_color_map, plot_legend
import matplotlib.pyplot as plt
import numpy as np
import textwrap
import sciris.core as sc
import matplotlib
from .utils import NDict
from .results import Result

def plot_multi_cascade(results,cascade,pops='all',year=None):
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
    cascade_data = sc.odict()
    for result in results:
        for t in year:
            cascade_data[label_fcn(result,t)] = result.get_cascade_vals(cascade,pops=pops,year=t)[0]

    # Determine the number of bars, per stage - based either on result or time point
    n_bars = len(cascade_data)
    bar_width = 1. # This is the width of the bars
    bar_gap = 0.15 # This is the width of the bars
    block_gap = 1. # This is the gap between blocks
    block_size = n_bars*(bar_width+bar_gap)
    x = np.arange(0,len(cascade_data[0].keys()))*(block_size+block_gap) # One block for each cascade stage
    colors = grid_color_map(n_bars)  # Default colors
    legend_entries = sc.odict()

    fig = plt.figure()
    fig.set_figwidth(fig.get_figwidth()*1.5)

    for offset,(bar_label,data) in enumerate(cascade_data.items()):
        legend_entries[bar_label] = colors[offset]
        for stage,vals in data.items():
            plt.bar(x+offset*(bar_width+bar_gap),vals,color=colors[offset],width=bar_width)
    plot_legend(legend_entries,fig=fig)
    ax = fig.axes[0]
    ax.set_xticks(x+(block_size-bar_gap-bar_width)/2)
    ax.set_xticklabels(['\n'.join(textwrap.wrap(k, 15)) for k in cascade_data[0].keys()])
    ax.get_xaxis().set_ticks_position('top')

    # Make the loss table
    cell_text = []
    for data in cascade_data.values():
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
    plt.table(cellText=cell_text,rowLabels=list(cascade_data.keys()),rowColours=None,colLabels=None,loc='bottom',cellLoc='center')

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
    cascade_vals,t = result.get_cascade_vals(cascade,pops,year)
    assert len(t) == 1, 'Plot cascade requires time aggregation'
    cascade_array = np.hstack(cascade_vals.values())

    fig = plt.figure()
    fig.set_figwidth(fig.get_figwidth()*1.5)
    ax = plt.gca()
    h= plt.bar(np.arange(len(cascade_vals)),cascade_array, width=0.5)
    ax.set_xticks(np.arange(len(cascade_vals)))
    ax.set_xticklabels([ '\n'.join(textwrap.wrap(x, 15)) for x in cascade_vals.keys()])

    ylim = ax.get_ylim()
    yticks = ax.get_yticks()
    data_yrange = np.diff(ylim)
    ax.set_ylim(-data_yrange*0.2,data_yrange*1.1)
    ax.set_yticks(yticks)
    for i,val in enumerate(cascade_array):
        plt.text(i, val*1.01, '%s' % sc.sigfig(val, sigfigs=3, sep=True), verticalalignment='bottom',horizontalalignment='center',size=fontsize)

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