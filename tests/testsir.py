# -*- coding: utf-8 -*-
"""
Tests the basic functionality of Core
Created on Fri Mar 23 16:37:15 2018
"""

## TEMPORARY IMPORTS
from optima import odict, saveobj, loadobj
from optima import tic, toc, blank
#from numpy import array

## IMPORTS
from optimacore.project import Project
from optimacore.workbook_export import writeWorkbook
from optimacore.system import SystemSettings as SS
from optimacore.framework import ProjectFramework
from optimacore.workbook_export import makeInstructions
from optimacore.project_settings import ProjectSettings

## DEFINE WHAT TO RUN
torun = [
         'makeframeworkfile',
         'makeframework',
         'saveframework',
         'loadframework',
#         'makedatabook',
         'makeproject',
         ]

def done(t=0):
    print('Done.')
    toc(t)
    blank()

blank()
print('Running tests:')
for i,test in enumerate(torun): print(('%i.  '+test) % (i+1))
blank()



##############################################################################
## The tests
##############################################################################

T = tic()

### Make a framework file
if 'makeframeworkfile' in torun:

    # First, generate an "Instructions" object which allows you to specify details of the framework file. Question, why isn't there an easier way to do this??? I should be able to pass in a dictionary to writeWorkbook.
    framework_instructions, use_instructions = makeInstructions(framework=None, data=None, workbook_type=SS.STRUCTURE_KEY_FRAMEWORK)
    framework_instructions.num_items = odict([('popatt', 4),        # Set the number of population attributes (not currently used)
                                              ('par', 10),          # Set the number of parameters
                                              ('comp', 4),          # Set the number of compartments
                                              ('popopt', 3),        # Set the number of ... ?
                                              ('progatt', 3),       # Set the number of program attributes (not current used) - what's the purpose of this?
                                              ('charac', 10),       # Set the number of characteristics, i.e., results
                                              ('progtype', 7), ])   # Set the number of program types - question, can we get rid of this?
    
    writeWorkbook(workbook_path="./frameworks/framework_test.xlsx", framework=None, data=None, instructions=framework_instructions, workbook_type=SS.STRUCTURE_KEY_FRAMEWORK)


### Make a framework by importing a framework file, then optionally save it
if 'makeframework' in torun:
    F = ProjectFramework(frameworkfilename="./frameworks/framework_sir.xlsx")
    
    # Save the framework object
    if 'saveframework' in torun:
        F.save('testframework.frw')
        
# Load a framework object
if 'loadframework' in torun:
    F = loadobj('testframework.frw')
    
### Export a databook from a framework
if 'makedatabook' in torun:    
    databook_instructions, use_instructions = makeInstructions(framework=F, data=None, workbook_type=SS.STRUCTURE_KEY_DATA)
    databook_instructions.num_items = odict([('prog', 3),       # Set the number of programs
                                             ('pop', 1), ])     # Set the number of populations
    F.writeDatabook(filename="./databooks/databook_sir_blank.xlsx", data=None, instructions=databook_instructions)

### Initialise a project with data and a framework file
if 'makeproject' in torun:
    P = Project(framework=F, databook="./databooks/databook_sir.xlsx")
    # Note, P.runsim() currently returns interpolated parameters

### Make parameters, run the model, produce results, plot... 
# Note, data is in P.data.specs
# Step 1 -- transform this to something like a dataframe or list -- NOT DONE, SKIPPED FOR NOW
# Step 2 -- transform the parameters into Par objects & put them in a Parset -- DONE
# Step 3 -- make sure that interpolation works -- DONE, but breaks for timepars (only works for constants)
# Step 4 -- figure out where the model is, and run it
# Step 5 -- implement results class, figure out characteristics
# Step 6 -- calibration

print('\n\n\nDONE: ran %i tests' % len(torun))
toc(T)


