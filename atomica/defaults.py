"""
Defines some defaults for Atomica projects
Version: 2018mar27
"""

from .framework import ProjectFramework
from .project import Project
from .system import AtomicaException, atomica_path, logger
import sciris as sc

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
                    ('diabetes', 'Diabetes'),        
                    ('hypertension',  'Hypertension'),
                    ('hypertension_dyn',  'Hypertension with demography'),
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


def default_project(which=None, do_run=True, addprogs=True, verbose=False, show_options=False, **kwargs):
    """
    Options for easily creating default projects based on different spreadsheets, including
    program information -- useful for testing
    Version: 2018mar27
    """
    
    options = sc.odict([ # ('diabetes', '1-population diabetes cascade'), 
                    ('udt',          'Undiagnosed-diagnosed-treated cascade (1 population)'),
                    ('usdt',         'Undiagnosed-screened-diagnosed-treated cascade (1 population)'),
                    ('sir',          'SIR model (1 population)'),       
                    ('diabetes',     'Diabetes cascade (1 population)'),        
                    ('service',      'Service delivery cascade (1 population)'),
                    ('hypertension', 'Hypertension cascade (4 populations)'),
                    ('hypertension_dyn', 'Hypertension cascade with demography (4 populations)'),
                    ('hiv',          'HIV care cascade (2 populations)'), 
                    ('tb',           'Tuberculosis model (10 populations)'), 
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
        P = Project(framework=framework_file, frw_name='SIR', databook_path=atomica_path(['tests', 'databooks']) + "databook_sir.xlsx", do_run=do_run, **kwargs)
        P.settings.sim_dt = 1.0
        if addprogs: P.load_progbook(progbook_path=atomica_path(['tests','databooks'])+"progbook_sir.xlsx", blh_effects=False)

    elif which=='tb':
        logger.info("Creating a TB epidemic project with programs...")
        if verbose: print('Loading framework')
        framework_file = atomica_path(['tests','frameworks'])+'framework_tb.xlsx'
        if verbose: print('Loading databook')
        P = Project(framework=framework_file, frw_name='TB', databook_path=atomica_path(['tests','databooks'])+"databook_tb.xlsx", do_run=do_run, **kwargs)
        if addprogs:
            if verbose: print('Loading progbook')
            P.load_progbook(progbook_path=atomica_path(['tests','databooks'])+"progbook_"+which+".xlsx", blh_effects=False)
            if verbose: print('Creating scenarios')
            P.demo_scenarios() # Add example scenarios
            if verbose: print('Creating optimizations')
            P.demo_optimization(tool='tb') # Add optimization example
            if verbose: print('Done!')

    elif which=='service':
        logger.info("Creating a disease-agnostic 5-stage service delivery cascade project...")
        
        framework_file = atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx'
        P = Project(framework=framework_file, frw_name='Service', databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=do_run, **kwargs)
        P.settings.sim_dt = 1.0
        if addprogs:
            if verbose: print('Progbook not implemented')

    elif which=='diabetes':
        logger.info("Creating a diabetes cascade project...")
        
        if verbose: print('Loading framework')
        framework_file = atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx'
        if verbose: print('Loading databook')
        P = Project(framework=framework_file, frw_name='Diabetes', databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=False, **kwargs)
        P.settings.sim_dt = 1.0
        if do_run: P.run_sim()
        if addprogs:
            if verbose: print('Loading progbook')
            P.load_progbook(progbook_path=atomica_path(['tests','databooks'])+"progbook_"+which+".xlsx", blh_effects=False)
            if verbose: print('Creating scenarios')
            P.demo_scenarios() # Add example scenarios
            if verbose: print('Creating optimizations')
            P.demo_optimization(tool='cascade') # Add optimization example
            if verbose: print('Done!')


    elif which=='udt':
        logger.info("Creating a generic 3-stage disease cascade project...")
        
        if verbose: print('Loading framework')
        framework_file = atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx'
        if verbose: print('Loading databook')
        P = Project(framework=framework_file, frw_name='UDT', databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=do_run, **kwargs)
        P.settings.sim_dt = 1.0
        if addprogs:
            if verbose: print('Loading progbook')
            P.load_progbook(progbook_path=atomica_path(['tests','databooks'])+"progbook_"+which+".xlsx", blh_effects=False)
            if verbose: print('Creating scenarios')
            P.demo_scenarios() # Add example scenarios
            if verbose: print('Creating optimizations')
            P.demo_optimization(tool='cascade') # Add optimization example
            if verbose: print('Done!')

    elif which=='usdt':
        logger.info("Creating a generic 4-stage disease cascade project...")
        
        if verbose: print('Loading framework')
        framework_file = atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx'
        if verbose: print('Loading databook')
        P = Project(framework=framework_file, frw_name='USDT', databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=do_run, **kwargs)
        P.settings.sim_dt = 1.0
        if addprogs:
            if verbose: print('Loading progbook')
            P.load_progbook(progbook_path=atomica_path(['tests','databooks'])+"progbook_"+which+".xlsx", blh_effects=False)
            if verbose: print('Creating scenarios')
            P.demo_scenarios() # Add example scenarios
            if verbose: print('Creating optimizations')
            P.demo_optimization(tool='cascade') # Add optimization example
            if verbose: print('Done!')

    elif which=='hypertension':
        logger.info("Creating a hypertension cascade project...")
        
        if verbose: print('Loading framework')
        framework_file = atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx'
        if verbose: print('Loading databook')
        P = Project(framework=framework_file, databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=do_run, **kwargs)
        P.settings.sim_dt = 1.0
        if addprogs:
            if verbose: print('Loading progbook')
            P.load_progbook(progbook_path=atomica_path(['tests','databooks'])+"progbook_"+which+".xlsx", blh_effects=False)
            if verbose: print('Creating scenarios')
            P.demo_scenarios() # Add example scenarios
            if verbose: print('Creating optimizations')
            P.demo_optimization(tool='cascade') # Add optimization example
            if verbose: print('Done!')

    elif which=='hypertension_dyn':
        logger.info("Creating a hypertension cascade project with demography...")
        
        if verbose: print('Loading framework')
        framework_file = atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx'
        if verbose: print('Loading databook')
        P = Project(framework=framework_file, frw_name='Hypertension', databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=do_run, **kwargs)
        P.settings.sim_dt = 1.0
        if addprogs:
            if verbose: print('Loading progbook')
            P.load_progbook(progbook_path=atomica_path(['tests','databooks'])+"progbook_"+which+".xlsx", blh_effects=False)
            if verbose: print('Creating scenarios')
            P.demo_scenarios() # Add example scenarios
            if verbose: print('Creating optimizations')
            P.demo_optimization(tool='cascade') # Add optimization example
            if verbose: print('Done!')

    elif which=='hiv':
        logger.info("Creating an HIV cascade project...")
        
        if verbose: print('Loading framework')
        framework_file = atomica_path(['tests','frameworks'])+'framework_'+which+'.xlsx'
        if verbose: print('Loading databook')
        P = Project(framework=framework_file, frw_name='HIV', databook_path=atomica_path(['tests','databooks'])+"databook_"+which+".xlsx", do_run=do_run, **kwargs)
        P.settings.sim_dt = 1.0
        if addprogs:
            if verbose: print('Loading progbook')
            P.load_progbook(progbook_path=atomica_path(['tests','databooks'])+"progbook_"+which+".xlsx", blh_effects=False)
            if verbose: print('Creating scenarios')
            P.demo_scenarios() # Add example scenarios
            if verbose: print('Creating optimizations')
            P.demo_optimization(tool='cascade') # Add optimization example
            if verbose: print('Done!')

    else:
        raise AtomicaException("Default project type '{0}' not understood; choices are 'sir', 'tb'.".format(which))
    return P


def demo(which=None, kind=None, do_plot=False, **kwargs):
    """ Create a simple demo project"""
    
    if kind is None: kind = 'project'
    
    if kind == 'framework': output = default_framework(which=which, **kwargs)
    elif kind == 'project': output = default_project(which=which, **kwargs)
    else:                   print('Sorry, no: %s' % kind)
    if do_plot:
        logger.warning("Plotting not implemented yet.")
    return output
