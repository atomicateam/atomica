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

if six.PY2: from inspect import getargspec as argspec   # Python 2 arg inspection.
else: from inspect import getfullargspec as argspec     # Python 3 arg inspection.

#%% Code for setting up a system settings class containing module-wide variables.

class SystemSettings(object):
    """ Stores all 'system' variables used by the Atomica module. """
    
    CODEBASE_DIRNAME = "atomica"
    CONFIG_LOGGER_FILENAME = "logging.ini"
    CONFIG_FRAMEWORK_FILENAME = "format_framework.ini"
    CONFIG_DATABOOK_FILENAME = "format_databook.ini"
    CONFIG_LIST_SEPARATOR = ","
    
    LOGGER_DEBUG_OUTPUT_PATH = "./previous_session.log"
    
    STRUCTURE_KEY_DATA = "databook"
    STRUCTURE_KEY_FRAMEWORK = "framework_file"

    FRAMEWORK_DEFAULT_TYPE = "example"
    DATABOOK_DEFAULT_TYPE = "standard"
    
    DEFAULT_SPACE_LABEL = " "
    DEFAULT_SPACE_NAME = "_"
    DEFAULT_SEPARATOR_LABEL = " - "
    DEFAULT_SEPARATOR_NAME = "_"
    DEFAULT_SYMBOL_YES = "y"
    DEFAULT_SYMBOL_NO = "n"
    DEFAULT_SYMBOL_INAPPLICABLE = "N.A."
    DEFAULT_SYMBOL_OR = "OR"
    DEFAULT_SUFFIX_PLURAL = "s"

#%% Code for determining module installation directory.

# Tool path
def atomicaPath(subdir=None, trailingsep=True):
    ''' Returns the parent path of the Atomica module. If subdir is not None, include it in the path '''
    import os
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    if subdir is not None:
        if not isinstance(subdir, list): subdir = [subdir] # Ensure it's a list
        tojoin = [path] + subdir
        if trailingsep: tojoin.append('') # This ensures it ends with a separator
        path = os.path.join(*tojoin) # e.g. ['/home/optima', 'tests', '']
    return path

#%% Code for creating a directory if it does not exist.

def prepareFilePath(file_path): # CK: duplicates makefilepath in sciris.utils
    """
    If a file path specifies directories that do not exist, an error will be thrown.
    This function ensures that a file can be created in the desired location.
    """
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        logger.warning("Directory '{0}' does not exist and is being constructed.".format(directory))
        os.makedirs(directory)

#%% Code for setting up a logger.

logging.config.fileConfig(atomicaPath(subdir=SystemSettings.CODEBASE_DIRNAME)+SystemSettings.CONFIG_LOGGER_FILENAME, 
                          defaults={"log_filename": "{0}".format(SystemSettings.LOGGER_DEBUG_OUTPUT_PATH)})
logger = logging.getLogger("atomica")

#%% Code for an exception specific to Atomica.

