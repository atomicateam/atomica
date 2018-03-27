# -*- coding: utf-8 -*-
"""
Optima Core parser file.
Contains functionality for parsing configuration files.
"""

from atomica.system import SystemSettings as SS

from atomica.system import logUsage, accepts, logger

import six

if six.PY2: import ConfigParser as configparser    # Python 2 configuration file parsing.
else: import configparser                          # Python 3 configuration file parsing.


@logUsage
@accepts(configparser.ConfigParser,str,str)
def getConfigValue(config, section, option, list_form = False, mute_warnings = False):
    """
    Returns the value of an option of a section within a parsed configuration file.
    If the list form option is set as true, the return value is a list of strings, otherwise the value is a string.
    Lists are broken apart by a separator set in system settings, with all values being stripped of surrounding whitespace.
    """
    value = None
    if not config.has_section(section):
        if not mute_warnings: logger.warning("Configuration file has no section with label '{0}'.".format(section))
        raise configparser.NoSectionError(section)
    if not config.has_option(section, option):
        if not mute_warnings: logger.warning("Configuration file, section '{0}', has no option with label '{1}'.".format(section,option))
        raise configparser.NoOptionError(section,option)
    if list_form:
        value = [item.strip() for item in config.get(section, option).strip().split(SS.CONFIG_LIST_SEPARATOR)]
    else:
        value = config.get(section, option).strip()
    return value

def loadConfigFile(undecorated_class):
    """
    Decorator that instructs a class to do an initial update of its attributes according to a configuration file.
    This is done at the import stage; failure means the class starts off incorrect and an import error is thrown.
    """
    try: undecorated_class.reloadConfigFile()
    except:
        logger.exception("Because a relevant configuration file failed to load, the initial state of class '{0}' is invalid. "
                         "Import failed.".format(undecorated_class.__name__))
        raise ImportError
    return undecorated_class