# This is a development script for implementing default
# programs in TB. It can probably be safely removed after
# it is implemented in the main codebase

import atomica as at
import numpy as np
import sciris as sc
import re

# This is the information that the FE needs to supply
fe_pops = sc.odict()
fe_pops["0-15"] = "Gen 0-15"
fe_pops["15+"] = "Gen 15+"
fe_pops["0-15 (HIV)"] = "Gen 0-15 PLHIV"  # This should match 0-15 only
fe_pops["15+ (HIV)"] = "Gen 15+ PLHIV"
fe_pops['0-4'] = 'Children 0-4'
fe_pops['5-14'] = 'Children 5-14'
fe_pops['15-64'] = 'Adults 15-64'
fe_pops['65+'] = 'Adults 65+'
fe_pops['Prisoners'] = 'Prisoners'
fe_transfers = sc.odict()
fe_transfers['aging'] = 'Aging'
fe_transfers['hiv'] = 'HIV infection'
fe_data_years = [2000, 2015]
fe_program_years = [2015, 2018]


def get_default_programs():
    F = at.ProjectFramework(at.LIBRARY_PATH + 'tb_framework.xlsx')
    default_pops = sc.odict()
    default_pops['^0.*'] = '^0.*'
    default_pops['.*HIV.*'] = '.*HIV.*'
    default_pops['.*[pP]rison.*'] = '.*[pP]rison.*'
    default_pops['^[^0](?!HIV)(?![pP]rison).*'] = '^[^0](?!HIV)(?![pP]rison).*'

    # Use these comments to make the blank template for *us* to fill out
    # Normally this is just a one-off process
    D = at.ProjectData.new(F, tvec=np.array([0]), pops=default_pops, transfers=0)
    default_progset = at.ProgramSet.from_spreadsheet(at.LIBRARY_PATH + 'tb_progbook_defaults.xlsx', framework=F, data=D)

    return sc.odict([(key, default_progset.programs[key].label) for key in default_progset.programs.keys()])


def generate_blank_default_spreadsheets(num_progs, default_pops=None):
    if default_pops is None:
        default_pops = sc.odict()
        default_pops['^0.*'] = '^0.*'
        default_pops['.*HIV.*'] = '.*HIV.*'
        default_pops['.*[pP]rison.*'] = '.*[pP]rison.*'
        default_pops['^[^0](?!HIV)(?![pP]rison).*'] = '^[^0](?!HIV)(?![pP]rison).*'

    F = at.ProjectFramework(at.LIBRARY_PATH + 'tb_framework.xlsx')
    D = at.ProjectData.new(F, tvec=np.array([0]), pops=default_pops, transfers=0)
    ps = at.ProgramSet.new(framework=F, data=D, progs=num_progs, tvec=np.array([0]))
    ps.save('template_blank.xlsx')


def generate_default_spreadsheets(fe_pops, fe_transfers, fe_data_years, fe_program_years, fe_progs=None):

    F = at.ProjectFramework(at.LIBRARY_PATH + 'tb_framework.xlsx')

    # These commands get used to both write and read the template progbook
    # In practice, the main requirement is that this list of template pops
    # matches the pops in the progbook containing the defaults
    default_pops = sc.odict()
    default_pops['^0.*'] = '^0.*'
    default_pops['.*HIV.*'] = '.*HIV.*'
    default_pops['.*[pP]rison.*'] = '.*[pP]rison.*'
    default_pops['^[^0](?!HIV)(?![pP]rison).*'] = '^[^0](?!HIV)(?![pP]rison).*'

    # Use these comments to make the blank template for *us* to fill out
    # Normally this is just a one-off process
    D = at.ProjectData.new(F, tvec=np.array([0]), pops=default_pops, transfers=0)
#    ps = at.ProgramSet.new(framework=F,data=D,progs=27,tvec=np.array([0]))
#    ps.save('template_blank.xlsx')

    # Normally, all we need to do is load in the filled out template
    # This is the file that contains the default values to use for each program
    # as well as the default targeting
    default_progset = at.ProgramSet.from_spreadsheet(at.LIBRARY_PATH + 'tb_progbook_defaults.xlsx', framework=F, data=D)

    # Next, instantiate a new ProjectData and ProgramSet using the FE values
    user_data = at.ProjectData.new(F, tvec=np.arange(fe_data_years[0], fe_data_years[1] + 1), pops=fe_pops, transfers=fe_transfers)
    progs = sc.odict()
    for prog in default_progset.programs.values():
        progs[prog.name] = prog.label
    user_progset = at.ProgramSet.new(framework=F, data=user_data, progs=progs, tvec=np.arange(fe_program_years[0], fe_program_years[1] + 1))

    # Assign a template pop to each user pop
    # It stops after the first match, so the regex should be ordered in
    # decreasing specificity in the template progbook
    # Maybe don't need this?
    pop_assignment = sc.odict()  # Which regex goes with each user pop {user_pop:template:pop}
    for user_pop in user_progset.pops:
        for default_pop in default_progset.pops:
            if re.match(default_pop, user_pop):
                pop_assignment[user_pop] = default_pop
                break
        else:
            pop_assignment[user_pop] = None

    if fe_progs is None:
        gen_progs = user_progset.programs
    else:
        gen_progs = sc.odict([(prog, user_progset.programs[prog]) for prog in user_progset.programs.keys() if prog in fe_progs or user_progset.programs[prog].label in fe_progs])

    for prog in gen_progs:

        u_prog = user_progset.programs[prog]
        d_prog = default_progset.programs[prog]

        # Copy target compartments
        u_prog.target_comps = d_prog.target_comps[:]  # Make a copy of the comp list (using [:], faster than dcp)

        # Assign target populations
        for user_pop in user_progset.pops:
            if pop_assignment[user_pop] in d_prog.target_pops:
                u_prog.target_pops.append(user_pop)

        # Copy assumptions from spending data
        u_prog.baseline_spend.assumption = d_prog.baseline_spend.assumption
        u_prog.capacity.assumption = d_prog.capacity.assumption
        u_prog.coverage.assumption = d_prog.coverage.assumption
        u_prog.unit_cost.assumption = d_prog.unit_cost.assumption
        u_prog.spend_data.assumption = d_prog.spend_data.assumption

    for user_par in user_progset.pars:
        for user_pop in user_progset.pops:
            default_pop = pop_assignment[user_pop]
            if (user_par, default_pop) in default_progset.covouts:
                user_progset.covouts[(user_par, user_pop)] = sc.dcp(default_progset.covouts[(user_par, default_pop)])
                user_progset.covouts[(user_par, user_pop)].pop = user_pop

    return user_data, user_progset


new_data, new_progset = generate_default_spreadsheets(fe_pops, fe_transfers, fe_data_years, fe_program_years)
tmpdir = at.atomica_path(['tests', 'temp'])
new_data.save(tmpdir + 'user_data.xlsx')
new_progset.save(tmpdir + 'user_progset.xlsx')

progs = get_default_programs()
print(progs)
