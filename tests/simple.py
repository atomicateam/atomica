"""
Minimal example of running Atomica.
"""
import atomica as at
import matplotlib.pyplot as plt

P = at.demo("sir")
d = at.PlotData(P.results[0], project=P)
figs = at.plot_series(d)
plt.show()