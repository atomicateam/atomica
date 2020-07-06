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

testdir = os.path.abspath(os.path.join(os.path.dirname(__file__))) + os.sep  # Must be relative to current file to work with tox
tempdir = os.path.join(testdir, 'temp') + os.sep


def get_project():
    P = at.Project(framework=at.ProjectFramework(testdir / 'timed_test_framework.xlsx'), databook=testdir / 'timed_test_databook.xlsx', do_run=False)
    P.settings.sim_dt = 1 / 12
    P.settings.sim_start = 2018
    P.settings.sim_end = 2020
    return P


def run_framework(fname):
    # Saves a single-pop databook from a framework, then loads it back and runs a simulation
    # This assumes the framework provides default values for all quantities
    F = at.ProjectFramework(testdir / fname)
    D = at.ProjectData.new(framework=F, tvec=[2018], pops=1, transfers=0)
    P = at.Project(framework=F, databook=D.to_spreadsheet(), do_run=False)
    P.settings.sim_dt = 0.25
    P.settings.sim_start = 2018
    P.settings.sim_end = 2023
    return P.run_sim()


def test_read_write_databook():
    # Test that the timed databook can be written and read
    F = at.ProjectFramework(testdir / 'timed_test_framework.xlsx')
    D = at.ProjectData.new(framework=F, tvec=[2018], pops=1, transfers=0)
    D.save('test.xlsx')
    P = at.Project(framework=F, databook='test.xlsx', do_run=False)
    P.load_databook('test.xlsx')


def test_zero_duration():
    # Test junction-like behaviour where the compartment empties every timestep
    # This makes sure the algorithm works when there is no lag
    P = get_project()
    ps = P.parsets[0].copy()
    ps.pars['nat_rec'].ts[0].insert(None, 0)  # Sub-timestep size
    res2 = P.run_sim(ps)
    d = at.PlotData(res2, [':inf', 'inf:', 'inf'])
    at.plot_series(d)

    pop = res2.model.pops[0]
    assert pop.get_variable('foi')[0].vals[0] == 24  # Flow into the compartment
    assert pop.get_variable('inf')[0].vals[1] == 24 * res2.dt  # Compartment contents should now equal the inflow
    assert pop.get_variable('inf')[0].vals[2] == 24 * res2.dt  # Same again, contents equals the inflow because it was flushed entirely

    # Check formally that total inflows equal total outflows
    assert pop.get_variable('inf')[0].vals[0] == sum(l.vals[0] for l in pop.get_variable('inf')[0].outlinks)
    assert pop.get_variable('inf')[0].vals[1] == sum(l.vals[1] for l in pop.get_variable('inf')[0].outlinks)


def test_timed_tb():
    # Just check that it runs as a demonstration
    P = at.Project(framework=testdir / 'timed_tb_framework.xlsx', databook=testdir / 'timed_tb_databook.xlsx', do_run=False)
    P.settings.sim_dt = 0.25
    return P.run_sim()


def test_spike():
    P = get_project()
    ps = P.parsets[0].copy()
    ps.pars['foi'].ts[0].insert(2018, 24)
    ps.pars['foi'].ts[0].insert(2018.99, 100)
    ps.pars['foi'].ts[0].insert(2019.01, 24)
    ps.pars['foi'].smooth(P.settings.tvec, 'previous')
    res2 = P.run_sim(ps)
    d = at.PlotData(res2, [':inf', 'inf:', 'inf'])
    at.plot_series(d)


