"""
SETTINGS
Store all the settings for a project.
Version: 2018mar26
"""

import numpy as np
from sciris.utils import defaultrepr

from atomica.system import logger


class ProjectSettings(object):
    def __init__(self, sim_start=None, sim_end=None, sim_dt=None):

        self.sim_start = sim_start if sim_start is not None else 2000.0
        self.sim_end = sim_end if sim_end is not None else 2030.0
        self.sim_dt = sim_dt if sim_dt is not None else 1.0 / 4

        # Other
        #        self.defaultblue = (0.16, 0.67, 0.94) # The color of Atomica
        #        self.safetymargin = 0.5 # Do not move more than this fraction of people on a single timestep
        #        self.infmoney = 1e10 # A lot of money
        logger.info("Initialized project settings.")

    def __repr__(self):
        """ Print object """
        output = defaultrepr(self)
        return output

    @property
    def tvec(self):
        return np.arange(self.sim_start, self.sim_end + self.sim_dt / 2, self.sim_dt)

    def update_time_vector(self, start=None, end=None, dt=None):
        """ Calculate time vector. """
        if start is not None:
            self.sim_start = start
        if end is not None:
            self.sim_end = end
        if dt is not None:
            self.sim_dt = dt
