"""
Defines some defaults for Atomica projects
Version: 2018mar27
"""

from atomica.system import logger
from atomica.framework import ProjectFramework
from atomica.project import Project
from atomica.system import AtomicaException
from atomica.system import atomica_path


def default_programs(project, addcostcovpars=False, addcostcovdata=False, filterprograms=None):
    """ Make some default programs"""
    pass


def default_progset(project, addcostcovpars=False, addcostcovdata=False, filterprograms=None):
    """ Make a default programset"""
    pass

#def defaultproject(which='sir', add_progs=True, verbose=2, do_run=True, **kwargs):
#    ''' 

def default_project(which='sir', **kwargs):
    """
    Options for easily creating default projects based on different spreadsheets, including
    program information -- useful for testing
    Version: 2018mar27
    """

    ##########################################################################################################################
    ## SIR
    ##########################################################################################################################
    
    if which=='sir':
        printv('Creating SIR project...', 2, verbose)
        
        F = ProjectFramework(name=which, filepath=atomica_path(['tests','frameworks'])+'framework_sir.xlsx')
        P = Project(framework=F, databook_path=atomica_path(['tests','databooks'])+"databook_sir.xlsx", do_run=do_run)
        
        
    ##########################################################################################################################
    ## TB
    ##########################################################################################################################
    
    elif which=='tb':
        printv('Creating TB project...', 2, verbose)
        
        F = ProjectFramework(name=which, filepath=atomica_path(['tests','frameworks'])+'framework_tb.xlsx')
        P = Project(framework=F, databook_path=atomica_path(['tests','databooks'])+"databook_tb.xlsx", do_run=do_run)
#        F = ProjectFramework(name=which, frameworkfilename=atomica_path(['tests', 'frameworks']) + 'framework_sir.xlsx')
#        P = Project(framework=F, databook=atomica_path(['tests', 'databooks']) + "databook_sir.xlsx")
        
    else:
        raise AtomicaException("Default project type '{0}' not understood; choices are 'sir'.".format(which))
    return P


def demo(doplot=False, **kwargs):
    """ Create a simple demo project"""
    P = default_project(**kwargs)
    if doplot:
        logger.warning("Plotting not implemented yet.")
    return P
