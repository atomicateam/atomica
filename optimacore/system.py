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
    
    
    

def logUsage(undecoratedFunction):
    """ Logs the usage of a function or method. """
    def decoratedFunction(*args,**kwargs):    
        """ Timestamps and times an undecorated function call. """
        datetime_before = datetime.datetime.now()  
        print "%s: Entering function '%s'" % (datetime_before, undecoratedFunction.__name__)                
        x = undecoratedFunction(*args,**kwargs)                
        datetime_after = datetime.datetime.now()                      
        print "%s: Exiting function '%s'\nTime elapsed: %s" % (datetime_after, 
                                                               undecoratedFunction.__name__, 
                                                               datetime_after - datetime_before)      
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