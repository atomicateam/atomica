"""
Defines some defaults for Atomica projects
Version: 2018mar27
"""

from .system import logger
from .framework import ProjectFramework
from .project import Project
from .system import AtomicaException
from .system import atomica_path


def default_programs(project, addcostcovpars=False, addcostcovdata=False, filterprograms=None):
    """ Make some default programs"""
    pass


def default_progset(project, addcostcovpars=False, addcostcovdata=False, filterprograms=None):
    """ Make a default programset"""
    pass


def default_project(which='sir', do_run=True, **kwargs):
    """
    Options for easily creating default projects based on different spreadsheets, including
    program information -- useful for testing
    Version: 2018mar27
    """

    #######################################################################################################
    # Simple
    #######################################################################################################

    if which == 'sir':
        logger.info("Creating an SIR epidemic project...")

        F = ProjectFramework(name=which, filepath=atomica_path(['tests', 'frameworks']) + 'framework_sir.xlsx')
        P = Project(framework=F, databook_path=atomica_path(['tests', 'databooks']) + "databook_sir.xlsx", do_run=do_run)

    elif which=='tb':
        logger.info("Creating a TB epidemic project...")
        
        F = ProjectFramework(name=which, filepath=atomica_path(['tests','frameworks'])+'framework_tb.xlsx')
        P = Project(framework=F, databook_path=atomica_path(['tests','databooks'])+"databook_tb.xlsx", do_run=do_run)

    elif which=='service':
        logger.info("Creating a disease-agnostic 5-stage service delivery cascade project...")
        
        F = ProjectFramework(name=which, filepath=atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx')
        P = Project(framework=F, databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=do_run)

    else:
        raise AtomicaException("Default project type '{0}' not understood; choices are 'sir', 'tb'.".format(which))
    return P


def demo(doplot=False, **kwargs):
    """ Create a simple demo project"""
    P = default_project(**kwargs)
    if doplot:
        logger.warning("Plotting not implemented yet.")
    return P
