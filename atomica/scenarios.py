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
from .utils import NamedItem, TimeSeries
from .programs import ProgramInstructions, ProgramSet
from .parameters import ParameterSet
from .results import Result

__all__ = ["Scenario", "CombinedScenario", "BudgetScenario", "CoverageScenario", "ParameterScenario"]


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

    def __init__(self, name: str, active: bool = True, parsetname: str = None, progsetname: str = None):
        NamedItem.__init__(self, name)
        self.parsetname = parsetname  #: Specify parset name when run via ``Project.run_scenarios``
        self.progsetname = progsetname  #: Specify progset name when run via ``Project.run_scenarios``
        self.active = active  #: Flag whether the scenario should be run via ``Project.run_scenarios``

    def get_parset(self, parset, project) -> ParameterSet:
        """
        Get scenario parset

        If the derived scenario class modifies the parset, return the modified version

        :param parset: Input :class:`ParameterSet`
        :return: Modified parset for use in the simulation

        """

        return parset

    def get_progset(self, progset: ProgramSet, project) -> ProgramSet:
        """
        Get scenario progset

        If the derived scenario class modifies the progset, return the modified version

        :param progset: Input :class:`ProgramSet`
        :return: Modified progset for use in the simulation

        """

        return progset

    def get_instructions(self, progset: ProgramSet, project) -> ProgramInstructions:
        """
        Get scenario instructions

        If the derived scenario class produces  program instructions, return
        them here.

        :param progset: Input :class:`ProgramSet`
        :return: :class:`ProgramInstructions` instance, or None if no instructions (in which case, programs will not be used)

        """

        return None

    def run(self, project, parset: ParameterSet = None, progset: ProgramSet = None, store_results: bool = True) -> Result:
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
                raise Exception("If using programs, the scenario must contain instructions specifying at minimum the program start year")
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

    def __init__(self, name: str = None, active: bool = True, parsetname: str = None, progsetname: str = None, scenario_values: dict = None, instructions: ProgramInstructions = None, interpolation: str = "linear"):
        super().__init__(name, active, parsetname, progsetname)
        self.scenario_values = scenario_values  #: Parameter scenario values (see :class:`ParameterScenario`)
        self.interpolation = interpolation  #: Interpolation method to use for parameter overwrite
        self.instructions = instructions  # : Program instructions for budget scenario (should already contain required overwrites)

    def get_parset(self, parset, project) -> ParameterSet:
        if self.scenario_values is not None:
            scenario_parset = ParameterScenario(scenario_values=self.scenario_values, interpolation=self.interpolation).get_parset(parset, project)
        else:
            scenario_parset = parset
        return scenario_parset

    def get_instructions(self, progset: ProgramSet, project) -> ProgramInstructions:
        return self.instructions


class BudgetScenario(Scenario):
    def __init__(self, name=None, active: bool = True, parsetname: str = None, progsetname: str = None, alloc: dict = None, start_year=2019):
        super().__init__(name, active, parsetname, progsetname)
        self.start_year = start_year  # Program start year
        self.alloc = sc.dcp(alloc) if alloc is not None else sc.odict()

    def get_instructions(self, progset: ProgramSet, project) -> ProgramInstructions:
        return ProgramInstructions(start_year=self.start_year, alloc=self.alloc)


class CoverageScenario(Scenario):
    def __init__(self, name=None, active: bool = True, parsetname: str = None, progsetname: str = None, coverage: dict = None, start_year=2019):
        super().__init__(name, active, parsetname, progsetname)
        self.start_year = start_year  # Program start year
        self.coverage = sc.dcp(coverage) if coverage is not None else sc.odict()

    def get_instructions(self, progset: ProgramSet, project) -> ProgramInstructions:
        return ProgramInstructions(start_year=self.start_year, coverage=self.coverage)


