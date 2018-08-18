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

Version: 2018jul29
"""

from .version import version
from .calibration import perform_autofit
from .data import ProjectData
from .framework import ProjectFramework
from .model import run_model
from .parameters import ParameterSet

from .programs import ProgramSet, ProgramInstructions
from .scenarios import Scenario, ParameterScenario
from .optimization import optimize, OptimInstructions
from .system import AtomicaException, logger
from .workbook_export import make_progbook
from .workbook_import import load_progbook
from .scenarios import BudgetScenario
from .utils import NDict
import sciris.core as sc
import numpy as np
from .excel import AtomicaSpreadsheet
from six import string_types

class ProjectSettings(object):
    def __init__(self, sim_start=None, sim_end=None, sim_dt=None):

        self.sim_start = sim_start if sim_start is not None else 2000.0
        self.sim_end = sim_end if sim_end is not None else 2035.0
        self.sim_dt = sim_dt if sim_dt is not None else 1.0 / 4

        logger.debug("Initialized project settings.")

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


class Project(object):
    def __init__(self, name="default", framework=None, databook_path=None, do_run=True):
        """ Initialize the project. """
        # INPUTS
        # - framework : a Framework to use. This could be
        #               - A filename to an Excel file on disk
        #               - An AtomicaSpreadsheet instance
        #               - A ProjectFramework instance
        #               - None (this should generally not be used though!)
        # - databook_path : The path to a databook file. The databook will be loaded into Project.data and the spreadsheet saved to Project.databook
        # - do_run : If True, a simulation will be run upon project construction

        self.name = name

        if isinstance(framework,string_types) or isinstance(framework,AtomicaSpreadsheet):
            self.framework = ProjectFramework(inputs=framework)
        elif isinstance(framework,ProjectFramework):
            self.framework = framework
        else:
            logger.warning('Project was constructed without a Framework - a framework should be provided')
            self.framework = None

        # Define the structure sets
        self.parsets  = NDict()
        self.progsets = NDict()
        self.scens    = NDict()
        self.optims   = NDict()
        self.results  = NDict()

        # Define metadata
        self.uid = sc.uuid()
        self.version = version
        self.gitinfo = sc.gitinfo(__file__)
        self.created = sc.today()
        self.modified = sc.today()

        self.progbook = None # This will contain an AtomicaSpreadsheet when the user loads one
        self.settings = ProjectSettings() # Global settings

        # Load project data, if available
        if framework and databook_path:
            # TODO: Consider compatibility checks for framework/databook.
            self.load_databook(databook_path=databook_path, do_run=do_run)
        elif databook_path:
            logger.warning('Project was constructed without a Framework - databook spreadsheet is being saved to project, but data is not being loaded')
            self.databook = AtomicaSpreadsheet(databook_path) # Just load the spreadsheet in so that it isn't lost
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
    def create_databook(self, databook_path=None, num_pops=1, num_transfers=0, num_interpops=0,data_start=2000.0, data_end=2020.0, data_dt=1.0):
        """ Generate an empty data-input Excel spreadsheet corresponding to the framework of this project. """
        if databook_path is None:
            databook_path = "./databook_" + self.name + ".xlsx"
        data = ProjectData.new(self.framework, np.arange(data_start,data_end+data_dt,data_dt), pops=num_pops, transfers=num_transfers)
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
        if isinstance(databook_path,string_types):
            full_path = sc.makefilepath(filename=databook_path, default=self.name, ext='xlsx')
            databook_spreadsheet = AtomicaSpreadsheet(full_path)
        else:
            databook_spreadsheet = databook_path

        self.data = ProjectData.from_spreadsheet(databook_spreadsheet,self.framework)
        self.data.validate(self.framework) # Make sure the data is suitable for use in the Project (as opposed to just manipulating the databook)
        self.databook = sc.dcp(databook_spreadsheet) # Actually a shallow copy is fine here because AtomicaSpreadsheet contains no mutable properties
        self.modified = sc.today()
        self.settings.update_time_vector(start=self.data.start_year)  # Align sim start year with data start year.

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

    def make_progbook(self, progbook_path=None, progs=None, blh_effects=False):
        ''' Make a programs databook'''

        # Check imports
        if progs is None:
            errormsg = 'Please specify programs for making a program book.'
            raise AtomicaException(errormsg)

        ## Get filepath
        full_path = sc.makefilepath(filename=progbook_path, default=self.name, ext='xlsx')

        ## Get other inputs
        F = self.framework
        comps = []
        for _,spec in F.comps.iterrows():
            if spec['is source']=='y' or spec['is sink']=='y' or spec['is junction']=='y':
                continue
            else:
                comps.append(spec.name)

        # TODO: Think about whether the following makes sense.
        parlist = [] 
        for _,spec in F.pars.iterrows():
            if spec['is impact']=='y':
                parlist.append((spec.name,spec['display name']))
        pars = sc.odict(parlist)


        make_progbook(full_path, pops=self.pop_labels, comps=comps, progs=progs, pars=pars, data_start=None, data_end=None, blh_effects=blh_effects)
        


    def load_progbook(self, progbook_path=None, make_default_progset=True, blh_effects=False):
        ''' Load a programs databook'''
        
        ## Load spreadsheet and update metadata
        if isinstance(progbook_path,string_types):
            full_path = sc.makefilepath(filename=progbook_path, default=self.name, ext='xlsx')
            progbook_spreadsheet = AtomicaSpreadsheet(full_path)
        else:
            progbook_spreadsheet = progbook_path

        progdata = load_progbook(progbook_spreadsheet, blh_effects=blh_effects)
        self.progbook = sc.dcp(progbook_spreadsheet)

        # Check if the populations match - if not, raise an error, if so, add the data
        if set(progdata['pops']) != set(self.pop_labels):
            errormsg = 'The populations in the programs databook are not the same as those that were loaded from the epi databook: "%s" vs "%s"' % (progdata['pops'], set(self.pop_labels))
            raise AtomicaException(errormsg)
        self.progdata = progdata

        self.modified = sc.today()

        if make_default_progset: self.make_progset(name="default")
        

    def make_progset(self, progdata=None, name="default", verbose=False):
        '''Make a progset from program spreadsheet data'''
        
        if verbose: print('Making ProgramSet')
        progset = ProgramSet(name=name)
        if verbose: print('Making program data')
        progset.make(progdata=progdata, project=self)
        if verbose: print('Updating program sets')
        self.progsets.append(progset)
        if verbose: print('Done with make_progset().')

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
        
    def make_scenario(self, name="default", which=None, instructions=None, json=None):
        if json is not None:
            if which=='budget':
                scenario = BudgetScenario(**json)
            else:
                raise Exception('Parameter scenarios from JSON not implemented')
        else:
            if which=='parameter':
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
#
#    def restorelinks(self):
#        ''' Loop over all objects that have links back to the project and restore them '''
#        for item in self.parsets.values()+self.progsets.values()+self.scens.values()+self.optims.values()+self.results.values():
#            if hasattr(item, 'projectref'):
#                item.projectref = Link(self)
#        return None
#

    def parset(self, key=None, verbose=2):
        ''' Shortcut for getting the latest parset '''
        if key is None: key = -1
        try:    return self.parsets[key]
        except: return sc.printv('Warning, parset "%s" not found!' %key, 1, verbose) # Returns None

    def progset(self, key=None, verbose=2):
        ''' Shortcut for getting the latest progset '''
        if key is None: key = -1
        try:    return self.progsets[key]
        except: return sc.printv('Warning, progset "%s" not found!' %key, 1, verbose) # Returns None

    def scen(self, key=None, verbose=2):
        ''' Shortcut for getting the latest scenario '''
        if key is None: key = -1
        try:    return self.scens[key]
        except: return sc.printv('Warning, scenario "%s" not found!' %key, 1, verbose) # Returns None

    def optim(self, key=None, verbose=2):
        ''' Shortcut for getting the latest optim '''
        if key is None: key = -1
        try:    return self.optims[key]
        except: return sc.printv('Warning, optim "%s" not found!' %key, 1, verbose) # Returns None

    def result(self, key=None, verbose=2):
        ''' Shortcut for getting the latest result '''
        if key is None: key = -1
        try:    return self.results[key]
        except: return sc.printv('Warning, results "%s" not found!' %key, 1, verbose) # Returns None



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
        if parset is None: parset = -1
        parset = self.parsets[parset]
        if adjustables is None:
            adjustables = list(self.framework.pars.index[self.framework.pars['can calibrate']=='y'])
            adjustables += list(self.framework.comps.index[self.framework.comps['can calibrate']=='y'])
            adjustables += list(self.framework.characs.index[self.framework.characs['can calibrate']=='y'])
        if measurables is None:
            measurables = list(self.framework.comps.index)
            measurables += list(self.framework.characs.index)
        for index, adjustable in enumerate(adjustables):
            if isinstance(adjustable, string_types):  # Assume that a parameter name was passed in if not a tuple.
                adjustables[index] = (adjustable, None, default_min_scale, default_max_scale)
        for index, measurable in enumerate(measurables):
            if isinstance(measurable, string_types):  # Assume that a parameter name was passed in if not a tuple.
                measurables[index] = (measurable, None, default_weight, default_metric)
        new_parset = perform_autofit(project=self, parset=parset,
                                     pars_to_adjust=adjustables, output_quantities=measurables, max_time=max_time)
        new_parset.name = new_name  # The new parset is a calibrated copy of the old, so change id.
        if save_to_project:
            self.parsets.append(new_parset)

        return new_parset

    def run_scenario(self, scenario, parset, progset=None, progset_instructions=None,
                     store_results=True):
        """ Run a scenario. """
        parset = parset if isinstance(parset,ParameterSet) else self.parsets[parset]
        if progset:
            progset = progset if isinstance(progset, ProgramSet) else self.progsets[progset]

        scenario = scenario if isinstance(scenario,Scenario) else self.scens[scenario]
        scenario_parset = scenario.get_parset(parset, self.settings)
        scenario_progset, progset_instructions = scenario.get_progset(progset, self.settings, progset_instructions)

        result = self.run_sim(parset=scenario_parset, progset=scenario_progset, progset_instructions=progset_instructions,
                            store_results=store_results, result_type="scenario", result_name=scenario.name)

        scenario.result_uid = result.uid
        return result
    
    def run_scenarios(self):
        results = []
        for scenario in self.scens.values():
            if scenario.active:
                result = scenario.run(project=self)
                results.append(result)
        return results

    def run_optimization(self, optimname=None, maxtime=None, maxiters=None):
        '''Run an optimization'''
        optim_ins = self.optim(optimname)
        optim = optim_ins.make(project=self)
        if maxtime is not None: optim.maxtime = maxtime
        if maxiters is not None: optim.maxiters = maxiters
        parset = self.parset(optim.parsetname)
        progset = self.progset(optim.progsetname)
        progset_instructions = ProgramInstructions(alloc=None, start_year=optim_ins.json['start_year'])
        original_end = self.settings.sim_end
        self.settings.sim_end = optim_ins.json['end_year']
        optimized_instructions = optimize(self, optim, parset, progset, progset_instructions)
        optimized_result   = self.run_sim(parset=parset,           progset=progset,           progset_instructions=optimized_instructions,                                       result_name="Optimized")
        unoptimized_result = self.run_sim(parset=optim.parsetname, progset=optim.progsetname, progset_instructions=ProgramInstructions(start_year=optim_ins.json['start_year']), result_name="Baseline")
        self.settings.sim_end = original_end
        results = [unoptimized_result, optimized_result]
        return results

    def save(self, filepath):
        """ Save the current project to a relevant object file. """
        filepath = sc.makefilepath(filename=filepath, ext='prj',sanitize=True)  # Enforce file extension.
        sc.saveobj(filepath, self)
        return None

    @staticmethod
    def load(filepath):
        """ Convenience class method for loading a project in the absence of an instance. """
        P = sc.loadobj(filepath)
        assert isinstance(P,Project)
        return P

    def demo_scenarios(self, dorun=False, doadd=True):
        json1 = sc.odict()
        json1['name']        ='Default budget'
        json1['parsetname']  = -1
        json1['progsetname'] = -1
        json1['start_year']  = 2020
        json1['alloc']       = self.progset(json1['progsetname']).get_budgets(year=json1['start_year'])
        json1['active']      = True

        json2 = sc.dcp(json1)
        json2['name']        ='Doubled budget'
        json2['alloc'][:]    *= 2.0
        json2['active']      = True

        json3 = sc.dcp(json1)
        json3['name']        ='Zero budget'
        json3['alloc'][:]    *= 0.0
        json3['active']      = True

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
    
    def demo_optimization(self, dorun=False):
        ''' WARNING, only works for TB '''
        json = sc.odict()
        json['name']              = 'Default optimization'
        json['parset_name']       = -1
        json['progset_name']      = -1
        json['start_year']        = 2018
        json['end_year']          = 2035
        json['budget_factor']     = 2.5
        json['objective_weights'] = {'finalstage':1,'conversion':0} # These are cascade-specific
        json['maxtime']           = 30 # WARNING, default!
        json['prog_spending']     = sc.odict()
        for prog_name in self.progset().programs.keys():
            json['prog_spending'][prog_name] = [0,None]
        optim = self.make_optimization(json=json)
        if dorun:
            results = self.run_optimization(optimization=json['name'])
            return results
        else:
            return optim
            

    def demo_tb_optimization(self, dorun=False):
        ''' WARNING, only works for TB '''
        json = sc.odict()
        json['name']              = 'Default optimization'
        json['parset_name']       = -1
        json['progset_name']      = -1
        json['start_year']        = 2018
        json['end_year']          = 2035
        json['budget_factor']     = 2.5
        json['objective_weights'] = {'alive':-1,'ddis':1,'acj':1} # These are TB-specific: maximize people alive, minimize people dead due to TB. Note that ASD minimizes the objective, so 'alive' has a negative weight
        json['maxtime']           = 3600 # WARNING, default!
        json['prog_spending']     = sc.odict()
        for prog_name in self.progset().programs.keys():
            json['prog_spending'][prog_name] = [0,None]
        optim = self.make_optimization(json=json)
        if dorun:
            results = self.run_optimization(optimization=json['name'])
            return results
        else:
            return optim