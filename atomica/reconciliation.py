"""
Implements the automatic reconciliation algorithm

In any given model run, the parameters calculated by the :py:class:`ProgramSet`
should ideally match up with the values in the :py:class:`ParameterSet` so that
there are no discontinuities in parameter value. This may not be the case depending
on the data gathered and the calibration. Reconciliation aims to adjust the
internal parameters of the :py:class:`ProgramSet` to best match a :py:class:`ParameterSet`
in a particular year.

"""

import numpy as np
import sciris as sc
from .system import logger
from .structure import FrameworkSettings as FS
import pandas as pd


def _extract_targets(result, progset, ti, eval_pars=None):
    # Store the target parset values in the same form as the progset computed parameter values
    # This will also mean that target_vals contains the par UIDs only for the impact parameters
    # requested for reconcilation (if None, then all will be used). For simplicity, just do it
    # for all programs and parameters, only the target ones will actually get looked at.
    #
    # INPUTS
    # - result : A result object for the baseline sim (it won't have a progset because it was run without programs)
    # - progset : The progset to use to get the target pars/pops and coverage denominator
    # - ti : Time indices to extract results from (could be several)
    # - eval_pars: Optional list of (par,pop) names for evaluation - otherwise, uses all impact pars

    # Get the parameter outcomes - assumes simulation end year was the reconciliation year (hence -1 index)
    target_vals = dict()
    for covout in progset.covouts.values():
        par_name, pop_name = covout.par, covout.pop
        if (eval_pars is None and result.framework.get_par(par_name)['targetable'] == 'y') or (par_name, pop_name) in eval_pars:
            par = result.get_variable(pop_name, par_name)[0]
            if par.units == FS.QUANTITY_TYPE_NUMBER:
                # If a transition parameter in number units is being targeted, then the program outcome is in units of per person reached
                # at each timestep, while the parameter units are people/year. Thus, we need to convert the model parameter into the program
                # output units prior to reconciling
                target_vals[(par_name, pop_name)] = par.vals[ti] * result.dt / np.array([par.source_popsize(x) for x in ti])
            else:
                target_vals[(par_name, pop_name)] = par.vals[ti]

    # Get the coverage denominator in the reconciliation year (it's always the same, so can do it once here)
    coverage_denominator = {x: y[ti] for x, y in result.get_coverage('denominator').items()}

    return target_vals, coverage_denominator


def _update_progset(asd_vals, mapping, progset):
    # Updates progset in place, inserting values
    # INPUTS:
    # - asd_vals - asd array
    # - mapping - list of tuples specifying where to insert elements from the ASD array
    #             e.g.  [('unit_cost','BCG'),('outcome','v_rate','0-4','BCG')]
    #             The mapping is
    #             unit_cost - program
    #             capacity - program
    #             baseline - par,pop
    #             outcome - par,pop,program
    # - progset : ProgramSet to modify, should have only one time
    for x, target in zip(asd_vals, mapping):
        if target[0] == 'unit_cost':
            assert len(progset.programs[target[1]].unit_cost.vals) == 1
            progset.programs[target[1]].unit_cost.vals[0] = x
        elif target[0] == 'capacity':
            assert len(progset.programs[target[1]].capacity.vals) == 1
            progset.programs[target[1]].capacity.vals[0] = x
        elif target[0] == 'baseline':
            progset.covouts[(target[1], target[2])].baseline = x
        elif target[0] == 'outcome':
            progset.covouts[(target[1], target[2])].progs[target[3]] = x


def _prepare_bounds(progset, unit_cost_bounds, baseline_bounds, capacity_bounds, outcome_bounds):
    # This is a separate function to _prepare_asd_inputs() because there may be complex logic related to
    # defaults for constructing the bounds. At the end, the bounds dict contains upper and lower limits
    # for every parameter being considered
    #
    # OUTPUTS
    # bounds dict : {quantity:{key:(lower,upper)} where quantity is 'unit_cost','capacity','baseline','outcome', and key is:
    #     for unit_cost - program
    #     for capacity - program
    #     for baseline - par,pop
    #     for outcome - par,pop,program

    bounds = dict()
    bounds['unit_cost'] = dict()
    bounds['capacity'] = dict()
    bounds['baseline'] = dict()
    bounds['outcome'] = dict()

    for prog in progset.programs.values():
        if unit_cost_bounds:
            bounds['unit_cost'][prog.name] = prog.unit_cost.vals * np.array([1 - unit_cost_bounds, 1 + unit_cost_bounds])
        if capacity_bounds and prog.capacity.has_data:
            bounds['capacity'][prog.name] = prog.capacity.vals * np.array([1 - capacity_bounds, 1 + capacity_bounds])

    for covout in progset.covouts.values():
        if baseline_bounds:
            bounds['baseline'][(covout.par, covout.pop)] = covout.baseline * np.array([1 - baseline_bounds, 1 + baseline_bounds])
        if outcome_bounds:
            for prog, outcome in covout.progs.items():
                bounds['outcome'][(covout.par, covout.pop, prog)] = outcome * np.array([1 - outcome_bounds, 1 + outcome_bounds])

    return bounds