def test_timed_indirect():
    # This tests the case where there are multiple junctions and they pass untimed inputs into a duration group
    res = run_framework('timed_test_indirect_framework.xlsx')
    pop = res.model.pops[0]

    # Check that the junctions are emptied
    assert pop.get_comp('cb').vals[0] == 0
    assert pop.get_comp('cc').vals[0] == 0
    assert pop.get_comp('cd').vals[0] == 0

    # At the initialization, we have flushed 400 people from cb to cc/cd and then ce/cf/cg/ch. Each of those should have 100 people
    assert pop.get_comp('ce').vals[0] == 100
    assert pop.get_comp('cf').vals[0] == 100
    assert pop.get_comp('cg').vals[0] == 100
    assert pop.get_comp('ch').vals[0] == 100

    # At the second timestep, the inflow should be 100
    assert pop.get_links('a0')[0].vals[1] == 100
    # Now, ca is a timed compartment, which flushes into cb
    # Therefore, the flow into cb should be 0 until the first flush year is reached
    assert pop.get_variable('ca:cb')[0].vals[0] == 0
    assert pop.get_variable('ca:cb')[0].vals[1] == 0
    assert pop.get_variable('ca:cb')[0].vals[2] == 0
    assert pop.get_variable('ca:cb')[0].vals[3] == 0
    assert pop.get_variable('ca:cb')[0].vals[4] == 100

    # Similarly, the flow into 'ce' should be the same (but with the 100 becoming 25 due to the 4-way split)
    assert pop.get_variable('cc:ce')[0].vals[0] == 0
    assert pop.get_variable('cc:ce')[0].vals[1] == 0
    assert pop.get_variable('cc:ce')[0].vals[2] == 0
    assert pop.get_variable('cc:ce')[0].vals[3] == 0
    assert pop.get_variable('cc:ce')[0].vals[4] == 25

    # The first batch of new arrivals needs to spend 4 timesteps in compartment ca. The first outflow from
    # ca is thus in the 5th timestep
    assert pop.get_variable('ca:cb')[0].vals[0] == 0
    assert pop.get_variable('ca:cb')[0].vals[1] == 0
    assert pop.get_variable('ca:cb')[0].vals[2] == 0
    assert pop.get_variable('ca:cb')[0].vals[3] == 0
    assert pop.get_variable('ca:cb')[0].vals[4] == 100
    assert pop.get_variable('ca:cb')[0].vals[5] == 100

    # For compartment ca, the size should increase to an equilibrium value of 400 (inflow is 100, outflow is 100,
    # and there are 4 subcompartments). Note that with a duration of 1 year, and an inflow of 400 people/year, we
    # would expect the equilibrium solution to be 400 people.
    assert pop.get_variable('ca')[0].vals[0] == 0
    assert pop.get_variable('ca')[0].vals[1] == 100
    assert pop.get_variable('ca')[0].vals[2] == 200
    assert pop.get_variable('ca')[0].vals[3] == 300
    assert pop.get_variable('ca')[0].vals[4] == 400
    assert pop.get_variable('ca')[0].vals[5] == 400

    # The initial 100 people in ce are assumed to be uniformly distributed over the subcompartments. Thus we lose 25 of them
    # every timestep. Further, once the initial 100 people are flushed, the flow from ca to ce corresponds to moving into a
    # new duration group. Thus the new arrivals in the 5th timestep don't start to leave until the 9th timestep.
    assert pop.get_variable('ce:sus')[0].vals[0] == 25
    assert pop.get_variable('ce:sus')[0].vals[1] == 25
    assert pop.get_variable('ce:sus')[0].vals[2] == 25
    assert pop.get_variable('ce:sus')[0].vals[3] == 25
    assert pop.get_variable('ce:sus')[0].vals[4] == 0
    assert pop.get_variable('ce:sus')[0].vals[5] == 0
    assert pop.get_variable('ce:sus')[0].vals[6] == 0
    assert pop.get_variable('ce:sus')[0].vals[7] == 0
    assert pop.get_variable('ce:sus')[0].vals[8] == 25


