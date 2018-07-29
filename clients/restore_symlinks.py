#!/usr/bin/env python

# Restores all symlinks that might be destroyed on Windows.
# Hard-coded to os.sep = / since symlinks won't work otherwise anyway!

import os

dryrun = False
folders = ['cascade', 'tb']
links = ['node_modules', 'package.json', 'static']
vueapp = 'src/components/app'

for folder in folders:
    for link in links:
        cmd1 = 'rm %s' % folder + '/' + link
        print(cmd1)
        if not dryrun:
            os.system(cmd1)

for folder in folders:
    for link in links:
        cmd2 = 'ln -s ../common/' + link + ' ' +  folder + '/' + link
        print(cmd2)
        if not dryrun:
            os.system(cmd2)

for folder in folders:
    cmd3 = 'ln -s ' + vueapp + ' ' + folder+'/vueapp'
    print(cmd3)
    if not dryrun:
        os.system(cmd3)

