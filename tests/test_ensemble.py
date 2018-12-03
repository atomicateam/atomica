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
store_all = lambda x: at.PlotData(x,outputs=['screen','diag','initiate'])
store_minimal = lambda x: at.PlotData(x,outputs=['screen','diag','initiate'],pops='m_rural').interpolate(2020)

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

fig = all_default.plot_distribution(year=2020,outputs='screen',pops='m_rural')
all_doubled.plot_distribution(year=2020,outputs='screen',pops='m_rural',fig=fig)
all_together.pairplot()


yld = lambda x: at.PlotData(x,outputs={'disease':['undx','scr','dx','tx']},t_bins=[2018,2023],time_aggregation='integrate')
default_yld = at.Ensemble(yld,'default')
default_yld.update(default_results)
doubled_yld = at.Ensemble(yld,'doubled')
doubled_yld.update(doubled_results)
fig = default_yld.plot_distribution(pops='m_rural')
doubled_yld.plot_distribution(pops='m_rural',fig=fig)



# There are two ways to compare distributions
# - Within an Ensemble
#   - Comparing multiple outputs/pops
#   - Comparing multiple results
# - Across an Ensemble
#   - Typically would be comparing corresponding outputs/pops
#   - In theory could do more, but in practice this would probably be confusing
#
# The Ensemble has a simple rule - calling `plot_distribution()` will render everything onto the same figure

