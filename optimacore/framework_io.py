# -*- coding: utf-8 -*-
"""
Optima Core project-framework input/output file.
Contains functions to create, import and export framework files.
This is primarily referenced by the ProjectFramework object.
"""

from optimacore.system import logger, logUsage, accepts, getOptimaCorePath
from optimacore.system import SystemSettings

import xlsxwriter as xw
try: import ConfigParser as configparser    # Python 2.
except ImportError: import configparser     # Python 3.
        
@logUsage
@accepts(configparser.ConfigParser,str,str)
def getConfigValue(config, section, option, list_form = False, mute_warnings = False):
    """
    Get the value of an option of a section within a parsed configuration file.
    If the list form option is set as true, the return value is a list of strings, otherwise the value is a string.
    Lists are broken apart by a separator set in system settings, with all values being stripped of surrounding whitespace.
    """
    value = None
    if not config.has_section(section):
        if not mute_warnings: logger.warn("Framework configuration file has no section with label '{0}'.".format(section))
        raise configparser.NoSectionError(section)
    if not config.has_option(section, option):
        if not mute_warnings: logger.warn("Framework configuration file, section '{0}', has no option with label '{1}'.".format(section,option))
        raise configparser.NoOptionError(section,option)
    if list_form:
        value = [item.strip() for item in config.get(section, option).strip().split(SystemSettings.CONFIG_FRAMEWORK_SEPARATOR)]
    else:
        value = config.get(section, option).strip()
    return value

@logUsage
@accepts(str)
def createFrameworkTemplate(framework_path, template_type = SystemSettings.FRAMEWORK_DEFAULT_TYPE,
                                            num_pop_attributes = None,
                                            num_categories_per_classification = None):
    """
    Creates a template framework Excel file.
    
    Inputs:
        framework_path (str)                    - Directory path for intended framework template.
                                                  Must include filename with extension '.xlsx'.
        template_type (str)                     - A string that denotes the type of template, e.g. what pages to include.
                                                  This acts as a preset id, which instructs what default values in file construction should be.
                                                  A user can specify kwargs to overwrite the template defaults, but the template type denotes baseline values.
        num_pop_attributes (int)                - The number of attributes to include in a population-types page.
        num_options_per_pop_attribute (int)     - The number of options to provide for each attribute.
    """
    # Parse through a framework configuration file.
    cp = configparser.ConfigParser()
    cp.read(getOptimaCorePath(subdir="optimacore")+SystemSettings.CONFIG_FRAMEWORK_FILENAME)
    
    # Get the set of keys that refer to framework-file pages and raise an error for the process if these are unavailable.
    try: framework_keys = getConfigValue(config = cp, section = "pages", option = "keys", list_form = True)
    except Exception:
        logger.exception("Framework template file cannot be constructed.")
        raise
    
    # Create a template file and non-variable standard formats.
    logger.info("Creating a template framework file: {0}".format(framework_path))
    framework_file = xw.Workbook(framework_path)
    format_bold = framework_file.add_format({"bold": True})
    
    # Establish framework-file format defaults by importing them from system settings.
    # Each key requires a corresponding system setting variable or an AttributeError will be thrown.
    format_keys = ["column_width","comment_xscale","comment_yscale"]
    format_values_filewide = {}
    for format_key in format_keys:
        exec("format_values_filewide[\"{0}\"] = SystemSettings.EXCEL_IO_DEFAULT_{1}".format(format_key, format_key.upper()))
    
    # Iterate through framework-file keys and generate pages if possible.
    for framework_key in framework_keys:
        try: page_name = getConfigValue(config = cp, section = "page_"+framework_key, option = "name")
        except:
            logger.warn("Skipping page construction for key '{0}'.".format(framework_key))
            continue
        logger.info("Creating page: {0}".format(page_name))
        framework_page = framework_file.add_worksheet(page_name)
        
        # Check if the page details any columns to construct.
        try: column_keys = getConfigValue(config = cp, section = "page_"+framework_key, option = "column_keys", list_form = True)
        except:
            logger.warn("Accordingly, page '{0}' seems to have no column details. Continuing process.".format(page_name))
            continue
        
        # Propagate file-wide formats to page-wide formats.
        # Overwrite page-wide formats if specified in config file.
        format_values_pagewide = {}
        for format_key in format_keys:
            format_values_pagewide[format_key] = format_values_filewide[format_key]
            try: 
                value_overwrite = float(getConfigValue(config = cp, section = "page_"+framework_key, option = format_key, mute_warnings = True))
                format_values_pagewide[format_key] = value_overwrite
            except ValueError: logger.warn("Framework configuration file for page-key '{0}' has an entry for '{1}' " 
                                           "that cannot be converted to a float. Using default.".format(framework_key, format_key))
            except: pass
        
        # Iterate through the column keys of a page and generate columns if possible.
        # The bare minimum of a column is a header name.
        col = 0
        for column_key in column_keys:
            try: header_name = getConfigValue(config = cp, section = "column_"+column_key, option = "name")
            except:
                logger.warn("Skipping column construction for key '{0}' in page '{1}'.".format(column_key, page_name))
                continue
            framework_page.write(0, col, header_name, format_bold)
            
            # Propagate page-wide formats to column-wide formats.
            # Overwrite column-wide formats if specified in config file.
            format_values_colwide = {}
            for format_key in format_keys:
                format_values_colwide[format_key] = format_values_pagewide[format_key]
                try: 
                    value_overwrite = float(getConfigValue(config = cp, section = "column_"+column_key, option = format_key, mute_warnings = True))
                    format_values_colwide[format_key] = value_overwrite
                except ValueError: logger.warn("Framework configuration file for page-key '{0}', column-key '{1}', has an entry for '{2}' " 
                                               "that cannot be converted to a float. Using default.".format(framework_key, column_key, format_key))
                except: pass
            
            # Comment the column header if a comment is available in the configuration file.
            try: 
                header_comment = getConfigValue(config = cp, section = "column_"+column_key, option = "comment")
                framework_page.write_comment(0, col, header_comment, 
                                             {"x_scale": format_values_colwide["comment_xscale"], 
                                              "y_scale": format_values_colwide["comment_yscale"]})
            except: pass
            
            # Adjust column size and continue to the next one.
            framework_page.set_column(col, col, format_values_colwide["column_width"])
            col += 1

    return
    