def test_timed_indirect2():
    # This tests the case where there are multiple junctions and the inflow is from a TimedCompartment
    # within the same duration group. This checks that flows via indirect junctions still preserve
    # time spent within the duration group

    res = run_framework('timed_test_indirect2_framework.xlsx')
    pop = res.model.pops[0]

    # In the default case, compartment ca starts with no people. Therefore, every timestep there is an inflow of 100 people
    # that all land in the initial subcompartment
    assert pop.get_variable(':ca')[0].vals[0] == 100
    assert pop.get_variable(':ca')[0].vals[1] == 100
    assert pop.get_variable(':ca')[0].vals[2] == 100

    # The outflow is drawn from parameter `a1` and should be 400 people/year, with a corresponding timestep flow of 100
    # Because everyone is in the initial subcompartment, of the 100 people in the compartment, all of them are eligible
    # for the transition, and we move them.
    assert pop.get_variable('a1')[0].vals[0] == 400
    assert pop.get_variable('ca:cb')[0].vals[0] == 0  # Nobody present initially
    assert pop.get_variable('ca:cb')[0].vals[1] == 100  # Outflow is 100 due to inflow
    assert pop.get_variable('ca:cb')[0].vals[2] == 100  # Outflow is 100 due to inflow

    # Nobody is ever flushed because they all go into cb
    assert all(pop.get_variable('ca:sus')[0].vals == 0)

    # People enter ca for the first time during the first timestep. Those people aren't eligible to leave in that same step
    # Therefore ca always has 100 people in it
    assert pop.get_variable('ca')[0].vals[0] == 0
    assert all(pop.get_variable('ca')[0].vals[1:] == 100)

    # When people arrive in ce, they have already been in the duration group for 1 timestep. Thus they only
    # spend 3 timesteps in ce before being flushed. i.e. they enter during step
    pop.get_variable(':ce')[0].vals[0] = 0
    pop.get_variable(':ce')[0].vals[1] = 25  # Inflow from the first batch in ca
    pop.get_variable(':ce')[0].vals[2] = 25  # Inflow from the first batch in ca

    assert pop.get_variable('ce:sus')[0].vals[4] == 25  # Outflow is 25 at ti=4 rather than ti=5 because they've already spent 1 timestep in ca
    assert pop.get_variable('sus')[0].vals[4] == 0  # Outflow is 25 at ti=4 rather than ti=5 because they've already spent 1 timestep in ca
    assert pop.get_variable('sus')[0].vals[5] == 100  # They move into sus for the first time at ti=5 because that's the duration (4 timesteps)
    assert pop.get_variable('sus')[0].vals[6] == 200


def test_timed_eligibility():
    # This test shows that time transitions only transfer people that are not required
    # to leave the duration group. We aren't able to target specifically people that are
    # not due to leave the group. Therefore, the actual number of people moved will typically
    # be less than the parameter value (in the same way as links may be downscaled to avoid negative
    # compartment sizes - but in this case, the rescaling happens on a per-subcompartment basis)

    res = run_framework('timed_test_eligibility_framework.xlsx')
    pop = res.model.pops[0]

    # Check initial compartment sizes
    assert pop.get_comp('c1').vals[0] == 100
    assert pop.get_comp('c2').vals[0] == 100
    assert pop.get_comp('c3').vals[0] == 0
    assert pop.get_comp('c4').vals[0] == 0

    # Check flow rate
    assert pop.get_variable('a1')[0].vals[0] == 100

    # Now - this gets disaggregated 50/50 between c1 and c2
    # c1->c3 remains within the duration group. Therefore, there are 90 people
    # eligible for the transition, and so we move 50*(90/100)=45 people
    assert pop.get_variable('c1:c3')[0].vals[0] == 45

    # These people are moved from all but the final subcompartment. Thus we still have 10 people
    # that need to be flushed from c1 to c5
    assert pop.get_variable('c1:c5')[0].vals[0] == 10

    # For c2->c4, this corresponds to leaving the duration group. Thus all 50 people are eligible
    # for the transition, and we have a flow of 50
    assert pop.get_variable('c2:c4')[0].vals[0] == 50

    # Of those 50, 50/10=5 of them came from the final subcompartment. Thus we still need to flush
    # 5 people out of the duration group.
    assert pop.get_variable('c2:c5')[0].vals[0] == 5


