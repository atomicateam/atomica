"""
Define internal system constants and functions

"""

import os
from .function_parser import supported_functions

# Set up a logger that can be imported elsewhere
import logging
logger = logging.getLogger('atomica')


def atomica_path(subdir=None, trailingsep=True):
    """ Returns paths relative to the Atomica parent module

    This function by default returns the directory containing the Atomica
    source files. It can also return paths relative to this directory using
    the optional additional arguments

    :param subdir: Append an additional path list to Atomica path
    :param trailingsep: If True, a trailing separator will be included so that the
                        returned path can have a file name string added to it easily
    :return: Absolute path string

    """

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    if subdir is not None:
        if not isinstance(subdir, list):
            subdir = [subdir]  # Ensure it's a list.
        tojoin = [path] + subdir
        if trailingsep:
            tojoin.append('')  # This ensures it ends with a separator.
        path = os.path.join(*tojoin)  # For example: ['/home/atomica', 'tests', '']
    return path


LIBRARY_PATH = atomica_path(['atomica', 'library'])


class NotFoundError(Exception):
    """
    Error for when an item was not found

    This error gets thrown if a user-specified input was not found. For example, if the
    user queries a Population for a non-existent variable.
    """

    pass


class FrameworkSettings:
    """
    Define system level keywords

    This class stores sets of keywords such as the keys for different variable types, or the
    supported quantity types (e.g., 'probability', 'number')

    """

    KEY_COMPARTMENT = "comp"
    KEY_CHARACTERISTIC = "charac"
    KEY_TRANSITION = "link"
    KEY_PARAMETER = "par"
    KEY_POPULATION = "pop"
    KEY_TRANSFER = "transfer"
    KEY_INTERACTION = "interpop"

    QUANTITY_TYPE_PROBABILITY = "probability"
    QUANTITY_TYPE_DURATION = "duration"
    QUANTITY_TYPE_NUMBER = "number"
    QUANTITY_TYPE_FRACTION = "fraction"
    QUANTITY_TYPE_PROPORTION = "proportion"
    STANDARD_UNITS = [QUANTITY_TYPE_PROBABILITY, QUANTITY_TYPE_DURATION, QUANTITY_TYPE_NUMBER, QUANTITY_TYPE_FRACTION, QUANTITY_TYPE_PROPORTION]

    DEFAULT_SYMBOL_INAPPLICABLE = "N.A."
    DEFAULT_POP_TYPE = 'default'

    RESERVED_KEYWORDS = ['t', 'flow', 'all', 'dt', 'total']  # A code_name in the framework cannot be equal to one of these values
    RESERVED_KEYWORDS += supported_functions.keys()

    RESERVED_SYMBOLS = set(':,;/+-*\'"')  # A code_name in the framework (for characs, comps, pars) cannot contain any of these characters
