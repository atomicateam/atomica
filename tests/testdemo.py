"""
Version:
"""


#%%
import numpy as np
import sciris as sc
import atomica.ui as au

to_run = ['quick','full'][0] 
run_scens = True
run_optim = True
maxtime   = 10
txtcolor  = 'blue'

T = sc.tic()
np.seterr(all='raise') # We don't expect numerical warnings in any of the demos

#%%
if to_run == 'quick':
    P = au.demo(which='tb')
    if run_scens:
            if len(P.scens): P.run_scenarios()
            else:             sc.colorize('green', 'No scenarios found')
    if run_optim:
        if len(P.optims): P.run_optimization(maxtime=maxtime)
        else:             sc.colorize('green', 'No optimizations found')


#%%
if to_run == 'full':
    import atomica as at
    frameworkoptions = at.defaults.default_framework(show_options=True)
    projectoptions   = at.defaults.default_project(show_options=True)
    nframes = len(frameworkoptions)
    nprojs = len(projectoptions)
    sc.blank()
    print('Testing %i frameworks and %i projects' % (nframes, nprojs))
    sc.blank()
    
    Flist = []
    for f,fkey,fname in frameworkoptions.enumitems():
        sc.colorize(txtcolor, 'Creating framework "%s" (%i/%i)...' % (fname, f+1, nframes))
        F = au.demo(which=fkey, kind='framework')
        Flist.append(F)
    
    Plist = []
    for p,pkey,pname in projectoptions.enumitems():
        sc.blank()
        sc.colorize(txtcolor, 'Creating project "%s" (%i/%i)...' % (pname, p+1, nprojs))
        P = au.demo(which=pkey, kind='project')
        if run_scens:
            if len(P.scens): P.run_scenarios()
            else:             sc.colorize('green', 'No scenarios found')
        if run_optim:
            if len(P.optims): P.run_optimization(maxtime=maxtime)
            else:             sc.colorize('green', 'No optimizations found')
        Plist.append(P)
    
    
sc.toc(T)
print('Done.')
    