# -*- coding: utf-8 -*-
"""
Atomica system functionality file.
Contains important functions that are used throughout Atomica.
Examples include logging, type-checking, etc.
"""

import logging.config
import os
import datetime
import inspect
import decorator
import six

if six.PY2:
    from inspect import getargspec as argspec  # Python 2 arg inspection.
else:
    from inspect import getfullargspec as argspec  # Python 3 arg inspection.


# Code for setting up a system settings class containing module-wide variables.

class SystemSettings(object):
    """ Stores all 'system' variables used by the Atomica module. """

    CODEBASE_DIRNAME = ["atomica", "core"]
    CONFIG_LOGGER_FILENAME = "logging.ini"
    CONFIG_FRAMEWORK_FILENAME = "format_framework.ini"
    CONFIG_DATABOOK_FILENAME = "format_databook.ini"
    CONFIG_LIST_SEPARATOR = ","

    LOGGER_DEBUG_OUTPUT_PATH = "./previous_session.log"

    STRUCTURE_KEY_DATA = "databook"
    STRUCTURE_KEY_FRAMEWORK = "framework_file"

    OBJECT_EXTENSION_PROJECT = ".prj"
    OBJECT_EXTENSION_FRAMEWORK = ".frw"
    OBJECT_EXTENSION_DATA = ".dat"

    QUANTITY_TYPE_ABSOLUTE = "absolute"
    QUANTITY_TYPE_RELATIVE = "relative"

    DEFAULT_SPACE_LABEL = " "
    DEFAULT_SPACE_NAME = "_"
    DEFAULT_SEPARATOR_LABEL = " - "
    DEFAULT_SEPARATOR_NAME = "_"
    DEFAULT_SYMBOL_YES = "y"
    DEFAULT_SYMBOL_NO = "n"
    DEFAULT_SYMBOL_INAPPLICABLE = "N.A."
    DEFAULT_SYMBOL_OR = "OR"
    DEFAULT_SYMBOL_TO = "--->"
    DEFAULT_SYMBOL_IGNORE = "..."
    DEFAULT_SUFFIX_PLURAL = "s"


# Code for determining module installation directory.

def atomica_path(subdir=None, trailingsep=True):
    """ Returns the parent path of the Atomica module. If subdir is not None, include it in the path. """
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    if subdir is not None:
        if not isinstance(subdir, list):
            subdir = [subdir]  # Ensure it's a list.
        tojoin = [path] + subdir
        if trailingsep:
            tojoin.append('')  # This ensures it ends with a separator.
        path = os.path.join(*tojoin)  # For example: ['/home/atomica', 'tests', '']
    return path


# Code for setting up a logger.

logging.config.fileConfig(atomica_path(subdir=SystemSettings.CODEBASE_DIRNAME) + SystemSettings.CONFIG_LOGGER_FILENAME,
                          defaults={"log_filename": "{0}".format(SystemSettings.LOGGER_DEBUG_OUTPUT_PATH)})
logger = logging.getLogger("atomica")


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

# Code for timestamping function/method usage.

def log_usage(undecorated_function):
    """ Logs the usage of a function or method. """

    def log_usage_decorated_function(*args, **kwargs):
        """ Timestamps and times an undecorated function call. """
        # If the function is unbound, logging information is limited.
        class_prefix = ""
        instance_name = ""
        descriptor = "function"
        # If the function is actually a method, the first argument is the owning class instance.
        # Extract class name and instance name, if the latter exists, for logging purposes.
        if inspect.ismethod(undecorated_function):
            class_prefix = undecorated_function.im_class.__name__ + "."
            try:
                instance_name = args[0].name  # Method 'getName' avoided due to recursion.
            except (IndexError, AttributeError):
                pass
            descriptor = "method"
        # Time and process the undecorated function, noting whether an exception is raised.
        time_before = datetime.datetime.now()
        logger.debug("   Entering {0}:   {1}".format(descriptor, class_prefix + undecorated_function.__name__))
        if not instance_name == "":
            logger.debug("   {0} name: {1}".format(class_prefix.rstrip('.'), instance_name))
        exception_raised = False
        e_saved = None
        x = None
        try:
            x = undecorated_function(*args, **kwargs)
        except Exception as e:
            exception_raised = True
            e_saved = e  # Make the exception persist beyond the try-except block.
        time_after = datetime.datetime.now()
        time_elapsed = time_after - time_before
        if exception_raised:
            logger.debug("   Abandoning {0}: {1}".format(descriptor, class_prefix + undecorated_function.__name__))
        else:
            logger.debug("   Exiting {0}:    {1}".format(descriptor, class_prefix + undecorated_function.__name__))
        if not instance_name == "":
            logger.debug("   {0} name: {1}".format(class_prefix.rstrip('.'), instance_name))
        logger.debug("   Time spent in {0}: {1}".format(descriptor, time_elapsed))
        # If an exception was raised while processing the function, it should be delayed no longer.
        if exception_raised:
            raise e_saved
        return x

    #    return log_usage_decorated_function
    return undecorated_function


