"""
Define internal system constants and functions

"""

import sciris as sc
from .function_parser import supported_functions
import pathlib

# Set up a logger that can be imported elsewhere
import logging

__all__ = ["atomica_path", "LIBRARY_PATH", "NotFoundError", "FrameworkSettings"]

logger = logging.getLogger("atomica")


def atomica_path(subdir=None) -> pathlib.Path:
    """
    Returns paths relative to the Atomica parent module

    This function by default returns the directory containing the Atomica
    source files. It can also return paths relative to this directory using
    the optional additional arguments

    Example usage:

        >>> at.atomica_path()
        WindowsPath('E:/projects/atomica/atomica')
        >>> at.atomica_path('foo')
        WindowsPath('E:/projects/atomica/atomica/foo')
        >>> at.atomica_path(['foo','bar'])
        WindowsPath('E:/projects/atomica/atomica/foo/bar')

    :param subdir: Optionally append a list of subdirectories to the path
    :return: Absolute Path object

    """

    path = pathlib.Path(__file__).parent.parent
    for d in sc.promotetolist(subdir):
        path /= d
    return path.resolve()


LIBRARY_PATH = atomica_path(["atomica", "library"])


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
    QUANTITY_TYPE_RATE = "rate"
    STANDARD_UNITS = [QUANTITY_TYPE_PROBABILITY, QUANTITY_TYPE_DURATION, QUANTITY_TYPE_NUMBER, QUANTITY_TYPE_FRACTION, QUANTITY_TYPE_PROPORTION, QUANTITY_TYPE_RATE]

    DEFAULT_SYMBOL_INAPPLICABLE = "N.A."
    DEFAULT_POP_TYPE = "default"

    RESERVED_KEYWORDS = ["t", "flow", "all", "dt", "total"]  # A code_name in the framework cannot be equal to one of these values
    RESERVED_KEYWORDS += supported_functions.keys()

    RESERVED_SYMBOLS = set(":,;/+-*'\" @")  # A code_name in the framework (for characs, comps, pars) cannot contain any of these characters
