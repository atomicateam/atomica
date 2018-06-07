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

Version: 2018jun04
"""

from atomica.version import version
from atomica.calibration import perform_autofit
from atomica.data import ProjectData
from atomica.excel import ExcelSettings as ES
from atomica.framework import ProjectFramework
from atomica.model import run_model
from atomica.parameters import ParameterSet
from atomica.programs import Program, ProgramSet
from atomica.scenarios import Scenario, ParameterScenario
from atomica.structure_settings import FrameworkSettings as FS, DataSettings as DS
from atomica.system import SystemSettings as SS, apply_to_all_methods, log_usage, AtomicaException, logger
from atomica.workbook_export import write_workbook, make_instructions
from atomica.workbook_import import read_workbook, load_progbook
from atomica.utils import SList
from atomica.optimization import Optim
from atomica.results import Result
import sciris.core as sc
import numpy as np



class ProjectSettings(object):
    def __init__(self, sim_start=None, sim_end=None, sim_dt=None):

        self.sim_start = sim_start if sim_start is not None else 2000.0
        self.sim_end = sim_end if sim_end is not None else 2030.0
        self.sim_dt = sim_dt if sim_dt is not None else 1.0 / 4

        # Other
        #        self.defaultblue = (0.16, 0.67, 0.94) # The color of Atomica
        #        self.safetymargin = 0.5 # Do not move more than this fraction of people on a single timestep
        #        self.infmoney = 1e10 # A lot of money
        logger.info("Initialized project settings.")

    def __repr__(self):
        """ Print object """
        output = sc.desc(self)
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



@apply_to_all_methods(log_usage)
class Project(object):
    def __init__(self, name="default", framework=None, databook_path=None, do_run=True):
        """ Initialize the project. """

        self.name = name
        # self.filename = None # Never saved to file
        self.framework = framework if framework else ProjectFramework()
        self.data = ProjectData()  # TEMPORARY

        # Define the structure sets
        self.parsets  = SList()
        self.progsets = SList()
        self.scens    = SList()
        self.optims   = SList()
        self.results  = SList()

        # Define metadata
        self.uid = sc.uuid()
        self.version = version
        self.gitinfo = sc.gitinfo(__file__)
        self.created = sc.today()
        self.modified = sc.today()
        self.databookloaddate = 'Databook never loaded'
        self.programdatabookloaddate = 'Programs databook never loaded'
        self.settings = ProjectSettings() # Global settings

        ## Load spreadsheet, if available
        if framework and databook_path: # Should we somehow check if these are compatible? Or should a spreadsheet somehow dominate, maybe just loading a datasheet should be enough to generate a framework?
            self.load_databook(databook_path=databook_path, do_run=do_run)

        return None

        # Load spreadsheet, if available
        if framework and databook_path:
            # TODO: Consider compatibility checks for framework/databook.
            self.load_databook(databook_path=databook_path, do_run=do_run)

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
        output += '  Datasheet loaded: %s\n' % sc.getdate(self.databookloaddate)
        output += '        Git branch: %s\n' % self.gitinfo['branch']
        output += '          Git hash: %s\n' % self.gitinfo['hash']
        output += '               UID: %s\n' % self.uid
        output += '============================================================\n'
        return output

    #######################################################################################################
    # Methods for I/O and spreadsheet loading
    #######################################################################################################
    def create_databook(self, databook_path=None, num_pops=None, num_trans=None, num_progs=None, data_start=None, data_end=None,
                        data_dt=None):
        """ Generate an empty data-input Excel spreadsheet corresponding to the framework of this project. """
        if databook_path is None:
            databook_path = "./databook_" + self.name + ES.FILE_EXTENSION
        databook_instructions, _ = make_instructions(framework=self.framework, workbook_type=SS.STRUCTURE_KEY_DATA)
        if num_pops is not None:
            databook_instructions.update_number_of_items(DS.KEY_POPULATION, num_pops)  # Set the number of populations.
        if num_trans is not None:
            databook_instructions.update_number_of_items(DS.KEY_TRANSFER, num_trans)  # Set the number of transfers.
        if num_progs is not None:
            databook_instructions.update_number_of_items(DS.KEY_PROGRAM, num_progs)  # Set the number of programs.
        databook_instructions.update_time_vector(data_start=data_start, data_end=data_end, data_dt=data_dt)
        write_workbook(workbook_path=databook_path, framework=self.framework, data=self.data,
                       instructions=databook_instructions, workbook_type=SS.STRUCTURE_KEY_DATA)

    def load_databook(self, databook_path=None, make_default_parset=True, do_run=True):
        """ Load a data spreadsheet. """
        full_path = sc.makefilepath(filename=databook_path, default=self.name, ext='xlsx')
        metadata = read_workbook(workbook_path=full_path, framework=self.framework, data=self.data,
                                 workbook_type=SS.STRUCTURE_KEY_DATA)

        self.databookloaddate = sc.today()  # Update date when spreadsheet was last loaded
        self.modified = sc.today()
        
        # Put the population keys somewhere easier to access- TEMP, TODO, fix
        self.popkeys = []
        self.popnames = []
        for k,v in self.data.specs['pop'].items():
            self.popkeys.append(k)
            self.popnames.append(v['label'])

        if metadata is not None and "data_start" in metadata:
            self.settings.update_time_vector(start=metadata["data_start"])  # Align sim start year with data start year.

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
        self.parsets[name].make_pars(self.data)
        return self.parsets[name]


    def load_progbook(self, databook_path=None, make_default_progset=True):
        ''' Load a programs databook'''
        
        ## Load spreadsheet and update metadata
        full_path = sc.makefilepath(filename=databook_path, default=self.name, ext='xlsx')
        progdata = load_progbook(filename=full_path)
        
        # Check if the populations match - if not, raise an error, if so, add the data
        if set(progdata['pops']) != set(self.popnames):
            errormsg = 'The populations in the programs databook are not the same as those that were loaded from the epi databook: "%s" vs "%s"' % (progdata['pops'], set(self.popnames))
            raise AtomicaException(errormsg)
        self.progdata = progdata

        self.programdatabookloaddate = sc.today() # Update date when spreadsheet was last loaded
        self.modified = sc.today()

        if make_default_progset: self.make_progset(name="default")
        

    def make_progset(self, progdata=None, name="default"):
        '''Make a progset from program spreadsheet data'''
        
<<<<<<< HEAD
        progset = ProgramSet(name=name)
        progset.make(progdata=progdata, project=self)
        self.progsets.insert(progset)
=======
        # Sort out inputs
        if progdata is None:
            if self.progdata is None:
                errormsg = 'You need to supply program data or a project with program data in order to make a program set.'
                raise AtomicaException(errormsg)
            else:
                progdata = self.progdata
                
        # Check if the populations match - if not, raise an error, if so, add the data
        if set(progdata['pops']) != set(self.popnames):
            errormsg = 'The populations in the program data are not the same as those that were loaded from the epi databook: "%s" vs "%s"' % (progdata['pops'], set(self.popnames))
            raise AtomicaException(errormsg)
                
        nprogs = len(progdata['progs']['short'])
        programs = []
        
        for n in range(nprogs):
            pkey = progdata['progs']['short'][n]
            data = {k: progdata[pkey][k] for k in ('cost', 'coverage')}
            data['t'] = progdata['years']
            prg = Program(short=pkey,
                        name=progdata['progs']['short'][n],
                        targetpops=[val for i,val in enumerate(progdata['pops']) if progdata['progs']['targetpops'][i]],
                        unitcost=progdata[pkey]['unitcost'],
                        capacity=progdata[pkey]['capacity'],
                        data=data
                        )
            programs.append(prg)
            
        progset = ProgramSet(name=name,programs=programs)
        self.progsets.append(progset)
        return progset
>>>>>>> tb-gui-demo

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
        
    def make_scenario(self, name="default", instructions=None):
        scenario = ParameterScenario(name=name, scenario_values=instructions)
        self.scens.append(scenario)
        return scenario


#    #######################################################################################################
#    ### Utilities
#    #######################################################################################################
#
#    def restorelinks(self):
#        ''' Loop over all objects that have links back to the project and restore them '''
#        for item in self.parsets.values()+self.progsets.values()+self.scens.values()+self.optims.values()+self.results.values():
#            if hasattr(item, 'projectref'):
#                item.projectref = Link(self)
#        return None
#
#
#    def pars(self, key=-1, verbose=2):
#        ''' Shortcut for getting the latest active set of parameters, i.e. self.parsets[-1].pars '''
#        try:    return self.parsets[key].pars
#        except: return printv('Warning, parameters dictionary not found!', 1, verbose) # Returns None
#    
#    def parset(self, key=-1, verbose=2):
#        ''' Shortcut for getting the latest active parameters set, i.e. self.parsets[-1] '''
#        try:    return self.parsets[key]
#        except: return printv('Warning, parameter set not found!', 1, verbose) # Returns None
#    
#    def programs(self, key=-1, verbose=2):
#        ''' Shortcut for getting the latest active set of programs '''
#        try:    return self.progsets[key].programs
#        except: return printv('Warning, programs not found!', 1, verbose) # Returns None
#
#    def progset(self, key=-1, verbose=2):
#        ''' Shortcut for getting the latest active program set, i.e. self.progsets[-1]'''
#        try:    return self.progsets[key]
#        except: return printv('Warning, program set not found!', 1, verbose) # Returns None
#    
#    def scen(self, key=-1, verbose=2):
#        ''' Shortcut for getting the latest scenario, i.e. self.scens[-1]'''
#        try:    return self.scens[key]
#        except: return printv('Warning, scenario not found!', 1, verbose) # Returns None
#
#    def optim(self, key=-1, verbose=2):
#        ''' Shortcut for getting the latest optimization, i.e. self.optims[-1]'''
#        try:    return self.optims[key]
#        except: return printv('Warning, optimization not found!', 1, verbose) # Returns None
#
#    def result(self, key=-1, verbose=2):
#        ''' Shortcut for getting the latest active results, i.e. self.results[-1]'''
#        try:    return self.results[key]
#        except: return printv('Warning, results set not found!', 1, verbose) # Returns None


    #######################################################################################################
    # Methods to perform major tasks
    #######################################################################################################

    def update_settings(self, sim_start=None, sim_end=None, sim_dt=None):
        """ Modify the project settings, e.g. the simulation time vector. """
        self.settings.update_time_vector(start=sim_start, end=sim_end, dt=sim_dt)

    def run_sim(self, parset=None, progset=None, progset_instructions=None,
                store_results=True, result_type=None, result_name=None):
        """
        Run model using a selected parset and store/return results.
        An optional program set and use instructions can be passed in to simulate budget-based interventions.
        """

        parset = parset if isinstance(parset,ParameterSet) else self.parsets[parset]
        if progset is not None:     # Do not grab a default program set in case one does not exist.
            progset = progset if isinstance(progset, ProgramSet) else self.progsets[progset]

        if progset is None:
            logger.info("Initiating a standard run of project '{0}' "
                        "(i.e. without the influence of programs).".format(self.name))
        elif progset_instructions is None:
            logger.info("Program set '{0}' will be ignored while running project '{1}' "
                        "due to the absence of program set instructions.".format(progset.name, self.name))

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
                           progset_instructions=progset_instructions, name=result_name)
        sc.toc(tm, label="running '{0}' model".format(self.name))

        if store_results:
            self.results.append(result)

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
        parset = self.parsets[parset]
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
        new_parset.name = new_name  # The new parset is a calibrated copy of the old, so change id.
        if save_to_project:
            self.parsets.append(new_parset)

        return new_parset

    #    def outcome(self):
    #        ''' Function to get the outcome for a particular sim and objective'''
    #        pass

    def run_scenario(self, scenario, parset, progset=None, progset_instructions=None,
                     store_results=True, result_name=None):
        """ Run a scenario. """
        parset = parset if isinstance(parset,ParameterSet) else self.parsets[parset]
        if progset:
            progset = progset if isinstance(progset, ProgramSet) else self.progsets[progset]

        scenario = scenario if isinstance(scenario,Scenario) else self.scens[scenario]
        scenario_parset = scenario.get_parset(parset, self.settings)
        scenario_progset, progset_instructions = scenario.get_progset(progset, self.settings, progset_instructions)
        return self.run_sim(parset=scenario_parset, progset=scenario_progset, progset_instructions=progset_instructions,
                            store_results=store_results, result_type="scenario", result_name=result_name)

    #    def optimize(self):
    #        '''Run an optimization'''

    def save(self, filepath):
        """ Save the current project to a relevant object file. """
        filepath = sc.makefilepath(filename=filepath, ext=SS.OBJECT_EXTENSION_PROJECT,
                                sanitize=True)  # Enforce file extension.
        sc.saveobj(filepath, self)
        return None

    @classmethod
    def load(cls, filepath):
        """ Convenience class method for loading a project in the absence of an instance. """
        return sc.loadobj(filepath)