def _prepare_asd_inputs(progset, bounds):
    # Return initial values, upper-lower bounds, and mapping to insert the arrays into a progset
    # Only quantities that appear in the bounds dict will be reconciled
    x0 = list()
    xmin = list()
    xmax = list()
    mapping = list()

    for prog in progset.programs.values():
        if prog.name in bounds['unit_cost']:  # Might need to check program_specific bounds here
            x0.append(prog.unit_cost.vals[0])
            xmin.append(bounds['unit_cost'][prog.name][0])
            xmax.append(bounds['unit_cost'][prog.name][1])
            mapping.append(('unit_cost', prog.name))
        if prog.name in bounds['capacity']:  # Might need to check program_specific bounds here
            x0.append(prog.capacity.vals[0])
            xmin.append(bounds['capacity'][prog.name][0])
            xmax.append(bounds['capacity'][prog.name][1])
            mapping.append(('capacity', prog.name))

    for covout in progset.covouts.values():
        if (covout.par, covout.pop) in bounds['baseline']:
            x0.append(covout.baseline)
            xmin.append(bounds['baseline'][(covout.par, covout.pop)][0])
            xmax.append(bounds['baseline'][(covout.par, covout.pop)][1])
            mapping.append(('baseline', covout.par, covout.pop))

            for prog, outcome in covout.progs.items():
                if (covout.par, covout.pop, prog) in bounds['outcome']:
                    x0.append(outcome)
                    xmin.append(bounds['outcome'][(covout.par, covout.pop, prog)][0])
                    xmax.append(bounds['outcome'][(covout.par, covout.pop, prog)][1])
                    mapping.append(('outcome', covout.par, covout.pop, prog))

    return x0, xmin, xmax, mapping


def _objective(x, mapping, progset, eval_years, target_vals, coverage_denominator, dt):
    _update_progset(x, mapping, progset)  # Apply the changes to the progset
    num_coverage = progset.get_num_coverage(tvec=eval_years, dt=dt, sample=False)  # Get number coverage using latest unit costs but default spending
    prop_coverage = progset.get_prop_coverage(tvec=eval_years, num_coverage=num_coverage, denominator=coverage_denominator, sample=False)

    obj = 0.0
    for i in range(0, len(eval_years)):
        outcomes = progset.get_outcomes(prop_coverage=prop_coverage, sample=False)
        for key in target_vals:  # Key is a (par,pop) tuple
            obj += (target_vals[key][i] - outcomes[key]) ** 2  # Add squared difference in parameter value
    return obj


def _convert_to_single_year(progset, reconciliation_year):
    # Take in a progset
    # Return a progset with values only in the reconciliation year
    # This is then what actually gets reconciled
    # And we can be sure that when we go to make changes in the reconciliation year, we do not
    # have any extra time points

    # Basically, we only need to modify program attributes
    reconciliation_year = sc.promotetoarray(reconciliation_year)
    new_progset = sc.dcp(progset)
    new_progset.tvec = reconciliation_year.copy()

    for prog in new_progset.programs.values():
        # NOTE - because of the TDVE format, we need to do the overwrite for ALL time series provided
        # (because they must all have the same time axis) even if they are not being modified by the reconciliation
        # This results in a clear mapping from the original progbook into the single-year format. Users can always
        # go back and modify the reconciled progbook
        if prog.spend_data.has_data:
            prog.spend_data.vals = prog.spend_data.interpolate(reconciliation_year)
            prog.spend_data.t = reconciliation_year.copy()
            prog.spend_data.assumption = None

        if prog.unit_cost.has_data:
            prog.unit_cost.vals = prog.unit_cost.interpolate(reconciliation_year)
            prog.unit_cost.t = reconciliation_year.copy()
            prog.unit_cost.assumption = None

        if prog.capacity.has_data:
            prog.capacity.vals = prog.capacity.interpolate(reconciliation_year)
            prog.capacity.t = reconciliation_year.copy()
            prog.capacity.assumption = None

        # This is tricky - maybe we do want to retain other values? Depends on what ends up happening with coverage
        if prog.coverage.has_data:
            prog.coverage.vals = prog.coverage.interpolate(reconciliation_year)
            prog.coverage.t = reconciliation_year.copy()
            prog.coverage.assumption = None

    return new_progset

# ASD takes in a list of values. So we need to map all of the things we are optimizing onto


