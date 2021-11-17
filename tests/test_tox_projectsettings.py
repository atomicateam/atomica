import atomica as at
import numpy as np


def test_projectsettings():

    # Check that the sim end year is automatically updated if the
    # end year or the timestep is changed
    s = at.ProjectSettings(sim_start=2000, sim_end=2005, sim_dt=1)

    # Test changing sim end
    s.sim_end = 2006.5
    assert s.sim_end == 2007

    # Test changing dt
    s.sim_dt = 2
    assert s.sim_end == 2008

    # Test changing via update time vector
    s.update_time_vector(end=2009)
    assert s.sim_end == 2010

    # Test changing during construction
    s = at.ProjectSettings(sim_start=2000, sim_end=2001.1, sim_dt=0.25)
    assert s.sim_end == 2001.25

    # Check that the tvec returned is inclusive of the end year
    s = at.ProjectSettings(sim_start=2000, sim_end=2003, sim_dt=1)
    assert np.all(s.tvec == np.array([2000, 2001, 2002, 2003]))


if __name__ == "__main__":
    test_projectsettings()
