# Test safe division in function_parser
import pytest
import atomica as at
import numpy as np
import matplotlib.pyplot as plt


@pytest.mark.parametrize("n_cols", [0, 1, 2])
@pytest.mark.parametrize("axis", ["outputs", "results", "pops"])
@pytest.mark.parametrize("legend_mode", ["together", "separate", ""])
def test_plot(n_cols, legend_mode, axis):

    P = at.demo("sir")
    d = at.PlotData(P.results[0], project=P)
    figs = at.plot_series(d, axis=axis, legend_mode=legend_mode, n_cols=n_cols)

    for fig in figs:
        plt.close(fig)
