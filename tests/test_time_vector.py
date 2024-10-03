# Test time vector
# The problem:
# In atomica, we want to include the end year: Say we're running a simulation from 2000 to 2050 ->
# we want to be able to get the results for year 2000, 2001, ... and 2050. Hence, we need to run
# more time steps after 2050

# # On develop branch: Creates 611 entries -> if taken the integer,the last year doesn't have enough entries
# On temporal weights: Creates 612 entries -> but 13 in 2038 and 11 in 2048

import atomica as at
import numpy as np


def test_time_vector():
    # Creating a setting object
    analysis_years = (2000, 2050)
    dt = 1 / 12
    settings = at.ProjectSettings(sim_start=analysis_years[0], sim_end=analysis_years[1] + 1 - dt, sim_dt=dt)  #: Atomica project settings
    tvec = settings.tvec  #: Simulation/result time points

    assert len(set(np.unique(tvec.astype(int), return_counts=True)[1])) == 1
    
    # on temporal weights branch: np.linspace(self.sim_start, self.sim_end, int(np.float32(((self.sim_end - self.sim_start) / self.sim_dt))) + 1)
    #  tvec = np.linspace(2000, 2051-1/12, int(np.float32(((2051-1/12 - 2000) / (1/12)))) + 1)

    # on develop branch: np.linspace(self.sim_start, self.sim_end, int((self.sim_end - self.sim_start) / self.sim_dt) + 1)
    # develop: tvec = np.linspace(2000, 2051-1/12, int((2051-1/12 - 2000) / (1/12)) + 1)
    # np.unique(tvec.astype(int), return_counts=True)



if __name__ == "__main__":
    test_time_vector()