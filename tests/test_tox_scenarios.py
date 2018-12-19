"""
Check whether automated model documentation template generation works
"""

import os
import atomica as at
import sciris as sc

def test_program_scenarios():

    P = at.demo('tb',do_run=False)

    # Get the default values for coverage etc.
    instructions = at.ProgramInstructions(2018)
    res_baseline = P.run_sim(result_name='Baseline',parset='default',progset='default',progset_instructions=instructions)

    alloc = res_baseline.get_alloc(2018)
    capacity = res_baseline.get_coverage('capacity',2018)
    coverage = res_baseline.get_coverage('fraction',2018)

    # # Run an allocation scenario manually
    # doubled_budget = {x: v * 2 for x, v in alloc.items()}
    # instructions = at.ProgramInstructions(2018,alloc=doubled_budget)
    # res_doubled = P.run_sim(result_name='Doubled budget',parset='default',progset='default',progset_instructions=instructions)
    #
    # # Compare spending in 2018
    # d = at.PlotData.programs([res_baseline, res_doubled],quantity='spending')
    # d.interpolate(2018)
    # at.plot_bars(d,stack_outputs='all')

    # Run a capacity scenario manually
    doubled_capacity = {x: v * 2 for x, v in capacity.items()}
    instructions = at.ProgramInstructions(2018,capacity=doubled_capacity)
    res_capacity = P.run_sim(result_name='Doubled capacity',parset='default',progset='default',progset_instructions=instructions)

    # Compare capacity in 2018
    d = at.PlotData.programs([res_baseline, res_capacity],quantity='coverage_capacity')
    d.interpolate(2018)
    at.plot_bars(d,stack_outputs='all')



    scen = at.BudgetScenario(name='Doubled budget', alloc=doubled_budget, start_year=2018)
    scen.run(proj, parset='default', progset='default')


    alloc[0] = alloc[0]*2

    # Get
    # Low level scenarios - assigning to ProgramInstructions directly
    alloc = proj.progsets[0].get_alloc(2018)
    doubled_budget = {x: v * 2 for x, v in alloc.items()}



    # Three different types of scenario
    def run_budget_scenario(proj):
        """ Run a budget scenario

        :param proj: A Project object
        :return: None

        """

        print('Testing budget scenario')

        alloc = proj.progsets[0].get_alloc(2018)
        doubled_budget = {x: v * 2 for x, v in alloc.items()}
        scen = at.BudgetScenario(name='Doubled budget', alloc=doubled_budget, start_year=2018)
        scen.run(proj, parset='default', progset='default')

        return

    def run_coverage_scenario(proj):
        """ Run a coverage scenario

        :param proj: A Project object
        :return: None

        """

        print('Testing coverage scenario')

        half_coverage = {x: 0.5 for x in proj.progsets[0].programs.keys()}
        scen = at.CoverageScenario(name='Reduced coverage', coverage=half_coverage, start_year=2018)
        scen.run(proj, parset='default', progset='default')

        return


if __name__ == '__main__':
    test_program_scenarios()