def test_timed_invalid():
    with pytest.raises(Exception):
        run_framework('timed_test_indirect_framework_invalid.xlsx')


def test_timed_transfer():
    # This test has transfers between populations where the same duration group has a different duration
    # This is a common scenario e.g. if the duration of something is different in a key population
    # In this case, c1 has durations 20, 10, and 5 timesteps in pops 0, 1, and 2, respectively. The initial
    # sizes are 200, 100, and 50, thus placing 10 people in each subcompartment. We seek to transfer a total
    # of 100 people out of pop 1 in the first timestep.

    P = at.Project(framework=testdir / 'timed_test_transfer_framework.xlsx', databook=testdir / 'timed_test_transfer_databook.xlsx', do_run=True)
    pops = P.results[0].model.pops

    # First, check the initial sizes
    assert pops[0].get_comp('c1').vals[0] == 200
    assert pops[1].get_comp('c1').vals[0] == 100
    assert pops[2].get_comp('c1').vals[0] == 50

    # Then, we have outflow of 100 requested (200 people/year per transfer)
    assert pops[1].get_variable('transfer_0_pop_1_to_pop_0')[0].vals[0] == 200
    assert pops[1].get_variable('transfer_0_pop_1_to_pop_2')[0].vals[0] == 200

    # This means we request 50 people per timestep per link. Of whom, 90 are eligible (not in final subcompartment)
    # Thus transferring 45 people from pop1 to pop0 and pop2. Note that the transfer links are guaranteed to appear
    # at the end of the outlinks list because they are instantitated after the population
    assert pops[1].get_comp('c1').outlinks[1].vals[0] == 45
    assert pops[1].get_comp('c1').outlinks[2].vals[0] == 45

    # In pop0 and pop1, 10 people are flushed at the first timestep, and 45 people arrive at the next timestep. The
    # net change in population should be 35
    assert pops[0].get_comp('c1').vals[1] == 235
    assert pops[2].get_comp('c1').vals[1] == 85

    # 45 people are transferred, which is 5 people per subcompartment
    # Going into pop0, there are more subcompartments, so we end up with all of them containing 15 people
    # And with no _other_ inflow, once the keyring is advanced, we have 0 people in the initial subcompartment
    assert pops[0].get_comp('c1')._vals[8, 1] == 15  # The 10th subcompartment recieved 5 people, then the keyring was advanced
    assert pops[0].get_comp('c1')._vals[9, 1] == 10  # The 11th subcompartment recieved 0 people, then the keyring was advanced
    assert pops[0].get_comp('c1')._vals[-1, 1] == 0  # The final subcompartment had no inflow

    # Going into pop1, there are fewer subcompartments - only 5. Thus, the 5th subcompartment receives people
    # from the link from subcompartments 5 through 10. That is, 6 subcompartments worth
    assert pops[2].get_comp('c1')._vals[2, 1] == 15  # The 4th subcompartment recieved 5 people, then the keyring was advanced
    assert pops[2].get_comp('c1')._vals[3, 1] == 40  # The 5th subcompartment recieved 30 people, then the keyring was advanced
    assert pops[2].get_comp('c1')._vals[-1, 1] == 0  # The final subcompartment had no inflow

    # The absolute total outflow from all three compartments should match the initialization plus the transfer
    assert sum([l.vals.sum() for l in pops[2].get_comp('c1').outlinks]) == 95  # 50 initialized, plus 45 transferred
    assert sum([l.vals.sum() for l in pops[1].get_comp('c1').outlinks]) == 100  # 90 transitioned out, plus 10 flushed
    assert sum([l.vals.sum() for l in pops[0].get_comp('c1').outlinks]) == 245  # 200 initialized, plus 45 transferred

    # Test writing out this databook too
    D = at.ProjectData.new(framework=P.framework, tvec=[2018, 2019], pops=3, transfers=2)
    D.save(tempdir / 'timed_transfer_databook_test.xlsx')


