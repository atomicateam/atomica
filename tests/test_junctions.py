## This script checks that the junction update is correct

import numpy as np
import atomica.ui as au
import os

testdir = au.parent_dir()
tmpdir = os.path.join(testdir,'temp','')

F_path = testdir + "framework_junction_test.xlsx"
D_path = tmpdir + "databook_junction_test.xlsx"

F = au.ProjectFramework(F_path)
D = au.ProjectData.new(F,np.arange(2000,2001),pops={'pop1':'Population 1'},transfers=0)
D.save(D_path)

P = au.Project(name="test", framework=F, do_run=False)
P.load_databook(databook_path=D_path, make_default_parset=True, do_run=True)

d = au.PlotData(P.results[0],[':ca',':cb','cb:',':cc',':ce','ce'],project=P)
au.plot_series(d,axis='pops')

# Do some validation checks
pop = P.results[0].model.pops[0]

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

# Which means that there are scheduled to be 25 people removed from A
assert pop.get_links('a1')[0].vals[1] == 25

# Which means that there should be 12.5 people transferred to C and D via those links
assert pop.get_links('jb1')[0].vals[1] == 12.5
assert pop.get_links('jb2')[0].vals[1] == 12.5

# Then, junction C has a total inflow of 12.5 people from B, and 25 people from A. Thus
# the flow to E and F should be (12.5+25)/2=18.75, while the flow to G and H should be
# 12.5/2=6.25. And that should be the same at ALL subsequent times (no NaN at the end)
assert np.all(pop.get_links('jc1:flow')[0].vals[1:] == 18.75)
assert np.all(pop.get_links('jc2:flow')[0].vals[1:] == 18.75)
assert np.all(pop.get_links('jd1:flow')[0].vals[1:] == 6.25)
assert np.all(pop.get_links('jd2:flow')[0].vals[1:] == 6.25)

print('Test successfully completed')