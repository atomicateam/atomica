# -*- coding: utf-8 -*-
"""
Optima Core can be imported in the following manner:

from optimacore import Project
or
import optimacore as op
or
from optimacore import *

License:

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


Version: 2017oct17
"""

# Specify the version, for the purposes of figuring out which version was used to create a project
from ._version import __version__, __updated__

# Print the license
optima_license = 'Optima Core %s (%s) -- (c) Optima Consortium' % (__version__, __updated__)
print(optima_license)

### Create an empty list to stored failed imports
##_failed = [] 
#
#
######################################################################################################################
#### Load helper functions/modules
######################################################################################################################
#
## General modules
#from uuid import uuid4 as uuid
#from copy import deepcopy as dcp
#
## Utilities -- import alphabetically
#from .utils import blank, boxoff, checkmem, checktype, compareversions, dataindex, dataframe, defaultrepr
#from .utils import drprint, findinds, findnearest, getdate, getfilelist, getvaliddata, gitinfo, indent, isnumber, isiterable
#from .utils import Link, LinkException, loadbalancer, makefilepath, objectid, objatt, objmeth, objrepr
#from .utils import odict, percentcomplete, perturb, printarr, printdata as pd, printv, printtologfile
#from .utils import promotetoarray, promotetolist, promotetoodict, quantile, runcommand, sanitize, scaleratio
#from .utils import sigfig, slacknotification, smoothinterp, tic, toc, today, vec2obj, sanitizefilename
#import utils as _utils; del utils
#
## Optimization algorithm
#from .asd import asd
#
## Interpolation
#from .pchip import pchip, plotpchip
#
## Color definitions
#from .colortools import alpinecolormap, bicolormap, gridcolors, vectocolor, shifthue
#import colortools as _colortools; del colortools
#
#
######################################################################################################################
#### Define debugging and exception functions/classes
######################################################################################################################
#
## Optima Path
#def optimapath(subdir=None, trailingsep=True):
#    ''' Returns the parent path of the Optima module. If subdir is not None, include it in the path '''
#    import os
#    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
#    if subdir is not None:
#        tojoin = [path, subdir]
#        if trailingsep: tojoin.append('') # This ensures it ends with a separator
#        path = os.path.join(*tojoin) # e.g. ['/home/optima', 'tests', '']
#    return path
#
## Debugging information
#def debuginfo(dooutput=False):
#    output = '\nOptima debugging info:\n'
#    output += '   Version: %s\n' % version
#    output += '   Branch:  %s\n' % gitinfo()[0]
#    output += '   SHA:     %s\n' % gitinfo()[1][:7]
#    output += '   Path:    %s\n' % optimapath()
#    if dooutput: 
#        return output
#    else: 
#        print(output)
#        return None
#
#class OptimaException(Exception):
#    ''' A tiny class to allow for Optima-specific exceptions -- define this here to allow for Optima-specific info '''
#    def __init__(self, errormsg, *args, **kwargs):
#        if isinstance(errormsg, basestring): errormsg = errormsg+debuginfo(dooutput=True) # If it's not a string, not sure what it is, but don't bother with this
#        Exception.__init__(self, errormsg, *args, **kwargs)
#
#
#
######################################################################################################################
#### Load Optima functions and classes
######################################################################################################################
#
## File I/O
#from .fileio import loadobj, saveobj, loadstr, dumpstr, loadpartable, loadtranstable, loaddatapars # CK: may want to tidy up
#import fileio as _fileio; del fileio
#
## Project settings
#from .settings import Settings, convertlimits, gettvecdt
#import settings as _settings; del settings
#
## Generate results -- import first because parameters use results
#from .results import Result, Resultset, Multiresultset, BOC, ICER, getresults
#import results as _results; del results
#
## Define the model parameters -- import before makespreadsheet because makespreadsheet uses partable to make a pre-filled spreadsheet
#from .parameters import Par, Dist, Constant, Metapar, Timepar, Popsizepar, Yearpar, Parameterset # Parameter and Parameterset classes
#from .parameters import makepars, makesimpars, applylimits, comparepars, comparesimpars, sanitycheck
#import parameters as _parameters; del parameters
#
## Create a blank spreadsheet
#try: from .makespreadsheet import makespreadsheet, makeprogramspreadsheet, default_datastart, default_dataend
#except Exception as E: _failed.append('makespreadsheet: %s' % E.__repr__())
#
## Load a completed a spreadsheet
#from .loadspreadsheet import loadspreadsheet, loadprogramspreadsheet
#
## Define and run the model
#from .model import model, runmodel
#
## Define the programs and cost functions
#from .programs import Program, Programset
#import programs as _programs; del programs
#
## Automatic calibration and sensitivity
#from .calibration import autofit
#import calibration as _calibration; del calibration
#
## Scenario analyses
#from .scenarios import Parscen, Budgetscen, Coveragescen, Progscen, runscenarios, makescenarios, baselinescenario, setparscenvalues, defaultscenarios
#import scenarios as _scenarios; del scenarios
#
## Optimization and ICER analyses
#from .optimization import Optim, defaultobjectives, defaultconstraints, optimize, multioptimize, outcomecalc, icers
#import optimization as _optimization; del optimization
#
## Plotting functions
#from .plotting import getplotselections, makeplots, plotepi, plotcascade, plotbudget, plotcoverage, plotallocations, plotcostcov, plotbycd4, ploticers, saveplots, reanimateplots, sanitizeresults, commaticks, SIticks
#import plotting as _plotting; del plotting
#
######################################################################################################################
#### Load high-level modules that depend on everything else
######################################################################################################################
#
## Load the code to load projects and portfolios (before defining them, oddly!)
#from .loadtools import migrate, loadproj, loadportfolio, optimaversion
#import loadtools as _loadtools; del loadtools
#changelog = _loadtools.setmigrations('changelog')
#
## Load batch functions (has to load projects, so has to come after migration)
#from .batchtools import batchautofit, batchBOC, reoptimizeprojects
#import batchtools as _batchtools; del batchtools
#
## Import the Project class that ties everything together
#from .project import Project
#import project as _project; del project
#
## Load the portfolio class (container of Projects), relies on batch functions, hence is here
#from .portfolio import Portfolio, makegeospreadsheet, makegeoprojects
#import portfolio as _portfolio; del portfolio
#
## Finally, load defaults
#from .defaults import defaultproject, defaultprogset, defaultprograms, demo
#import defaults as _defaults; del defaults
#
#
######################################################################################################################
#### Load optional Python GUI
######################################################################################################################
#
## Load high level GUI module
#try: 
#    from .gui import plotresults, pygui, plotpeople, plotpars, manualfit, showplots, loadplot, geogui
#    import gui as _gui; del gui
#except Exception as E: _failed.append('gui: %s' % E.__repr__())
#
#try: 
#    from .webserver import browser
#    import webserver as _webserver; del webserver
#except Exception as E: _failed.append('webserver: %s' % E.__repr__())
#
#
#if len(_failed): print('The following import errors were encountered:\n%s' % _failed)
#else: del _failed # If it's empty, don't bother keeping it