def reconcile(project, parset, progset, reconciliation_year, max_time=10, unit_cost_bounds=0.0, baseline_bounds=0.0, capacity_bounds=0.0, outcome_bounds=0.0, eval_pars=None, eval_range=None):
    # INTERIM
    #
    # unit_cost_bounds = 0.2 means +/- 20%
    # Same for the other bounds
    """
    Reconciles progset to identified parset, the objective being to match the parameters as closely as possible with identified standard deviation sigma

    Params:
        project                    Project object to run simulations for reconciliation process (type: Python object)
        reconciliation year: The year in which reconciliation is to be performed


        limits : Specifies how much each quantity can be adjusted by. Can be
                 - A single number. This is shorthard for the limits being `value*[(1-limit),(1+limit)]` e.g. 0.2 would mean +/- 20%
                 - A single number, specific to a particular quantity. A quantity can be:
                 - A program unit cost - limits[prog_name]['unit_cost'] = 0.2


        constrain_budget        Flag to inform algorithm whether to constrain total budget or not (type: bool)

        eval_years  : Optional, [start_year,stop_year] can evaluate match between progset and parset over this range of times
    Returns:
        progset                 Updated progset with reconciled values
        outcome                 String denoting original and reconciled parset/progset impact comparison

    """
    # Sanitize inputs
    parset = project.parset(parset)
    progset = project.progset(progset)

    logger.warning('Reconcilation when parameter is in number units not fully tested')

    reconciliation_year = sc.promotetoarray(reconciliation_year)
    assert len(reconciliation_year) == 1, 'Reconciliation year must be a scalar'

    if eval_range is None:
        eval_range = [reconciliation_year[0], reconciliation_year[0] + project.settings.sim_dt]

    # Do a prerun to get the baseline values and coverage denominator
    parset_results = project.run_sim(parset=parset, progset=progset, store_results=False)
    ti = np.where((parset_results.model.t >= eval_range[0]) & (parset_results.model.t < eval_range[1]))[0]
    eval_years = parset_results.t[ti]
    target_vals, coverage_denominator = _extract_targets(parset_results, progset, ti, eval_pars)

    # Prepare ASD inputs
    new_progset = _convert_to_single_year(progset, reconciliation_year[0])
    bounds = _prepare_bounds(new_progset, unit_cost_bounds, baseline_bounds, capacity_bounds, outcome_bounds)  # Convert reconcile() inputs into full detailed bounds
    x0, xmin, xmax, mapping = _prepare_asd_inputs(new_progset, bounds)  # Assemble ASD variables

    logger.info("Reconciling in %.2f, evaluating from %.2f up to %.2f", reconciliation_year, eval_range[0], eval_range[1])

    args = {
        'mapping': mapping,
        'progset': new_progset,
        'eval_years': eval_years,
        'target_vals': target_vals,
        'coverage_denominator': coverage_denominator,
        'dt': project.settings.sim_dt,
    }

    optim_args = {
        # TODO - tune these variables specifically for reconciliation
        # 'stepsize': project.settings.autofit_params['stepsize'],
        # 'maxiters': project.settings.autofit_params['maxiters'],
        # 'maxtime': project.settings.autofit_params['maxtime'],
        # 'sinc': project.settings.autofit_params['sinc'],
        # 'sdec': project.settings.autofit_params['sdec'],
        'fulloutput': False,
        # 'reltol': None,
        'xmin': xmin,
        'xmax': xmax,
        'verbose': 2,  # default verbosity
        'maxtime': max_time,
    }

    x_opt, _, _ = sc.asd(_objective, x0, args, **optim_args)
    _update_progset(x_opt, mapping, new_progset)  # Apply the changes to the progset

    # Before/after for quantities
    records = [(item[0], item[1:], orig_val, opt_val) for item, orig_val, opt_val in zip(mapping, x0, x_opt)]
    progset_comparison = pd.DataFrame.from_records(records, columns=['Quantity', 'Identifier', 'Before reconciliation', 'After reconciliation'])

    # Before/after for parameters
    records = []
    old_num_coverage = progset.get_num_coverage(tvec=eval_years, dt=project.settings.sim_dt)
    new_num_coverage = new_progset.get_num_coverage(tvec=eval_years, dt=project.settings.sim_dt)
    old_prop_coverage = progset.get_prop_coverage(tvec=eval_years, num_coverage=old_num_coverage, denominator=coverage_denominator)
    new_prop_coverage = new_progset.get_prop_coverage(tvec=eval_years, num_coverage=new_num_coverage, denominator=coverage_denominator)
    for i, year in enumerate(eval_years):
        old_outcomes = progset.get_outcomes(prop_coverage={prog: cov[[i]] for prog, cov in old_prop_coverage.items()})  # Program outcomes for this year
        new_outcomes = new_progset.get_outcomes(prop_coverage={prog: cov[[i]] for prog, cov in new_prop_coverage.items()})  # Program outcomes for this year
        for (par, pop), target in target_vals.items():
            records.append((par, pop, year, target[0], old_outcomes[(par, pop)], new_outcomes[(par, pop)]))
    parameter_comparison = pd.DataFrame.from_records(records, columns=['Parameter', 'Population', 'Year', 'Target', 'Before reconciliation', 'After reconciliation'])
    parameter_comparison['Difference'] = parameter_comparison['Before reconciliation'] - parameter_comparison['After reconciliation']

    return new_progset, progset_comparison, parameter_comparison
