## This script performs various tests on Result objects

import numpy as np
import atomica as at
import matplotlib.pyplot as plt
import os
import sciris as sc
import pytest



tmpdir = at.atomica_path(['tests','temp'])

def test_interpolation():
    ts = at.TimeSeries([0,1],[0,2])

    assert np.allclose(var1.vals[var1.t == 2010][0], var2.vals[var2.t == 2010][0], equal_nan=True)
    assert np.allclose(var2.vals[var2.t == 2015][0], 0.1, equal_nan=True)
    assert np.allclose(var2.vals[var2.t == 2018][0], 0.15, equal_nan=True)
    assert np.allclose(var2.vals[var2.t == 2019][0], 0.15, equal_nan=True)  # Check that the function didn't turn back on

    assert np.isclose(a, b, rtol=rtol, atol=atol, equal_nan=equal_nan))



if __name__ == '__main__':
    test_interpolation()
