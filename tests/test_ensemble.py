import atomica as at
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import sciris as sc

testdir = at.parent_dir()

# def test_parset_sampling():
P = at.Project(framework=testdir + 'test_uncertainty_framework.xlsx', databook=testdir + 'test_uncertainty_databook.xlsx')
P.load_progbook(testdir + 'test_uncertainty_high_progbook.xlsx')


low_uncertainty_progset = at.ProgramSet.from_spreadsheet(testdir + 'test_uncertainty_low_progbook.xlsx',project=P)
high_uncertainty_progset = at.ProgramSet.from_spreadsheet(testdir + 'test_uncertainty_high_progbook.xlsx',project=P) # Alternatively, could have copied and set the uncertainties manually
default_budget = at.ProgramInstructions(start_year=2018, alloc=P.progsets[0])
doubled_budget = default_budget.scale(2)

# Test the outcome of one of the budgets on a scalar in a particular year
fn = lambda x: at.PlotData(x,outputs='con',pops='m_rural').interpolate(2020)
single_output_single_pop = at.Ensemble(fn) # Create Ensemble, binding the function to it - could be done in one line of course

fn = lambda x: at.PlotData(x,outputs='con').interpolate(2020)
single_output_multi_pop = at.Ensemble(fn) # Create Ensemble, binding the function to it - could be done in one line of course

fn = lambda x: at.PlotData(x,outputs='screen').interpolate(2020)
multi_output_multi_pop = at.Ensemble(fn) # Create Ensemble, binding the function to it - could be done in one line of course

baseline = P.run_sim(P.parsets[0],progset=P.progsets[0],progset_instructions=default_budget)
single_output_single_pop.set_baseline(baseline)
single_output_multi_pop.set_baseline(baseline)
multi_output_multi_pop.set_baseline(baseline)


for i in range(100):
    sampled_parset = P.parsets[0].sample()
    sample_low = P.run_sim(sampled_parset,progset=low_uncertainty_progset.sample(),progset_instructions=default_budget)
    # sample_high = P.run_sim(sampled_parset,progset=high_uncertainty_progset.sample(),progset_instructions=default_budget)

    single_output_single_pop.add(sample_low)
    single_output_multi_pop.add(sample_low)
    multi_output_multi_pop.add(sample_low)

single_output_single_pop.plot_distribution()
single_output_multi_pop.plot_distribution()
multi_output_multi_pop.plot_distribution()

# # Test the outcome of one of the budgets on a full TimeSeries
# fn = lambda x: x.get_variable('m_rural','con')[0].vals # Function mapping a result to an outcome
# ensemble = at.Ensemble(fn)
# baseline = P.run_sim(P.parsets[0],progset=P.progsets[0],progset_instructions=default_budget)
# ensemble.set_baseline(baseline)
# for i in range(100):
#     ensemble.add_sample(P.run_sim(P.parsets[0].sample(),progset=P.progsets[0].sample(),progset_instructions=default_budget))
# ensemble.plot_distribution(ti=5)


## TODO - Write out all the plots to generate
# - Comparisons of distributions for different cases and different times
# - Pairwise difference distribution
# - Timeseries versions of those same plots

# for i in range(100):
#     ensemble.add_sample(P.run_sim(P.parsets[0].sample()))
#
#
#
# #
# def test_progset_sampling():
#     P = at.Project(framework=testdir + 'test_uncertainty_framework.xlsx', databook=testdir + 'test_uncertainty_databook.xlsx')
#
#     low_uncertainty_progset = at.ProgramSet.from_spreadsheet(testdir + 'test_uncertainty_low_progbook.xlsx',project=P)
#     high_uncertainty_progset = at.ProgramSet.from_spreadsheet(testdir + 'test_uncertainty_high_progbook.xlsx',project=P) # Alternatively, could have copied and set the uncertainties manually
#
#     baseline = P.run_sim('default',progset=low_uncertainty_progset, progset_instructions=at.ProgramInstructions(start_year=2018))
#
#     res_low = []
#     res_high = []
#
#     for i in range(100):
#         res_low.append(P.run_sim('default',progset=low_uncertainty_progset.sample(),progset_instructions=at.ProgramInstructions(start_year=2018)))
#         res_high.append(P.run_sim('default',progset=high_uncertainty_progset.sample(),progset_instructions=at.ProgramInstructions(start_year=2018)))
#
#     # Get the distribution over outcomes
#     fn = lambda x: x.get_variable('m_rural','con')[0].vals[-1]
#     kernel_low = stats.gaussian_kde(np.array([fn(x) for x in res_low]).ravel())
#     kernel_high = stats.gaussian_kde(np.array([fn(x) for x in res_high]).ravel())
#
#     x = np.linspace(58,62,500)
#     plt.figure()
#     plt.plot(x,kernel_low(x),label='Low uncertainty')
#     plt.plot(x,kernel_high(x),label='High uncertainty')
#     plt.axvline(fn(baseline),color='r',label='Baseline values')
#     plt.legend()

# if __name__ == '__main__':
#     test_parset_sampling()
#     test_progset_sampling()

