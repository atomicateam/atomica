"""
Define classes for handling scenarios


This module implements the classes used to represent the four
main types of scenarios in Atomica:

- Parameter scenarios
- Budget scenarios
- Capacity scenarios
- Coverage scenarios

There are broadly two kinds of scenario

- Parameter scenarios which involve modifying a :class:`ParameterSet` instance
- Program scenarios (budget, capacity, coverage) which involve modifying a :class:`ProgramInstructions` instance

"""

import numpy as np
import sciris as sc
from .system import logger
from .utils import NamedItem
from .programs import ProgramInstructions
from .utils import TimeSeries

class Scenario(NamedItem):
    """
    Base scenario class

    All Scenario objects share this type. It is a NamedItem that also has an
    ``active`` property which represents whether the scenario should be run
    as part of :meth:`project.Project.run_scenarios`

    """

    def __init__(self, name, active=None):
        NamedItem.__init__(self, name)
        self.active = active if active is not None else True

    def run(self):
        """
        Run scenario simulation

        This method should compute the modified parset or progset, pass it to
        :meth:`project.Project.run_sim` and then return the result. It needs to be
        implemented for each derived class.

        :return: A Result object

        """
        raise NotImplementedError('Derived classes should implement this')

class ParameterScenario(Scenario):
    def __init__(self, name=None, scenario_values:dict =None, active=None, parsetname=None):
        """
        Define and run parameter scenarios

        This object stores overwrites to parameter values that are used to modify
        a :class:`ParameterSet` instance before running a simulation.

        :param name: The name of the scenario. This will also be used to name the result
        :param scenario_values: A dict of overwrites to parameter values. The structure is
            ``{parameter_label: {pop_label: dict o}`` where the overwrite ``o`` contains keys
             - ``t`` : np.array or list with year values
             - ``y`` : np.array or list with corresponding parameter values
             - ``smooth_onset`` (optional): Smoothly ramp parameter value rather than having a stepped change
        :param active: If running via ``Project.run_scenarios`` this flags whether to run the scenario
        :param parsetname: If running via ``Project.run_scenarios`` this identifies which parset to use from the project

        Example usage:

        >>> scvalues = dict()
        >>> param = 'birth_transit'
        >>> scvalues[param] = dict()
        >>> scvalues[param]['Pop1'] = dict()
        >>> scvalues[param]['Pop1']['y'] = [3e6, 1e4, 1e4, 2e6]
        >>> scvalues[param]['Pop1']['t'] = [2003.,2004.,2014.,2015.]
        >>> scvalues[param]['Pop1']['smooth_onset'] = 1
        >>> scvalues[param]['Pop1']['smooth_onset'] = [1,2,3,4] (same length as y)
        >>> pscenario = ParameterScenario(name="examplePS",scenario_values=scvalues)

        """

        super(ParameterScenario, self).__init__(name, active)
        self.parsetname = parsetname
        # TODO - could do some extra validation here
        self.scenario_values = scenario_values

    def get_parset(self, parset=None, settings=None):
        """
        Return modified parset

        This method takes in a :class:`ParameterSet` and modifies it by applying the overwrites
        present in the scenario. This can thus be used to return the :class:`ParameterSet` for use in
        other simulations that are manually run, or to do things like perform a budget scenario simulation
        in conjunction with a parameter scenario.

        Get the corresponding parameterSet for this scenario, given an input parameterSet for the default baseline
        activity.

        The output depends on whether to overwrite (replace) or add values that appear in both the
        parameterScenario's parameterSet to the baseline parameterSet.

        :param parset: A :class:`ParameterSet` instance
        :param settings: A :class:`ProjectSettings` instance (e.g. ``proj.settings``)
        :return: A new, modified :class:`ParameterSet` object

        """

        # Note - the parset will be overwritten between the first and last year specified in scvalues
        # on a per-parameter+pop basis. Within the scenario, only the data points in scvalues will be used

        new_parset = sc.dcp(parset)

        for par_label in self.scenario_values.keys():
            par = new_parset.pars[par_label]  # This is the parameter we are updating

            for pop_label, overwrite in self.scenario_values[par_label].items():

                if not par.has_values(pop_label):
                    raise Exception("You cannot specify overwrites for a parameter with a function, instead you should overwrite its dependencies")

                original_y_end = par.interpolate(np.array([max(overwrite['t']) + 1e-5]), pop_label)

                # If the Parameter had an assumption, then insert the assumption value in the start year
                if not par.ts[pop_label].has_time_data:
                    par.ts[pop_label].insert(settings.sim_start, par.ts[pop_label].assumption)

                if 'smooth_onset' not in overwrite:
                    overwrite['smooth_onset'] = 1e-5

                if np.isscalar(overwrite['smooth_onset']):
                    onset = np.zeros((len(overwrite['y']),))
                    onset[0] = overwrite['smooth_onset']
                else:
                    assert len(overwrite['smooth_onset']) == len(overwrite['y']), 'Smooth onset must be either a scalar or an array with length matching y-values'
                    onset = overwrite['smooth_onset']

                # Now, insert all of the program overwrites
                if len(overwrite['t']) != len(overwrite['y']):
                    raise Exception('Number of time points in overwrite does not match number of values')

                if len(overwrite['t']) == 1:
                    logger.warning('Only one time point was specified in the overwrite, which means that the overwrite will not have any effect')

                for i in range(0, len(overwrite['t'])):

                    # Account for smooth onset
                    if onset[i] > 0:
                        t = overwrite['t'][i] - onset[i]

                        if i > 0 and t > overwrite['t'][i - 1]:
                            # If the smooth onset extends to before the previous point, then just use the
                            # previous point directly instead
                            y = overwrite['y'][i - 1] / par.y_factor[pop_label] / par.meta_y_factor
                            par.ts[pop_label].remove_between([overwrite['t'][i - 1], overwrite['t'][i]])
                            par.ts[pop_label].insert(t,y)
                        else:
                            # Otherwise, get the value at the smooth onset time, add it as a control
                            # point, and remove any intermediate points
                            y = par.interpolate(np.array([t]), pop_label)
                            par.ts[pop_label].remove_between([t, overwrite['t'][i]])  # Remove values during onset period
                            par.ts[pop_label].insert(t,y)
                    elif i > 0:
                        # If not doing smooth onset, and this is not the first point being overwritten,
                        # then remove all control points between this point and the last one
                        par.ts[pop_label].remove_between([overwrite['t'][i - 1], overwrite['t'][i]])

                    # Insert the overwrite value - assume scenario value is AFTER y-factor rescaling
                    par.ts[pop_label].insert(overwrite['t'][i], overwrite['y'][i] / par.y_factor[pop_label] / par.meta_y_factor)

                # Add an extra point to return the parset back to it's original value after the final overwrite
                par.ts[pop_label].insert(max(overwrite['t']) + 1e-5, original_y_end)

            new_parset.name = self.name + '_' + parset.name
            return new_parset

    def run(self, project=None, parset=None, store_results=True):
        """
        Run parameter scenario

        :param project: A :class:`Project` instance
        :param parset: Optionally a :class:`ParameterSet` instance, otherwise will use ``self.parsetname``
        :param store_results: If True, the results will be copied into the project
        :return: A :class:`Result` object

        """

        if parset is None:
            parset = project.parsets[self.parsetname]

        scenario_parset = self.get_parset(parset, project.settings)
        result = project.run_sim(parset=scenario_parset, result_name=self.name, store_results=store_results)
        return result


