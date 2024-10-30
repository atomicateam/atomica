# This script checks that parameter scale factors work correctly

import numpy as np
import atomica as at
import pytest

testdir = at.parent_dir()
tmpdir = testdir / "temp"


def test_scale_factors():
    P = at.demo("sir", do_run=False)

    res = P.run_sim("default")
    baseline = res.get_variable("infdeath")[0].vals[0]

    ps2 = P.make_parset("scaled")
    ps2.pars["infdeath"].y_factor["adults"] = 1.5
    res = P.run_sim(ps2)
    scale1 = res.get_variable("infdeath")[0].vals[0]

    ps2.pars["infdeath"].meta_y_factor = 2.0
    res = P.run_sim(ps2)
    scale2 = res.get_variable("infdeath")[0].vals[0]

    assert np.isclose(scale1, baseline * 1.5, 1e-4)
    assert np.isclose(scale2, baseline * 3, 1e-4)


def test_load_legacy_calibrations():
    # Test loading old versions of saved calibrations
    for model in ["tb", "sir", "combined"]:
        P = at.demo(model, do_run=False)
        P.parsets[0].load_calibration(testdir / "calibration" / f"test_calibration_{model}.xlsx")

    P = at.demo("combined", do_run=False)
    P.parsets[0].load_calibration(testdir / "calibration" / "test_calibration_combined_inexact.xlsx")


def test_save_load_calibrations():
    P = at.demo("tb", do_run=False)
    ps1 = P.make_parset("ps1")
    ps2 = P.make_parset("ps2")

    ps1.pars["alive"].y_factor["0-4"] = 2
    ps1.transfers["age"]["0-4"].y_factor["5-14"] = 3
    ps1.interactions["w_ctc"]["0-4"].y_factor["5-14"] = 4
    ps1.pars["alive"].meta_y_factor = 5
    ps1.transfers["age"]["0-4"].meta_y_factor = 6
    ps1.interactions["w_ctc"]["0-4"].meta_y_factor = 7

    assert ps2.pars["alive"].y_factor["0-4"] == 1
    assert ps2.transfers["age"]["0-4"].y_factor["5-14"] == 1
    assert ps2.interactions["w_ctc"]["0-4"].y_factor["5-14"] == 1
    assert ps2.pars["alive"].meta_y_factor == 1
    assert ps2.transfers["age"]["0-4"].meta_y_factor == 1
    assert ps2.interactions["w_ctc"]["0-4"].meta_y_factor == 1

    ss = ps1.calibration_spreadsheet()
    ps2.load_calibration(ss)

    assert ps2.pars["alive"].y_factor["0-4"] == 2
    assert ps2.transfers["age"]["0-4"].y_factor["5-14"] == 3
    assert ps2.interactions["w_ctc"]["0-4"].y_factor["5-14"] == 4
    assert ps2.pars["alive"].meta_y_factor == 5
    assert ps2.transfers["age"]["0-4"].meta_y_factor == 6
    assert ps2.interactions["w_ctc"]["0-4"].meta_y_factor == 7

    _ = ps2.y_factors


if __name__ == "__main__":
    # test_scale_factors()
    test_load_legacy_calibrations()
    # test_save_load_calibrations()
