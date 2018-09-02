import atomica.ui as au
import numpy as np
import sciris as sc

F = au.ProjectFramework("./frameworks/framework_tb.xlsx")
D = au.ProjectData.from_spreadsheet("./databooks/databook_tb.xlsx",framework=F)
# pset = au.ProgramSet.from_spreadsheet("./databooks/progbook_tb.xlsx",F,D)
# pset.save('temp/progbook_test.xlsx')
# pset = au.ProgramSet.from_spreadsheet("temp/progbook_test.xlsx",F,D)
# pset.save('temp/progbook_test2.xlsx')
#
# # Test adding things
# pset.add_program('newprog','New Program')
# pset.add_par('newpar','New Parameter')
# pset.add_pop('newpop','New Pop')
# pset.save('temp/progbook_test3.xlsx')
#
# # Test removing things
# pset.remove_pop('Miners')
# pset.remove_pop('PLHIV Miners')
# pset.remove_comp('Susceptible')
# pset.remove_par('v_rate')
# pset.remove_par('LTBI treatment uptake rate')
# pset.save('temp/progbook_test4.xlsx')
#
# # Test making a new one
# pset = au.ProgramSet.new(tvec=np.arange(2015,2018),progs=2,framework=F,data=D)
# pset.save("temp/progbook_test5.xlsx")
#
# progs = sc.odict()
# progs['BCG'] = 'BCG vaccination'
# progs['PCF'] = 'Passive case finding'
# progs['ACF'] = 'Active case finding - contact tracing'
# progs['ACF-p'] = 'Active case finding - prisoners'
# progs['HospDS'] = 'Hospital focused treatment (DS)'
# progs['HospMDR'] = 'Hospital focused treatment (MDR)'
# progs['HospXDR'] = 'Hospital focused treatment (XDR)'
# progs['AmbDS'] = 'Ambulatory treatment (DS)'
# progs['AmbMDR'] = 'Ambulatory treatment (MDR)'
# progs['AmbXDR'] = 'Ambulatory treatment (XDR)'
# progs['PrisDS'] = 'Prisoner treatment (DS)'
# progs['PrisMDR'] = 'Prisoner treatment (MD)'
# progs['PrisXDR'] = 'Prisoner treatment (XDR)'
# pset = au.ProgramSet.new(tvec=np.arange(2015,2018),progs=progs,framework=F,data=D)
# pset.save("temp/progbook_test6.xlsx")

# Test performance of a random coverage interaction simulation
P = au.Project(framework="./frameworks/framework_tb.xlsx",databook_path="./databooks/databook_tb.xlsx",do_run=False)
P.load_progbook("./databooks/progbook_tb.xlsx")
instructions = au.ProgramInstructions(start_year=2018)
pset = P.progsets[0]
for covout in pset.covouts.values():
    covout.cov_interaction = 'additive'
P.run_sim(parset='default',progset='default',progset_instructions=instructions)

# THIS DOES VERSIONING
# which = ['tb','sir','udt','hiv','usdt','hypertension']
# for a in which:
#     F = au.ProjectFramework("./frameworks/framework_%s.xlsx" % (a))
#     D = au.ProjectData.from_spreadsheet("./databooks/databook_%s.xlsx" % (a),framework=F)
#     pset = au.ProgramSet.from_spreadsheet("./databooks/progbook_%s.xlsx" % (a),F,D)
#     pset.save("./databooks/progbook_%s.xlsx" % (a))