# Code for validating function argument types.

class ArgumentTypeError(ValueError):
    """ Raised when the argument type of a function is incorrect. """

    def __init__(self, func_name, arg_name, accepted_arg_type, func_sig=""):
        self.error = "Value supplied to arg '{0}' in '{1}{2}' was not of type '{3}'.".format(arg_name, func_name,
                                                                                             func_sig,
                                                                                             accepted_arg_type.__name__)

    def __str__(self):
        return self.error


def accepts(*arg_types):
    """
    Validates that the arguments of a function are of a specified type.
    Ignores the zeroth argument if it is 'self', i.e. the function is an instance method.
    Does not work with class methods due to non-standard zeroth arguments.
    """

    @decorator.decorator
    def check_accepts(undecorated_function, *args, **kwargs):
        # Check if the first argument of function signature is 'self', thus denoting a method.
        # If the undecorated function is a method, skip self when checking arg types.
        sig = tuple(argspec(undecorated_function).args)
        arg_start = 0
        if len(sig) > 0:
            arg_start = int(sig[0] == 'self')
        arg_count = arg_start
        try:
            for (arg, accepted_type) in zip(args[arg_start:], arg_types):
                if accepted_type == str:
                    accepted_type = six.string_types
                if not isinstance(arg, accepted_type):
                    raise ArgumentTypeError(func_name=undecorated_function.__name__,
                                            arg_name=sig[arg_count],
                                            accepted_arg_type=accepted_type,
                                            func_sig=str(sig).replace("'", "").replace(",)", ")"))
                arg_count += 1
        except ArgumentTypeError as e:
            logger.exception(str(e))
            raise
        return undecorated_function(*args, **kwargs)

    return check_accepts


# Code for validating function return types.

class ReturnTypeError(ValueError):
    """ Raised when the return type of a function is incorrect. """

    def __init__(self, func_name, accepted_return_type, func_sig=""):
        self.error = "Value returned from '{0}{1}' was not of type '{2}'.".format(func_name, func_sig,
                                                                                  accepted_return_type.__name__)

    def __str__(self):
        return self.error


def returns(return_type):
    """
    Validates that the returned value of a function is of a specified type.
    Is not particularly useful for tupled multi-variable returns.
    """

    @decorator.decorator
    def check_returns(undecorated_function, *args, **kwargs):
        # Check if the first argument of function signature is 'self', thus denoting a method.
        # If the undecorated function is a method, skip self when checking arg types.
        sig = tuple(argspec(undecorated_function).args)
        return_value = undecorated_function(*args, **kwargs)
        try:
            if not type(return_value) == return_type:
                raise ReturnTypeError(func_name=undecorated_function.__name__,
                                      accepted_return_type=return_type,
                                      func_sig=str(sig).replace("'", "").replace(",)", ")"))
        except ReturnTypeError as e:
            logger.exception(e.message)
            raise
        return return_value

    return check_returns


# Code for conveniently applying a decorator to each method in a class.

def apply_to_all_methods(func):
    """ Decorator that takes a function argument and applies it to all methods of a class. """

    def class_decorator(undecorated_class):
        """
        The true underlying decorator, i.e. with no arguments in the signature, applied to an undecorated class.
        The function argument of the wrapper propagates into the undecorated class.
        """
        for method_name, method in inspect.getmembers(undecorated_class, inspect.ismethod):
            setattr(undecorated_class, method_name, func(method))
        return undecorated_class

    return class_decorator


# String utility functions.

def display_name(name, as_title=False):
    """ Minor function to convert name into text display format. """
    text = name
    if as_title:
        text = text.title()
    return text.replace(SystemSettings.DEFAULT_SPACE_NAME, SystemSettings.DEFAULT_SPACE_LABEL)
