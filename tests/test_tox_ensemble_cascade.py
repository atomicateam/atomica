## CASCADE ENSEMBLES
# This script demonstrates how to use the CascadeEnsemble to plot cascades with uncertainty

import atomica as at
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import sciris as sc

def test_ensemble_cascade():
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
    ensemble = at.CascadeEnsemble(P.framework, 'main')
    ensemble.run_sims(P, parset='default', n_samples=100)
    ensemble.plot_multi_cascade(years=[2018,2020,2023])
    plt.title('Default parset')

    ensemble.run_sims(P,parset='default',progset=low_uncertainty_progset,progset_instructions=default_budget,n_samples=100)
    ensemble.plot_multi_cascade(years=[2018,2020,2023])
    plt.title('Default progset (low uncertainty)')

    ensemble.run_sims(P,parset='default',progset=high_uncertainty_progset,progset_instructions=default_budget,n_samples=100)
    ensemble.plot_multi_cascade(years=[2018,2020,2023])
    plt.title('Default progset (high uncertainty)')

    # Demonstrate calling an inherited Ensemble plotting function - in this case, a basic
    # series plot showing cascade evolution over time. Note that the Ensemble was created
    # with only 3 time points, so the series plot also only contains those three times
    ensemble.plot_series(style='std',pops='m_rural')
    plt.legend()

    ## COMPARING RESULTS
    #
    # We have a shortcut for comparing parameter scenarios - pass multiple instructions into `Ensemble.run_sims()` to automatically run them
    # A less common task would be to compare different progsets or parsets - these aren't built into `run_sims()` which is instead aimed at
    # the common task of testing different program scenarios against the same parset and progset samples, which is the most valid way
    # to examine uncertainty in differences (as illustrated in the final example in this file)

    ensemble = at.CascadeEnsemble(P.framework,'main',[2020,2023])
    ensemble.run_sims(P,parset='default',progset=high_uncertainty_progset,progset_instructions=[default_budget,doubled_budget],n_samples=100,result_names=['Default','Doubled'])

    ensemble.plot_multi_cascade(years=2020)
    plt.title('Spending comparison 2020')

    ensemble.plot_multi_cascade(years=2023)
    plt.title('Spending comparison 2023')

    ## VIRTUAL STAGES
    #
    # In normal cascade plots, all cascade stages must consist of comps/characs only. Because `CascadeEnsemble` has a plotting
    # routine built around `PlotData` instead of `Result` objects, it is possible to introduce arbitrarily defined cascade stages.
    # This is aimed at advanced users of course, because the normal cascade plotting routine has validation checks like ensuring that
    # the cascade is properly nested, whereas these validation checks aren't performed here because of the arbitrary possibilities

    cascade = {
        'Prevalent':'all_people',
        'Screened':'all_screened',
        'Pre-diagnosed':'0.8*all_screened', # This 'stage' is not a compartment/characteristic at all
        'Diagnosed':'all_dx',
        'Treated':'all_tx',
        'Controlled':'all_con'
    }

    ensemble = at.CascadeEnsemble(P.framework,cascade,[2020,2023])
    ensemble.run_sims(P,parset='default',progset=high_uncertainty_progset,progset_instructions=[default_budget,doubled_budget],n_samples=100,result_names=['Default','Doubled'])
    ensemble.plot_multi_cascade(years=2020)
    plt.title('Spending comparison 2020 with virtual stage')

    ## CUSTOM MAPPING
    #
    # Make a cascade plot showing the difference between default and doubled spending
    # This demonstrates how to override the cascade ensemble's default mapping function
    # while still making use of `CascadeEnsemble.plot_multi_cascade`

    ensemble = at.CascadeEnsemble(P.framework,0,[2020,2023]) # Just put '0' to use the first cascade - doesn't matter which one since it gets overwritten below

    def cascade_difference(results):
        cascade_dict = at.sanitize_cascade(results[0].framework,'main')[1] # Use `sanitize_cascade` to retrieve the cascade dictionary
        d1 = at.PlotData(results[0],outputs=cascade_dict)
        d2 = at.PlotData(results[1],outputs=cascade_dict)
        return d2-d1

    ensemble.mapping_function = cascade_difference
    ensemble.run_sims(P,parset='default',progset=high_uncertainty_progset,progset_instructions=[default_budget,doubled_budget],n_samples=100,result_names=['Default','Doubled'])
    ensemble.plot_multi_cascade(years=2023)
    plt.title('Difference between doubled budget and default budget')


if __name__ == "__main__":
    test_ensemble_cascade()