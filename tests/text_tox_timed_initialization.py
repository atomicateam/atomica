import atomica as at
import sciris as sc
import os
import pytest
import sys
import itertools

# # P = at.Project(framework='dummy_framework.xlsx',databook='dummy_databook.xlsx')
# # # P.run_sim()
# # P = at.demo('tb',do_run=True)
# # P.results[0].plot()
# # P = at.Project.load('asdf2.prj')
#
# # P = at.Project(framework=at.LIBRARY_PATH+'tb_framework.xlsx')
# # P.load_databook(at.LIBRARY_PATH+'tb_databook.xlsx')
# P = at.demo('tb',do_run=True)

testdir = at.rootdir / "tests"
tmpdir = testdir / "temp"


def test_timed_initialization():

    F = at.ProjectFramework(testdir / "timed_initialization_test_framework.xlsx")
    D = at.ProjectData.new(F, [2018], 1, 0)
    D.tdve["tx_rate"].ts[0].insert(2018, 0)
    D.tdve["tx_rate"].ts[0].insert(2021, 0)
    D.tdve["tx_rate"].ts[0].insert(2022, 0.5)

    def set_initialization_basic(F, D, year, y_factor=True):
        # Conventional approach using Y-factor adjustment only
        res = P.run_sim(P.parsets[0].make_constant(2018))
        ps2 = at.ParameterSet(F, D, "basic")

        # Set initial compartment sizes for initialization quantities
        for qty in itertools.chain(F.characs.index[F.characs["setup weight"] > 0], F.comps.index[F.comps["setup weight"] > 0]):
            for pop in D.pops:
                if y_factor:
                    ps2.pars[qty].meta_y_factor = 1
                    ps2.pars[qty].y_factor[pop] = res.get_variable(qty, pop)[0].vals[-1] / ps2.pars[qty].ts[pop].interpolate(year)
                else:
                    ps2.pars[qty].ts[pop].insert(year, res.get_variable(qty, pop)[0].vals[-1])

        return ps2

    P = at.Project(framework=F, databook=D, do_run=False)
    P.settings.sim_dt = 1 / 12
    P.settings.sim_start = 2018
    P.settings.sim_end = 2023

    res1 = P.run_sim()

    # Basic steady state initialization
    ps = set_initialization_basic(F, D, 2018)
    res2 = P.run_sim(ps, result_name="basic")

    # Advanced steady state initialization
    ps2 = at.ParameterSet(F, D)
    ps2.set_initialization(res1, 2021)
    res3 = P.run_sim(ps2, result_name="advanced")

    ps2.pars["alive"].y_factor[0] = 1.1

    ps2.save_calibration(tmpdir / "test_cal.xlsx")
    res3 = P.run_sim(ps2, result_name="advanced")

    ps4 = P.make_parset("saved")
    ps4.load_calibration(tmpdir / "test_cal.xlsx")
    res4 = P.run_sim(ps4, result_name="loaded")

    d = at.PlotData([res1, res2, res3, res4], ["sus", "inf", "rec"])
    at.plot_series(d)


if __name__ == "__main__":
    test_timed_initialization()