class OptimaException(Exception): # CK: needs to be renamed
    """ A wrapper class to allow for Atomica-specific exceptions. """
    def __init(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

#%% Code for timestamping function/method usage.

def logUsage(undecoratedFunction):
    """ Logs the usage of a function or method. """
    def logUsageDecoratedFunction(*args,**kwargs):    
        """ Timestamps and times an undecorated function call. """
        # If the function is unbound, logging information is limited.
        class_prefix = ""
        instance_name = ""
        descriptor = "function"
        # If the function is actually a method, the first argument is the owning class instance.
        # Extract class name and instance name, if the latter exists, for logging purposes.
        if inspect.ismethod(undecoratedFunction):
            class_prefix = undecoratedFunction.im_class.__name__ + "."
            try: instance_name = args[0].name       # Method 'getName' avoided due to recursion.
            except: pass
            descriptor = "method"
        # Time and process the undecorated function, noting whether an exception is raised.
        time_before = datetime.datetime.now()
        logger.debug("   Entering {0}:   {1}".format(descriptor, class_prefix + undecoratedFunction.__name__))
        if not instance_name == "":
            logger.debug("   {0} name: {1}".format(class_prefix.rstrip('.'), instance_name))
        exception_raised = False
        e_saved = None
        try: x = undecoratedFunction(*args,**kwargs)
        except Exception as e:
            exception_raised = True
            e_saved = e     # Make the exception persist beyond the try-except block.
        time_after = datetime.datetime.now()
        time_elapsed = time_after - time_before
        if exception_raised: logger.debug("   Abandoning {0}: {1}".format(descriptor, class_prefix + undecoratedFunction.__name__))
        else: logger.debug("   Exiting {0}:    {1}".format(descriptor, class_prefix + undecoratedFunction.__name__))
        if not instance_name == "":
            logger.debug("   {0} name: {1}".format(class_prefix.rstrip('.'), instance_name))
        logger.debug("   Time spent in {0}: {1}".format(descriptor, time_elapsed))
        # If an exception was raised while processing the function, it should be delayed no longer.
        if exception_raised: raise e_saved
        return x                                             
#    return logUsageDecoratedFunction
    return undecoratedFunction
    
#%% Code for validating function argument types.

class ArgumentTypeError(ValueError):
    """ Raised when the argument type of a function is incorrect. """
    def __init__(self, func_name, arg_name, accepted_arg_type, func_sig = ""):
        self.error = "Value supplied to arg '{0}' in '{1}{2}' was not of type '{3}'.".format(arg_name, func_name, func_sig,
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
    def checkAccepts(undecoratedFunction, *args, **kwargs):
        # Check if the first argument of function signature is 'self', thus denoting a method.
        # If the undecorated function is a method, skip self when checking arg types.
        sig = tuple(argspec(undecoratedFunction).args)
        arg_start = 0
        if len(sig) > 0:
            arg_start = int(sig[0] == 'self')
        arg_count = arg_start
        try:
            for (arg, accepted_type) in zip(args[arg_start:], arg_types):
                if accepted_type == str: accepted_type = six.string_types
                if not isinstance(arg, accepted_type):
                    raise ArgumentTypeError(func_name = undecoratedFunction.__name__,
                                            arg_name = sig[arg_count], 
                                            accepted_arg_type = accepted_type,
                                            func_sig = str(sig).replace("'","").replace(",)",")"))
                arg_count += 1
        except ArgumentTypeError as e:
            logger.exception(e.message)
            raise
        return undecoratedFunction(*args, **kwargs)
    return checkAccepts

#%% Code for validating function return types.

class ReturnTypeError(ValueError):
    """ Raised when the return type of a function is incorrect. """
    def __init__(self, func_name, accepted_return_type, func_sig = ""):
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
    def checkReturns(undecoratedFunction, *args, **kwargs):
        # Check if the first argument of function signature is 'self', thus denoting a method.
        # If the undecorated function is a method, skip self when checking arg types.
        sig = tuple(argspec(undecoratedFunction).args)
        return_value = undecoratedFunction(*args, **kwargs)
        try:    
            if not type(return_value) == return_type:
                raise ReturnTypeError(func_name = undecoratedFunction.__name__,
                                      accepted_return_type = return_type,
                                      func_sig = str(sig).replace("'","").replace(",)",")"))
        except ReturnTypeError as e:
            logger.exception(e.message)
            raise
        return return_value
    return checkReturns

#%% Code for conveniently applying a decorator to each method in a class.

def applyToAllMethods(function):
    """ Decorator that takes a function argument and applies it to all methods of a class. """
    def classDecorator(undecorated_class):
        """
        The true underlying decorator, i.e. with no arguments in the signature, applied to an undecorated class.
        The function argument of the wrapper propagates into the undecorated class.
        """        
        for method_name, method in inspect.getmembers(undecorated_class, inspect.ismethod):
            setattr(undecorated_class, method_name, function(method))                
        return undecorated_class
    return classDecorator

#%% String utility functions.

def displayName(name, as_title = False):
    """ Minor function to convert name into text display format. """
    text = name
    if as_title: text = text.title()
    return text.replace(SystemSettings.DEFAULT_SPACE_NAME, SystemSettings.DEFAULT_SPACE_LABEL)