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
            if pop_name == "all":
                par = parset.pars[par_name]
                par.meta_y_factor = y_factors[i]
            else:
                parset.pars[par_name].y_factor[pop_name] = y_factors[i]
        else:
            # Handle transfers here
            tokens = par_name.split("_from_")
            par = parset.transfers[tokens[0]][tokens[1]]
            par.y_factor[pop_name] = y_factors[i]
            raise NotImplementedError


def _calculate_objective(y_factors, pars_to_adjust, output_quantities, parset, project, *args, **kwargs) -> float:
    """
    Run the model for a given set of y-factors and return the objective/goodness-of-fit

    Additional extra arguments will be ignored but will not raise an error.

    :param y_factors: array of y-factors to apply to specified output_quantities
    :param pars_to_adjust: list of tuples (par_name,pop_name,...) recognized by parset.update()
    :param output_quantities: a tuple containing (pop, var, weight, metric, start_year, end_year) - start year and end year are inclusive
    :param parset:
    :param project:
    :return: The value of the objective function defined by the output_quantities
    """

    _update_parset(parset, y_factors, pars_to_adjust)

    try:
        result = project.run_sim(parset=parset, store_results=False)
    except BadInitialization:  # If the proposed parameters lead to invalid initial compartment sizes
        return np.inf

    objective = 0.0

    for var_label, pop_name, weight, metric, start_year, end_year in output_quantities:

        target = project.data.get_ts(var_label, pop_name)  # This is the TimeSeries with the data for the requested quantity
        if target is None:
            continue
        if not target.has_time_data:  # Only use this output quantity if the user entered time-specific data
            continue
        var = result.model.get_pop(pop_name).get_variable(var_label)
        data_t, data_v = target.get_arrays()
        inds = (data_t >= start_year) & (data_t <= end_year)
        if np.count_nonzero(inds) == 0:
            # If no time points remain after filtering down to the time points the user requested
            logger.info(f'No data points remaining after filtering down to requested time period. Skipping...')
            continue
        data_t = data_t[inds]
        data_v = data_v[inds]

        # Interpolate the model outputs onto the data times
        # If there is data outside the range when the model was simulated, don't
        # extrapolate the model outputs
        y = data_v
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


