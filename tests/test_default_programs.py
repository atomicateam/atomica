# This is a development script for implementing default
# programs in TB. It can probably be safely removed after
# it is implemented in the main codebase

import atomica.ui as au
import numpy as np
import sciris as sc
import re

# This is the information that the FE needs to supply
fe_pops = sc.odict()
fe_pops["0-15"] = "Gen 0-15"
fe_pops["15+"] = "Gen 15+"
fe_pops["15+ (HIV)"] = "Gen 15+ PLHIV"
fe_transfers = sc.odict()
fe_transfers['aging'] = 'Aging'
fe_transfers['hiv'] = 'HIV infection'
fe_data_years = [2000,2015]
fe_program_years = [2015,2018]

def generate_default_spreadsheets(fe_pops,fe_transfers,fe_data_years,fe_program_years):

    F = au.ProjectFramework("./frameworks/framework_tb.xlsx")

    # These commands get used to both write and read the template progbook
    # In practice, the main requirement is that this list of template pops
    # matches the pops in the progbook containing the defaults
    template_pops = sc.odict()
    template_pops["^0.*"] = "^0.*"
    template_pops[".*HIV.*"] = ".*HIV.*"

    # Use these comments to make the blank template for *us* to fill out
    # Normally this is just a one-off process
    D = au.ProjectData.new(F,tvec=np.array([0]),pops=template_pops,transfers=0)
    ps = au.ProgramSet.new(framework=F,data=D,progs=2,tvec=np.array([0]))
    ps.save('template_blank.xlsx')

    # Normally, all we need to do is load in the filled out template
    # This is the file that contains the default values to use for each program
    # as well as the default targeting
    default_progset = au.ProgramSet.from_spreadsheet('./databooks/progbook_tb_defaults.xlsx',framework=F,data=D)

    # Next, instantiate a new ProjectData and ProgramSet using the FE values
    user_data = au.ProjectData.new(F,tvec=np.arange(fe_data_years[0],fe_data_years[1]+1),pops=fe_pops,transfers=fe_transfers)
    progs = {prog.name:prog.label for prog in default_progset.programs.values()}
    user_progset = au.ProgramSet.new(framework=F,data=user_data,progs=progs,tvec=np.arange(fe_program_years[0],fe_program_years[1]+1))

    # Now copy over the targeting and effects into the user's progset
    for prog in user_progset.programs:

        u_prog = user_progset.programs[prog]
        d_prog = default_progset.programs[prog]

        # Copy target compartments
        u_prog.target_comps = d_prog.target_comps[:] # Make a copy of the comp list (using [:], faster than dcp)

        # Use regex matching for target pops
        for template_pop in d_prog.target_pops:
            # targeted_pops is the regex string of populations to assign as targets
            regex = re.compile(template_pop)
            for pop in user_progset.pops:
                if regex.match(pop):
                    u_prog.target_pops.append(pop)

        # Copy assumptions from spending data
        u_prog.baseline_spend.assumption = d_prog.baseline_spend.assumption
        u_prog.capacity.assumption = d_prog.capacity.assumption
        u_prog.coverage.assumption = d_prog.coverage.assumption
        u_prog.unit_cost.assumption = d_prog.unit_cost.assumption
        u_prog.spend_data.assumption = d_prog.spend_data.assumption

        # TODO - copy program effects here

    return user_data, user_progset

new_data, new_progset = generate_default_spreadsheets(fe_pops,fe_transfers,fe_data_years,fe_program_years)
new_data.save('temp/user_data.xlsx')
new_progset.save('temp/user_progset.xlsx')
