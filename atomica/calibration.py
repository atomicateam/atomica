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

# CALIBRATION LAYOUT
# Auto calibration proceeds using y-factors. The input should thus be a list
# of parameters to calibrate. The output metric would be a list of characteristics
# or flow rates that need to be matched. So calibration requires
# - A list of parameters to adjust
# - A list of output characteristics to match
#
# For example, the input parameters could be a list of birth rates and transfer rates
# and HIV infection rates, and the output parameters could be a list of characteristics
# In theory these could be population-specific?

def update_parset(parset,y_factors,pars_to_adjust):
    for i,x in enumerate(pars_to_adjust):
        par_name = x[0]
        pop_name = x[1]

        if par_name in parset.par_ids['cascade'] or par_name in parset.par_ids['characs']:
            if pop_name is None:
                par = parset.getPar(par_name)
                for pop in par.pops:
                    parset.set_scaling_factor(par_name, pop, y_factors[i])
            else:
                parset.set_scaling_factor(par_name, pop_name, y_factors[i])
        else: # For now, must be in there...
            raise NotImplemented
            tokens = par_name.split('_from_')
            par = parset.transfers[tokens[0]][tokens[1]]
            par.y_factor[pop_name] = y_factors[i]

def calculateObjective(y_factors,pars_to_adjust,output_quantities,parset,project):
    # y-factors, array of y-factors to apply to specified output_quantities
    # pars_to_adjust - list of tuples (par_name,pop_name) recognized by parset.update()
    # output_quantities - a tuple like (pop,var,weight,metric) understood by model.getPop[pop].getVar(var)
    # TODO - support Link flow rates and parameters, need to auto adjust

    update_parset(parset,y_factors, pars_to_adjust)

    result = project.runSim(parset = parset, store_results = False)

    objective = 0.0

    for var_label,pop_name,weight,metric in output_quantities:
        var = result.model.getPop(pop_name).getVariable(var_label)
        if isinstance(var[0],Characteristic):
            target = project.data.getSpec('ch_prev')['data'][pop_name]
            data_t,data_v = target.get_arrays()
        else:
            raise AtomicaException('Not yet implemented')

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

def performAutofit(proj,parset,pars_to_adjust,output_quantities,max_time=60):
    """
    Run an autofit and save resulting parameterset

    pars_to_adjust - list of tuples, (par,pop,scale) where allowed Y-factor range is 1-scale to 1+scale
    Params:
        project
        paramset
        new_parset_name     name of resulting parameterset
        target_characs      a list of characteristic and population label pairs
        calibration_settings
        useYFactor            boolean of flag whether we should use yvalues directly, or y_factor
   
    """

    args = {
        'project': proj,
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

            if pop_name is None:
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
