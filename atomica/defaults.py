"""
Defines some defaults for Atomica projects
Version: 2018sep24
"""

import sciris as sc
from .framework import ProjectFramework
from .project import Project
from .system import LIBRARY_PATH, logger

def default_framework(which=None, show_options=False):

    options = sc.odict([
        ('udt', 'Undiagnosed-diagnosed-treated'),
        ('usdt', 'Undiagnosed-screened-diagnosed-treated'),
        ('cervicalcancer', 'Cervical cancer'),
        ('sir', 'SIR model'),
        ('diabetes', 'Diabetes'),
        ('hypertension', 'Hypertension'),
        ('hypertension_dyn', 'Hypertension with demography'),
        # ('service', 'Service delivery'),
        ('hiv', 'HIV care cascade'),
        ('hiv_dyn', 'HIV care cascade with demography'),
        ('tb_simple', 'Tuberculosis'),
        ('tb_simple_dyn', 'Tuberculosis with demography'),
        ('environment', 'SIR model with environment'),
        ('tb', 'Tuberculosis with transmission dynamics'),
    ])

    if which is None or which == 'default':
        which = 'udt'
    elif which not in options.keys():
        if which in options.values():
            which = options.keys()[options.values().index(which)]
        else:
            errormsg = '"%s" not found; must be in %s or %s' % (which, options.keys(), options.values())
            raise Exception(errormsg)
    if show_options:
        return options
    else:
        label = options[which]
        F = ProjectFramework(name=label, inputs=LIBRARY_PATH + which + "_framework.xlsx")
    return F


def default_project(which=None, do_run=True, addprogs=True, verbose=False, show_options=False, **kwargs):
    """
    Options for easily creating default projects based on different spreadsheets, including
    program information -- useful for testing
    Version: 2018mar27
    """

    options = sc.odict([
        ('udt', 'Undiagnosed-diagnosed-treated cascade (1 population)'),
        ('udt_dyn', 'Undiagnosed-diagnosed-treated cascade with demography (1 population)'),
        ('usdt', 'Undiagnosed-screened-diagnosed-treated cascade (1 population)'),
        ('cervicalcancer', 'Cervical cancer cascade (1 population)'),
        ('sir', 'SIR model (1 population)'),
        ('diabetes', 'Diabetes cascade (1 population)'),
        ('combined', 'Combined SIR+UDT model (5 populations)'),
        # ('service', 'Service delivery cascade (1 population)'),
        ('hypertension', 'Hypertension cascade (4 populations)'),
        ('hypertension_dyn', 'Hypertension cascade with demography (4 populations)'),
        ('hiv', 'HIV care cascade (2 populations)'),
        ('hiv_dyn', 'HIV care cascade with demography (2 populations)'),
        ('tb_simple', 'Tuberculosis (1 population)'),
        ('tb_simple_dyn', 'Tuberculosis with demography (1 population)'),
        ('environment', 'SIR model with environment (2 population)'),
        ('tb', 'Tuberculosis with transmission dynamics'),
    ])

    dtdict = sc.odict.fromkeys(options.keys(), 1.)
    dtdict['tb'] = 0.5

    tool = 'tb' if which=='tb' else 'cascade'
    if which is None or which == 'default':
        which = 'udt'
    elif which not in options.keys():
        if which in options.values():
            which = options.keys()[options.values().index(which)]
        else:
            errormsg = '"%s" not found; must be in %s or %s' % (which, options.keys(), options.values())
            raise Exception(errormsg)

    if show_options:
        return options

    logger.info("Creating a " + which + " project...")

    if verbose:
        print('Loading framework')
    framework_file = LIBRARY_PATH + which + '_framework.xlsx'
    if verbose:
        print('Loading databook')
    P = Project(framework=framework_file, databook=LIBRARY_PATH + which + "_databook.xlsx", do_run=False, **kwargs)
    P.settings.sim_dt = dtdict[which]
    if do_run:
        P.run_sim(store_results=True)
    if addprogs:
        if verbose:
            print('Loading progbook')
        P.load_progbook(progbook_path=LIBRARY_PATH + which + "_progbook.xlsx")
        if verbose:
            print('Creating scenarios')
        P.demo_scenarios()  # Add example scenarios
        if verbose:
            print('Creating optimizations')
        P.demo_optimization(tool=tool)  # Add optimization example
        if verbose:
            print('Done!')

    return P


def demo(which=None, kind=None, do_plot=False, **kwargs):
    """ Create a simple demo project"""

    if kind is None:
        kind = 'project'

    if kind == 'framework':
        output = default_framework(which=which, **kwargs)
    elif kind == 'project':
        output = default_project(which=which, **kwargs)
    else:
        print('Sorry, no: %s' % kind)
    if do_plot:
        logger.warning("Plotting not implemented yet.")
    return output
