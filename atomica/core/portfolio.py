# -*- coding: utf-8 -*-
"""
Atomica portfolio definition file.
Implements a container class for Atomica (and derived classes) projects of all types.
"""

from atomica.core.system import apply_to_all_methods, log_usage


@apply_to_all_methods(log_usage)
class Portfolio(object):
    """ The Atomica portfolio class, a higher-level container for Atomica projects. """

    def __init__(self, name="default"):
        """ Initialize the portfolio. """
        self.name = name
