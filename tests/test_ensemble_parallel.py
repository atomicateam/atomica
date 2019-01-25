## CASCADE ENSEMBLES
# This script demonstrates how to use the CascadeEnsemble to plot cascades with uncertainty

import atomica as at
import sciris as sc
import logging
at.logger.setLevel(logging.WARNING)

if __name__ == '__main__':
    ## BASIC SETUP
    testdir = at.parent_dir()

    P = at.Project(framework=testdir + 'test_uncertainty_framework.xlsx', databook=testdir + 'test_uncertainty_databook.xlsx')

    low_uncertainty_progset = at.ProgramSet.from_spreadsheet(testdir + 'test_uncertainty_low_progbook.xlsx',project=P)
    high_uncertainty_progset = at.ProgramSet.from_spreadsheet(testdir + 'test_uncertainty_high_progbook.xlsx',project=P)
    default_budget = at.ProgramInstructions(start_year=2018, alloc=low_uncertainty_progset)
    doubled_budget = default_budget.scale_alloc(2)

    ## COMPARING YEARS
    #
    # Make a cascade plot comparing the same Results at different years, with
    # and without progsets

    ensemble = at.CascadeEnsemble(P.framework,'main')

    # t1 = sc.tic()
    # ensemble.run_sims(P, parset='default', progset=high_uncertainty_progset, progset_instructions=default_budget, n_samples=1000,parallel=False)
    # sc.toc(t1,label='serial run')

    t1 = sc.tic()
    ensemble.run_sims(P, parset='default', progset=high_uncertainty_progset, progset_instructions=default_budget, n_samples=1000,parallel=True)
    sc.toc(t1,label='parallel run')

