#!/usr/bin/env python
# Install any missing client modules. Note -- shared by all clients,
# but located here for simplicity.
# Version: 2018jul16

import os
os.chdir(os.path.join(os.pardir, 'common'))
os.system('npm install')
