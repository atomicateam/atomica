#!/usr/bin/env python

from sciris.tests import testfiles

filelist = [
'testworkflow',
]

testfiles(path='.', filelist=filelist)

# TEMPORARY -- try to create a demo project
from atomica.defaults import demo
P = demo(0)
