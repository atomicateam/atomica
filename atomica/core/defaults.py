"""
Defines some defaults for Atomica projects
Version: 2018mar27
"""

from .system import logger
from .framework import ProjectFramework
from .project import Project
from .system import AtomicaException
from .system import atomica_path
import sciris.core as sc


def default_programs(project, addcostcovpars=False, addcostcovdata=False, filterprograms=None):
    """ Make some default programs"""
    pass


def default_progset(project, addcostcovpars=False, addcostcovdata=False, filterprograms=None):
    """ Make a default programset"""
    pass


def default_framework(which=None, show_options=False):
    
    options = sc.odict([
                    ('udt',      'Undiagnosed-diagnosed-treated'),       
                    ('usdt',     'Undiagnosed-screened-diagnosed-treated'),       
                    ('sir',      'SIR model'),       
                    # ('diabetes', 'Diabetes'),        
                    ('hypertension',  'Hypertension'),
                    ('service',  'Service delivery'),
                    ('hiv',      'HIV care cascade'),  
                    ('tb',       'Tuberculosis'),  
                    ])
                             
    if which is None:
        which = 'udt'
    if which not in options.keys():
        if which in options.values():
            which = options.keys()[options.values().index(which)]
        else:
            errormsg = '"%s" not found; must be in %s or %s' % (which, options.keys(), options.values())
            raise Exception(errormsg)
    label = options[which]
    if show_options:
        return options
    else:
        F = ProjectFramework(name=label, inputs=atomica_path(['tests', 'frameworks'])+"framework_" + which + ".xlsx")
    return F


def default_project(which=None, do_run=True, verbose=False, show_options=False, **kwargs):
    """
    Options for easily creating default projects based on different spreadsheets, including
    program information -- useful for testing
    Version: 2018mar27
    """
    
    options = sc.odict([
                    ('udt',      '1-population undiagnosed-diagnosed-treated cascade'),
                    ('usdt',     '1-population undiagnosed-screened-diagnosed-treated cascade'),
                    ('sir',      '1-population SIR model'),       
                    # ('diabetes', '1-population diabetes cascade'),        
                    ('service',  '1-population service delivery cascade'),
                    ('hypertension',  '4-population hypertension cascade (Malawi)'),
                    ('hiv',      '2-population HIV care cascade'), 
                    ('tb',       '14-population tuberculosis model'), 
                    ])
    
    if which is None:
        which = 'udt'
    if which not in options.keys():
        if which in options.values():
            which = options.keys()[options.values().index(which)]
        else:
            errormsg = '"%s" not found; must be in %s or %s' % (which, options.keys(), options.values())
            raise Exception(errormsg)
    
    if show_options:
        return options
    
    if which == 'sir':
        logger.info("Creating an SIR epidemic project...")

        framework_file = atomica_path(['tests', 'frameworks']) + 'framework_sir.xlsx'
        P = Project(framework=framework_file, databook_path=atomica_path(['tests', 'databooks']) + "databook_sir.xlsx", do_run=do_run)
        P.load_progbook(progbook_path=atomica_path(['tests','databooks'])+"progbook_sir.xlsx", make_default_progset=True, blh_effects=True)

    elif which=='tb':
        logger.info("Creating a TB epidemic project with programs...")
        if verbose: print('Loading framework')
        framework_file = atomica_path(['tests','frameworks'])+'framework_tb.xlsx'
        if verbose: print('Loading databook')
        P = Project(framework=framework_file, databook_path=atomica_path(['tests','databooks'])+"databook_tb.xlsx", do_run=do_run)
        if verbose: print('Loading progbook')
        P.load_progbook(progbook_path=atomica_path(['tests','databooks'])+"progbook_tb.xlsx", make_default_progset=True, blh_effects=False)
        if verbose: print('Creating scenarios')
        P.demo_scenarios() # Add example scenarios
        if verbose: print('Creating optimizations')
        P.demo_optimization() # Add optimization example
        if verbose: print('Done!')
    
    elif which=='service':
        logger.info("Creating a disease-agnostic 5-stage service delivery cascade project...")
        
        framework_file = atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx'
        P = Project(framework=framework_file, databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=do_run)

    elif which=='diabetes':
        logger.info("Creating a diabetes cascade project...")
        
        framework_file = atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx'
        P = Project(framework=framework_file, databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=do_run)

    elif which=='udt':
        logger.info("Creating a generic 3-stage disease cascade project...")
        
        if verbose: print('Loading framework')
        framework_file = atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx'
        if verbose: print('Loading databook')
        P = Project(framework=framework_file, databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=do_run)
        if verbose: print('Loading progbook')
        P.load_progbook(progbook_path=atomica_path(['tests','databooks'])+"progbook_"+which+".xlsx", make_default_progset=True, blh_effects=False)
        if verbose: print('Creating scenarios')
        P.demo_scenarios() # Add example scenarios
        if verbose: print('Creating optimizations')
        P.demo_optimization() # Add optimization example
        if verbose: print('Done!')

    elif which=='usdt':
        logger.info("Creating a generic 4-stage disease cascade project...")
        
        if verbose: print('Loading framework')
        framework_file = atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx'
        if verbose: print('Loading databook')
        P = Project(framework=framework_file, databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=do_run)
        if verbose: print('Loading progbook')
        P.load_progbook(progbook_path=atomica_path(['tests','databooks'])+"progbook_"+which+".xlsx", make_default_progset=True, blh_effects=False)
        if verbose: print('Creating scenarios')
        P.demo_scenarios() # Add example scenarios
        if verbose: print('Creating optimizations')
        P.demo_optimization() # Add optimization example
        if verbose: print('Done!')

    elif which=='hypertension':
        logger.info("Creating a hypertension cascade project based on Malawi...")
        
        if verbose: print('Loading framework')
        framework_file = atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx'
        if verbose: print('Loading databook')
        P = Project(framework=framework_file, databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=do_run)
        if verbose: print('Loading progbook')
        P.load_progbook(progbook_path=atomica_path(['tests','databooks'])+"progbook_"+which+".xlsx", make_default_progset=True, blh_effects=False)
        if verbose: print('Creating scenarios')
        P.demo_scenarios() # Add example scenarios
        if verbose: print('Creating optimizations')
        P.demo_optimization() # Add optimization example
        if verbose: print('Done!')

    elif which=='hiv':
        logger.info("Creating an HIV cascade project...")
        
        if verbose: print('Loading framework')
        framework_file = atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx'
        if verbose: print('Loading databook')
        P = Project(framework=framework_file, databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=do_run)
        if verbose: print('Loading progbook')
        P.load_progbook(progbook_path=atomica_path(['tests','databooks'])+"progbook_"+which+".xlsx", make_default_progset=True, blh_effects=False)
        if verbose: print('Creating scenarios')
        P.demo_scenarios() # Add example scenarios
        if verbose: print('Creating optimizations')
        P.demo_optimization() # Add optimization example
        if verbose: print('Done!')

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
