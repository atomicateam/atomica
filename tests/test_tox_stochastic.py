import numpy as np
import atomica as at
import os
import matplotlib.pyplot as plt


def test_stochastic():

    testdir = at.parent_dir()  # Must be relative to current file to work with tox

    F0 = at.ProjectFramework(testdir / "framework_sir_dynamic.xlsx")
    P0 = at.Project(name="test", framework=F0, do_run=False)
    P0.load_databook(databook_path=testdir / "databook_sir_dynamic.xlsx", make_default_parset=True, do_run=False)
    baseline = P0.run_sim(result_name="default")

    F = at.ProjectFramework(testdir / "framework_stochastic_test.xlsx")
    P = at.Project(name="test", framework=F, do_run=False)
    P.load_databook(databook_path=testdir / "databook_sir_dynamic.xlsx", make_default_parset=True, do_run=False)
    ensemble = at.Ensemble(mapping_function=lambda x: at.PlotData(x), baseline_results=baseline)
    ensemble.run_sims(P, "default", n_samples=100, result_names="default")
    fig = ensemble.plot_series()
    at.relabel_legend(fig, ["Susceptible", "Infected", "Recovered"])
    plt.ylabel("Number of people")


if __name__ == "__main__":
    test_stochastic()