def calibrate(project, parset: ParameterSet, pars_to_adjust, output_quantities, max_time=None, method="asd", time_period=(-np.inf, np.inf), **kwargs) -> ParameterSet:
    """
    Run automated calibration

    :param project: A project instance to provide data and sim settings
    :param parset: A :class:`ParameterSet` instance to calibrate
    :param pars_to_adjust: list of tuples, `(par_name, pop_name, lower_bound, upper_bound, initial_value)`
                           the pop name can be None, which will be expanded to all populations
                           relevant to the parameter independently, or 'all' which will instead operate
                           on the meta y factor.
    :param output_quantities: list of tuples, (var_label,pop_name,weight,metric), for use in the objective
                              function. pop_name=None will expand to all pops. pop_name='all' is not supported. The
                              output can optionally contain `(var_label, pop_name, weight, metric, start_year, end_year)`
                              to select a subset of the data for evaluating the objective. The start year and end year
                              specified here will take precedence over the time_period argument
    :param max_time: If using ASD, the maximum run time
    :param time_period: Tuple of start and end years to use for the objective function. Applies to all outputs unless
                        the output has an explicitly specified start and end year
    :param method: 'asd' or 'pso'. If using 'pso' all upper and lower limits must be finite
    :param kwargs: Dictionary of additional arguments to be passed to the optimization function, e.g. stepsize or pinitial
    :return: A calibrated :class:`ParameterSet`

    """


    # Expand out pop=None in pars_to_adjust
    p2 = []
    for par_tuple in pars_to_adjust:
        if len(par_tuple) == 5:
            initial_value = par_tuple[4]
        else:
            initial_value = None

        if par_tuple[1] is None:  # If the pop name is None
            par = parset.pars[par_tuple[0]]
            for pop_name in par.pops:
                p2.append((par_tuple[0], pop_name, par_tuple[2], par_tuple[3], initial_value))
        else:
            p2.append((par_tuple[0], par_tuple[1], par_tuple[2], par_tuple[3], initial_value))

    pars_to_adjust = p2

    # Expand out pop=None in output_quantities
    outputs = []
    for output_tuple in output_quantities:
        var_label = output_tuple[0]
        pop_name = output_tuple[1]
        weight = output_tuple[2]
        metric = output_tuple[3]
        if len(output_tuple) == 6:
            start_year = output_tuple[4]
            end_year = output_tuple[5]
        else:
            start_year = time_period[0]
            end_year = time_period[1]

        if pop_name is None:  # If the pop name is None
            for pop in project.data.pops.keys():
                outputs.append((var_label, pop, weight, metric, start_year, end_year))
        else:
            outputs.append((var_label, pop_name, weight, metric, start_year, end_year))

    output_quantities = outputs

    x0 = []
    xmin = []
    xmax = []
    filtered_pars_to_adjust = []
    parset = parset.copy()

    for i, x in enumerate(pars_to_adjust):
        par_name, pop_name, scale_min, scale_max, initial_value = x

        if par_name in parset.pars:
            par = parset.pars[par_name]
        else:
            tokens = par_name.split("_from_")
            par = parset.transfers[tokens[0]][tokens[1]]

        #if initial_value has not been explicitly set in the tuple: use y_factor in parset
        if initial_value is None:
            if pop_name == "all":
                initial_value = par.meta_y_factor
            else:
                initial_value = par.y_factor[pop_name]
            #if this value is outside the min and max bounds, make it equal to min or max (whichever is closest)
            #if min == max, this should make the initial value equal to min and max
            initial_value = np.clip(initial_value, scale_min, scale_max)
        else:
            assert (initial_value >= scale_min) and (initial_value <= scale_max), 'Initial value is not consistent with the lower/upper bounds'

        #update y_factors in parset
        if pop_name == 'all':
            par.meta_y_factor = initial_value
        else:
            par.y_factor[pop_name] = initial_value

        if scale_min != scale_max:
            # Only include the y-factor in the adjustments made in the optimization function if a range
            # of y-factor values is permitted
            filtered_pars_to_adjust.append(x)
            x0.append(initial_value)
            xmin.append(scale_min)
            xmax.append(scale_max)



    args = {
        "project": project,
        "parset": parset,
        "pars_to_adjust": filtered_pars_to_adjust,
        "output_quantities": output_quantities,
    }

    original_sim_end = project.settings.sim_end
    project.settings.sim_end = min(project.data.tvec[-1], original_sim_end)

    if len(filtered_pars_to_adjust) > 0:
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
                    "maxtime": 60 if max_time is None else max_time,
                    "minval": 0,
                }
                optim_args.update(kwargs)

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

        _update_parset(args["parset"], x1, args["pars_to_adjust"])
    else:
        logger.info('No parameters to adjust provided to the optimisation function. Skipping optimisation...')

    # Log out the commands required for equivalent manual calibration if desired
    for i, x in enumerate(pars_to_adjust):
        par_name = x[0]
        pop_name = x[1]

        if par_name in parset.pars:
            par = args["parset"].pars[par_name]

            if pop_name == "all":
                logger.debug("parset.get_par('{}').meta_y_factor={:.2f}".format(par_name, par.meta_y_factor))
            else:
                logger.debug("parset.get_par('{}').y_factor['{}']={:.2f}".format(par_name, pop_name, par.y_factor[pop_name]))

        else:
            tokens = par_name.split("_from_")
            par = args["parset"].transfers[tokens[0]][tokens[1]]
            logger.debug("parset.transfers['{}']['{}'].y_factor['{}']={:.2f}".format(tokens[0], tokens[1], pop_name, par.y_factor[pop_name]))
            raise NotImplementedError  # Transfers might be handled differently in Atomica

    args["parset"].name = "calibrated_" + args["parset"].name

    return args["parset"]
