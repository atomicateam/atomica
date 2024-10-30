# This test demonstrates running samples in parallel

import atomica as at
import sciris as sc
import logging

at.logger.setLevel(logging.WARNING)

# Checking `__name__ == '__main__'` is essential on Windows
if __name__ == "__main__":

    # BASIC SETUP
    testdir = at.parent_dir()
    P = at.Project(framework=testdir / "test_uncertainty_framework.xlsx", databook=testdir / "test_uncertainty_databook.xlsx")
    low_uncertainty_progset = at.ProgramSet.from_spreadsheet(testdir / "test_uncertainty_low_progbook.xlsx", project=P)
    high_uncertainty_progset = at.ProgramSet.from_spreadsheet(testdir / "test_uncertainty_high_progbook.xlsx", project=P)
    default_budget = at.ProgramInstructions(start_year=2018, alloc=low_uncertainty_progset)
    doubled_budget = default_budget.scale_alloc(2)

    n_samples = 150

    # Serial result generation
    with sc.Timer(label="serial runs") as t:
        results = P.run_sampled_sims(parset="default", progset=high_uncertainty_progset, progset_instructions=default_budget, n_samples=n_samples, parallel=False)

    # Parallel result generation
    # Note that parallization on a quad-core Windows machine has a 50% speedup at 1000 samples
    # and breaks even at around 150 samples i.e. parallization only starts to provide
    # benefits with >150 samples for the demo model (results may be different for different models - likely
    # to see benefits starting at fewer samples for more intensive models because there's less overhead relative
    # to model computation time)
    with sc.Timer(label="parallel runs") as t:
        results = P.run_sampled_sims(parset="default", progset=high_uncertainty_progset, progset_instructions=default_budget, n_samples=n_samples, parallel=True)

    # Serial result via Ensemble
    ensemble = at.CascadeEnsemble(P.framework, "main")
    with sc.Timer(label="serial via Ensemble") as t:
        ensemble.run_sims(P, parset="default", progset=high_uncertainty_progset, progset_instructions=default_budget, n_samples=n_samples, parallel=False)

    # Parallel simulations via Ensemble
    # If there is insufficient memory to store all raw results, can run the simulation via the Ensemble instead in which
    # case only the output of the mapping function is stored - which is usual an order of magnitude or two less than
    # the raw output
    ensemble = at.CascadeEnsemble(P.framework, "main")
    with sc.Timer(label="parallel via Ensemble") as t:
        ensemble.run_sims(P, parset="default", progset=high_uncertainty_progset, progset_instructions=default_budget, n_samples=n_samples, parallel=True)