class BudgetScenario(Scenario):

    def __init__(self, name=None, parsetname=None, progsetname=None, alloc=None, start_year=None, active=None, alloc_year=None, budget_factor=1.0):
        # A BudgetScenario specifies spending overwrites
        # The start_year corresponds to the year in which the programs turn on
        # The alloc can be a dict of scalar spends, that take effect in the program start year, or a TimeSeries of spending values
        # If it is a TimeSeries of spending values, the BudgetScenario will attempt to unify them with the program data. ProgramInstructions
        # uses the alloc directly, to provide maximum control of spending. The BudgetScenario is where the fact that the scenario should linearly
        # ramp spending is defined. As a shortcut, if the alloc_year is specified, then the alloc will be converted to the appropriate form
        super(BudgetScenario, self).__init__(name, active)
        logger.debug('Creating budget scenario with name=%s, parsetname=%s, progsetname=%s, start_year=%s' % (name, progsetname, parsetname, start_year))
        self.parsetname = parsetname
        self.progsetname = progsetname
        self.alloc_year = alloc_year  # If the alloc has scalar values, add them in this year
        self.alloc = sc.dcp(alloc)
        self.start_year = start_year  # Turn on programs in this year (can be different to when the spending changes are applied)
        self.budget_factor = budget_factor
        return None

    def run(self, project=None, parset=None, progset=None, store_results=True):
        # Run the BudgetScenario
        # If parset and progset are not provided, use the ones set in self.parsetname and self.progsetname

        if parset is None:
            parset = project.parsets[self.parsetname]

        if progset is None:
            progset = project.progsets[self.progsetname]

        if self.alloc_year is not None:
            # If the alloc_year is prior to the program start year, then just use the spending value directly for all times
            # For more sophisticated behaviour, the alloc should be passed into the BudgetScenario as a TimeSeries
            alloc = sc.odict()
            for prog_name, val in self.alloc.items():
                assert not isinstance(val, TimeSeries)  # Value must not be a TimeSeries
                if val is None:
                    continue  # Use default spending for any program that does not have a spending overwrite
                alloc[prog_name] = TimeSeries(self.alloc_year, val)
                if self.alloc_year > self.start_year:
                    # If adding spending in a future year, linearly ramp from the start year
                    spend_data = progset.programs[prog_name].spend_data
                    alloc[prog_name].insert(self.start_year, spend_data.interpolate(self.start_year))  # This will result in a linear ramp
        else:
            alloc = sc.odict()
            for prog_name, val in self.alloc.items():
                if not isinstance(val, TimeSeries):
                    alloc[prog_name] = TimeSeries(self.start_year, val)
                else:
                    alloc[prog_name] = sc.dcp(val)

        for ts in alloc.values():
            ts.vals = [x * self.budget_factor for x in ts.vals]  # TimeSeries uses lists instead of arrays for fast insertion/removal

        instructions = ProgramInstructions(alloc=alloc, start_year=self.start_year)  # Instructions for default spending
        result = project.run_sim(parset=parset, progset=progset, progset_instructions=instructions, result_name=self.name, store_results=store_results)
        return result


