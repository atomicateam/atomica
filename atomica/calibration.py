"""
Implements automatic calibration

This module defines the :func:`calibrate` function, which is the entry-point for
automatic calibration

"""

import numpy as np
import sciris as sc
from .model import BadInitialization
from .system import logger
from .parameters import ParameterSet
import logging
import atomica

__all__ = ["calibrate"]

# TODO: Determine whether this is necessary.
calibration_settings = dict()
calibration_settings["tolerance"] = 1e-6


def _update_parset(parset, y_factors, pars_to_adjust):
    # Insert updated y-values into the parset
    # - parset : a ParameterSet object
    # - y_factors : Array with as many elements as pars_to_adjust
    # - pars_to_adjust : Array of tuples (par_name,pop_name,...) with special value pop='all' supported to set meta factor
    #                    Must have as many elements as y_factors. pop=None is not allowed - it must be converted
    #                    to a full list of pops previously (in perform_autofit)

    for i, x in enumerate(pars_to_adjust):
        par_name = x[0]
        pop_name = x[1]

        if par_name in parset.pars:
            if pop_name.lower() == "all":
                par = parset.pars[par_name]
                par.meta_y_factor = y_factors[i]
            else:
                parset.pars[par_name].y_factor[pop_name] = y_factors[i]
        else:
            # Handle transfers here
            tokens = par_name.split("_from_")
            par = parset.transfers[tokens[0]][tokens[1]]
            par.y_factor[pop_name] = y_factors[i]


def _calculate_objective(y_factors, pars_to_adjust, output_quantities, parset, project):
    # y-factors, array of y-factors to apply to specified output_quantities
    # pars_to_adjust - list of tuples (par_name,pop_name,...) recognized by parset.update()
    # output_quantities - a tuple like (pop,var,weight,metric) understood by model.get_pop[pop].getVar

    _update_parset(parset, y_factors, pars_to_adjust)

    try:
        result = project.run_sim(parset=parset, store_results=False)
    except BadInitialization:  # If the proposed parameters lead to invalid initial compartment sizes
        return np.inf

    objective = 0.0

    for var_label, pop_name, weight, metric in output_quantities:
        target = project.data.get_ts(var_label, pop_name)  # This is the TimeSeries with the data for the requested quantity
        if target is None:
            continue
        if not target.has_time_data:  # Only use this output quantity if the user entered time-specific data
            continue

        if pop_name.lower() == "total":
            var = atomica.PlotData(result, outputs=var_label, pops="total", project=project)
        else:
            var = result.model.get_pop(pop_name).get_variable(var_label)

        data_t, data_v = target.get_arrays()

        # Interpolate the model outputs onto the data times
        # If there is data outside the range when the model was simulated, don't
        # extrapolate the model outputs
        y = data_v
        if pop_name.lower() == "total":
            y2 = np.interp(data_t, var.series[0].tvec, var.series[0].vals, left=np.nan, right=np.nan)
        else:
            y2 = np.interp(data_t, var[0].t, var[0].vals, left=np.nan, right=np.nan)

        idx = ~np.isnan(y) & ~np.isnan(y2)
        objective += weight * sum(_calculate_fitscore(y[idx], y2[idx], metric))

    return objective


def _get_fitscore_func(metric):
    availfns = globals().copy()
    availfns.update(locals())
    try:
        return availfns.get("_calc_%s" % metric)
    except Exception:
        raise NotImplementedError("No method associated with _calc_%s (calibration.py)" % metric)


def _calculate_fitscore(y_obs, y_fit, metric="meansquare"):
    return _get_fitscore_func(metric)(y_obs, y_fit)


def _calc_meansquare(y_obs, y_fit):
    """
    Calcs the RMS error.

    Note: could also use implementation from sklearn in future ...
    """
    return np.sqrt(((y_fit - y_obs) ** 2).mean())


def _calc_fractional(y_obs, y_fit):
    return np.abs((y_fit - y_obs) / np.clip(y_obs, 1, None))  # Use clipping to handle cases where data has value 0


def _calc_wape(y_obs, y_fit):
    """
    Calculates the weighted absolute percentage error
    """
    return abs(y_fit - y_obs) / (y_obs.mean() + calibration_settings["tolerance"])