class ParameterScenario(Scenario):
    """
    Define and run parameter scenarios

    This object stores overwrites to parameter values that are used to modify
    a :class:`ParameterSet` instance before running a simulation.

    Example usage:

    >>> scvalues = dict()
    >>> param = 'birth_transit'
    >>> scvalues[param] = dict()
    >>> scvalues[param]['Pop1'] = dict()
    >>> scvalues[param]['Pop1']['y'] = [3e6, 1e4, 1e4, 2e6]
    >>> scvalues[param]['Pop1']['t'] = [2003.,2004.,2014.,2015.]
    >>> pscenario = ParameterScenario(name="examplePS",scenario_values=scvalues)

    :param name: The name of the scenario. This will also be used to name the result
    :param scenario_values: A dict of overwrites to parameter values. The structure is
        ``{parameter_label: {pop_identifier: dict o}`` where the overwrite ``o`` contains keys
         - ``t`` : np.array or list with year values
         - ``y`` : np.array or list with corresponding parameter values
         The ``pop_identifier`` is a single population name if the ``parameter_label`` corresponds to a Framework parameter
         or it should be a tuple/list ``(from_pop,to_pop)`` if the ``parameter_label`` corresponds to an interaction or transfer.
    :param active: If running via ``Project.run_scenarios`` this flags whether to run the scenario
    :param parsetname: If running via ``Project.run_scenarios`` this identifies which parset to use from the project
    :param interpolation: The specified interpolation method will be used to interpolate scenario values onto simulation times. Common options are 'linear' (smoothly change) and 'previous' (stepped)

    """

    def __init__(self, name: str = None, scenario_values: dict = None, active: bool = True, parsetname: str = None, interpolation: str = "linear"):

        super().__init__(name, active, parsetname)
        self.scenario_values = sc.dcp(scenario_values) if scenario_values is not None else dict()  #: Store dictionary containing the overwrite values
        self.interpolation = interpolation  #: Stores the name of a supported interpolation method

    def add(self, par_name: str, pop_name: str, t, y) -> None:
        """
        Add overwrite to scenario

        This method adds a TimeSeries with parameter overwrite values to the
        ParameterSet

        Example usage:

        >>> pscenario = ParameterScenario(name="examplePS")
        >>> pscenario.add('rec_rate','Pop1',[2004.,2014],[3e6, 1e4])
        >>> pscenario.add('aging',('Pop1','Pop2'),[2004.,2014],[0.05,0.06])

        This can provide a more readable way to define a parameter scenario, without having to
        assemble a dict of the overwrites in advance.

        :param par_name: Name of the parameter to overwrite. This can also be the code name of a transfer or interaction
        :param pop_name: Population to overwrite values for. If the ``par_name`` is a transfer or interaction, this
                         should be a tuple containing ``(from_pop,to_pop)``
        :param t: scalar, list, or array of times
        :param y: scalar, list, or array of overwrite values
        :param end_overwrite: If True, after the final overwrite, the parameter will revert to its baseline value

        """

        t = sc.promotetoarray(t).copy()
        y = sc.promotetoarray(y).copy()

        assert len(t) == len(y), "To add an overwrite, the same number of time points and values must be provided"

        if par_name not in self.scenario_values:
            self.scenario_values[par_name] = dict()
        if pop_name not in self.scenario_values[par_name]:
            self.scenario_values[par_name][pop_name] = dict()
        self.scenario_values[par_name][pop_name] = {"t": t, "y": y}

    def get_parset(self, parset: ParameterSet, project) -> ParameterSet:
        """
        Return modified parset

        This method takes in a :class:`ParameterSet` and modifies it by applying the overwrites
        present in the scenario. This can thus be used to return the :class:`ParameterSet` for use in
        other simulations that are manually run, or to do things like perform a budget scenario simulation
        in conjunction with a parameter scenario.

        The returned :class:`ParameterSet` will have been pre-interpolated onto the simulation times.

        :param parset: A :class:`ParameterSet` instance
        :param project: A :class:`Project` instance (required for simulation times and to identify function parameters)
        :return: A new :class:`ParameterSet` object

        """

        new_parset = sc.dcp(parset)
        new_parset.name = self.name + "_" + parset.name
        tvec = project.settings.tvec  # Simulation times

        for par_label in self.scenario_values.keys():

            if par_label in new_parset.pars:
                has_function = project.framework.pars.at[par_label, "function"]  # Flag whether this is a function parameter in the framework
            else:
                has_function = False  # Interactions and transfers do not have functions

            for pop_specifier, overwrite in self.scenario_values[par_label].items():

                if sc.isstring(pop_specifier):
                    par = new_parset.get_par(par_label)
                    pop_label = pop_specifier
                else:
                    par = new_parset.get_par(par_label, pop_specifier[0])
                    pop_label = pop_specifier[1]

                # Sanitize the overwrite values
                overwrite = sc.dcp(overwrite)
                overwrite["t"] = sc.promotetoarray(overwrite["t"]).astype("float")  # astype('float') converts None to np.nan
                overwrite["y"] = sc.promotetoarray(overwrite["y"]).astype("float")
                idx = ~np.isnan(overwrite["t"]) & ~np.isnan(overwrite["y"])
                if not np.any(idx):
                    continue

                # Expand out the baseline values and remove any other values
                scen_start = min(overwrite["t"])
                vals = par.interpolate(tvec[tvec < scen_start], pop_label)  # Interpolate parameter onto valid sim times, using default interpolation. To override this, interpolate the parameter before calling ``ParameterScenario.get_parset()``
                par.ts[pop_label].t = tvec[tvec < scen_start].tolist()
                par.ts[pop_label].vals = vals.tolist()

                # Insert the overwrites
                assert len(overwrite["t"]) == len(overwrite["y"]), "Number of time points in overwrite does not match number of values"
                for t, y in zip(overwrite["t"], overwrite["y"]):
                    par.ts[pop_label].insert(t, y)
                par.smooth(tvec[tvec >= scen_start], pop_names=pop_label, method=self.interpolation)

                # Disable parameter function during scenario
                if has_function:
                    par.skip_function[pop_label] = (scen_start, np.inf)

        return new_parset
