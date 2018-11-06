"""
Define internal system constants and functions

"""

import os
import sys
from six import reraise

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


LIBRARY_PATH = atomica_path(['atomica', 'library'])

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


def reraise_modify(caught_exc, append_msg, prepend=True):
    """Append message to exception while preserving attributes.

    Preserves exception class, and exception traceback.

    Note:
        This function needs to be called inside an except because
        `sys.exc_info()` requires the exception context.

    Args:
        caught_exc(Exception): The caught exception object
        append_msg(str): The message to append to the caught exception
        prepend(bool): If True prepend the message to args instead of appending

    Returns:
        None

    Side Effects:
        Re-raises the exception with the preserved data / trace but
        modified message

    From https://stackoverflow.com/questions/9157210/how-do-i-raise-the-same-exception-with-a-custom-message-in-python/9157277
    by Bryce Guinta
    """
    ExceptClass = type(caught_exc)
    # Keep old traceback
    traceback = sys.exc_info()[2]
    if not caught_exc.args:
        # If no args, create our own tuple
        arg_list = [append_msg]
    else:
        # Take the last arg
        # If it is a string
        # append your message.
        # Otherwise append it to the
        # arg list(Not as pretty)
        arg_list = list(caught_exc.args[:-1])
        last_arg = caught_exc.args[-1]
        if isinstance(last_arg, str):
            if prepend:
                arg_list.append(append_msg + last_arg)
            else:
                arg_list.append(last_arg + append_msg)
        else:
            arg_list += [last_arg, append_msg]
    caught_exc.args = tuple(arg_list)
    reraise(ExceptClass, caught_exc, traceback)
