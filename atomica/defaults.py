"""
Defines some defaults for Atomica projects
Version: 2018mar27
"""

from sciris.core import printv # TODO replace
from atomica.framework import ProjectFramework
from atomica.project import Project
from atomica.system import OptimaException # TODO rename
from atomica import atomicapath


def defaultprograms(project, addcostcovpars=False, addcostcovdata=False, filterprograms=None):
    ''' Make some default programs'''
    pass
    
def defaultprogset(P, addcostcovpars=False, addcostcovdata=False, filterprograms=None, verbose=2):
    ''' Make a default programset'''
    pass

def defaultproject(which='sir', verbose=2, **kwargs):
    ''' 
    Options for easily creating default projects based on different spreadsheets, including
    program information -- useful for testing 
    Version: 2018mar27
    '''
    
    ##########################################################################################################################
    ## Simple
    ##########################################################################################################################
    
    if which=='sir':
        printv('Creating an SIR epidemic project...', 2, verbose)
        
        F = ProjectFramework(name=which, frameworkfilename=atomicapath(['tests','frameworks'])+'framework_sir.xlsx')
        P = Project(framework=F, databook=atomicapath(['tests','databooks'])+"databook_sir.xlsx")
        
    else:
        raise OptimaException('Default project type "%s" not understood: choices are "sir"' % which)
    return P



def demo(doplot=False, verbose=2, **kwargs):
    ''' Create a simple demo project'''
    P = defaultproject(**kwargs)
    if doplot: 
        printv('Plotting not implemented yet.', 2, verbose)
    return P
