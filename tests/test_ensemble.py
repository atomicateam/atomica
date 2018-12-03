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
high_uncertainty_progset = at.ProgramSet.from_spreadsheet(testdir + 'test_uncertainty_high_progbook.xlsx',project=P)
default_budget = at.ProgramInstructions(start_year=2018, alloc=P.progsets[0])
doubled_budget = default_budget.scale(2)

# Set up the ensembles
store_all = lambda x: at.PlotData(x,outputs=['screen','diag'])
store_minimal = lambda x: at.PlotData(x,outputs=['screen','diag'],pops='m_rural').interpolate(2020)

all_default = at.Ensemble(store_all)
all_doubled = at.Ensemble(store_all)
all_together = at.Ensemble(store_all)
minimal_default = at.Ensemble(store_all)
minimal_doubled = at.Ensemble(store_all)
minimal_together = at.Ensemble(store_all)

# Do some baseline runs
default_baseline = P.run_sim(P.parsets[0],progset=P.progsets[0],progset_instructions=default_budget,result_name='default')
doubled_baseline = P.run_sim(P.parsets[0],progset=P.progsets[0],progset_instructions=doubled_budget,result_name='doubled')

all_default.set_baseline(default_baseline)
all_doubled.set_baseline(doubled_baseline)
all_together.set_baseline([default_baseline,doubled_baseline])
minimal_default.set_baseline(default_baseline)
minimal_doubled.set_baseline(doubled_baseline)
minimal_together.set_baseline([default_baseline,doubled_baseline])

# Also hold onto the results to demonstrate using them as a list later on
default_results = []
doubled_results = []

for i in range(100):
    try:
        sampled_parset = P.parsets[0].sample()
        sampled_progset = P.progsets[0].sample()
        default_sample = P.run_sim(sampled_parset, progset=sampled_progset, progset_instructions=default_budget, result_name='default')
        doubled_sample = P.run_sim(sampled_parset, progset=sampled_progset, progset_instructions=doubled_budget, result_name='doubled')
    except at.BadInitialization:
        continue

    default_results.append(default_sample)
    doubled_results.append(doubled_sample)

    all_default.add(default_sample)
    all_doubled.add(doubled_sample)
    all_together.add([default_sample, doubled_sample])
    minimal_default.add(default_sample)
    minimal_doubled.add(doubled_sample)
    minimal_together.add([default_sample, doubled_sample])
#
# # Get all the colors
# def get_colors(fig):
#     colors = set()
#     for ax in fig.axes:
#         for obj in ax.get_children():
#             if hasattr(obj,'get_color'):
#                 colors.add(obj.get_color())
#     return colors
#
# def accumulate_children(obj,colors=None):
#     if accum is None:
#         accum = set()
#     accum.append(obj)
#     if hasattr(obj,'get_children'):
#         for child in obj.get_children():
#             accumulate_children(child,accum)
#     return accum
# print(accumulate_children(fig))



fig = all_default.plot_distribution(year=2020,outputs='screen',pops='m_rural')
all_doubled.plot_distribution(year=2020,outputs='screen',pops='m_rural',fig=fig)

# There are two ways to compare distributions
# - Within an Ensemble
#   - Comparing multiple outputs/pops
#   - Comparing multiple results
# - Across an Ensemble
#   - Typically would be comparing corresponding outputs/pops
#   - In theory could do more, but in practice this would probably be confusing
#
# The Ensemble has a simple rule - calling `plot_distribution()` will render everything onto the same figure


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

