# -*- coding: utf-8 -*-
"""
Optima Core system functionality file.
Contains important functions that are used throughout Optima Core.
Examples include logging, type-checking, etc.
"""

import datetime
import inspect

class SystemSettings(object):
    """ Stores all 'system' variables used by the Optima Core module. """
    
    LOGGER_INCLUDES_DATE = False
    


def logUsage(undecoratedFunction):
    """ Logs the usage of a function or method. """
    def decoratedFunction(*args,**kwargs):    
        """ Timestamps and times an undecorated function call. """
        # If the function is unbound, logging information is limited.
        indent = " - "
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
        output_time_before = time_before
        if not SystemSettings.LOGGER_INCLUDES_DATE:
            output_time_before = datetime.datetime.time(time_before)
        print "{0}{1}Entering {2}: {3}".format(output_time_before, indent, descriptor, 
                                               class_prefix + undecoratedFunction.__name__)
        if not instance_name == "":
            print "{0:{1}}{2} instance: {3}".format("", len(str(output_time_before) + indent), 
                                                    class_prefix.rstrip('.'), instance_name)     
        x = undecoratedFunction(*args,**kwargs)                
        time_after = datetime.datetime.now()
        time_elapsed = time_after - time_before
        output_time_after = time_after
        if not SystemSettings.LOGGER_INCLUDES_DATE:
            output_time_after = datetime.datetime.time(time_after)
        print "{0}{1}Exiting {2}:  {3}".format(output_time_after, indent, descriptor, 
                                               class_prefix + undecoratedFunction.__name__)
        if not instance_name == "":
            print "{0:{1}}{2} instance: {3}".format("", len(str(output_time_after) + indent), 
                                                    class_prefix.rstrip('.'), instance_name)  
        print "{0:{1}}Time spent in {2}: {3}".format("", len(str(output_time_after) + indent),
                                                     descriptor, time_elapsed)     
        return x                                             
    return decoratedFunction
    
    

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