class CoverageScenario(Scenario):

    def __init__(self, name=None, parsetname=None, progsetname=None, coverage=None, start_year=None, active=None):
        # A BudgetScenario specifies spending overwrites
        # The start_year corresponds to the year in which the programs turn on
        # The alloc can be a dict of scalar spends, that take effect in the program start year, or a TimeSeries of spending values
        # If it is a TimeSeries of spending values, the BudgetScenario will attempt to unify them with the program data. ProgramInstructions
        # uses the alloc directly, to provide maximum control of spending. The BudgetScenario is where the fact that the scenario should linearly
        # ramp spending is defined. As a shortcut, if the alloc_year is specified, then the alloc will be converted to the appropriate form
        super(CoverageScenario, self).__init__(name, active)
        logger.debug('Creating coverage scenario with name=%s, parsetname=%s, progsetname=%s, start_year=%s' % (name, progsetname, parsetname, start_year))
        self.parsetname = parsetname
        self.progsetname = progsetname
        self.coverage = sc.dcp(coverage)
        self.start_year = start_year  # Turn on programs in this year (can be different to when the spending changes are applied)
        return None

    def run(self, project=None, parset=None, progset=None, store_results=True):
        # Run the BudgetScenario
        # If parset and progset are not provided, use the ones set in self.parsetname and self.progsetname

        if parset is None:
            parset = project.parsets[self.parsetname]

        if progset is None:
            progset = project.progsets[self.progsetname]

        coverage = sc.odict()
        for prog_name, val in self.coverage.items():
            if not isinstance(val, TimeSeries):
                coverage[prog_name] = TimeSeries(self.start_year, val)
            else:
                coverage[prog_name] = sc.dcp(val)

        instructions = ProgramInstructions(coverage=coverage, start_year=self.start_year)  # Instructions for default spending
        result = project.run_sim(parset=parset, progset=progset, progset_instructions=instructions, result_name=self.name, store_results=store_results)
        return result
