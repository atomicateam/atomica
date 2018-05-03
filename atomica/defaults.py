"""
Defines some defaults for Atomica projects
Version: 2018mar27
"""

from sciris.core import printv # TODO replace
from atomica.framework import ProjectFramework
from atomica.project import Project
from atomica.system import AtomicaException
from atomica.system import atomica_path


def defaultprograms(project, addcostcovpars=False, addcostcovdata=False, filterprograms=None):
    ''' Make some default programs'''
    pass
    
def defaultprogset(P, addcostcovpars=False, addcostcovdata=False, filterprograms=None, verbose=2):
    ''' Make a default programset'''
    pass

def defaultproject(which='sir', add_progs=True, verbose=2, do_run=True, **kwargs):
    ''' 
    Options for easily creating default projects based on different spreadsheets, including
    program information -- useful for testing 
    Version: 2018mar27
    '''
    
    ##########################################################################################################################
    ## SIR
    ##########################################################################################################################
    
    if which=='sir':
        printv('Creating SIR project...', 2, verbose)
        
        F = ProjectFramework(name=which, file_path=atomica_path(['tests','frameworks'])+'framework_sir.xlsx')
        P = Project(framework=F, databook_path=atomica_path(['tests','databooks'])+"databook_sir.xlsx", do_run=do_run)
        
        
    ##########################################################################################################################
    ## TB
    ##########################################################################################################################
    
    elif which=='tb':
        printv('Creating TB project...', 2, verbose)
        
        F = ProjectFramework(name=which, file_path=atomica_path(['tests','frameworks'])+'framework_tb.xlsx')
        P = Project(framework=F, databook_path=atomica_path(['tests','databooks'])+"databook_tb.xlsx", do_run=do_run)
        
    else:
        raise AtomicaException('Default project type "%s" not understood: choices are "sir"' % which)
    return P



def demo(do_run=True, do_plot=False, verbose=2, **kwargs):
    ''' Create a simple demo project'''
    P = defaultproject(**kwargs)
    if do_plot: 
        printv('Plotting not implemented yet.', 2, verbose)
    return P
