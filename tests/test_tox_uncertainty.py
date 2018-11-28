import atomica as at
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

def test_parset_sampling():
    P = at.Project(framework='test_uncertainty_framework.xlsx', databook='test_uncertainty_databook.xlsx')

    baseline = P.run_sim(P.parsets[0])

    res = []

    for i in range(100):
        res.append(P.run_sim(P.parsets[0].sample()))

    # Get the distribution over outcomes
    fn = lambda x: x.get_variable('m_rural','con')[0].vals[-1]
    kernel = stats.gaussian_kde(np.array([fn(x) for x in res]).ravel())

    x = np.linspace(105,115,500)
    plt.figure()
    plt.plot(x,kernel(x),label='With uncertainty')
    plt.axvline(fn(baseline),color='r',label='Baseline values')
    plt.legend()


def test_progset_sampling():
    P = at.Project(framework='test_uncertainty_framework.xlsx', databook='test_uncertainty_databook.xlsx')

    low_uncertainty_progset = at.ProgramSet.from_spreadsheet('test_uncertainty_low_progbook.xlsx',project=P)
    high_uncertainty_progset = at.ProgramSet.from_spreadsheet('test_uncertainty_high_progbook.xlsx',project=P) # Alternatively, could have copied and set the uncertainties manually

    baseline = P.run_sim('default',progset=low_uncertainty_progset, progset_instructions=at.ProgramInstructions(start_year=2018))

    res_low = []
    res_high = []

    for i in range(100):
        res_low.append(P.run_sim('default',progset=low_uncertainty_progset.sample(),progset_instructions=at.ProgramInstructions(start_year=2018)))
        res_high.append(P.run_sim('default',progset=high_uncertainty_progset.sample(),progset_instructions=at.ProgramInstructions(start_year=2018)))

    # Get the distribution over outcomes
    fn = lambda x: x.get_variable('m_rural','con')[0].vals[-1]
    kernel_low = stats.gaussian_kde(np.array([fn(x) for x in res_low]).ravel())
    kernel_high = stats.gaussian_kde(np.array([fn(x) for x in res_high]).ravel())

    x = np.linspace(58,62,500)
    plt.figure()
    plt.plot(x,kernel_low(x),label='Low uncertainty')
    plt.plot(x,kernel_high(x),label='High uncertainty')
    plt.axvline(fn(baseline),color='r',label='Baseline values')
    plt.legend()

if __name__ == '__main__':
    test_parset_sampling()
    test_progset_sampling()

