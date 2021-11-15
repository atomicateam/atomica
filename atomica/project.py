"""
Implements the :class:`Project` user interface for Atomica

The :class:`Project` class serves as the primary user interface for
Atomica. Almost all functionality can be accessed via this interface.

A project is based around 5 major lists:
    1. parsets -- an odict of parameter sets
    2. progsets -- an odict of program sets
    3. scens -- an odict of scenario structures
    4. optims -- an odict of optimization structures
    5. results -- an odict of results associated with parsets, scens, and optims

In addition, a project contains:
    1. data -- loaded from the spreadsheet
    2. settings -- timestep, indices, etc.
    3. various kinds of metadata -- project name, creation date, etc.

"""

from .version import version, gitinfo
from .calibration import calibrate
from .data import ProjectData
from .framework import ProjectFramework
from .model import run_model
from .parameters import ParameterSet

from .programs import ProgramSet
from .scenarios import Scenario, ParameterScenario, CombinedScenario, BudgetScenario, CoverageScenario
from .optimization import Optimization, optimize, InvalidInitialConditions
from .system import logger
from .utils import NDict, evaluate_plot_string, NamedItem, parallel_progress, Quiet
from .plotting import PlotData, plot_series
from .results import Result
from .migration import migrate
import sciris as sc
import numpy as np
import tqdm
import logging
from datetime import timezone
import functools

__all__ = ["ProjectSettings", "Project"]


class ProjectSettings:
    def __init__(self, sim_start=2000, sim_end=2035, sim_dt=0.25):
        self._sim_start = sim_start
        self._sim_dt = sim_dt
        self._sim_end = 0.0
        self.update_time_vector(end=sim_end)

    def __repr__(self):
        """Print object"""
        output = sc.prepr(self)
        return output

    @property
    def sim_start(self):
        return self._sim_start

    @property
    def sim_end(self):
        return self._sim_end

    @property
    def sim_dt(self):
        return self._sim_dt

    @sim_start.setter
    def sim_start(self, sim_start):
        self._sim_start = sim_start

    @sim_end.setter
    def sim_end(self, sim_end):
        self._sim_end = self.sim_start + np.ceil((sim_end - self.sim_start) / self.sim_dt) * self.sim_dt
        if sim_end != self._sim_end:
            logger.info(f"Changing sim end from {sim_end} to {self._sim_end} ({(self._sim_end - self._sim_start) / self._sim_dt:.0f} timesteps)")

    @sim_dt.setter
    def sim_dt(self, sim_dt):
        assert sim_dt > 0, "Simulation timestep must be greater than 0"
        self._sim_dt = sim_dt
        self.sim_end = self.sim_end  # Call the setter function to change sim_end if it is no longer valid

    @property
    def tvec(self) -> np.ndarray:
        """
        Return simulation time vector

        This method uses `linspace` rather than `arange` to avoid accumulating numerical errors that prevent
        integer years aligning exactly.

        :return: Array of simulation times

        """

        return np.linspace(self.sim_start, self.sim_end, int((self.sim_end - self.sim_start) / self.sim_dt) + 1)

    def update_time_vector(self, start: float = None, end: float = None, dt: float = None) -> None:
        """
        Update the project simulation times

        :param start: Optionally provide new start year (e.g. '2018')
        :param end: Optionally provide new end year (e.g. '2035')
        :param dt: Optionally provide new step size, in years (e.g. '0.25' for quarterly steps

        """

        if start is not None:
            self.sim_start = start

        if dt is not None:
            if end is None:
                self.sim_dt = dt  # Update the simulation end year automatically to account for the new timestep
            else:
                self._sim_dt = dt  # Change sim_dt internally so that the sim_end is only changed once

        if end is not None:
            self.sim_end = end


