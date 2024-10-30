# This script checks that the junction update is correct

import numpy as np
import atomica as at
import matplotlib.pyplot as plt
import os


def test_seasonal():
    testdir = at.rootdir / "tests"
    tmpdir = testdir / "temp"

    F_path = testdir / "framework_seasonal_test.xlsx"
    D_path = tmpdir / "databook_seasonal_test.xlsx"

    F = at.ProjectFramework(F_path)
    D = at.ProjectData.new(F, np.arange(2000, 2001), pops={"pop1": "Population 1"}, transfers=0)
    D.save(D_path)

    P = at.Project(name="test", framework=F, do_run=False)
    P.settings.update_time_vector(end=2005, dt=0.02)
    P.load_databook(databook_path=D_path, make_default_parset=True, do_run=True)
    r = P.results[0]

    d = at.PlotData(r, outputs=["seasonal_max"], project=P)
    at.plot_series(d)
    plt.title("Seasonal rainfall")

    d = at.PlotData(r, outputs=["seasonal_jan", "seasonal_jun"], project=P)
    at.plot_series(d)
    plt.title("Seasonal rainfall")

    d = at.PlotData(r, outputs=["birth"], project=P)
    at.plot_series(d)

    d = at.PlotData(r, outputs=["mos"], project=P)
    at.plot_series(d)


if __name__ == "__main__":
    test_seasonal()
