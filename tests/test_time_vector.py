# Test time vector
# The problem:
# In atomica, we want to include the end year: Say we're running a simulation from 2000 to 2050 ->
# we want to be able to get the results for year 2000, 2001, ... and 2050. Hence, we need to run
# more time steps after 2050, in particular up to 2051-1/12

# Currently, at.ProjectSettings.tvec creates 611 entries -> if taken the integer,the last year doesn't have enough entries

import atomica as at
import numpy as np
import pandas as pd


def test_time_vector():
    # Test 1
    # Creating a setting object
    analysis_years = (2000, 2050)
    dt = 1 / 12
    settings = at.ProjectSettings(sim_start=analysis_years[0], sim_end=analysis_years[1] + 1 - dt, sim_dt=dt)  #: Atomica project settings
    tvec = settings.tvec  #: Simulation/result time points
    assert set(np.unique(tvec.astype(int), return_counts=True)[1]) == {1 / dt}  # or pd.Series(tvec).astype(int).value_counts()


if __name__ == "__main__":
    test_time_vector()
