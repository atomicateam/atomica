# This script checks that the junction update is correct

import numpy as np
import atomica as at
import os

testdir = os.path.abspath(os.path.join(os.path.dirname(__file__))) + os.sep  # Must be relative to current file to work with tox


def test_junctions():

    F = at.ProjectFramework(testdir + "framework_junction_test.xlsx")
    D = at.ProjectData.new(F, np.arange(2000, 2001), pops={'pop1': 'Population 1'}, transfers=0)

    P = at.Project(name="test", framework=F, do_run=False)
    P.settings.update_time_vector(dt=0.25)
    P.load_databook(databook_path=D.to_spreadsheet(), make_default_parset=True, do_run=True)

    d = at.PlotData(P.results[0], [':ca', ':cb', 'cb:', ':cc', ':ce', 'ce'], project=P)
    at.plot_series(d, axis='pops')

    # Do some validation checks
    pop = P.results[0].model.pops[0]

    # The junction setup is this - B, C, and D are all junctions. We have
    # B -> C,D (50/50)
    # C -> E,F (50/50)
    # D -> G,H (50/50)
    #
    # We also have that junction C has an extra 100 people/year after the simulation starts

    # CHECK INITIAL FLUSH
    # Initially, the junctions are all initialized as having 500 people. And there is a 50% split between
    # all junctions. Therefore, we should have
    # Junction C and D acquire 250 people at the first timestep, for a total of 750 people
    # Compartments E, F, G, H each get 750/2=375 people at the first timestep

    # Check junctions are flushed
    assert pop.get_comp('cb').vals[0] == 0
    assert pop.get_comp('cc').vals[0] == 0
    assert pop.get_comp('cd').vals[0] == 0

    assert pop.get_comp('ce').vals[0] == 375
    assert pop.get_comp('cf').vals[0] == 375
    assert pop.get_comp('cg').vals[0] == 375
    assert pop.get_comp('ch').vals[0] == 375

    # After this initial flush, the junctions should now be empty. However, junction C has an inflow of
    # 100 people per year directly from the input. Therefore, the flow into E and F should be 25/2=12.5, while
    # flow into G and H should be zero
    assert pop.get_links('jb1:flow')[0].vals[0] == 0
    assert pop.get_links('jb2:flow')[0].vals[0] == 0
    assert pop.get_links('jc1:flow')[0].vals[0] == 12.5
    assert pop.get_links('jc2:flow')[0].vals[0] == 12.5
    assert pop.get_links('jd1:flow')[0].vals[0] == 0
    assert pop.get_links('jd2:flow')[0].vals[0] == 0

    # Then, after the first timestep, there are 25 people in compartment A
    assert pop.get_comp('ca').vals[1] == 25

    # Which means that there are scheduled to be 25/4 people removed from A
    # (i.e. an annual probability of 1 means that 25% of the compartment is removed this timestep)
    assert pop.get_links('a1')[0].vals[1] == 25 / 4

    # Which means that there should have been be 50% of this number transferred to C and D via those links
    # at that timestep
    assert pop.get_links('jb1')[0].vals[1] == 25 / 4 / 2
    assert pop.get_links('jb2')[0].vals[1] == 25 / 4 / 2

    # Then, junction C has a total inflow of 3.125 people from B, and 25 people from src. Thus
    # the flow to E and F should be (3.125+25)/2=14.0625, while the flow to G and H should be
    # 3.125/2=1.5625. And that should be the same at ALL subsequent times (no NaN at the end)
    assert np.all(pop.get_links('jc1:flow')[0].vals[1] == 14.0625)
    assert np.all(pop.get_links('jc2:flow')[0].vals[1] == 14.0625)
    assert np.all(pop.get_links('jd1:flow')[0].vals[1] == 1.5625)
    assert np.all(pop.get_links('jd2:flow')[0].vals[1] == 1.5625)

    # The equilibrium solution has 100 people/year flowing into A with 100% outflow implying
    # 25 people flowing out per timestep. Thus the final values should be that 25 people get
    # removed per timestep from A, not 25/4. So in the long term, we converge asymptotically
    # to the values below - no NaN at the end
    assert np.allclose(pop.get_links('jc1:flow')[0].vals[-1], 18.75, 1e-3)
    assert np.allclose(pop.get_links('jc2:flow')[0].vals[-1], 18.75, 1e-3)
    assert np.allclose(pop.get_links('jd1:flow')[0].vals[-1], 6.25, 1e-3)
    assert np.allclose(pop.get_links('jd2:flow')[0].vals[-1], 6.25, 1e-3)

    print('Test successfully completed')


def test_only_junctions():
    # This is a minimal framework that has a source connected only to junctions and then sinks
    # So there are no normal compartments
    F = at.ProjectFramework(testdir + "test_only_junctions_framework.xlsx")
    D = at.ProjectData.new(F, [2018], pops=1, transfers=0)

    P = at.Project(name="test", framework=F, databook=D.to_spreadsheet(), do_run=True)
    res = P.results[0]

    assert res.get_variable('state1')[0].vals[0] == 0
    assert res.get_variable('state1')[0].vals[1] == 40
    assert res.get_variable('state1')[0].vals[2] == 80

    assert res.get_variable('state2')[0].vals[0] == 0
    assert res.get_variable('state2')[0].vals[1] == 60
    assert res.get_variable('state2')[0].vals[2] == 120


if __name__ == '__main__':
    # test_junctions()
    test_only_junctions()
