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


def default_framework(which=None, **kwargs):
    
    if which is None: which = 'tb'

    if   which == "sir":      args = {"num_comps":4, "num_characs":8, "num_pars":6}
    elif which == "tb":       args = {"num_comps":40, "num_characs":70, "num_pars":140}
    elif which == "diabetes": args = {"num_comps":13, "num_characs":9, "num_pars":16}
    elif which == "service":  args = {"num_comps":7, "num_characs":4, "num_pars":10}
#    path = ProjectFramework.create_template(path=tmpdir + "framework_" + test + "_blank.xlsx", **args)
    F = ProjectFramework(name=which.upper(), filepath=atomica_path(['tests', 'frameworks'])+"framework_" + which + ".xlsx")
    return F


def default_project(which=None, do_run=True, verbose=False, **kwargs):
    """
    Options for easily creating default projects based on different spreadsheets, including
    program information -- useful for testing
    Version: 2018mar27
    """
    
    if which is None: which = 'tb'

    #######################################################################################################
    # Simple
    #######################################################################################################

    if which == 'sir':
        logger.info("Creating an SIR epidemic project...")

        F = ProjectFramework(name=which, inputs=atomica_path(['tests', 'frameworks']) + 'framework_sir.xlsx')
        P = Project(framework=F, databook_path=atomica_path(['tests', 'databooks']) + "databook_sir.xlsx", do_run=do_run)

    elif which=='tb':
        logger.info("Creating a TB epidemic project with programs...")
        if verbose: print('Loading framework')
        F = ProjectFramework(name=which, inputs=atomica_path(['tests','frameworks'])+'framework_tb.xlsx')
        if verbose: print('Loading databook')
        P = Project(framework=F, databook_path=atomica_path(['tests','databooks'])+"databook_tb.xlsx", do_run=do_run)
        if verbose: print('Loading progbook')
        P.load_progbook(progbook_path=atomica_path(['tests','databooks'])+"progbook_tb.xlsx", make_default_progset=True)
        if verbose: print('Creating scenarios')
        P.demo_scenarios() # Add example scenarios
        if verbose: print('Creating optimizations')
        P.demo_optimization() # Add optimization example
        if verbose: print('Done!')
    
    elif which=='service':
        logger.info("Creating a disease-agnostic 5-stage service delivery cascade project...")
        
        F = ProjectFramework(name=which, inputs=atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx')
        P = Project(framework=F, databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=do_run)

    elif which=='diabetes':
        logger.info("Creating a diabetes cascade project...")
        
        F = ProjectFramework(name=which, inputs=atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx')
        P = Project(framework=F, databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=do_run)

    elif which=='udt':
        logger.info("Creating a generic 3-stage disease cascade project...")
        
        F = ProjectFramework(name=which, inputs=atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx')
        P = Project(framework=F, databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=do_run)

    else:
        raise AtomicaException("Default project type '{0}' not understood; choices are 'sir', 'tb'.".format(which))
    return P


def demo(which=None, kind=None, doplot=False, **kwargs):
    """ Create a simple demo project"""
    
    if kind is None: kind = 'project'
    
    if kind == 'framework': output = default_framework(which=which, **kwargs)
    elif kind == 'project': output = default_project(which=which, **kwargs)
    else:                   print('Sorry, no: %s' % kind)
    if doplot:
        logger.warning("Plotting not implemented yet.")
    return output
