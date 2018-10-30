#!/usr/bin/env python

"""
TESTALL

Run all tests. It runs everything in the same namespace, but deletes variables that get
added along the way.

Version: 2018oct26
"""

## Initialization
from time import time as TIME # Use caps to distinguish 'global' variables
from sys import exc_info as EXC_INFO, argv as ARGV, exit
from glob import glob as GLOB
import os as OS


## Run the tests in a loop
VARIABLES = []
VERYSTART = TIME()
FAILED = []
SUCCEEDED = []
MASTER = GLOB(OS.path.dirname(OS.path.realpath(__file__))+OS.sep+'test_*.py') # Figure out the path -- adapted from defaults.py
for TEST in MASTER:
    try:
        THISSTART = TIME()
        VARIABLES = locals().keys() # Get the state before the test is run
        print('\n'*10+'#'*200)
        print('NOW RUNNING: %s' % TEST)
        print('#'*200+'\n'*3)
        exec(open(TEST).read()) # Run the test!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        SUCCEEDED.append({'test':TEST, 'time':TIME()-THISSTART})
        for KEY in locals().keys(): # Clean up -- delete any new variables added
            if KEY not in VARIABLES:
                print('       "%s" complete; deleting "%s"' % (TEST, KEY))
                exec('del '+KEY)
    except:
        FAILED.append({'test':TEST, 'msg':EXC_INFO()[1]})


print('\n'*5)
print('Total elapsed time: %0.1f s.' % (TIME()-VERYSTART))
for SUCCESS in SUCCEEDED: print('SUCCESS: %s: %0.1f s' % (SUCCESS['test'], SUCCESS['time']))
if len(FAILED):
    print('The following %i/%i tests failed :(' % (len(FAILED), len(MASTER)))
    for FAIL in FAILED: print('FAILURE: %s: %s' % (FAIL['test'], FAIL['msg']))
    exit(1) # Exit with nonzero status to flag that everything was not OK
else:
    print('All %i tests passed!!! You are the best!!' % len(MASTER))
    exit(0)