"""
Version:
"""

#%%
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


def render_separate_legend(ax, handles=None, labels=None):
    
    # Allows an argument of a figure instead of an ax
    if isinstance(ax, pl.Figure):
        ax = ax.axes[0]
    
    if handles is None:
        handles, labels = ax.get_legend_handles_labels()
    else:
        labels = [h.get_label() for h in handles]

    fig, ax = pl.subplots()
    ax.set_position([-0.05,-0.05,1.1,1.1])
    
    legendsettings = {'loc': 'center', 'bbox_to_anchor': None, 'frameon': False}

    # A legend renders the line/patch based on the object handle. However, an object
    # can only appear in one figure. Thus, if the legend is in a different figure, the
    # object cannot be shown in both the original figure and in the legend. Thus we need
    # to copy the handles, and use the copies to render the legend
    from copy import copy
    handles = [copy(x) for x in handles]

    ax.legend(handles=handles, labels=labels, **legendsettings)

    return fig


fig,ax = make_fig()
legend = render_separate_legend(ax)

f1 = sw.mpld3ify(fig, jsonify=False)
f2 = sw.mpld3ify(legend, jsonify=False)
f2['axes'][0]['axes'][0]['fontsize'] = 0
f2['axes'][0]['axes'][1]['fontsize'] = 0

sw.browser([f1,f2])