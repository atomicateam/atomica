"""
Defines some defaults for Atomica projects

Version: 2018sep24

"""

import sciris as sc
from .project import Project
from .system import LIBRARY_PATH, logger
from .scenarios import BudgetScenario
from .utils import TimeSeries

__all__ = ["demo", "make_demo_scenarios"]


def demo(which: str = None, do_run: bool = True, addprogs: bool = True) -> Project:
    """
    Return a demo project

    :param which: A supported demo project type e.g. 'sir', 'tb'
    :param do_run: If True, run the model and store a set of results
    :param addprogs: If True, load the progbook and create program scenarios
    :return: A Project instance

    """

    options = [
        "udt",
        "udt_dyn",
        "usdt",
        "cervicalcancer",
        "sir",
        "diabetes",
        "combined",
        # 'service',
        "hypertension",
        "hypertension_dyn",
        "hiv",
        "hiv_dyn",
        "tb_simple",
        "tb_simple_dyn",
        "environment",
        "tb",
    ]

    dtdict = sc.odict.fromkeys(options, 1.0)
    dtdict["tb"] = 0.5

    if which is None or which not in options:
        raise Exception("Supported project types are:\n%s" % ("\n".join(options)))

    framework = LIBRARY_PATH / f"{which}_framework.xlsx"
    databook = LIBRARY_PATH / f"{which}_databook.xlsx"
    progbook = LIBRARY_PATH / f"{which}_progbook.xlsx"

    logger.debug("Creating a " + which + " project...")
    P = Project(framework=framework, databook=databook, do_run=False)
    P.settings.sim_dt = dtdict[which]

    if do_run:
        P.run_sim(store_results=True)

    if addprogs:
        logger.debug("Loading progbook")
        P.load_progbook(progbook)

        logger.debug("Creating program scenarios")
        make_demo_scenarios(P)

    logger.debug("Finished creating demo project")

    return P


def make_demo_scenarios(proj: Project) -> None:
    """
    Create demo scenarios

    This method creates three default budget scenarios

    - Default budget
    - Doubled budget
    - Zero budget

    The scenarios will be created and added to the project's list of scenarios

    :param proj: A :class:`Project` instance. New scenarios will be added in-place

    """

    parsetname = proj.parsets[-1].name
    progset = proj.progsets[-1]
    start_year = proj.data.end_year

    # Come up with the current allocation by truncating after the start year
    current_budget = {}
    for prog in progset.programs.values():
        if prog.spend_data.has_time_data:
            current_budget[prog.name] = sc.dcp(prog.spend_data)
        else:
            current_budget[prog.name] = TimeSeries(start_year, prog.spend_data.assumption)

    # Add default budget scenario
    # proj.scens.append(CombinedScenario(name='Default budget',parsetname=parsetname,progsetname=progset.name,active=True,instructions=ProgramInstructions(start_year,alloc=current_budget)))
    proj.scens.append(BudgetScenario(name="Default budget", parsetname=parsetname, progsetname=progset.name, active=True, alloc=current_budget, start_year=start_year))

    # Add doubled budget
    doubled_budget = sc.dcp(current_budget)
    for ts in doubled_budget.values():
        ts.insert(start_year, ts.interpolate(start_year))
        ts.remove_after(start_year)
        ts.insert(start_year + 1, ts.get(start_year) * 2)
    # proj.scens.append(CombinedScenario(name='Doubled budget',parsetname=parsetname,progsetname=progset.name,active=True,instructions=ProgramInstructions(start_year,alloc=doubled_budget)))
    proj.scens.append(BudgetScenario(name="Doubled budget", parsetname=parsetname, progsetname=progset.name, active=True, alloc=doubled_budget, start_year=start_year))

    # Add zero budget
    zero_budget = sc.dcp(doubled_budget)
    for ts in zero_budget.values():
        ts.insert(start_year + 1, 0.0)
    # proj.scens.append(CombinedScenario(name='Zero budget',parsetname=parsetname,progsetname=progset.name,active=True,instructions=ProgramInstructions(start_year,alloc=zero_budget)))
    proj.scens.append(BudgetScenario(name="Zero budget", parsetname=parsetname, progsetname=progset.name, active=True, alloc=zero_budget, start_year=start_year))
