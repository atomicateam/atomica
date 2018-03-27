#!/usr/bin/env python

from sciris.tests import testfiles

filelist = [
'loadframework',
'loadproject',
'makedatabook',
'makeframeworkfile',
'makeframework',
'makeproject',
'readworkbook',
'saveframework',
'saveproject',
]

testfiles(path='./scripts', filelist=filelist)