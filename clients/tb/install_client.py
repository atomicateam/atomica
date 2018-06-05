#!/usr/bin/env python
# Install any missing client modules.
import os
thisdir = os.getcwd()
os.chdir('..'+os.sep+'client')
os.system('npm install')
os.chdir(thisdir)