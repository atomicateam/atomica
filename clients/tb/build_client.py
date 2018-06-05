#!/usr/bin/env python
import os
thisdir = os.getcwd()
os.chdir('..'+os.sep+'client')
os.system('npm run build')
os.chdir(thisdir)