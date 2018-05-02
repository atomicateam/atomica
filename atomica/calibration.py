import logging
logger = logging.getLogger(__name__)

from atomica.system import AtomicaException
from sciris.utils import tic, toc, odict
from atomica.asd import asd

from atomica.model import Compartment, Characteristic, Link, Parameter

import numpy as np
from copy import deepcopy as dcp

from atomica.interpolation import interpolateFunc

"""

Calibration and sensitivity analysis

"""

def update_parset(parset,y_factors,pars_to_adjust):
    # Insert updated y-values into the parset
    # - parset : a ParameterSet object
    # - y_factors : Array with as many elements as pars_to_adjust
    # - pars_to_adjust : Array of tuples (par_name,pop_name,...) with special value pop='all' supported
    #                    Must have as many elements as y_factors. pop=None is not allowed - it must be converted
    #                    to a full list of pops previously (in performAutofit)

    for i,x in enumerate(pars_to_adjust):
        par_name = x[0]
        pop_name = x[1]

        if par_name in parset.par_ids['cascade'] or par_name in parset.par_ids['characs']:
            if pop_name == 'all':
                par = parset.getPar(par_name)
                for pop in par.pops:
                    parset.set_scaling_factor(par_name, pop, y_factors[i])
            else:
                parset.set_scaling_factor(par_name, pop_name, y_factors[i])
        else:
            # Handle transfers here
            raise NotImplemented
            tokens = par_name.split('_from_')
            par = parset.transfers[tokens[0]][tokens[1]]
            par.y_factor[pop_name] = y_factors[i]

def calculateObjective(y_factors,pars_to_adjust,output_quantities,parset,project):
    # y-factors, array of y-factors to apply to specified output_quantities
    # pars_to_adjust - list of tuples (par_name,pop_name,...) recognized by parset.update()
    # output_quantities - a tuple like (pop,var,weight,metric) understood by model.getPop[pop].getVar

    update_parset(parset,y_factors, pars_to_adjust)

    result = project.runSim(parset = parset, store_results = False)

    objective = 0.0

    for var_label,pop_name,weight,metric in output_quantities:
        var = result.model.getPop(pop_name).getVariable(var_label)
        target = project.data.getSpec(var_label)['data'][pop_name]
        data_t,data_v = target.get_arrays()

        y = data_v
        y2 = interpolateFunc(var[0].t,var[0].vals,data_t)

        objective += weight* sum(_calculateFitscore(y, y2, metric))

    return objective

def _getFitscoreFunc(metric):
    """
    
    
    """
    availfns = globals().copy()
    availfns.update(locals())
    try:
        return availfns.get('_calc_%s'%metric)
    except:
        raise NotImplementedError("No method associated with _calc_%s (calibration.py)"%metric)
           
def _calculateFitscore(y_obs, y_fit,metric="meansquare"):
    """
    

    """
    return _getFitscoreFunc(metric)(y_obs,y_fit)
    
def _calc_meansquare(y_obs,y_fit):
    """
    Calcs the RMS error. 
    
    Note: could also use implementation from sklearn in future ... 
    """
    return np.sqrt(((y_fit - y_obs) ** 2).mean())

def _calc_fractional(y_obs,y_fit):
    return np.abs((y_fit-y_obs)/np.clip(y_obs,1,None)) # Use clipping to handle cases where data has value 0

def _calc_wape(y_obs,y_fit):
    """
    Calculates the weighted absolute percentage error 
    """
    return abs(y_fit - y_obs) / (y_obs.mean() + settings.TOLERANCE)

def _calc_R2(y_obs,y_fit):
    """
    
    """
    raise NotImplementedError

