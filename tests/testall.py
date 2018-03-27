#!/usr/bin/env python

from sciris.tests import testfiles

filelist = [
'testworkflow',
]

testfiles(path='.', filelist=filelist)

from atomica.defaults import demo
P = demo(0)