import sciris.core as sc
import atomica.ui as au

def new_project(name, start, end, pops):
    # Todo - actually use start, end, pops
    P = au.Project(name, framework='tb_gui_framework.xlsx', databook_path=None, do_run=False)
    return P

def run(P,start, end, parset_name):
    if end < start: raise au.AtomicaInputError
    if parset_name not in P.parsets: raise au.NotFoundError
    P.settings.update_time_vector(start,end)
    return P.run(parset=parset_name,store_results=True)


def calibrate(P,start, end, parset_name, mode, max_time):
    if end < start: raise au.AtomicaInputError
    if parset_name not in P.parsets: raise au.NotFoundError
    if mode not in ['demographic','epi']: raise au.AtomicaInputError

    if mode == 'demographic':
        adjustables, measurables = demographic_inputs(P.parsets[parset_name])
    else:
        adjustables, measurables = epi_inputs(P.parsets[parset_name])

    P.settings.update_time_vector(start,end)
    new_parset = P.calibrate(parset_name, adjustables, measurables, max_time, save_to_project=True)
    return new_parset

def demographic_inputs(parset):

    # Adjust birth rates
    adjustables = []
    adjustables.append(('b_rate',None,0.5,2.0)) # Birth rate

    # Adjust all transfer parameters
    for x in parset.transfers.values(): # for transfer type
        for y in x.values(): # for from_pop
            adjustables.append((y.label,None,0.1,2.0))

    # Adjust death rate
    adjustables.append(('doth_rate',None,0.5,2.0)) # Birth rate

    # TODO - uncomment commands below but base it on Atomica HIV population attribute
    # death_pars.append(('doth_rate_off_art','15-64 (HIV+)',0.1,10.0))
    # death_pars.append(('doth_rate_off_art','65+ (HIV+)',0.1,10.0))
    # death_pars.append(('doth_rate_on_art','15-64 (HIV+)',0.1,10.0))
    # death_pars.append(('doth_rate_on_art','65+ (HIV+)',0.1,10.0))
    # death_pars.append(('doth_rate','15-64 (HIV+)',0.1,10.0))
    # death_pars.append(('doth_rate','65+ (HIV+)',0.1,10.0))

    # Adjust emigration TODO - decide if GUI Framework will include this
    adjustables.append(('emi_rate','all',0.1,1.2))

    # Collate the output demographic quantities (just alive for all pops)
    measurables = []
    measurables.append(('alive',None,1.0,"fractional"))

    return (adjustables,measurables)


def epi_inputs(project, parset, max_time=60):

    # Adjust force of infection
    adjustables = []
    adjustables.append(('spd_infxness', 'all', 0.01, 100))
    adjustables.append(('phi_early', 'all', 0.01, 100))
    adjustables.append(('phi_late', 'all', 0.01, 100))
    adjustables.append(('p_act_early', 'all', 0.01, 100))
    adjustables.append(('xi', 'all', 0.01, 100))
    adjustables.append(('xi_off_art', '15-64 (HIV+)', 1, 100))
    adjustables.append(('xi_off_art', '65+ (HIV+)', 1, 100))
    adjustables.append(('p_act_early_off_art', '15-64 (HIV+)', 1, 100))
    adjustables.append(('p_act_early_off_art', '65+ (HIV+)', 1, 100))

    # Calibrate initially to total number of infections
    measurables = []
    measurables.append(('le_inf',None,1.0,"fractional"))
    measurables.append(('ll_inf',None,1.0,"fractional"))
    measurables.append(('l_inf',None,1.0,"fractional"))
    measurables.append(('ac_inf',None,1.0,"fractional"))

    return (adjustables,measurables)