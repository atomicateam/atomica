#!/usr/bin/env python

"""
TESTALL

Run all tests in the scripts folder

To run everything, either set everything = True below, or at the command line type

./testall everything

Version: 2018mar27 by romesh
Version: 2018jan04 by cliffk
"""

## Initialization
from time import time as TIME # Use caps to distinguish 'global' variables
from sys import exc_info as EXC_INFO, argv as ARGV
from glob import glob as GLOB
import os
import sys
import shutil

## ADD DIRECTORIES
rootdir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..','..'))
sys.path.append(os.path.join(rootdir,'optimacore'))
sys.path.append(os.path.join(rootdir,'optima'))
testdir = os.path.join(rootdir,'optimacore','tests')
tempdir = os.path.join(testdir,'temp')

MASTER = GLOB(os.path.join(testdir,'scripts','*.py'))


if len(ARGV)>1:
    MASTER=[os.path.join(testdir,'scripts',ARGV[1])]

def runscript(fname):
    exec(open(fname).read()) # Run the test!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

## Run the tests in a loop
VERYSTART = TIME()
FAILED = []
SUCCEEDED = []
for TEST in MASTER:
    try:
        THISSTART = TIME()
        print('\n'*10+'#'*200)
        print('NOW RUNNING: %s' % TEST)
        print('#'*200+'\n'*3)
        runscript(TEST)
        SUCCEEDED.append({'test':TEST, 'time':TIME()-THISSTART})
    except:
        FAILED.append({'test':TEST, 'msg':EXC_INFO()[1]})


print('\n'*5)
if len(FAILED):
    print('The following %i/%i tests failed :(' % (len(FAILED), len(MASTER)))
    for FAIL in FAILED: print('  %s: %s' % (FAIL['test'], FAIL['msg']))
else:
    print('All %i tests passed!!! You are the best!!' % len(MASTER))
    for SUCCESS in SUCCEEDED: print('  %s: %0.1f s' % (SUCCESS['test'], SUCCESS['time']))
    shutil.rmtree(tempdir)
print('Elapsed time: %0.1f s.' % (TIME()-VERYSTART))