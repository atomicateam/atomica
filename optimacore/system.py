# -*- coding: utf-8 -*-
"""
Optima Core system functionality file.
Contains important functions that are used throughout Optima Core.
Examples include logging, type-checking, etc.
"""

import logging.config
import os
import datetime
import inspect
import functools
import decorator

#%% Code for setting up a system settings class containing module-wide variables.

class SystemSettings(object):
    """ Stores all 'system' variables used by the Optima Core module. """
    
    LOGGER_DEBUG_OUTPUT_PATH = "./previous.log"

#%% Code for determining module installation directory.

def getOptimaCorePath(subdir = None, end_with_sep = True):
    """
    Returns the parent path of the Optima module.
    If subdir is not None, include it in the path.
    If end_with_sep is True, cap off the path with a separator (i.e. the path is to be appended by a filename).
    """
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    tojoin = [path]
    if subdir is not None: tojoin.append(subdir)
    if end_with_sep: tojoin.append('')
    path = os.path.join(*tojoin)
    return path

#%% Code for setting up a logger.

logging.config.fileConfig(getOptimaCorePath(subdir="optimacore")+"logging.ini", defaults={"log_filename": "{0}".format(SystemSettings.LOGGER_DEBUG_OUTPUT_PATH)})
logger = logging.getLogger("optimacore")

#%% Code for timestamping function and method usage.

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
        # Time and process the undecorated function.
        time_before = datetime.datetime.now()
        logger.debug("Entering {0}: {1}".format(descriptor, class_prefix + undecoratedFunction.__name__))
        if not instance_name == "":
            logger.debug("{0} name: {1}".format(class_prefix.rstrip('.'), instance_name)) 
        x = undecoratedFunction(*args,**kwargs)                
        time_after = datetime.datetime.now()
        time_elapsed = time_after - time_before
        logger.debug("Exiting {0}:  {1}".format(descriptor, class_prefix + undecoratedFunction.__name__))
        if not instance_name == "":
            logger.debug("{0} name: {1}".format(class_prefix.rstrip('.'), instance_name))
        logger.debug("Time spent in {0}: {1}".format(descriptor, time_elapsed))
        return x                                             
    return logUsageDecoratedFunction
    
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
    Ignores the zeroth argument if it is 'self', i.e. the function is a method.
    """
    def checkAccepts(undecoratedFunction):
        """
        The true underlying decorator, i.e. with no arguments in the signature, applied to an undecorated function.
        The types specified by the wrapper propagate into the undecorated function.
        """
        @functools.wraps(undecoratedFunction)
        def checkAcceptsDecoratedFunction(*args, **kwargs):
            # Check if the first argument of function signature is 'self', thus denoting a method.
            # If the undecorated function is a method, skip self when checking arg types.
            sig = tuple(inspect.getargspec(undecoratedFunction).args)
            print undecoratedFunction
            print inspect.getargspec(undecoratedFunction)
            arg_start = 0
            if len(sig) > 0:
                arg_start = int(sig[0] == 'self')
            arg_count = arg_start
            try:
                for (arg, accepted_type) in zip(args[arg_start:], arg_types):
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
        return checkAcceptsDecoratedFunction
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
    def checkReturns(undecoratedFunction):
        """
        The true underlying decorator, i.e. with no arguments in the signature, applied to an undecorated function.
        The types specified by the wrapper propagate into the undecorated function.
        """
        @functools.wraps(undecoratedFunction)
        def checkReturnsDecoratedFunction(*args, **kwargs):
            # Check if the first argument of function signature is 'self', thus denoting a method.
            # If the undecorated function is a method, skip self when checking arg types.
            sig = tuple(inspect.getargspec(undecoratedFunction).args)
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
        return checkReturnsDecoratedFunction
    return checkReturns

#%% Code for conveniently applying a decorator to each method in a class.

def applyToAllMethods(function):
    """ Decorator that takes a function argument and applies it to all methods of an instantiated class. """
    def classDecorator(undecorated_class_instance):
        """
        The true underlying decorator, i.e. with no arguments in the signature, applied to an undecorated class.
        The function argument of the wrapper propagates into the undecorated class.
        """        
        for method_name, method in inspect.getmembers(undecorated_class_instance, inspect.ismethod):
            setattr(undecorated_class_instance, method_name, function(method))                
        return undecorated_class_instance
    return classDecorator