def performAutofit(project,parset,pars_to_adjust,output_quantities,max_time=60):
    """
    Run an autofit and save resulting parameterset

    pars_to_adjust - list of tuples, (par_name,pop_name,lower_limit,upper_limit)
                     the pop name can be None, which will be expanded to all populations
                     relevant to the parameter independently, or 'all' which will use the
                     same y-factor for all populations. The initial y-value is the current
                     y-value OR in the case of 'all', the average of the y-values across pops
    output_quantities - list of tuples, (var_label,pop_name,weight,metric), for use in the objective
                        function. pop_name=None will expand to all pops. pop_name='all' is not supported
    Params:
        project
        paramset
        new_parset_name     name of resulting parameterset
        target_characs      a list of characteristic and population label pairs
        calibration_settings
        useYFactor            boolean of flag whether we should use yvalues directly, or y_factor
   
    """

    # Expand out pop=None in pars_to_adjust
    p2 = []
    for par_tuple in pars_to_adjust:
        if par_tuple[1] is None: # If the pop name is None
            par = parset.getPar(par_tuple[0])
            for pop_name in par.pops:
                p2.append((par_tuple[0],pop_name,par_tuple[2],par_tuple[3]))
        else:
            p2.append(par_tuple)
    pars_to_adjust = p2

    # Expand out pop=None in output_quantities
    o2 = []
    for output_tuple in output_quantities:
        if output_tuple[1] is None: # If the pop name is None
            pops = project.data.getSpec(output_tuple[0])['data'].keys()
            for pop_name in pops:
                o2.append((output_tuple[0],pop_name,output_tuple[2],output_tuple[3]))
        else:
            o2.append(output_tuple)
    output_quantities = o2


    args = {
        'project': project,
        'parset': dcp(parset),
        'pars_to_adjust': pars_to_adjust,
        'output_quantities': output_quantities,
    }

    x0 = []
    xmin = []
    xmax = []
    for i,x in enumerate(pars_to_adjust):
        par_name, pop_name, scale_min, scale_max = x
        if par_name in parset.par_ids['cascade'] or par_name in parset.par_ids['characs']:
            par = parset.getPar(par_name)
            if pop_name == 'all':
                x0.append(np.mean([par.y_factor[p] for p in par.pops]))
            else:
                x0.append(par.y_factor[pop_name])
        else:
            tokens = par_name.split('_from_')
            par = parset.transfers[tokens[0]][tokens[1]]
            x0.append(par.y_factor[pop_name])
        xmin.append(scale_min)
        xmax.append(scale_max)

    optim_args = {
                 'stepsize': 0.1,
                 'maxiters': 2000,
                 'sinc': 1.5,
                 'sdec': 2.,
                 'fulloutput': False,
                 'reltol': 1e-3,
                 'abstol':1e-6,
                 'xmin': xmin,
                 'xmax': xmax,
                 }

    if not max_time is None:
        optim_args['maxtime'] = max_time

    x1, _, _ = asd(calculateObjective, x0, args, **optim_args)

    update_parset(args['parset'],x1,pars_to_adjust)

    for i,x in enumerate(pars_to_adjust):
        par_name = x[0]
        pop_name = x[1]

        if par_name in parset.par_ids['cascade'] or par_name in parset.par_ids['characs']:
            par = args['parset'].getPar(par_name)

            if pop_name is None or pop_name == 'all':
                for pop in par.pops:
                    print("parset.getPar('{}').y_factor['{}']={:.2f}" .format(par_name, pop, par.y_factor[pop]))
            else:
                print("parset.getPar('{}').y_factor['{}']={:.2f}".format(par_name, pop_name, par.y_factor[pop_name]))

        else:
            raise NotImplemented # Transfers might be handled differently in Atomica
            tokens = par_name.split('_from_')
            par = args['parset'].transfers[tokens[0]][tokens[1]]
            print("parset.transfers['{}']['{}'].y_factor['{}']={:.2f}".format(tokens[0], tokens[1], pop_name,par.y_factor[pop_name]))

    args['parset'].name = 'calibrated_' + args['parset'].name
    return args['parset']
