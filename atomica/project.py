"""
Implements the :py:class:`Project` user interface for Atomica

The :py:class:`Project` class serves as the primary user interface for
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

from .version import version
from .calibration import perform_autofit
from .data import ProjectData
from .framework import ProjectFramework
from .model import run_model
from .parameters import ParameterSet

from .programs import ProgramSet
from .scenarios import Scenario, ParameterScenario, BudgetScenario, CoverageScenario
from .optimization import Optimization, optimize, OptimInstructions, InvalidInitialConditions
from .system import logger
from .cascade import get_cascade_outputs
from .utils import NDict, evaluate_plot_string
from .plotting import PlotData, plot_series
from .results import Result
from .migration import migrate
import sciris as sc
import numpy as np
from .excel import AtomicaSpreadsheet


class ProjectSettings(object):
    def __init__(self, sim_start=None, sim_end=None, sim_dt=None):

        self.sim_start = sim_start if sim_start is not None else 2000.0
        self.sim_end = sim_end if sim_end is not None else 2035.0
        self.sim_dt = sim_dt if sim_dt is not None else 0.25
        logger.debug("Initialized project settings.")

    def __repr__(self):
        """ Print object """
        output = sc.prepr(self)
        return output

    @property
    def tvec(self):
        return np.arange(self.sim_start, self.sim_end + self.sim_dt / 2, self.sim_dt)

    def update_time_vector(self, start=None, end=None, dt=None):
        """ Calculate time vector. """
        if start is not None:
            self.sim_start = start
        if end is not None:
            self.sim_end = end
        if dt is not None:
            self.sim_dt = dt
        return None


class Project(object):
    def __init__(self, name="default", framework=None, frw_name=None, databook_path=None, do_run=True, **kwargs):
        """ Initialize the project. Keywords are passed to ProjectSettings. """
        # INPUTS
        # - framework : a Framework to use. This could be
        #               - A filename to an Excel file on disk
        #               - An AtomicaSpreadsheet instance
        #               - A ProjectFramework instance
        #               - None (this should generally not be used though!)
        # - databook_path : The path to a databook file. The databook will be loaded into Project.data and the spreadsheet saved to Project.databook
        # - do_run : If True, a simulation will be run upon project construction

        self.name = name

        if sc.isstring(framework) or isinstance(framework, AtomicaSpreadsheet):
            self.framework = ProjectFramework(inputs=framework, name=frw_name)
        elif isinstance(framework, ProjectFramework):
            self.framework = framework
        else:
            logger.warning('Project was constructed without a Framework - a framework should be provided')
            self.framework = None

        # Define the structure sets
        self.parsets = NDict()
        self.progsets = NDict()
        self.scens = NDict()
        self.optims = NDict()
        self.results = NDict()

        # Define metadata
        self.uid = sc.uuid()
        self.version = version
        self.gitinfo = sc.gitinfo(__file__)
        self.created = sc.now()
        self.modified = sc.now()
        self.filename = None

        self.progbook = None  # This will contain an AtomicaSpreadsheet when the user loads one
        self.settings = ProjectSettings(**kwargs)  # Global settings

        self._result_update_required = False  # This flag is set to True by migration is the result objects contained in this Project are out of date due to a migration change

        # Load project data, if available
        if framework and databook_path:
            # TODO: Consider compatibility checks for framework/databook.
            self.load_databook(databook_path=databook_path, do_run=do_run)
        elif databook_path:
            logger.warning('Project was constructed without a Framework - databook spreadsheet is being saved to project, but data is not being loaded')
            self.databook = AtomicaSpreadsheet(databook_path)  # Just load the spreadsheet in so that it isn't lost
            self.data = None
        else:
            self.databook = None  # This will contain an AtomicaSpreadsheet when the user loads one
            self.data = None

    def __repr__(self):
        """ Print out useful information when called """
        output = sc.objrepr(self)
        output += '      Project name: %s\n' % self.name
        output += '    Framework name: %s\n' % self.framework.name
        output += '\n'
        output += '    Parameter sets: %i\n' % len(self.parsets)
        output += '      Program sets: %i\n' % len(self.progsets)
        output += '         Scenarios: %i\n' % len(self.scens)
        output += '     Optimizations: %i\n' % len(self.optims)
        output += '      Results sets: %i\n' % len(self.results)
        output += '\n'
        output += '   Atomica version: %s\n' % self.version
        output += '      Date created: %s\n' % sc.getdate(self.created)
        output += '     Date modified: %s\n' % sc.getdate(self.modified)
#        output += '  Datasheet loaded: %s\n' % sc.getdate(self.databookloaddate)
        output += '        Git branch: %s\n' % self.gitinfo['branch']
        output += '          Git hash: %s\n' % self.gitinfo['hash']
        output += '               UID: %s\n' % self.uid
        output += '============================================================\n'
        return output

    @property
    def pop_names(self):
        if self.data is None:
            return []
        else:
            return list(self.data.pops.keys())

    @property
    def pop_labels(self):
        if self.data is None:
            return []
        else:
            return list([x['label'] for x in self.data.pops.values()])

    #######################################################################################################
    # Methods for I/O and spreadsheet loading
    #######################################################################################################
    def create_databook(self, databook_path=None, num_pops=1, num_transfers=0, num_interpops=0, data_start=2000.0, data_end=2020.0, data_dt=1.0):
        """ Generate an empty data-input Excel spreadsheet corresponding to the framework of this project. """
        if databook_path is None:
            databook_path = "./databook_" + self.name + ".xlsx"
        data = ProjectData.new(self.framework, np.arange(data_start, data_end + data_dt, data_dt), pops=num_pops, transfers=num_transfers)
        data.save(databook_path)
        return data

    def load_databook(self, databook_path=None, make_default_parset=True, do_run=True):
        """
        Load a data spreadsheet.

        INPUTS:
        - databook_path: a path string, which will load a file from disk, or an AtomicaSpreadsheet
                         containing the contents of a databook
        - make_default_parset: If True, a Parset called "default" will be immediately created from the
                               newly-added data
        - do_run: If True, a simulation will be run using the new parset
        """
        if sc.isstring(databook_path):
            full_path = sc.makefilepath(filename=databook_path, default=self.name, ext='xlsx', makedirs=False)
            databook_spreadsheet = AtomicaSpreadsheet(full_path)
        else:
            databook_spreadsheet = databook_path

        self.data = ProjectData.from_spreadsheet(databook_spreadsheet, self.framework)
        self.data.validate(self.framework)  # Make sure the data is suitable for use in the Project (as opposed to just manipulating the databook)
        self.databook = sc.dcp(databook_spreadsheet)  # Actually a shallow copy is fine here because AtomicaSpreadsheet contains no mutable properties
        self.modified = sc.now()
        self.settings.update_time_vector(start=self.data.start_year)  # Align sim start year with data start year.

        if not (self.framework.comps['is source'] == 'y').any():
            self.settings.update_time_vector(end=self.data.end_year + 5.0)  # Project only forecasts 5 years if not dynamic (with births)

        if make_default_parset:
            self.make_parset(name="default")
        if do_run:
            if not make_default_parset:
                logger.warning("Project has been requested to run a simulation after loading databook, "
                               "despite no request to create a default parameter set.")
            self.run_sim(parset="default")

    def make_parset(self, name="default"):
        """ Transform project data into a set of parameters that can be used in model simulations. """
        self.parsets.append(ParameterSet(name))
        self.parsets[name].make_pars(self.framework, self.data)
        return self.parsets[name]

    def make_progbook(self, progbook_path=None, progs=None, data_start=None, data_end=None, blh_effects=False):
        ''' Make a blank program databook'''
        # Get filepath
        if self.data is None:
            errormsg = 'Please upload a databook before creating a program book. The databook defines which populations will appear in the program book.'
            raise Exception(errormsg)
        full_path = sc.makefilepath(filename=progbook_path, default=self.name, ext='xlsx', makedirs=False)  # Directory will be created later in progset.save()
        if data_start is None:
            data_start = self.data.tvec[0]
        if data_end is None:
            data_end = self.data.tvec[-1]
        progset = ProgramSet.new(tvec=np.arange(data_start, data_end + 1), progs=progs, framework=self.framework, data=self.data)
        progset.save(full_path)

    def load_progbook(self, progbook_path=None, name="default", blh_effects=False, verbose=False):
        ''' Load a programs databook'''
        if verbose:
            print('Making ProgramSet')
        if verbose:
            print('Uploading program data')
        if self.data is None:
            errormsg = 'Please upload a databook before uploading a program book. The databook contains the population definitions required to read the program book.'
            raise Exception(errormsg)

        if sc.isstring(progbook_path):
            full_path = sc.makefilepath(filename=progbook_path, default=self.name, ext='xlsx', makedirs=False)
            progbook_spreadsheet = AtomicaSpreadsheet(full_path)
        else:
            progbook_spreadsheet = progbook_path

        progset = ProgramSet.from_spreadsheet(spreadsheet=progbook_spreadsheet, framework=self.framework, data=self.data)
        progset.validate()
        self.progbook = sc.dcp(progbook_spreadsheet)  # Actually a shallow copy is fine here because AtomicaSpreadsheet contains no mutable properties

        if verbose:
            print('Updating program sets')
        self.progsets.append(progset)
        if verbose:
            print('Done with make_progset().')

    def make_scenario(self, name="default", which=None, instructions=None, json=None):
        if json is not None:
            if which == 'budget':
                scenario = BudgetScenario(**json)
            elif which == 'coverage':
                scenario = CoverageScenario(**json)
            else:
                raise Exception('Parameter scenarios from JSON not implemented')
        else:
            if which == 'parameter':
                scenario = ParameterScenario(name=name, scenario_values=instructions)
            else:
                raise Exception('Budget scenarios not from JSON not implemented')

        self.scens.append(scenario)
        return scenario

    def make_optimization(self, json=None):
        optim_ins = OptimInstructions(json=json)
        self.optims[optim_ins.json['name']] = optim_ins
        return optim_ins


#    #######################################################################################################
#    ### Utilities
#    #######################################################################################################

    def parset(self, key=None, verbose=2):
        ''' Shortcut for getting a parset '''
        if key is None:
            key = -1
        if isinstance(key, ParameterSet):
            return key  # It's already a parameter set, do nothing
        else:
            try:
                return self.parsets[key]
            except:
                sc.printv('Warning, parset "%s" not found!' % key, 1, verbose)
                return None

    def progset(self, key=None, verbose=2):
        ''' Shortcut for getting a progset '''
        if key is None:
            key = -1
        if isinstance(key, ProgramSet):
            return key  # It's already a program set, do nothing
        else:
            try:
                return self.progsets[key]
            except:
                sc.printv('Warning, progset "%s" not found!' % key, 1, verbose)
                return None

    def scen(self, key=None, verbose=2):
        ''' Shortcut for getting a scenario '''
        if key is None:
            key = -1
        if isinstance(key, Scenario):
            return key  # It's already a scenario, do nothing
        else:
            try:
                return self.scens[key]
            except:
                sc.printv('Warning, scenario "%s" not found!' % key, 1, verbose)
                return None

    def optim(self, key=None, verbose=2):
        ''' Shortcut for getting an optimization '''
        if key is None:
            key = -1
        if isinstance(key, Optimization):
            return key  # It's already an optimization, do nothing
        else:
            try:
                return self.optims[key]
            except:
                sc.printv('Warning, scenario "%s" not found!' % key, 1, verbose)
                return None

    def result(self, key=None, verbose=2):
        ''' Shortcut for getting an result -- a little special since they don't have a fixed type '''
        if key is None:
            key = -1
        if not sc.isstring(key) and not sc.isnumber(key) and not isinstance(key, tuple):
            if not isinstance(key, [Result, list, sc.odict]):
                print('Warning: result "%s" is of unexpected type: "%s"' % (key, type(key)))
            return key  # It's not something that looks like a key
        else:
            try:
                return self.scens[key]
            except:
                sc.printv('Warning, scenario "%s" not found!' % key, 1, verbose)
                return None

        if key is None:
            key = -1
        try:
            return self.results[key]
        except:
            return sc.printv('Warning, results "%s" not found!' % key, 1, verbose)  # Returns None

    #######################################################################################################
    # Methods to perform major tasks
    #######################################################################################################

    def plot(self, results=None, key=None, outputs=None, pops=None):

        def get_supported_plots():
            df = self.framework.sheets['plots'][0]
            plots = sc.odict()
            for name, output in zip(df['name'], df['quantities']):
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
                figs = plot_series(plotdata, axis='pops', plot_type='stacked', legend_mode='together')
                allfigs += figs
            except Exception as e:
                print('WARNING, %s failed (%s)' % (output, str(e)))
        return allfigs

    def update_settings(self, sim_start=None, sim_end=None, sim_dt=None):
        """ Modify the project settings, e.g. the simulation time vector. """
        self.settings.update_time_vector(start=sim_start, end=sim_end, dt=sim_dt)

    def run_sim(self, parset=None, progset=None, progset_instructions=None,
                store_results=True, result_type=None, result_name=None):
        """
        Run model using a selected parset and store/return results.
        An optional program set and use instructions can be passed in to simulate budget-based interventions.
        """

        parset = self.parset(parset)
        if progset is not None:     # Do not grab a default program set in case one does not exist.
            progset = progset if isinstance(progset, ProgramSet) else self.progset(progset)

        if progset is None:
            logger.info("Initiating a standard run of project '%s' (no programs)", self.name)
        elif progset_instructions is None:
            logger.info("Program set '%s' will be ignored while running project '%s' due to the absence of program set instructions", progset.name, self.name)
        else:
            logger.info("Initiating a run of project '%s' with programs", self.name)

        if result_name is None:
            base_name = "parset_" + parset.name
            if progset is not None:
                base_name = base_name + "_progset_" + progset.name
            if result_type is not None:
                base_name = result_type + "_" + base_name

            k = 1
            result_name = base_name
            while result_name in self.results:
                result_name = base_name + "_" + str(k)
                k += 1

        tm = sc.tic()
        result = run_model(settings=self.settings, framework=self.framework, parset=parset, progset=progset,
                           program_instructions=progset_instructions, name=result_name)
        sc.toc(tm, label="running '{0}' model".format(self.name))

        if store_results:
            self.results.append(result)

        return result

    def calibrate(self, parset=None, adjustables=None, measurables=None, max_time=60, save_to_project=True, new_name=None,
                  default_min_scale=0.0, default_max_scale=2.0, default_weight=1.0, default_metric="fractional"):
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
            parset = -1
        parset = self.parsets[parset]
        if new_name is None:
            new_name = parset.name + ' (auto-calibrated)'
        if adjustables is None:
            adjustables = list(self.framework.pars.index[~self.framework.pars['calibrate'].isnull()])
            adjustables += list(self.framework.comps.index[~self.framework.comps['calibrate'].isnull()])
            adjustables += list(self.framework.characs.index[~self.framework.characs['calibrate'].isnull()])
        if measurables is None:
            measurables = list(self.framework.comps.index)
            measurables += list(self.framework.characs.index)
        for index, adjustable in enumerate(adjustables):
            if sc.isstring(adjustable):  # Assume that a parameter name was passed in if not a tuple.
                adjustables[index] = (adjustable, None, default_min_scale, default_max_scale)
        for index, measurable in enumerate(measurables):
            if sc.isstring(measurable):  # Assume that a parameter name was passed in if not a tuple.
                measurables[index] = (measurable, None, default_weight, default_metric)
        new_parset = perform_autofit(project=self, parset=parset,
                                     pars_to_adjust=adjustables, output_quantities=measurables, max_time=max_time)
        new_parset.name = new_name  # The new parset is a calibrated copy of the old, so change id.
        if save_to_project:
            self.parsets.append(new_parset)

        return new_parset

    def run_scenarios(self, store_results=True):
        results = []
        for scenario in self.scens.values():
            if scenario.active:
                result = scenario.run(project=self, store_results=store_results)
                results.append(result)
        return results

    def run_optimization(self, optimname=None, maxtime=None, maxiters=None, store_results=True):
        '''Run an optimization'''
        optim_ins = self.optim(optimname)
        optim, unoptimized_instructions = optim_ins.make(project=self)
        if maxtime is not None:
            optim.maxtime = maxtime
        if maxiters is not None:
            optim.maxiters = maxiters
        parset = self.parset(optim.parsetname)
        progset = self.progset(optim.progsetname)
        original_end = self.settings.sim_end
        self.settings.sim_end = optim_ins.json['end_year']  # Simulation should be run up to the user's end year
        try:
            optimized_instructions = optimize(self, optim, parset, progset, unoptimized_instructions)
        except InvalidInitialConditions:
            if optim_ins.json['optim_type'] == 'money':
                raise Exception('It was not possible to achieve the optimization target even with an increased budget. Specify or raise upper limits for spending, or decrease the optimization target')
            else:
                raise  # Just raise it as-is

        self.settings.sim_end = original_end  # Note that if the end year is after the original simulation year, the result won't be visible (although it will have been optimized for)
        optimized_result = self.run_sim(parset=parset, progset=progset, progset_instructions=optimized_instructions, result_name="Optimized", store_results=store_results)
        unoptimized_result = self.run_sim(parset=parset, progset=progset, progset_instructions=unoptimized_instructions, result_name="Baseline", store_results=store_results)
        results = [unoptimized_result, optimized_result]
        return results

    def save(self, filename=None, folder=None):
        """ Save the current project to a relevant object file. """
        fullpath = sc.makefilepath(filename=filename, folder=folder, default=[self.filename, self.name], ext='prj', sanitize=True)
        self.filename = fullpath
        sc.saveobj(fullpath, self)
        return fullpath

    @staticmethod
    def load(filepath):
        """ Convenience class method for loading a project in the absence of an instance. """
        P = sc.loadobj(filepath)
        assert isinstance(P, Project)
        P = migrate(P)
        return P

    def demo_scenarios(self, dorun=False, doadd=True):
        json1 = sc.odict()
        json1['name'] = 'Default budget'
        json1['parsetname'] = -1
        json1['progsetname'] = -1
        json1['start_year'] = self.data.end_year  # This allows the tests to run on the BE where this default never gets modified e.g. by set_scen_info()
        json1['alloc_year'] = self.data.end_year
        json1['alloc'] = self.progset(json1['progsetname']).get_alloc(tvec=json1['alloc_year'])
        json1['active'] = True

        json2 = sc.dcp(json1)
        json2['name'] = 'Doubled budget'
        json2['alloc'][:] *= 2.0
        json2['active'] = True

        json3 = sc.dcp(json1)
        json3['name'] = 'Zero budget'
        json3['alloc'][:] *= 0.0
        json3['active'] = True

        if doadd:
            for json in [json1, json2, json3]:
                self.make_scenario(which='budget', json=json)
            if dorun:
                results = self.run_scenarios()
                return results
            else:
                return None
        else:
            return json1

    def demo_optimization(self, dorun=False, tool=None, optim_type=None):
        # INPUTS
        # - dorun : If True, runs optimization immediately
        # - tool : Choose optimization objectives based on whether tool is 'cascade' or 'tb'
        # - optim_type : set to 'outcome' or 'money' - use 'money' to minimize money
        #
        # Note that if optim_type='money' then the optimization 'weights' entered in the FE are
        # actually treated as relative scalings for the minimization target. e.g. If ':ddis' has a weight
        # of 25, this is a objective weight factor for optim_type='outcome' but it means 'we need to reduce
        # deaths by 25%' if optim_type='money' (since there is no weight factor for the minimize money epi targets)
        if optim_type is None:
            optim_type = 'outcome'
        assert tool in ['cascade', 'tb']
        assert optim_type in ['outcome', 'money']
        json = sc.odict()
        if optim_type == 'outcome':
            json['name'] = 'Default outcome optimization'
        elif optim_type == 'money':
            json['name'] = 'Default money optimization'
        json['parset_name'] = -1
        json['progset_name'] = -1
        json['start_year'] = self.data.end_year
        json['end_year'] = self.settings.sim_end
        json['budget_factor'] = 1.0
        json['optim_type'] = optim_type
        json['tool'] = tool
        json['method'] = 'asd'  # Note: may want to change this if PSO is improved

        if tool == 'cascade':
            json['objective_weights'] = sc.odict()
            json['objective_labels'] = sc.odict()

            for cascade_name in self.framework.cascades:
                cascade = get_cascade_outputs(self.framework, cascade_name)

                if optim_type == 'outcome':
                    json['objective_weights']['conversion:%s' % (cascade_name)] = 1.
                elif optim_type == 'money':
                    json['objective_weights']['conversion:%s' % (cascade_name)] = 0.
                else:
                    raise Exception('Unknown optim_type')

                if cascade_name.lower() == 'cascade':
                    json['objective_labels']['conversion:%s' % (cascade_name)] = 'Maximize the conversion rates along each stage of the cascade'
                else:
                    json['objective_labels']['conversion:%s' % (cascade_name)] = 'Maximize the conversion rates along each stage of the %s cascade' % (cascade_name)

                for stage_name in cascade.keys():
                    # We checked earlier that there are no ':' symbols here, but asserting that this is true, just in case
                    assert ':' not in cascade_name
                    assert ':' not in stage_name
                    objective_name = 'cascade_stage:%s:%s' % (cascade_name, stage_name)

                    if optim_type == 'outcome':
                        json['objective_weights'][objective_name] = 1
                    elif optim_type == 'money':
                        json['objective_weights'][objective_name] = 0
                    else:
                        raise Exception('Unknown optim_type')

                    if cascade_name.lower() == 'cascade':
                        json['objective_labels'][objective_name] = 'Maximize the number of people in cascade stage "%s"' % (stage_name)
                    else:
                        json['objective_labels'][objective_name] = 'Maximize the number of people in stage "%s" of the %s cascade' % (stage_name, cascade_name)

        elif tool == 'tb':
            if optim_type == 'outcome':
                json['objective_weights'] = {'ddis': 1, 'acj': 1, 'ds_inf': 0, 'mdr_inf': 0, 'xdr_inf': 0}  # These are TB-specific: maximize people alive, minimize people dead due to TB
                json['objective_labels'] = {'ddis': 'Minimize TB-related deaths',
                                            'acj': 'Minimize total new active TB infections',
                                            'ds_inf': 'Minimize prevalence of active DS-TB',
                                            'mdr_inf': 'Minimize prevalence of active MDR-TB',
                                            'xdr_inf': 'Minimize prevalence of active XDR-TB'}
            elif optim_type == 'money':
                # The weights here default to 0 because it's possible, depending on what programs are selected, that improvement
                # in one or more of them might be impossible even with infinite money. Also, can't increase money too much because otherwise
                # run the risk of a local minimum stopping optimization early with the current algorithm (this will change in the future)
                json['objective_weights'] = {'ddis': 0, 'acj': 5, 'ds_inf': 0, 'mdr_inf': 0, 'xdr_inf': 0}  # These are TB-specific: maximize people alive, minimize people dead due to TB
                json['objective_labels'] = {'ddis': 'Minimize TB-related deaths',
                                            'acj': 'Total new active TB infections',
                                            'ds_inf': 'Prevalence of active DS-TB',
                                            'mdr_inf': 'Prevalence of active MDR-TB',
                                            'xdr_inf': 'Prevalence of active XDR-TB'}

            else:
                raise Exception('Unknown optim_type')

        else:
            raise Exception('Tool "%s" not recognized' % tool)
        json['maxtime'] = 30  # WARNING, default!
        json['prog_spending'] = sc.odict()
        for prog_name in self.progset().programs.keys():
            json['prog_spending'][prog_name] = [0, None]
        optim = self.make_optimization(json=json)
        if dorun:
            results = self.run_optimization(optimname=json['name'])
            return results
        else:
            return optim
