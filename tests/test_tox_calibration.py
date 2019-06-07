## This script checks that parameter scale factors work correctly

import numpy as np
import atomica as at
import matplotlib.pyplot as plt
import os

def test_scale_factors():
    P = at.demo('sir',do_run=False)

    res = P.run_sim('default')
    baseline = res.get_variable('infdeath')[0].vals[0]

    ps2 = P.make_parset('scaled')
    ps2.pars['infdeath'].y_factor['adults'] = 1.5
    res = P.run_sim(ps2)
    scale1 = res.get_variable('infdeath')[0].vals[0]

    ps2.pars['infdeath'].meta_y_factor = 2.0
    res = P.run_sim(ps2)
    scale2 = res.get_variable('infdeath')[0].vals[0]

    assert np.isclose(scale1, baseline*1.5, 1e-4)
    assert np.isclose(scale2, baseline*3, 1e-4)

if __name__ == '__main__':
    test_scale_factors()
