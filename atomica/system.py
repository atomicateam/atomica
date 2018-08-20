# -*- coding: utf-8 -*-
"""
Atomica system functionality file.
Contains important functions that are used throughout Atomica.
"""

import os

# Set up a logger that can be imported elsewhere
import logging
logger = logging.getLogger('atomica')

# Code for determining module installation directory.
def atomica_path(subdir=None, trailingsep=True):
    """ Returns the parent path of the Atomica module. If subdir is not None, include it in the path. """
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    if subdir is not None:
        if not isinstance(subdir, list):
            subdir = [subdir]  # Ensure it's a list.
        tojoin = [path] + subdir
        if trailingsep:
            tojoin.append('')  # This ensures it ends with a separator.
        path = os.path.join(*tojoin)  # For example: ['/home/atomica', 'tests', '']
    return path

# Code for exceptions specific to Atomica

class AtomicaException(Exception):
    """ A wrapper class to allow for Atomica-specific exceptions. """
    pass

class NotFoundError(AtomicaException):
    # Throw this error if a user-specified input was not found
    pass

class NotAllowedError(AtomicaException):
    # Throw this error if the user requested an illegal operation
    pass

class AtomicaInputError(AtomicaException):
    # Throw this error if the code was not able to understand the user's input
    pass



