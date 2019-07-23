import atomica as at
import sciris as sc
import os
import pytest
import sys

# # P = at.Project(framework='dummy_framework.xlsx',databook='dummy_databook.xlsx')
# # # P.run_sim()
# # P = at.demo('tb',do_run=True)
# # P.results[0].plot()
# # P = at.Project.load('asdf2.prj')
#
# # P = at.Project(framework=at.LIBRARY_PATH+'tb_framework.xlsx')
# # P.load_databook(at.LIBRARY_PATH+'tb_databook.xlsx')
# P = at.demo('tb',do_run=True)
#
#

testdir = os.path.abspath(os.path.join(os.path.dirname(__file__),'tests')) + os.sep  # Must be relative to current file to work with tox

def get_framework():
    return at.ProjectFramework(testdir + 'timed_test_framework.xlsx')

def get_project():
    P = at.Project(framework=get_framework(), databook=testdir + 'timed_test_databook.xlsx', do_run=False)
    P.settings.sim_dt = 1/12
    P.settings.sim_start = 2018
    P.settings.sim_end = 2020
    return P

def run_framework(fname):
    F = at.ProjectFramework(testdir + fname)
    D = at.ProjectData.new(framework=F,tvec=[2018],pops=1,transfers=0)
    P = at.Project(framework=F,databook=D.to_spreadsheet(),do_run=False)
    P.settings.sim_dt = 1
    P.settings.sim_start = 2018
    P.settings.sim_end = 2023
    return P.run_sim()

def test_read_write_databook():
    # Test that the timed databook can be written and read
    F = get_framework()
    D = at.ProjectData.new(framework=F,tvec=[2018],pops=1,transfers=0)
    D.save('test.xlsx')
    P = at.Project(framework=F,databook='test.xlsx',do_run=False)
    P.load_databook('test.xlsx')

# Baseline sim
# res = P.run_sim('default')
# sc.toc()
# d = at.PlotData(res,[':inf','inf:','inf'])
# at.plot_series(d)

# Test a spike in infections

# at.plot_series(d)

def test_spike():
    P = get_project()
    ps = P.parsets[0].copy()
    ps.pars['foi'].ts[0].insert(2018,24)
    ps.pars['foi'].ts[0].insert(2018.99,100)
    ps.pars['foi'].ts[0].insert(2019.01,24)
    ps.pars['foi'].smooth(P.settings.tvec,'previous')
    res2 = P.run_sim(ps)
    d = at.PlotData(res2,[':inf','inf:','inf'])
    at.plot_series(d)


def test_zero_duration():
    # Test junction-like behaviour where the compartment empties every timestep
    # This makes sure the algorithm works when there is no lag
    P = get_project()
    ps = P.parsets[0].copy()
    ps.pars['nat_rec'].ts[0].insert(None,0) # Sub-timestep size
    res2 = P.run_sim(ps)
    d = at.PlotData(res2,[':inf','inf:','inf'])
    at.plot_series(d)

# Do some numeric tests
def test_flows():
    P = get_project()
    ps = P.parsets[0].copy()

    ps.pars['b_rate'].ts[0].insert(None,0) # Zero birth rate
    ps.pars['foi'].ts[0].insert(None,0) # Zero new infections
    ps.pars['inf'].ts[0].insert(2018,0) # Start out with no infections
    ps.pars['alive'].ts[0].insert(2018,0) # Zero birth rate
    ps.pars['sus'].ts[0].insert(2018,0) # Zero birth rate

def test_timed_tb():
    P = at.Project(framework=testdir + 'tb_timed_framework.xlsx', databook=testdir + 'tb_timed_databook.xlsx', do_run=True)

def test_lifespan():
    F = at.ProjectFramework(testdir + 'timed_test_lifespan_framework.xlsx')
    D = at.ProjectData.new(framework=F,tvec=[2018],pops=1,transfers=0)
    P = at.Project(framework=F,databook=D.to_spreadsheet(),do_run=True)
    P.results

def test_junctions():
    res = run_framework('timed_junctions_1.xlsx')

def test_indirect():
    res = run_framework('timed_test_indirect_framework.xlsx')


if __name__ == '__main__':
    # test_read_write_databook()
    # test_zero_duration()

    # test_spike()
    test_lifespan()

    # test_junctions()
    # test_indirect()
    # test_timed_tb()