def test_timed_transfer_2():
    # This test has zero duration in the second population

    P = at.Project(framework=testdir / 'timed_test_transfer_framework.xlsx', databook=testdir / 'timed_test_transfer_databook_2.xlsx', do_run=True)
    pops = P.results[0].model.pops

    # First, check the initial sizes
    assert pops[0].get_comp('c1').vals[0] == 200
    assert pops[1].get_comp('c1').vals[0] == 100

    # Check the outgoing transfer is as expected (200 people/year)
    assert pops[0].get_variable('transfer_0_pop_0_to_pop_1')[0].vals[0] == 200

    # This means we request 50 people per timestep. The duration in the first population is 10 timesteps. There are thus 10 bins. We move 5
    # people per bin out of 9 bins, so we move 45 people in total.
    assert pops[0].get_comp('c1').outlinks[1].vals[0] == 45

    # At the second timestep, everyone has been flushed from C1 in Pop 1. 45 people have then entered. So there should be 45 people in the compartment
    assert pops[1].get_comp('c1').vals[1] == 45

    # In the Pop 0, there were 200 people in 10 bins, so 20 people per bin. People in the final subcompartment weren't eligible to be
    # transferred because the transfer was within the same duration group. Therefore, all 20 people moved to C2 in Pop 0
    assert pops[0].get_comp('c2').vals[1] == 20


def test_timed_transfer_3():
    # This test has zero duration in the first population

    P = at.Project(framework=testdir / 'timed_test_transfer_framework.xlsx', databook=testdir / 'timed_test_transfer_databook_3.xlsx', do_run=True)
    pops = P.results[0].model.pops

    # First, check the initial sizes
    assert pops[0].get_comp('c1').vals[0] == 200
    assert pops[1].get_comp('c1').vals[0] == 100

    # Check the outgoing transfer is as expected (200 people/year)
    assert pops[0].get_variable('transfer_0_pop_0_to_pop_1')[0].vals[0] == 200

    # At the first timestep, everyone is flushed from C1 to C2 in Pop 0. Therefore, nobody makes the transfer from C1 to C2
    assert pops[0].get_comp('c1').vals[1] == 0
    assert pops[0].get_comp('c2').vals[1] == 200

    # In Pop 1, 10 people transition (due to the keyring advancing)
    assert pops[1].get_comp('c1').vals[1] == 90
    assert pops[1].get_comp('c2').vals[1] == 10

    # At the second timestep, now we can transfer 50 people from P0C2 to P1C2
    # Further, 10 more people move from P1C1 to P1C2 due to the keyring advancing
    # So we end up with
    assert pops[1].get_comp('c1').vals[2] == 80
    assert pops[1].get_comp('c2').vals[2] == 10 + 50 + 10


def test_timed_vac_duration():
    P = at.Project(framework=at.LIBRARY_PATH + 'sir_vaccine_framework.xlsx', databook=at.LIBRARY_PATH + 'sir_vaccine_databook.xlsx', do_run=False)
    P.settings.sim_dt = 0.25
    P.settings.sim_start = 2018
    P.settings.sim_end = 2030
    parset = P.make_parset('test')
    parset.pars['v_rate'].smooth(P.settings.tvec, 'previous')
    res = P.run_sim(parset)

    d = at.PlotData(res, 'v_rate')
    at.plot_series(d)

    d = at.PlotData(res, ['sus:vac', 'vac:sus'])
    at.plot_series(d)

    d = at.PlotData(res, ['sus', 'vac'])
    at.plot_series(d)

    d = at.PlotData(res, ['sus:inf', 'vac:inf'])
    at.plot_series(d)


if __name__ == '__main__':

    test_timed_invalid()
    test_timed_indirect()
    test_timed_indirect2()
    test_timed_eligibility()
    test_timed_transfer()
    test_timed_transfer_2()
    test_timed_transfer_3()
    test_spike()
    test_read_write_databook()
    test_zero_duration()
    test_timed_tb()
    test_timed_vac_duration()