def calibrate(project, parset: ParameterSet, pars_to_adjust, output_quantities, max_time=60, method="asd", **kwargs) -> ParameterSet:
    """
    Run automated calibration

    :param project: A project instance to provide data and sim settings
    :param parset: A :class:`ParameterSet` instance to calibrate
    :param pars_to_adjust: list of tuples, (par_name,pop_name,lower_limit,upper_limit)
                           the pop name can be None, which will be expanded to all populations
                           relevant to the parameter independently, or 'all' which will instead operate
                           on the meta y factor. To calibrate a transfer, the parameter name should be set to
                           ``'<tranfer_code_name>_from_<from_pop>'`` and then the destination population can be specified
                           as the ``pop_name``. For example, to automatically calibrate an aging transfer 'age' from 5-14
                           to 15-64, the tuple would contain ``pars_to_adjust=[('age_from_5-14','15-64',...)]``
    :param output_quantities: list of tuples, (var_label,pop_name,weight,metric), for use in the objective
                              function. pop_name=None will expand to all pops. pop_name='all' is not supported. In some cases,
                              it may be desirable to fit to an aggregated total value across populations. In such cases, the
                              databook should have an extra row in the TDVE table for a population called "Total". The measurable
                              can then be given pop_name="Total" which will cause the Atomica model outputs to be aggregated over
                              all populations, and the aggregate value compared to the "Total" data. The aggregation methods will
                              be automatically selected depending on units of the quantity (sum for "number" units, average for others).
    :param max_time: If using ASD, the maximum run time
    :param method: 'asd' or 'pso'. If using 'pso' all upper and lower limits must be finite
    :param kwargs: Dictionary of additional arguments to be passed to the optimization function, e.g. stepsize or pinitial
    :return: A calibrated :class:`ParameterSet`

    """

    # Expand out pop=None in pars_to_adjust
    p2 = []
    for par_tuple in pars_to_adjust:
        if par_tuple[1] is None:  # If the pop name is None
            par = parset.pars[par_tuple[0]]
            for pop_name in par.pops:
                p2.append((par_tuple[0], pop_name, par_tuple[2], par_tuple[3]))
        else:
            p2.append(par_tuple)
    pars_to_adjust = p2

    # Expand out pop=None in output_quantities
    o2 = []
    for output_tuple in output_quantities:
        if output_tuple[1] is None:  # If the pop name is None
            pops = project.data.pops.keys()
            for pop_name in pops:
                o2.append((output_tuple[0], pop_name, output_tuple[2], output_tuple[3]))
        else:
            o2.append(output_tuple)
    output_quantities = o2

    args = {
        "project": project,
        "parset": parset.copy(),
        "pars_to_adjust": pars_to_adjust,
        "output_quantities": output_quantities,
    }

    x0 = []
    xmin = []
    xmax = []
    for i, x in enumerate(pars_to_adjust):
        par_name, pop_name, scale_min, scale_max = x
        if par_name in parset.pars:
            par = parset.pars[par_name]
            if pop_name.lower() == "all":
                x0.append(par.meta_y_factor)
            else:
                x0.append(par.y_factor[pop_name])
        else:
            tokens = par_name.split("_from_")
            par = parset.transfers[tokens[0]][tokens[1]]
            x0.append(par.y_factor[pop_name])
        xmin.append(scale_min)
        xmax.append(scale_max)

    original_sim_end = project.settings.sim_end
    project.settings.sim_end = min(project.data.tvec[-1], original_sim_end)

    try:
        if method == "asd":
            optim_args = {
                "stepsize": 0.1,
                "maxiters": 2000,
                "sinc": 1.5,
                "sdec": 2.0,
                "reltol": 1e-3,
                "abstol": 1e-6,
                "xmin": xmin,
                "xmax": xmax,
            }
            optim_args.update(kwargs)

            if max_time is not None:
                optim_args["maxtime"] = max_time

            log_level = logger.getEffectiveLevel()
            if log_level < logging.WARNING:
                optim_args["verbose"] = 2
            else:
                optim_args["verbose"] = 0

            opt_result = sc.asd(_calculate_objective, x0, args, **optim_args)
            x1 = opt_result["x"]
        elif method == "pso":
            import pyswarm

            optim_args = {"maxiter": 3, "lb": xmin, "ub": xmax, "minstep": 1e-3, "debug": True}
            if np.any(~np.isfinite(xmin)) or np.any(~np.isfinite(xmax)):
                errormsg = "PSO optimization requires finite upper and lower bounds to specify the search domain (i.e. every parameter being adjusted needs to have finite bounds)"
                raise Exception(errormsg)

            x1, _ = pyswarm.pso(_calculate_objective, kwargs=args, **optim_args)
        else:
            raise Exception("Unrecognized method")
    except Exception as e:
        raise e
    finally:
        project.settings.sim_end = original_sim_end  # Restore the simulation end year

    _update_parset(args["parset"], x1, pars_to_adjust)

    # Log out the commands required for equivalent manual calibration if desired
    for i, x in enumerate(pars_to_adjust):
        par_name = x[0]
        pop_name = x[1]

        if par_name in parset.pars:
            par = args["parset"].pars[par_name]

            if pop_name.lower() == "all":
                logger.debug("parset.get_par('{}').meta_y_factor={:.2f}".format(par_name, par.meta_y_factor))
            else:
                logger.debug("parset.get_par('{}').y_factor['{}']={:.2f}".format(par_name, pop_name, par.y_factor[pop_name]))

        else:
            tokens = par_name.split("_from_")
            par = args["parset"].transfers[tokens[0]][tokens[1]]
            logger.debug("parset.transfers['{}']['{}'].y_factor['{}']={:.2f}".format(tokens[0], tokens[1], pop_name, par.y_factor[pop_name]))

    args["parset"].name = "calibrated_" + args["parset"].name

    return args["parset"]