class Project(NamedItem):
    """
    Main simulation container

    A Project provides a centralized point of storage when working with Atomica. It contains

    - A framework
    - Data
    - Parameters
    - Programs
    - Scenarios and optimizations
    - Results

    Importantly, it is generally assumed that saving and loading work is done by saving and
    loading projects.

    :param name:
    :param framework: a Framework to use. This could be
                      - A filename to an Excel file on disk
                      - An sc.Spreadsheet instance
                      - A ProjectFramework instance
                      - None (this should generally not be used though!)
    :param databook: The path to a databook file. The databook will be loaded into Project.data and the spreadsheet saved to Project.databook
    :param do_run: If True, a simulation will be run upon project construction
    :param kwargs: These are passed to the :class`ProjectSettings` constructor

    """

    def __init__(self, name="default", framework=None, databook=None, do_run=True, **kwargs):
        NamedItem.__init__(self, name)

        if isinstance(framework, ProjectFramework):
            self.framework = framework
        elif framework is None:
            logger.warning("Project was constructed without a Framework - a framework should be provided")
            self.framework = None
        else:
            self.framework = ProjectFramework(inputs=framework)

        # Define the structure sets
        self.parsets = NDict()  #: Dictionary of :class:`ParameterSet` instances
        self.progsets = NDict()
        self.scens = NDict()
        self.optims = NDict()
        self.results = NDict()

        # Define metadata
        self.uid = sc.uuid()
        self.version = version
        self.gitinfo = sc.dcp(gitinfo)
        self.filename = None

        self.progbook = None  # This will contain an sc.Spreadsheet when the user loads one
        self.settings = ProjectSettings(**kwargs)  # Global settings

        self._update_required = False  # This flag is set to True by migration is the result objects contained in this Project are out of date due to a migration change

        # Load project data, if available
        if framework and databook:
            self.load_databook(databook_path=databook, do_run=do_run)
        elif databook:
            logger.warning("Project was constructed without a Framework - databook spreadsheet is being saved to project, but data is not being loaded")
            self.databook = sc.Spreadsheet(databook)  # Just load the spreadsheet in so that it isn't lost
            self.data = None
        else:
            self.databook = None  # This will contain an sc.Spreadsheet when the user loads one
            self.data = None

    def __repr__(self):
        """Print out useful information when called"""
        output = sc.objrepr(self)
        output += "      Project name: %s\n" % self.name
        output += "    Framework name: %s\n" % self.framework.name
        output += "\n"
        output += "    Parameter sets: %i\n" % len(self.parsets)
        output += "      Program sets: %i\n" % len(self.progsets)
        output += "         Scenarios: %i\n" % len(self.scens)
        output += "     Optimizations: %i\n" % len(self.optims)
        output += "      Results sets: %i\n" % len(self.results)
        output += "\n"
        output += "   Atomica version: %s\n" % self.version
        output += "      Date created: %s\n" % sc.getdate(self.created.replace(tzinfo=timezone.utc).astimezone(tz=None), dateformat="%Y-%b-%d %H:%M:%S %Z")
        output += "     Date modified: %s\n" % sc.getdate(self.modified.replace(tzinfo=timezone.utc).astimezone(tz=None), dateformat="%Y-%b-%d %H:%M:%S %Z")
        #        output += '  Datasheet loaded: %s\n' % sc.getdate(self.databookloaddate)
        output += "        Git branch: %s\n" % self.gitinfo["branch"]
        output += "          Git hash: %s\n" % self.gitinfo["hash"]
        output += "               UID: %s\n" % self.uid
        output += "============================================================\n"
        return output

    # @property
    # def pop_names(self):
    #     if self.data is None:
    #         return []
    #     else:
    #         return list(self.data.pops.keys())
    #
    # @property
    # def pop_labels(self):
    #     if self.data is None:
    #         return []
    #     else:
    #         return list([x['label'] for x in self.data.pops.values()])

    #######################################################################################################
    # Methods for I/O and spreadsheet loading
    #######################################################################################################
    def create_databook(self, databook_path=None, num_pops=1, num_transfers=0, data_start=2000.0, data_end=2020.0, data_dt=1.0):
        """Generate an empty data-input Excel spreadsheet corresponding to the framework of this project."""
        if databook_path is None:
            databook_path = "./databook_" + self.name + ".xlsx"
        data = ProjectData.new(self.framework, np.arange(data_start, data_end + data_dt, data_dt), pops=num_pops, transfers=num_transfers)
        data.save(databook_path)
        return data

    def load_databook(self, databook_path, make_default_parset: bool = True, do_run: bool = True) -> None:
        """
        Load a data spreadsheet

        :param databook_path: Databook input. Supported inputs are:
                                - A path string, which will load a file from disk
                                - An `sc.Spreadsheet` containing the contents of a databook
                                - A `ProjectData` instance
        :param make_default_parset: If True, a Parset called "default" will be immediately created from the newly-added data
        :param do_run: If True, a simulation will be run using the new parset

        """

        if isinstance(databook_path, ProjectData):
            # If the user passed in a ProjectData instance, use it directly
            data = databook_path
            databook = data.to_spreadsheet()
        else:
            if isinstance(databook_path, sc.Spreadsheet):
                databook = databook_path
            else:
                databook = sc.Spreadsheet(databook_path)
            data = ProjectData.from_spreadsheet(databook, self.framework)

        # If there are existing progsets, make sure the new data is consistent with them
        if self.progsets:
            data_pops = set((x, y["label"]) for x, y in data.pops.items())
            for progset in self.progsets.values():
                assert data_pops == set((x, y["label"]) for x, y in progset.pops.items()), "Existing progsets exist with populations that do not match the new databook"

        self.data = data
        self.data.validate(self.framework)  # Make sure the data is suitable for use in the Project (as opposed to just manipulating the databook)
        self.databook = sc.dcp(databook)
        self.modified = sc.now(utc=True)
        self.settings.update_time_vector(start=self.data.start_year)  # Align sim start year with data start year.

        if not (self.framework.comps["is source"] == "y").any():
            self.settings.update_time_vector(end=self.data.end_year + 5.0)  # Project only forecasts 5 years if not dynamic (with births)

        if make_default_parset:
            self.make_parset(name="default")
        if do_run:
            if not make_default_parset:
                logger.warning("Project has been requested to run a simulation after loading databook, " "despite no request to create a default parameter set.")
            self.run_sim(parset="default", store_results=True)

    def make_parset(self, name="default"):
        """Transform project data into a set of parameters that can be used in model simulations."""
        self.parsets.append(ParameterSet(self.framework, self.data, name))
        return self.parsets[name]

    def make_progbook(self, progbook_path: str = None, progs=None, data_start: float = None, data_end: float = None) -> str:
        """
        Save a blank program book

        This method will create a temporary ``ProgramSet`` and save it to the requested path

        :param progbook_path: Path to save program book
        :param progs: A program specification supposed by ``ProgramSet.new()``
        :param data_start: The start year for data entry
        :param data_end: The end year for data entry
        :return: The full path of the newly created program book

        """

        # Get filepath
        if self.data is None:
            errormsg = "Please upload a databook before creating a program book. The databook defines which populations will appear in the program book."
            raise Exception(errormsg)
        full_path = sc.makefilepath(filename=progbook_path, default=self.name, ext="xlsx", makedirs=False)  # Directory will be created later in progset.save()
        if data_start is None:
            data_start = self.data.tvec[0]
        if data_end is None:
            data_end = self.data.tvec[-1]
        progset = ProgramSet.new(tvec=np.arange(data_start, data_end + 1), progs=progs, framework=self.framework, data=self.data)
        progset.save(full_path)
        return full_path

    def load_progbook(self, progbook_path=None, name="default"):
        """
        Create a ProgramSet given a progbook

        :param progbook_path: Path to a program spreadsheet or an AtomicaSpreadsheet instance
        :param name: The name to assign to the new ProgramSet
        :return: The newly created ProgramSet (also stored in ``self.progsets``)

        """

        if self.data is None:
            errormsg = "Please upload a databook before uploading a program book. The databook contains the population definitions required to read the program book."
            raise Exception(errormsg)

        if sc.isstring(progbook_path):
            full_path = sc.makefilepath(filename=progbook_path, default=self.name, ext="xlsx", makedirs=False)
            progbook_spreadsheet = sc.Spreadsheet(full_path)
        else:
            progbook_spreadsheet = progbook_path

        progset = ProgramSet.from_spreadsheet(spreadsheet=progbook_spreadsheet, framework=self.framework, data=self.data, name=name)
        progset.validate()
        self.progbook = sc.dcp(progbook_spreadsheet)  # Actually a shallow copy is fine here because AtomicaSpreadsheet contains no mutable properties
        self.progsets.append(progset)
        return progset

    def make_scenario(self, which: str = "combined", **kwargs) -> Scenario:
        """
        Make new scenario and store in Project

        :param which: String identifying type - one of ``['parameter','budget','coverage','combined']``
        :param kwargs: Arguments to pass to appropriate :class:`Scenario` constructor
        :return: New scenario instance

        """

        types = {"parameter": ParameterScenario, "budget": BudgetScenario, "coverage": CoverageScenario, "combined": CombinedScenario}
        scenario = types[which](**kwargs)
        self.scens.append(scenario)
        return scenario

    #    #######################################################################################################
    #    ### Utilities
    #    #######################################################################################################

    def parset(self, key=None, verbose=2):
        """Shortcut for getting a parset"""
        if key is None:
            key = -1
        if isinstance(key, ParameterSet):
            return key  # It's already a parameter set, do nothing
        else:
            try:
                return self.parsets[key]
            except Exception:
                sc.printv('Warning, parset "%s" not found!' % key, 1, verbose)
                return None

    def progset(self, key=None, verbose=2):
        """Shortcut for getting a progset"""
        if key is None:
            key = -1
        if isinstance(key, ProgramSet):
            return key  # It's already a program set, do nothing
        else:
            try:
                return self.progsets[key]
            except Exception:
                sc.printv('Warning, progset "%s" not found!' % key, 1, verbose)
                return None

    def scen(self, key=None, verbose=2):
        """Shortcut for getting a scenario"""
        if key is None:
            key = -1
        if isinstance(key, Scenario):
            return key  # It's already a scenario, do nothing
        else:
            try:
                return self.scens[key]
            except Exception:
                sc.printv('Warning, scenario "%s" not found!' % key, 1, verbose)
                return None

    def optim(self, key=None, verbose=2):
        """Shortcut for getting an optimization"""
        if key is None:
            key = -1
        if isinstance(key, Optimization):
            return key  # It's already an optimization, do nothing
        else:
            try:
                return self.optims[key]
            except Exception:
                sc.printv('Warning, scenario "%s" not found!' % key, 1, verbose)
                return None

    def result(self, key=None, verbose=2):
        """Shortcut for getting an result -- a little special since they don't have a fixed type"""
        if key is None:
            key = -1
        if not sc.isstring(key) and not sc.isnumber(key) and not isinstance(key, tuple):
            if not isinstance(key, [Result, list, sc.odict]):
                print('Warning: result "%s" is of unexpected type: "%s"' % (key, type(key)))
            return key  # It's not something that looks like a key
        else:
            try:
                return self.scens[key]
            except Exception:
                sc.printv('Warning, scenario "%s" not found!' % key, 1, verbose)
                return None

        if key is None:
            key = -1
        try:
            return self.results[key]
        except Exception:
            return sc.printv('Warning, results "%s" not found!' % key, 1, verbose)  # Returns None

    #######################################################################################################
    # Methods to perform major tasks
    #######################################################################################################

    def plot(self, results=None, key=None, outputs=None, pops=None):
        def get_supported_plots():
            df = self.framework.sheets["plots"][0]
            plots = sc.odict()
            for name, output in zip(df["name"], df["quantities"]):
                plots[name] = evaluate_plot_string(output)
            return plots

        if outputs is None:
            supported_plots = get_supported_plots()
            outputs = [{plot_name: supported_plots[plot_name]} for plot_name in supported_plots.keys()]
        if results is None:
            results = self.result(key)

        allfigs = []
        for output in outputs:
            try:
                if not isinstance(list(output.values())[0], list):
                    output = list(output.values())[0]
                plotdata = PlotData(results, outputs=output, project=self, pops=pops)
                figs = plot_series(plotdata, axis="pops", plot_type="stacked", legend_mode="together")
                allfigs += figs
            except Exception as e:
                print("WARNING, %s failed (%s)" % (output, str(e)))
        return allfigs

    def update_settings(self, sim_start=None, sim_end=None, sim_dt=None):
        """Modify the project settings, e.g. the simulation time vector."""
        self.settings.update_time_vector(start=sim_start, end=sim_end, dt=sim_dt)

    def run_sim(self, parset=None, progset=None, progset_instructions=None, store_results=False, result_name: str = None):
        """
        Run a single simulation

        This function is the main entry point for running model simulations, given a
        parset and optionally program set + instructions.

        :param parset: A :class:`ParameterSet` instance, or the name of a parset contained in ``self.parsets``.
                        If ``None``, then the most recently added parset will be used (the last entry in ``self.parsets``)
        :param progset: Optionally pass in a :class:`ProgramSet` instance, or the name of a progset contained in ``self.progsets``
        :param progset_instructions: A :class:`ProgramInstructions` instance. Programs will only be used if a instructions are provided
        :param store_results: If True, then the result will automatically be stored in ``self.results``
        :param result_name: Optionally assign a specific name to the result (otherwise, a unique default name will automatically be selected)
        :return: A :class:`Result` instance

        """

        parset = self.parset(parset)
        if progset is not None:
            progset = self.progset(progset)
            if progset_instructions is None:
                logger.info("Program set '%s' will be ignored while running project '%s' due to the absence of program set instructions", progset.name, self.name)

        if result_name is None:
            base_name = "parset_" + parset.name
            if progset is not None:
                base_name = base_name + "_progset_" + progset.name
            k = 1
            result_name = base_name
            while result_name in self.results:
                result_name = base_name + "_" + str(k)
                k += 1

        tm = sc.tic()
        result = run_model(settings=self.settings, framework=self.framework, parset=parset, progset=progset, program_instructions=progset_instructions, name=result_name)
        logger.info('Elapsed time for running "%s": %ss', self.name, sc.sigfig(sc.toc(tm, output=True), 3))
        if store_results:
            self.results.append(result)

        return result

    def run_sampled_sims(self, parset, progset=None, progset_instructions=None, result_names=None, n_samples: int = 1, parallel=False, max_attempts=None, num_workers=None) -> list:
        """
        Run sampled simulations

        This method samples from the parset (and progset if provided). It is separate from `run_sim` for
        several reasons

        - To avoid inadvertantly blowing up the size of the project, `run_sampled_sims` does not support automatic result saving
        - `run_sim` always returns a `Result` - if rolled into one function, the return type would not be predictable
        - `run_sim` only takes in a single ``ProgramInstructions`` and ``result_name`` whereas `run_sampled_sims` supports iteration
           over multiple instructions

        The other common scenario is having multiple results

        :param n_samples: An integer number of samples
        :param parset: A :class:`ParameterSet` instance
        :param progset: Optionally a :class:`ProgramSet` instance
        :param progset_instructions: This can be a list of instructions
        :param result_names: Optionally specify names for each result. The most common usage would be when passing in a list of program instructions
                             corresponding to different budget scenarios. The result names should be a list the same length as the instructions, or
                             containing a single element if not using programs.
        :param parallel: If True, run simulations in parallel (on Windows, must have ``if __name__ == '__main__'`` gating the calling code)
        :param max_attempts: Number of retry attempts for bad initializations
        :param num_workers: If ``parallel`` is True, this determines the number of parallel workers to use (default is usually number of CPUs)
        :return: A list of Results that can be passed to `Ensemble.update()`. If multiple instructions are provided, the return value of this
                 function will be a list of lists, where the inner list iterates over different instructions for the same parset/progset samples.
                 It is expected in that case that the Ensemble's mapping function would take in a list of results

        """

        assert (not progset) == (not progset_instructions), "If running with programs, both a progset and instructions must be provided"

        parset = self.parset(parset)
        progset = self.progset(progset) if progset is not None else None
        progset_instructions = sc.promotetolist(progset_instructions, keepnone=True)

        if not result_names:
            if len(progset_instructions) > 1:
                result_names = ["instructions_%d" % (i) for i in range(len(progset_instructions))]
            else:
                result_names = ["default"]
        else:
            result_names = sc.promotetolist(result_names)
            assert (len(result_names) == 1 and not progset) or (len(progset_instructions) == len(result_names)), "Number of result names must match number of instructions"

        show_progress = n_samples > 1 and logger.getEffectiveLevel() <= logging.INFO

        if parallel:
            fcn = functools.partial(_run_sampled_sim, proj=self, parset=parset, progset=progset, progset_instructions=progset_instructions, result_names=result_names, max_attempts=max_attempts)
            results = parallel_progress(fcn, n_samples, show_progress=show_progress, num_workers=num_workers)
        elif show_progress:
            # Print the progress bar if the logging level was INFO or lower
            # This means that the user can still set the logging level higher e.g. WARNING to suppress output from Atomica in general
            # (including any progress bars)
            with Quiet():
                results = [_run_sampled_sim(self, parset, progset, progset_instructions, result_names, max_attempts=max_attempts) for _ in tqdm.trange(n_samples)]
        else:
            results = [_run_sampled_sim(self, parset, progset, progset_instructions, result_names, max_attempts=max_attempts) for _ in range(n_samples)]

        return results

    def calibrate(self, parset=None, adjustables=None, measurables=None, max_time=60, save_to_project=False, new_name=None, default_min_scale=0.0, default_max_scale=2.0, default_weight=1.0, default_metric="fractional") -> ParameterSet:
        """
        Method to perform automatic calibration.

        The adjustables argument should be a list in the form of...
            [par_name_1, par_name_2, charac_name_1]
        ...or...
            [(par_name_1, pop_1, min_scale_1, max_scale_1)
             (par_name_2, None, min_scale_2, max_scale_2),
             (charac_name_1, pop_2, min_scale_3, max_scale_3)]
        The former instructs specified parameter values for all populations to be varied between default scaling limits.
        The latter varies specified parameters for specified populations, within specified scaling limits.
        'None' in the population position represents independent scaling across all populations.

        The measurables argument should be a list in the form of...
            [charac_name_1, charac_name_2]
        ...or...
            [(charac_name_1, pop_1, weight_1, "fractional")
             (charac_name_2, None, weight_2, "wape")]
        The former calculates a 'fractional' data comparison metric across specified characteristics for all pops.
        The latter calculates its metric for specified populations and for both specified weights and metric types.
        'None' represents combining the metric across all populations.

        To calibrate a project-attached parameter set in place, provide its key as the new name argument to this method.
        Current fitting metrics are: "fractional", "meansquare", "wape"
        Note that scaling limits are absolute, not relative.
        """

        if parset is None:
            parset = self.parsets[-1]
        elif not isinstance(parset, ParameterSet):
            parset = self.parsets[parset]

        if new_name is None:
            new_name = parset.name + " (auto-calibrated)"
        if adjustables is None:
            adjustables = list(self.framework.pars.index[~self.framework.pars["calibrate"].isnull()])
            adjustables += list(self.framework.comps.index[~self.framework.comps["calibrate"].isnull()])
            adjustables += list(self.framework.characs.index[~self.framework.characs["calibrate"].isnull()])
        if measurables is None:
            measurables = list(self.framework.comps.index)
            measurables += list(self.framework.characs.index)
        for index, adjustable in enumerate(adjustables):
            if sc.isstring(adjustable):  # Assume that a parameter name was passed in if not a tuple.
                adjustables[index] = (adjustable, None, default_min_scale, default_max_scale)
        for index, measurable in enumerate(measurables):
            if sc.isstring(measurable):  # Assume that a parameter name was passed in if not a tuple.
                measurables[index] = (measurable, None, default_weight, default_metric)
        new_parset = calibrate(project=self, parset=parset, pars_to_adjust=adjustables, output_quantities=measurables, max_time=max_time)
        new_parset.name = new_name  # The new parset is a calibrated copy of the old, so change id.
        if save_to_project:
            self.parsets.append(new_parset)

        return new_parset

    def run_scenarios(self, store_results: bool = True) -> list:
        """
        Run all active scenarios

        :param store_results: If True, results will be appended to the project
        :return: List of results (one for each active scenario)

        """

        results = []
        for scenario in self.scens.values():
            if scenario.active:
                result = scenario.run(project=self, store_results=store_results)
                results.append(result)
        return results

    def run_optimization(self, optimname=None, maxtime=None, maxiters=None, store_results=True):
        """Run an optimization"""
        optim_ins = self.optim(optimname)
        optim, unoptimized_instructions = optim_ins.make(project=self)
        if maxtime is not None:
            optim.maxtime = maxtime
        if maxiters is not None:
            optim.maxiters = maxiters
        parset = self.parset(optim.parsetname)
        progset = self.progset(optim.progsetname)
        original_end = self.settings.sim_end
        self.settings.sim_end = optim_ins.json["end_year"]  # Simulation should be run up to the user's end year
        try:
            optimized_instructions = optimize(self, optim, parset, progset, unoptimized_instructions)
        except InvalidInitialConditions:
            if optim_ins.json["optim_type"] == "money":
                raise Exception("It was not possible to achieve the optimization target even with an increased budget. Specify or raise upper limits for spending, or decrease the optimization target")
            else:
                raise  # Just raise it as-is

        self.settings.sim_end = original_end  # Note that if the end year is after the original simulation year, the result won't be visible (although it will have been optimized for)
        optimized_result = self.run_sim(parset=parset, progset=progset, progset_instructions=optimized_instructions, result_name="Optimized", store_results=store_results)
        unoptimized_result = self.run_sim(parset=parset, progset=progset, progset_instructions=unoptimized_instructions, result_name="Baseline", store_results=store_results)
        results = [unoptimized_result, optimized_result]
        return results

    def save(self, filename: str = None, folder: str = None) -> str:
        """
        Save binary project file

        This method saves the entire project as a binary blob to disk

        :param filename: Name of the file to save
        :param folder: Optionally specify a folder
        :return: The full path of the file that was saved

        """

        fullpath = sc.makefilepath(filename=filename, folder=folder, default=[self.filename, self.name], ext="prj", sanitize=True)
        self.filename = fullpath
        sc.saveobj(fullpath, self)
        return fullpath

    @staticmethod
    def load(filepath):
        """
        Load binary project file

        This method is an alternate constructor that is used to load a binary file
        saved using :meth:`Project.save`. Migration is automatically performed as
        part of the loading operation.

        :param filepath: The file path/name to load
        :return: A new :class:`Project` instance

        """

        P = sc.loadobj(filepath, die=True)
        assert isinstance(P, Project)
        return P

    def __setstate__(self, d):
        self.__dict__ = d
        P = migrate(self)
        self.__dict__ = P.__dict__


