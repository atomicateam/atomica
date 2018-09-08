"""
Version:
"""

#%%
import sciris as sc
import scirisweb as sw
import pylab as pl

def make_fig():
    fig = pl.figure()
    ax = fig.add_subplot(111)
    ax.plot([1,4,3,4,], label='mish')
    ax.plot([8,4,3,2], label='mish')
    ax.legend()
    return fig,ax


def make_legend(ax):
    legendfig = []
    return legendfig


def separatelegend(ax=None, handles=None, labels=None, reverse=False, legendsettings=None):
    
    # Handle settings
    settings = {'loc': 'center', 'bbox_to_anchor': None, 'frameon': False}
    if legendsettings is None: legendsettings = {}
    settings.update(legendsettings)
    
    # Handle figure/axes
    if ax is None: ax = pl.gca() # Get current axes, if none supplied
    if isinstance(ax, pl.Figure): ax = ax.axes[0] # Allows an argument of a figure instead of an axes
    
    # Handle handles
    axhandles, axlabels = ax.get_legend_handles_labels()
    if handles is None: handles = axhandles
    if labels is None: labels = axlabels

    # Set up new plot
    fig, ax = pl.subplots()
    ax.set_position([-0.05,-0.05,1.1,1.1])
    
    # A legend renders the line/patch based on the object handle. However, an object
    # can only appear in one figure. Thus, if the legend is in a different figure, the
    # object cannot be shown in both the original figure and in the legend. Thus we need
    # to copy the handles, and use the copies to render the legend
    handles = [sc.cp(x) for x in handles]
    
    # Reverse order, e.g. for stacked plots
    if reverse:
        handles = handles[::-1]
        labels   = labels[::-1]
    
    # Plot the new legend
    ax.legend(handles=handles, labels=labels, **settings)

    return fig


fig,ax = make_fig()
legend = separatelegend(ax)

f1 = sw.mpld3ify(fig, jsonify=False)
f2 = sw.mpld3ify(legend, jsonify=False)
f2['axes'][0]['axes'][0]['fontsize'] = 0
f2['axes'][0]['axes'][1]['fontsize'] = 0

sw.browser([f1,f2])