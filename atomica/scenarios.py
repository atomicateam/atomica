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
from .programs import ProgramInstructions, ProgramSet
from .parameters import ParameterSet
from .results import Result

class Scenario(NamedItem):
    """
    Base scenario class

    All Scenario objects share this type. It is a NamedItem that also has an
    ``active`` property which represents whether the scenario should be run
    as part of :meth:`project.Project.run_scenarios`

    The optional variables ``parsetname`` and ``progsetname`` reference the name of parsets
    and progsets to use via :meth:`Scenario.run`. These should match the names of objects in the
    project passed into :meth:`Scenario.run`. However, :meth:`Scenario.run` can also take in
    a parset and/or progset directly, allowing the scenario to be used with other parsets and
    progsets on the fly. If  ``parsetname`` and ``progsetname`` are not set in the :class:`Scenario`
    then they must be passed into :meth:`Scenario.run`.

    :param name: The name of the scenario - also sets the result name via :meth:`Scenario.run`
    :param parsetname: If running via ``Project.run_scenarios`` this identifies which parset to use from the project
    :param progsetname: If running via ``Project.run_scenarios`` this identifies which progset to use. If set to ``None`` then programs will not be used
    :param active: If running via ``Project.run_scenarios`` this flags whether to run the scenario

    """

    def __init__(self, name:str, active:bool=True, parsetname:str =None, progsetname:str =None):
        NamedItem.__init__(self, name)
        self.parsetname = parsetname
        self.progsetname = progsetname
        self.active = active

    def get_parset(self,parset,project) -> ParameterSet:
        """
        Get scenario parset

        If the derived scenario class modifies the parset, return the modified version

        :param parset: Input :class:`ParameterSet`
        :return: Modified parset for use in the simulation

        """

        return parset

    def get_progset(self, progset:ProgramSet, project) -> ProgramSet:
        """
        Get scenario progset

        If the derived scenario class modifies the progset, return the modified version

        :param progset: Input :class:`ProgramSet`
        :return: Modified progset for use in the simulation

        """

        return progset

    def get_instructions(self, progset:ProgramSet, project) -> ProgramInstructions:

        """
        Get scenario instructions

        If the derived scenario class produces  program instructions, return
        them here.

        :param progset: Input :class:`ProgramSet`
        :return: :class:`ProgramInstructions` instance, or None if no instructions (in which case, programs will not be used)

        """

        return None

    def run(self, project, parset:ParameterSet =None, progset:ProgramSet =None, store_results:bool =True) -> Result:
        """
        Run scenario

        :param project: A :class:`Project` instance
        :param parset: Optionally a :class:`ParameterSet` instance, otherwise will use ``self.parsetname``
        :param progset: Optionally a :class:`ProgramSet` instance, otherwise will use ``self.progsetname``
        :param store_results: If True, the results will be copied into the project
        :return: A :class:`Result` object

        """

        if parset is None:
            parset = project.parsets[self.parsetname]
        else:
            parset = project.parset(parset)

        if progset is None and self.progsetname is not None:
            progset = project.progsets[self.progsetname]
        elif progset is not None:
            progset = project.progset(progset)

        parset = self.get_parset(parset, project)
        progset = self.get_progset(progset, project)
        instructions = self.get_instructions(progset, project)

        if progset is not None:
            if instructions is None:
                raise Exception('If using programs, the scenario must contain instructions specifying at minimum the program start year')
            result = project.run_sim(parset=parset, progset=progset, progset_instructions=instructions, result_name=self.name, store_results=store_results)
        else:
            result = project.run_sim(parset=parset, result_name=self.name, store_results=store_results)

        return result


class CombinedScenario(Scenario):
    """
    Define combined (budget+program) scenario

    This object stores both a set of scenario values and a set of program instructions.
    This allows it to simultaneously apply parameter, budget, and coverage overwrites.

    As usual, parameter values from programs take precedence over parameter values from parsets, and
    within programs, coverage takes precedence ovetoxr budgets.

    :param name: The name of the scenario. This will also be used to name the result
    :param active: If running via ``Project.run_scenarios`` this flags whether to run the scenario
    :param parsetname: If running via ``Project.run_scenarios`` this identifies which parset to use from the project
    :param progsetname: If running via ``Project.run_scenarios`` this identifies which progset to use. If set to ``None`` then programs will not be used
    :param scenario_values: Parameter value overwrites, used as input to :class:`ParameterScenario`
    :param instructions: A :class`ProgramInstructions` instance containing required program overwrites (budget, capacity, coverage)

    """

    def __init__(self, name:str =None, active:bool =True, parsetname:str =None, progsetname:str =None, scenario_values:dict =None, instructions:ProgramInstructions =None):
        super().__init__(name, active, parsetname, progsetname)
        self.scenario_values = scenario_values
        self.instructions = instructions

    def get_parset(self, parset, project) -> ParameterSet:
        if self.scenario_values is not None:
            scenario_parset = ParameterScenario(scenario_values=self.scenario_values).get_parset(parset, project)
        else:
            scenario_parset = parset
        return scenario_parset

    def get_instructions(self, progset:ProgramSet, project) -> ProgramInstructions:
        return self.instructions


