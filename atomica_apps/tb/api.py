import sciris.core as sc
import atomica.au as au

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

### PLOTTING ###

supported_plots = {
'Population size':'alive',
'Latent infections':'lt_inf',
'Active TB':'ac_inf',
'Active DS-TB':'ds_inf',
'Active MDR-TB':'mdr_inf',
'Active XDR-TB':'xdr_inf',
'New active DS-TB':{'New active DS-TB':['pd_div:flow','nd_div:flow']},
'New active MDR-TB':{'New active MDR-TB':['pm_div:flow','nm_div:flow']},
'New active XDR-TB':{'New active XDR-TB':['px_div:flow','nx_div:flow']},
'Smear negative active TB':'sn_inf',
'Smear positive active TB':'sp_inf',
'Latent diagnoses':{'Latent diagnoses':['le_treat:flow','ll_treat:flow']},
'New active TB diagnoses':{'Active TB diagnoses':['pd_diag:flow','pm_diag:flow','px_diag:flow','nd_diag:flow','nm_diag:flow','nx_diag:flow']},
'New active DS-TB diagnoses':{'Active DS-TB diagnoses':['pd_diag:flow','nd_diag:flow']},
'New active MDR-TB diagnoses':{'Active MDR-TB diagnoses':['pm_diag:flow','nm_diag:flow']},
'New active XDR-TB diagnoses':{'Active XDR-TB diagnoses':['px_diag:flow','nx_diag:flow']},
'Latent treatment':'ltt_inf',
'Active treatment':'num_treat',
'TB-related deaths':':ddis',
},

def plot(P,result_names,plot_names):
    result_names = sc.promotetolist(result_names)
    plot_names = sc.promotetolist(plot_names)

    results = [P.results[name] for name in result_names]

    h = []
    for plot_name in plot_names:
        d = au.PlotData(results,outputs=supported_plots[plot_name],project=P)
        # Todo - customize plot formatting here
        h += au.plot_series(d,data=P.data)

    return h