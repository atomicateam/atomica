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
    ax.plot([8,4,3,2], label='mush')
    return fig,ax

fig,ax = make_fig()
legend = sc.separatelegend(ax)

f1 = sw.mpld3ify(fig,    jsonify=False)
f2 = sw.mpld3ify(legend, jsonify=False)
f2['axes'][0]['texts'][1]['text'] = 'mash' # Shows the direct editing of the JSON

sw.browser([f1,f2])