class BudgetScenario(Scenario):

    def __init__(self, name=None, active:bool=True, parsetname:str =None, progsetname:str =None, alloc:dict =None, start_year=2018):
        super().__init__(name, active, parsetname, progsetname)
        self.start_year = start_year # Program start year
        self.alloc = sc.dcp(alloc) if alloc is not None else sc.odict()

    def get_instructions(self, progset:ProgramSet, project) -> ProgramInstructions:
        return ProgramInstructions(start_year=self.start_year, alloc=self.alloc)


class CoverageScenario(Scenario):

    def __init__(self, name=None, active:bool=True, parsetname:str =None, progsetname:str =None, coverage:dict =None, start_year=2018):
        super().__init__(name, active, parsetname, progsetname)
        self.start_year = start_year # Program start year
        self.coverage = sc.dcp(coverage) if coverage is not None else sc.odict()

    def get_instructions(self, progset:ProgramSet, project) -> ProgramInstructions:
        return ProgramInstructions(start_year=self.start_year, coverage=self.coverage)


class ParameterScenario(Scenario):
    def __init__(self, name:str =None, scenario_values:dict =None, active:bool=True, parsetname:str =None):
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
        super().__init__(name, active, parsetname)
        self.parsetname = parsetname
        # TODO - could do some extra validation here
        self.scenario_values = sc.dcp(scenario_values) if scenario_values is not None else dict()

    def get_parset(self, parset:ParameterSet, project) -> ParameterSet:
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
        new_parset.name = self.name + '_' + parset.name

        for par_label in self.scenario_values.keys():
            par = new_parset.pars[par_label]  # This is the parameter we are updating
            has_function = project.framework.pars.at[par.name, 'function'] # Flag whether this is a function parameter in the framework

            for pop_label, overwrite in self.scenario_values[par_label].items():

                # Remove Nones and Nans
                overwrite = sc.dcp(overwrite)
                overwrite['t'] = sc.promotetoarray(overwrite['t']).astype('float') # astype('float') converts None to np.nan
                overwrite['y'] = sc.promotetoarray(overwrite['y']).astype('float')
                idx = ~np.isnan(overwrite['t']) & ~np.isnan(overwrite['y'])
                if not np.any(idx):
                    continue
                overwrite['t'] = overwrite['t'][idx]
                overwrite['y'] = overwrite['y'][idx]

                original_y_end = par.interpolate(np.array([max(overwrite['t']) + 1e-5]), pop_label)

                # If the Parameter had an assumption, then insert the assumption value in the start year
                if not par.ts[pop_label].has_time_data:
                    par.ts[pop_label].insert(project.settings.sim_start, par.ts[pop_label].assumption)

                if has_function and 'smooth_onset' in overwrite:
                    raise Exception('Parameter function overwrites cannot have smooth onsets (because the value at the onset time is not yet known)')

                if 'smooth_onset' not in overwrite:
                    # Note parameter functions still get smooth onset set here - this ensures
                    # correct non-smooth-onset behaviour _during_ the overwrite
                    overwrite['smooth_onset'] = 1e-5

                if np.isscalar(overwrite['smooth_onset']):
                    onset = [overwrite['smooth_onset']]*len(overwrite['y'])
                else:
                    assert len(overwrite['smooth_onset']) == len(overwrite['y']), 'Smooth onset must be either a scalar or an array with length matching y-values'
                    onset = overwrite['smooth_onset']

                # Now, insert all of the program overwrites
                if len(overwrite['t']) != len(overwrite['y']):
                    raise Exception('Number of time points in overwrite does not match number of values')

                if len(overwrite['t']) == 1:
                    raise Exception('Only one time point was specified in the overwrite, which means that the overwrite will not have any effect')

                for i in range(0, len(overwrite['t'])):

                    # Account for smooth onset
                    if onset[i] > 0:
                        t = overwrite['t'][i] - onset[i]

                        if i > 0 and t <= overwrite['t'][i - 1]:
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

                if has_function:
                    par.skip_function[pop_label] = (min(overwrite['t']), max(overwrite['t']))

        return new_parset

