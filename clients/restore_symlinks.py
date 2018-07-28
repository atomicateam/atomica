#!/usr/bin/env python

# Restores all symlinks that might be destroyed on Windows.

import os

dryrun = False
folders = ['cascade', 'tb']
links = ['node_modules', 'package.json', 'static']

for folder in folders:
    for link in links:
        cmd1 = 'rm %s' % folder + os.sep + link
        cmd2 = 'ln -s ' + os.pardir + os.sep + 'common' + os.sep + link + ' ' +  folder + os.sep + link
        print(cmd1)
        print(cmd2)
        if not dryrun:
            os.system(cmd1)
            os.system(cmd2)
