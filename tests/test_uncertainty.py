import atomica as at
from tqdm import tqdm
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

# for demo in ['udt','udt_dyn','usdt','cervicalcancer','sir','diabetes','hypertension','hypertension_dyn','hiv','hiv_dyn','tb','tb_simple','tb_simple_dyn',]:
#     P = at.demo(demo)
#     d = at.PlotData(P.results[0])
#     figs=at.plot_series(d,plot_type='stacked')
#     at.save_figs(figs,prefix='%s_old_' % (demo))
#

# F = at.ProjectFramework('tests/test_uncertainty_framework.xlsx')
# D = at.ProjectData.from_spreadsheet('tests/test_uncertainty_databook.xlsx',F)
# pset = at.ProgramSet.from_spreadsheet('tests/test_uncertainty_progbook.xlsx',F,D)
# pset.save('tests/test_uncertainty_progbook.xlsx')
at.logger.setLevel('WARNING') # Quieter

P = at.Project(framework='test_uncertainty_framework.xlsx', databook='test_uncertainty_databook.xlsx')
low_uncertainty_progset = at.ProgramSet.from_spreadsheet('test_uncertainty_low_progbook.xlsx',project=P)
high_uncertainty_progset = at.ProgramSet.from_spreadsheet('test_uncertainty_high_progbook.xlsx',project=P) # Alternatively, could have copied and set the uncertainties manually


baseline = P.run_sim('default',progset=low_uncertainty_progset, progset_instructions=at.ProgramInstructions(start_year=2018))

res_low = []
res_high = []

for i in tqdm(range(100)):
    res_low.append(P.run_sim('default',progset=low_uncertainty_progset.sample(),progset_instructions=at.ProgramInstructions(start_year=2018)))
    res_high.append(P.run_sim('default',progset=high_uncertainty_progset.sample(),progset_instructions=at.ProgramInstructions(start_year=2018)))

# Get the distribution over outcomes
fn = lambda x: x.get_variable('m_rural','con')[0].vals[-1]
kernel_low = stats.gaussian_kde(np.array([fn(x) for x in res_low]).ravel())
kernel_high = stats.gaussian_kde(np.array([fn(x) for x in res_high]).ravel())

x = np.linspace(58,62,500)
plt.plot(x,kernel_low(x),label='Low uncertainty')
plt.plot(x,kernel_high(x),label='High uncertainty')
plt.axvline(fn(baseline),color='r',label='Baseline values')
plt.legend()


# P = at.demo('hiv',do_run=False)
# P.settings.update_time_vector(dt=1)
# for i in range(0,20):
#     print(i)
#     P.run_sim('default', 'default', at.ProgramInstructions(start_year=2000))
# import sciris as sc
# sc.saveobj('hypertension_test.bin',P.results)
# # P.run_sim('default')
# # P.run_sim('default')
# # P.run_sim('default')
# # P.run_sim('default')
# # P.run_sim('default')
# # P.run_sim('default','default',at.ProgramInstructions(start_year=2000))
# # P.run_sim('default','default',at.ProgramInstructions(start_year=2000))
# # P.run_sim('default','default',at.ProgramInstructions(start_year=2000))
# # P.run_sim('default','default',at.ProgramInstructions(start_year=2000))
# # P.run_sim('default','default',at.ProgramInstructions(start_year=2000))
#
# # new_parset = P.parsets.copy('default','manually_calibrated')
# # new_parset.pars['foi_out'].y_factor['0-4'] = 0.0
# # new_parset.pars['foi_out'].y_factor['15-64'] = 0.0
# # new_parset.pars['foi_out'].y_factor['65+'] = 0.0
# # new_parset.pars['foi_out'].y_factor['5-14'] = 0.0
# # res_manually_calibrated = P.run_sim(parset='manually_calibrated')
# # d = at.PlotData(P.results,outputs='ac_inf',project=P)
# # at.plot_series(d, axis='results');
# #
# #
# d = at.PlotData(P.results,pops='0-4')
# at.plot_series(d, plot_type='stacked')