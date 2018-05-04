"""
PROJECT

The main project class. Almost all functionality is provided by this class.

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

Methods for structure lists:
    1. add -- add a new structure to the odict
    2. remove -- remove a structure from the odict
    3. copy -- copy a structure in the odict
    4. rename -- rename a structure in the odict

Version: 2018mar22
"""

from sciris.core import tic, toc, odict, today, makefilepath, gitinfo, getdate, objrepr, dcp, saveobj, loadobj, uuid

from atomica._version import __version__
# from atomica.programs import Programset
from atomica.calibration import perform_autofit
from atomica.data import ProjectData
from atomica.excel import ExcelSettings as ES
from atomica.framework import ProjectFramework
from atomica.model import runModel
from atomica.parameters import ParameterSet
from atomica.project_settings import ProjectSettings
from atomica.scenarios import ParameterScenario
from atomica.structure_settings import FrameworkSettings as FS, DataSettings as DS
from atomica.system import SystemSettings as SS, apply_to_all_methods, log_usage, AtomicaException, logger
from atomica.workbook_export import writeWorkbook, makeInstructions
from atomica.workbook_import import readWorkbook


# from numpy.random import seed, randint

@apply_to_all_methods(log_usage)
class Project(object):
    def __init__(self, name="default", framework=None, databook_path=None, do_run=True):
        """ Initialize the project. """

        self.name = name
        # self.filename = None # Never saved to file
        self.framework = framework if framework else ProjectFramework()
        self.data = ProjectData()  # TEMPORARY

        # Define the structure sets
        self.parsets = odict()
        self.progsets = odict()
        self.scens = odict()
        self.optims = odict()
        self.results = odict()

        # Define metadata
        self.uid = uuid()
        self.version = __version__
        self.gitinfo = gitinfo()
        self.created = today()
        self.modified = today()
        self.databookloaddate = 'Databook never loaded'
        self.settings = ProjectSettings()  # Global settings

        # Load spreadsheet, if available
        if framework and databook_path:
            # TODO: Consider compatibility checks for framework/databook.
            self.load_databook(databook_path=databook_path, do_run=do_run)

    def __repr__(self):
        """ Print out useful information when called """
        output = objrepr(self)
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
        output += '      Date created: %s\n' % getdate(self.created)
        output += '     Date modified: %s\n' % getdate(self.modified)
        output += '  Datasheet loaded: %s\n' % getdate(self.databookloaddate)
        output += '        Git branch: %s\n' % self.gitinfo['branch']
        output += '          Git hash: %s\n' % self.gitinfo['hash']
        output += '               UID: %s\n' % self.uid
        output += '============================================================\n'
        return output

    #######################################################################################################
    # Methods for I/O and spreadsheet loading
    #######################################################################################################
    def create_databook(self, databook_path=None, num_pops=None, num_progs=None, data_start=None, data_end=None,
                        data_dt=None):
        """ Generate an empty data-input Excel spreadsheet corresponding to the framework of this project. """
        if databook_path is None:
            databook_path = "./databook_" + self.name + ES.FILE_EXTENSION
        databook_instructions, _ = makeInstructions(framework=self.framework, workbook_type=SS.STRUCTURE_KEY_DATA)
        if num_pops is not None:
            databook_instructions.updateNumberOfItems(DS.KEY_POPULATION, num_pops)  # Set the number of populations.
        if num_progs is not None:
            databook_instructions.updateNumberOfItems(DS.KEY_PROGRAM, num_progs)  # Set the number of programs.
        databook_instructions.updateTimeVector(data_start=data_start, data_end=data_end, data_dt=data_dt)
        writeWorkbook(workbook_path=databook_path, framework=self.framework, data=self.data,
                      instructions=databook_instructions, workbook_type=SS.STRUCTURE_KEY_DATA)

    def load_databook(self, databook_path=None, make_default_parset=True, do_run=True):
        """ Load a data spreadsheet. """
        full_path = makefilepath(filename=databook_path, default=self.name, ext='xlsx')
        metadata = readWorkbook(workbook_path=full_path, framework=self.framework, data=self.data,
                                workbook_type=SS.STRUCTURE_KEY_DATA)

        self.databookloaddate = today()  # Update date when spreadsheet was last loaded
        self.modified = today()

        if metadata is not None and "data_start" in metadata:
            self.settings.updateTimeVector(start=metadata["data_start"])  # Align sim start year with data start year.

        if make_default_parset:
            self.make_parset(name="default")
        if do_run:
            if not make_default_parset:
                logger.warning("Project has been requested to run a simulation after loading databook, "
                               "despite no request to create a default parameter set.")
            self.run_sim(parset="default")

    def make_parset(self, name="default", overwrite=False):
        """ Transform project data into a set of parameters that can be used in model simulations. """

        # TODO: Develop some flag or check for data 'emptiness'.
        #        if not self.data: raise AtomicaException("ERROR: No data exists for project '{0}'.".format(self.name))
        self.set_parset(parset_key=name, parset_object=ParameterSet(name=name), overwrite=overwrite)
        self.parsets[name].makePars(self.data)
        return self.parsets[name]

    def make_progset(self, name="default"):
        pass

    #    def makedefaults(self, name=None, scenname=None, overwrite=False):
    #        ''' When creating a project, create a default program set, scenario, and optimization to begin with '''
    #
    #        # Handle inputs
    #        if name is None: name = 'default'
    #        if scenname is None: scenname = 'default'
    #
    #        # Make default progset, scenarios and optimizations
    #        if overwrite or name not in self.progsets:
    #            progset = Programset(name=name, project=self)
    #            self.addprogset(progset)
    #
    #        if overwrite or scenname not in self.scens:
    #            scenlist = [Parscen(name=scenname, parsetname=name,pars=[])]
    #            self.addscens(scenlist)
    #
    #        if overwrite or name not in self.optims:
    #            optim = Optim(project=self, name=name)
    #            self.addoptim(optim)
    #
    #        return None

    def make_scenario(self, name="default", instructions=None, save_to_project=True, overwrite=False):
        scenario = ParameterScenario(name=name, scenario_values=instructions)
        if save_to_project:
            self.set_scenario(scenario_key=name, scenario_object=scenario, overwrite=overwrite)
        return scenario

    #######################################################################################################
    # Methods to handle common tasks with structure lists
    #######################################################################################################

    @staticmethod
    def set_structure(structure_key, structure_object, structure_list, structure_string, overwrite=False):
        """
        Base function for setting elements of structure lists to a structure object.
        Contains optional overwrite validation.
        """
        if structure_key in structure_list:
            if not overwrite:
                raise AtomicaException(
                    "A {0} is already attached to a project under the key '{1}'.".format(structure_string,
                                                                                         structure_key))
            else:
                logger.warning("A {0} already attached to the project with key '{1}' is being overwritten.".format(
                    structure_string, structure_key))
        structure_list[structure_key] = structure_object

    def set_parset(self, parset_key, parset_object, overwrite=False):
        """ 'Set' method for parameter sets to prevent overwriting unless explicit. """
        self.set_structure(structure_key=parset_key, structure_object=parset_object, structure_list=self.parsets,
                           structure_string="parameter set", overwrite=overwrite)

    def set_scenario(self, scenario_key, scenario_object, overwrite=False):
        """ 'Set' method for scenarios to prevent overwriting unless explicit. """
        self.set_structure(structure_key=scenario_key, structure_object=scenario_object, structure_list=self.scens,
                           structure_string="scenario", overwrite=overwrite)

    def copy_parset(self, old_name="default", new_name="copy"):
        """ Deep copy an existent parameter set. """
        parset_object = dcp(self.parsets[old_name])
        parset_object.change_id(new_name=new_name)
        self.set_parset(parset_key=new_name, parset_object=parset_object)

    def get_structure(self, structure, structure_list, structure_string):
        """
        Base method that allows structures to be retrieved via an object or string handle.
        If the latter, validates for existence.
        """
        if structure is None:
            if len(structure_list) < 1:
                raise AtomicaException("Project '{0}' appears to have no {1}s. "
                                       "Cannot select a default to run process.".format(self.name, structure_string))
            else:
                try:
                    structure = structure_list["default"]
                    logger.warning("Project '{0}' has selected {1} with key 'default' "
                                   "to run process.".format(self.name, structure_string))
                except KeyError:
                    structure = structure_list[0]
                    logger.warning("In the absence of a parameter set with key 'default', project '{0}' "
                                   "has selected {1} with name '{2}' to run process.".format(self.name,
                                                                                             structure_string,
                                                                                             structure.name))
        else:
            if isinstance(structure, str):
                if structure not in structure_list:
                    raise AtomicaException("Project '{0}' is lacking a {1} named '{2}'. "
                                           "Cannot run process.".format(self.name, structure_string, structure))
                structure = structure_list[structure]
        return structure

    def get_parset(self, parset):
        """ Allows for parsets to be retrieved from an object or string handle. """
        return self.get_structure(structure=parset, structure_list=self.parsets, structure_string="parameter set")

    def get_scenario(self, scenario):
        """ Allows for scenarios to be retrieved from an object or string handle. """
        return self.get_structure(structure=scenario, structure_list=self.scens, structure_string="scenario")

    #######################################################################################################
    # Methods to perform major tasks
    #######################################################################################################

    def update_settings(self, sim_start=None, sim_end=None, sim_dt=None):
        """ Modify the project settings, e.g. the simulation time vector. """
        self.settings.updateTimeVector(start=sim_start, end=sim_end, dt=sim_dt)

    def run_sim(self, parset=None, progset=None, options=None, store_results=True, result_type=None, result_name=None):
        """ Run model using a selected parset and store/return results. """

        parset = self.get_parset(parset=parset)

        # if progset is None:
        #    try: progset = self.progsets[progset_name]
        #    except: logger.info("Initiating a standard run of project '{0}' "
        #                        "(i.e. without the influence of programs).".format(self.name))
        # if progset is not None:
        #    if options is None:
        #        logger.info("Program set '{0}' will be ignored while running project '{1}' "
        #                    "due to no options specified.".format(progset.name, self.name))
        #        progset = None

        if result_name is None:
            base_name = "parset_" + parset.name
            if progset is not None:
                base_name = base_name + "_progset_" + progset.name
            if result_type is not None:
                base_name = result_type + "_" + base_name

            k = 1  # consider making this 2?
            result_name = base_name
            while result_name in self.results:
                result_name = base_name + "_" + str(k)
                k += 1

        tm = tic()
        result = runModel(settings=self.settings, framework=self.framework, parset=parset, progset=progset,
                          options=options, name=result_name)
        toc(tm, label="running '{0}' model".format(self.name))

        if store_results:
            self.results[result_name] = result

        return result

    def calibrate(self, parset, adjustables=None, measurables=None, max_time=60, save_to_project=True, new_name=None,
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
        parset = self.get_parset(parset=parset)
        if adjustables is None:
            adjustables = self.framework.specs[FS.KEY_PARAMETER].keys()
        if measurables is None:
            measurables = self.framework.specs[FS.KEY_COMPARTMENT].keys()
            measurables += self.framework.specs[FS.KEY_CHARACTERISTIC].keys()
        for index, adjustable in enumerate(adjustables):
            if isinstance(adjustable, str):  # Assume that a parameter name was passed in if not a tuple.
                adjustables[index] = (adjustable, None, default_min_scale, default_max_scale)
        for index, measurable in enumerate(measurables):
            if isinstance(measurable, str):  # Assume that a parameter name was passed in if not a tuple.
                measurables[index] = (measurable, None, default_weight, default_metric)
        new_parset = perform_autofit(project=self, parset=parset,
                                     pars_to_adjust=adjustables, output_quantities=measurables, max_time=max_time)
        new_parset.change_id(new_name=new_name)  # The new parset is a calibrated copy of the old, so change id.
        if save_to_project:
            self.set_parset(parset_key=new_parset.name, parset_object=new_parset, overwrite=True)

        return new_parset

    #    def outcome(self):
    #        ''' Function to get the outcome for a particular sim and objective'''
    #        pass

    def run_scenario(self, scenario, parset=None, progset=None, options=None, store_results=True, result_name=None):
        """ Run a scenario. """
        parset = self.get_parset(parset)
        scenario = self.get_scenario(scenario)
        scenario_parset = scenario.get_parset(parset, self.settings)
        scenario_progset, scenario_options = scenario.get_progset(progset, self.settings, options)
        return self.run_sim(parset=scenario_parset, progset=scenario_progset, options=scenario_options,
                            store_results=store_results, result_type="scenario", result_name=result_name)

    #    def optimize(self):
    #        '''Run an optimization'''

    def save(self, filepath):
        """ Save the current project to a relevant object file. """
        filepath = makefilepath(filename=filepath, ext=SS.OBJECT_EXTENSION_PROJECT,
                                sanitize=True)  # Enforce file extension.
        saveobj(filepath, self)

    @classmethod
    def load(cls, filepath):
        """ Convenience class method for loading a project in the absence of an instance. """
        return loadobj(filepath)