def _run_sampled_sim(proj, parset, progset, progset_instructions: list, result_names: list, max_attempts: int = None):
    """
    Internal function to run simulation with sampling

    This function is intended for internal use only. It's purpose is to facilitate the implementation
    of parallelization. It should normally be called via :meth:`Project.run_sim`.

    This standalone function samples and runs a simulation. It is a standalone function rather than
    a method of :class:`Project` or :class:`Ensemble` so that it can be pickled for use in
    ``sc.parallelize`` (otherwise, an error relating to not being able to pickle local functions or the
    base class gets raised).

    A sampled simulation may result in bad initial conditions. If that occurs, the parameters and program
    set will be resampled up to a maximum of ``n_attempts`` times, after which an error will be raised.

    :param proj: A :class:`Project` instance
    :param parset: A :class:`ParameterSet` instance
    :param progset: A :class:`ProgramSet` instance
    :param progset_instructions: A list of instructions to run against a single sample
    :param result_names: A list of result names (strings)
    :param max_attempts: Maximum number of sampling attempts before raising an error
    :return: A list of results that either contains 1 result, or the same number of results as instructions

    """

    from .model import BadInitialization  # avoid circular import

    if max_attempts is None:
        max_attempts = 50

    attempts = 0
    while attempts < max_attempts:
        try:
            if progset:
                sampled_parset = parset.sample()
                sampled_progset = progset.sample()
                results = [proj.run_sim(parset=sampled_parset, progset=sampled_progset, progset_instructions=x, result_name=y) for x, y in zip(progset_instructions, result_names)]
            else:
                sampled_parset = parset.sample()
                results = [proj.run_sim(parset=sampled_parset, result_name=y) for y in result_names]
            return results
        except BadInitialization:
            attempts += 1
    raise Exception("Failed simulation after %d attempts - something might have gone wrong" % (max_attempts))
