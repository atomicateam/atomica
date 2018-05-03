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

from atomica.system import SystemSettings as SS, apply_to_all_methods, log_usage, AtomicaException, logger
from atomica.structure_settings import FrameworkSettings as FS, DatabookSettings as DS
from atomica.excel import ExcelSettings as ES
from atomica.framework import ProjectFramework
from atomica.data import ProjectData
from atomica.project_settings import ProjectSettings
from atomica.parameters import ParameterSet
<<<<<<< HEAD
from atomica.programs import Program, ProgramSet
from atomica.calibration import performAutofit
=======
#from atomica.programs import Programset
from atomica.calibration import perform_autofit
>>>>>>> fusion
from atomica.scenarios import ParameterScenario
from atomica.model import runModel
from atomica.results import Result
from atomica.workbook_export import writeWorkbook, makeInstructions
from atomica.workbook_import import readWorkbook, loadprogramspreadsheet
from atomica._version import __version__
from sciris.core import tic, toc, odict, today, makefilepath, printv, isnumber, promotetolist, gitinfo, getdate, objrepr, Link, dcp, saveobj, loadobj, uuid

#from numpy.random import seed, randint

@apply_to_all_methods(log_usage)
class Project(object):
    def __init__(self, name="default", framework=None, databook_path=None, do_run=True):
        """ Initialize the project. """

        self.name = name
#        self.filename = None # Never saved to file
        self.framework = framework if framework else ProjectFramework()
        self.data = ProjectData() # TEMPORARY

        ## Define the structure sets
        self.parsets  = odict()
        self.progsets = odict()
        self.scens    = odict()
        self.optims   = odict()
        self.results  = odict()

        ## Define metadata
        self.uid = uuid()
        self.version = __version__
        self.gitinfo = gitinfo()
        self.created = today()
        self.modified = today()
        self.databookloaddate = 'Databook never loaded'
        self.programdatabookloaddate = 'Programs databook never loaded'
        self.settings = ProjectSettings() # Global settings

        ## Load spreadsheet, if available
        if framework and databook_path: # Should we somehow check if these are compatible? Or should a spreadsheet somehow dominate, maybe just loading a datasheet should be enough to generate a framework?
            self.loadDatabook(databook_path=databook_path, do_run=do_run)

        return None


    def __repr__(self):
        ''' Print out useful information when called '''
        output = objrepr(self)
        output += '      Project name: %s\n'    % self.name
        output += '    Framework name: %s\n'    % self.framework.name
        output += '\n'
        output += '    Parameter sets: %i\n'    % len(self.parsets)
        output += '      Program sets: %i\n'    % len(self.progsets)
        output += '         Scenarios: %i\n'    % len(self.scens)
        output += '     Optimizations: %i\n'    % len(self.optims)
        output += '      Results sets: %i\n'    % len(self.results)
        output += '\n'
        output += '   Atomica version: %s\n'    % self.version
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += '  Datasheet loaded: %s\n'    % getdate(self.databookloaddate)
        output += '        Git branch: %s\n'    % self.gitinfo['branch']
        output += '          Git hash: %s\n'    % self.gitinfo['hash']
        output += '               UID: %s\n'    % self.uid
        output += '============================================================\n'
        return output
    

    #######################################################################################################
    ### Methods for I/O and spreadsheet loading
    #######################################################################################################
    def createDatabook(self, databook_path=None, num_pops=None, num_progs=None, data_start=None, data_end=None, data_dt=None):
        """ Generate an empty data-input Excel spreadsheet corresponding to the framework of this project. """
        if databook_path is None: databook_path = "./databook_" + self.name + ES.FILE_EXTENSION
        databook_instructions, _ = makeInstructions(framework=self.framework, workbook_type=SS.STRUCTURE_KEY_DATA)
        if not num_pops is None: databook_instructions.updateNumberOfItems(DS.KEY_POPULATION, num_pops)     # Set the number of populations.
        if not num_progs is None: databook_instructions.updateNumberOfItems(DS.KEY_PROGRAM, num_progs)      # Set the number of programs.
        databook_instructions.updateTimeVector(data_start=data_start, data_end=data_end, data_dt=data_dt)
        writeWorkbook(workbook_path=databook_path, framework=self.framework, data=self.data, instructions=databook_instructions, workbook_type=SS.STRUCTURE_KEY_DATA)
    

    def loadDatabook(self, databook_path=None, make_default_parset=True, do_run=True):
        """ Load a data spreadsheet. """
        ## Load spreadsheet and update metadata
        full_path = makefilepath(filename=databook_path, default=self.name, ext='xlsx')
        metadata = readWorkbook(workbook_path=full_path, framework=self.framework, data=self.data, workbook_type=SS.STRUCTURE_KEY_DATA)

        self.databookloaddate = today() # Update date when spreadsheet was last loaded
        self.modified = today()
        
        # Put the population keys somewhere easier to access- TEMP, TODO, fix
        self.popkeys = []
        self.popnames = []
        for k,v in self.data.specs['pop'].iteritems():
            self.popkeys.append(k)
            self.popnames.append(v['label'])
        
        if metadata is not None and "data_start" in metadata:
            self.settings.updateTimeVector(start = metadata["data_start"])  # Align sim start year with data start year.

        if make_default_parset: self.makeParset(name="default")
        if do_run: 
            if not make_default_parset: logger.warning("Project has been requested to run a simulation after loading databook, despite no request to "
                                                       "create a default parameter set.")
            self.runSim(parset="default")

        return None


    def makeParset(self, name="default", overwrite=False):
        """ Transform project data into a set of parameters that can be used in model simulations. """
        
        # TODO: Develop some flag or check for data 'emptiness'.
#        if not self.data: raise AtomicaException("ERROR: No data exists for project '{0}'.".format(self.name))
        self.set_parset(parset_key = name, parset_object = ParameterSet(name=name), overwrite=overwrite)
        self.parsets[name].makePars(self.data)
        return self.parsets[name]


    def load_progbook(self, databook_path=None, make_default_progset=True):
        ''' Load a programs databook'''
        
        ## Load spreadsheet and update metadata
        full_path = makefilepath(filename=databook_path, default=self.name, ext='xlsx')
        progdata = loadprogramspreadsheet(filename=full_path)
        
        # Check if the populations match - if not, raise an error, if so, add the data
        if set(progdata['pops']) != set(self.popnames):
            errormsg = 'The populations in the programs databook are not the same as those that were loaded from the epi databook: "%s" vs "%s"' % (progdata['pops'], set(self.popnames))
            raise AtomicaException(errormsg)
        self.progdata = progdata

        self.programdatabookloaddate = today() # Update date when spreadsheet was last loaded
        self.modified = today()

        if make_default_progset: self.make_progset(name="default")
        

    def make_progset(self, progdata=None, name="default",add=True):
        '''Make a progset from program spreadsheet data'''
        
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
        
        for np in range(nprogs):
            pkey = progdata['progs']['short'][np]
            data = {k: progdata[pkey][k] for k in ('cost', 'coverage')}
            data['t'] = progdata['years']
            p = Program(short=pkey,
                        name=progdata['progs']['short'][np],
                        targetpops=[val for i,val in enumerate(progdata['pops']) if progdata['progs']['targetpops'][i]],
                        unitcost=progdata[pkey]['unitcost'],
                        capacity=progdata[pkey]['capacity'],
                        data=data
                        )
            programs.append(p)
            
        progset = ProgramSet(name=name,programs=programs)
        if add:
            self.set_progset(progset_key=name,progset_object=progset)
            return None
        else:
            return progset



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
        if save_to_project: self.set_scenario(scenario_key = name, scenario_object = scenario, overwrite=overwrite)
        return scenario
        


    #######################################################################################################
    ### Methods to handle common tasks with structure lists
    #######################################################################################################

    def set_structure(self, structure_key, structure_object, structure_list, structure_string, overwrite = False):
        """ Base method for setting elements of structure lists to a structure object, with optional overwrite validation. """
        if structure_key in structure_list:
            if not overwrite: raise AtomicaException("A {0} is already attached to a project under the key '{1}'.".format(structure_string,structure_key))
            else: logger.warning("A {0} already attached to the project with key '{1}' is being overwritten.".format(structure_string,structure_key))
        structure_list[structure_key] = structure_object

    def set_parset(self, parset_key, parset_object, overwrite = False):
        """ 'Set' method for parameter sets to prevent overwriting unless explicit. """
        self.set_structure(structure_key=parset_key, structure_object=parset_object, structure_list=self.parsets, 
                           structure_string="parameter set", overwrite=overwrite)

    def set_scenario(self, scenario_key, scenario_object, overwrite = False):
        """ 'Set' method for scenarios to prevent overwriting unless explicit. """
        self.set_structure(structure_key=scenario_key, structure_object=scenario_object, structure_list=self.scens, 
                           structure_string="scenario", overwrite=overwrite)
    
    def copy_parset(self, old_name = "default", new_name = "copy"):
        """ Deep copy an existent parameter set. """
        parset_object = dcp(self.parsets[old_name])
        parset_object.change_id(new_name = new_name)
        self.set_parset(parset_key = new_name, parset_object = parset_object)
        
    def get_structure(self, structure, structure_list, structure_string):
        """ Base method that allows structures to be retrieved via an object or string handle and, if the latter, validates for existence. """
        if structure is None:
            if len(structure_list) < 1:
                raise AtomicaException("Project '{0}' appears to have no {1}s. Cannot select a default to run process.".format(self.name,structure_string))
            else:
                try:
                    structure = structure_list["default"]
                    logger.warning("Project '{0}' has selected {1} with key 'default' to run process.".format(self.name,structure_string))
                except: 
                    structure = structure_list[0]
                    logger.warning("In the absence of a parameter set with key 'default', "
                                   "project '{0}' has selected {1} with name '{2}' to run process.".format(self.name,structure_string,structure.name))
        else:
            if isinstance(structure,str):
                if structure not in structure_list:
                    raise AtomicaException("Project '{0}' is lacking a {1} named '{2}'. Cannot run process.".format(self.name,structure_string,structure))
                structure = structure_list[structure]
        return structure
        
    def get_parset(self, parset):
        """ Allows for parsets to be retrieved from an object or string handle, the latter of which is checked against project attributes. """
        return self.get_structure(structure=parset, structure_list=self.parsets, structure_string="parameter set")
      
    def get_scenario(self, scenario):
        """ Allows for scenarios to be retrieved from an object or string handle, the latter of which is checked against project attributes. """
        return self.get_structure(structure=scenario, structure_list=self.scens, structure_string="scenario")

    def set_progset(self, progset_key, progset_object, overwrite = False):
        """ 'Set' method for parameter sets to prevent overwriting unless explicit. """
        self.set_structure(structure_key=progset_key, structure_object=progset_object, structure_list=self.progsets, 
                           structure_string="program set", overwrite=overwrite)

#    def getwhat(self, item=None, what=None):
#        '''
#        Figure out what kind of structure list is being requested, e.g.
#            structlist = getwhat('parameters')
#        will return P.parset.
#        '''
#        if item is None and what is None: raise AtomicaException('No inputs provided')
#        if what is not None: # Explicitly define the type
#            if what in ['p', 'pars', 'parset', 'parameters']: structlist = self.parsets
#            elif what in ['pr', 'progs', 'progset', 'progsets']: structlist = self.progsets 
#            elif what in ['s', 'scen', 'scens', 'scenario', 'scenarios']: structlist = self.scens
#            elif what in ['o', 'opt', 'opts', 'optim', 'optims', 'optimisation', 'optimization', 'optimisations', 'optimizations']: structlist = self.optims
#            elif what in ['r', 'res', 'result', 'results']: structlist = self.results
#            else: raise AtomicaException('Structure list "%s" not understood' % what)
#        else: # Figure out the type based on the input
#            if type(item)==Parameterset: structlist = self.parsets
#            elif type(item)==Programset: structlist = self.progsets
#            elif type(item)==Resultset: structlist = self.results
#            else: raise AtomicaException('Structure list "%s" not understood' % str(type(item)))
#        return structlist
#
#
#    def checkname(self, what=None, checkexists=None, checkabsent=None, overwrite=True):
#        ''' Check that a name exists if it needs to; check that a name doesn't exist if it's not supposed to '''
#        if type(what)==odict: structlist=what # It's already a structlist
#        else: structlist = self.getwhat(what=what)
#        if isnumber(checkexists): # It's a numerical index
#            try: checkexists = structlist.keys()[checkexists] # Convert from 
#            except: raise AtomicaException('Index %i is out of bounds for structure list "%s" of length %i' % (checkexists, what, len(structlist)))
#        if checkabsent is not None:
#            if checkabsent in structlist:
#                if overwrite==False:
#                    raise AtomicaException('Structure list "%s" already has item named "%s"' % (what, checkabsent))
#                else:
#                    printv('Structure list already has item named "%s"' % (checkabsent), 3, self.settings.verbose)
#                
#        if checkexists is not None:
#            if not checkexists in structlist:
#                raise AtomicaException('Structure list has no item named "%s"' % (checkexists))
#        return None
#
#
#    def add(self, name=None, item=None, what=None, overwrite=True, consistentnames=True):
#        ''' Add an entry to a structure list -- can be used as add('blah', obj), add(name='blah', item=obj), or add(item) '''
#        if name is None:
#            try: name = item.name # Try getting name from the item
#            except: name = 'default' # If not, revert to default
#        if item is None:
#            if type(name)!=str: # Maybe an item has been supplied as the only argument
#                try: 
#                    item = name # It's actully an item, not a name
#                    name = item.name # Try getting name from the item
#                except: raise AtomicaException('Could not figure out how to add item with name "%s" and item "%s"' % (name, item))
#            else: # No item has been supplied, add a default one
#                if what=='parset':  
#                    item = Parameterset(name=name, project=self)
#                    item.makepars(self.data, verbose=self.settings.verbose) # Create parameters
#                elif what=='progset': 
#                    item = Programset(name=name, project=self)
##                elif what=='scen':
##                    item = Parscen(name=name)
##                elif what=='optim': 
##                    item = Optim(project=self, name=name)
#                else:
#                    raise AtomicaException('Unable to add item of type "%s", please supply explicitly' % what)
#        structlist = self.getwhat(item=item, what=what)
#        self.checkname(structlist, checkabsent=name, overwrite=overwrite)
#        structlist[name] = item
#        if consistentnames: structlist[name].name = name # Make sure names are consistent -- should be the case for everything except results, where keys are UIDs
##        if hasattr(structlist[name], 'projectref'): structlist[name].projectref = Link(self) # Fix project links
##        printv('Item "%s" added to "%s"' % (name, what), 3, self.settings.verbose)
#        self.modified = today()
#        return None
#
#
#    def remove(self, what=None, name=None):
#        ''' Remove an entry from a structure list by name '''
#        if name is None: name = -1 # If no name is supplied, remove the last item
#        structlist = self.getwhat(what=what)
#        self.checkname(what, checkexists=name)
#        structlist.pop(name)
##        printv('%s "%s" removed' % (what, name), 3, self.settings.verbose)
#        self.modified = today()
#        return None
#
#
#    def copy(self, what=None, orig=None, new=None, overwrite=True):
#        ''' Copy an entry in a structure list '''
#        if orig is None: orig = -1
#        if new  is None: new = 'new'
#        structlist = self.getwhat(what=what)
#        self.checkname(what, checkexists=orig, checkabsent=new, overwrite=overwrite)
#        structlist[new] = dcp(structlist[orig])
#        structlist[new].name = new  # Update name
#        structlist[new].created = today() # Update dates
#        structlist[new].modified = today() # Update dates
##        if hasattr(structlist[new], 'projectref'): structlist[new].projectref = Link(self) # Fix project links
##        printv('%s "%s" copied to "%s"' % (what, orig, new), 3, self.settings.verbose)
#        self.modified = today()
#        return None
#
#
#    def rename(self, what=None, orig=None, new=None, overwrite=True):
#        ''' Rename an entry in a structure list '''
#        if orig is None: orig = -1
#        if new  is None: new = 'new'
#        structlist = self.getwhat(what=what)
#        self.checkname(what, checkexists=orig, checkabsent=new, overwrite=overwrite)
#        structlist.rename(oldkey=orig, newkey=new)
#        structlist[new].name = new # Update name
##        printv('%s "%s" renamed "%s"' % (what, orig, new), 3, self.settings.verbose)
#        self.modified = today()
#        return None
#        
#
#    def addparset(self,   name=None, parset=None,   overwrite=True): self.add(what='parset',   name=name, item=parset,  overwrite=overwrite)
#    def addprogset(self,  name=None, progset=None,  overwrite=True): self.add(what='progset',  name=name, item=progset, overwrite=overwrite)
#    def addscen(self,     name=None, scen=None,     overwrite=True): self.add(what='scen',     name=name, item=scen,    overwrite=overwrite)
#    def addoptim(self,    name=None, optim=None,    overwrite=True): self.add(what='optim',    name=name, item=optim,   overwrite=overwrite)
#
#    def rmparset(self,   name=None): self.remove(what='parset',   name=name)
#    def rmprogset(self,  name=None): self.remove(what='progset',  name=name)
#    def rmscen(self,     name=None): self.remove(what='scen',     name=name)
#    def rmoptim(self,    name=None): self.remove(what='optim',    name=name)
#
#
#    def copyparset(self,  orig=None, new=None, overwrite=True): self.copy(what='parset',   orig=orig, new=new, overwrite=overwrite)
#    def copyprogset(self, orig=None, new=None, overwrite=True): self.copy(what='progset',  orig=orig, new=new, overwrite=overwrite)
#    def copyscen(self,    orig=None, new=None, overwrite=True): self.copy(what='scen',     orig=orig, new=new, overwrite=overwrite)
#    def copyoptim(self,   orig=None, new=None, overwrite=True): self.copy(what='optim',    orig=orig, new=new, overwrite=overwrite)
#
#    def renameparset(self,  orig=None, new=None, overwrite=True): self.rename(what='parset',   orig=orig, new=new, overwrite=overwrite)
#    def renameprogset(self, orig=None, new=None, overwrite=True): self.rename(what='progset',  orig=orig, new=new, overwrite=overwrite)
#    def renamescen(self,    orig=None, new=None, overwrite=True): self.rename(what='scen',     orig=orig, new=new, overwrite=overwrite)
#    def renameoptim(self,   orig=None, new=None, overwrite=True): self.rename(what='optim',    orig=orig, new=new, overwrite=overwrite)
#
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
    ### Methods to perform major tasks
    #######################################################################################################


    def update_settings(self, sim_start=None, sim_end=None, sim_dt=None):
        """ Modify the project settings, e.g. the simulation time vector. """
        self.settings.updateTimeVector(start=sim_start, end=sim_end, dt=sim_dt)

    def runSim(self, parset=None, progset=None, options=None, store_results=True, result_type=None, result_name=None):
        """ Run model using a selected parset and store/return results. """
        
        parset = self.get_parset(parset=parset)

#        if progset is None:
#            try: progset = self.progsets[progset_name]
#            except: logger.info("Initiating a standard run of project '{0}' (i.e. without the influence of programs).".format(self.name))
#        if progset is not None:
#            if options is None:
#                logger.info("Program set '{0}' will be ignored while running project '{1}' due to no options specified.".format(progset.name, self.name))
#                progset = None

        if result_name is None:
            base_name = "parset_" + parset.name
            if not progset is None:
                base_name = base_name + "_progset_" + progset.name
            if result_type is not None:
                base_name = result_type + "_" + base_name

            k = 1  # consider making this 2?
            result_name = base_name
            while result_name in self.results:
                result_name = base_name + "_" + str(k)
                k += 1

        tm = tic()
        result = runModel(settings=self.settings, framework=self.framework, parset=parset, progset=progset, options=options,name=result_name)
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
        The former will instruct the autofit algorithm to vary specified parameter values for all populations between default scaling limits.
        The latter will vary specified parameters for specified populations, with 'None' denoting all pops, and within specified scaling limits.
        
        The measurables argument should be a list in the form of...
            [charac_name_1, charac_name_2]
        ...or...
            [(charac_name_1, pop_1, weight_1, "fractional")
             (charac_name_2, None, weight_2, "wape")]
        The former will instruct calculation of a 'fractional' data-simulation comparison metric summed across specified characteristics for all pops.
        The latter will calculate its metric for specified populations, with 'None' denoting all pops, and for specified weights and metric types.
        
        To calibrate a project-attached parameter set in place, provide its key as the new name argument to this method.
        Current fitting metrics are: "fractional", "meansquare", "wape"
        Note that scaling limits are absolute, not relative.
        """
        parset = self.get_parset(parset=parset)
        if adjustables is None: adjustables = self.framework.specs[FS.KEY_PARAMETER].keys()
        if measurables is None: measurables = self.framework.specs[FS.KEY_COMPARTMENT].keys() + self.framework.specs[FS.KEY_CHARACTERISTIC].keys()
        for index, adjustable in enumerate(adjustables):
            if isinstance(adjustable, str):     # Assume that a parameter name was passed in if not a tuple.
                adjustables[index] = (adjustable, None, default_min_scale, default_max_scale)
        for index, measurable in enumerate(measurables):
            if isinstance(measurable, str):     # Assume that a parameter name was passed in if not a tuple.
                measurables[index] = (measurable, None, default_weight, default_metric)
        new_parset = perform_autofit(project=self, parset=parset,
                                     pars_to_adjust=adjustables, output_quantities=measurables, max_time=max_time)
        new_parset.change_id(new_name=new_name)     # The new parset is a calibrated copy of the old, so change id.
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
        scenario_progset, scenario_options = scenario.get_progset(progset, self.settings,options)
        return self.runSim(parset=scenario_parset, progset=scenario_progset, options=scenario_options, 
                           store_results=store_results, result_type="scenario", result_name=result_name)

#    def optimize(self):
#        '''Run an optimization'''
    
    def save(self, filepath):
        """ Save the current project to a relevant object file. """
        filepath = makefilepath(filename=filepath, ext=SS.OBJECT_EXTENSION_PROJECT, sanitize=True)  # Enforce file extension.
        saveobj(filepath, self)
    
    @classmethod
    def load(cls, filepath):
        """ Convenience class method for loading a project in the absence of an instance. """
        return loadobj(filepath)


#    def export(self, filename=None, folder=None, datasheetpath=None, verbose=2):
#        '''
#        Export a script that, when run, generates this project.
#        '''
#        
#        fullpath = makefilepath(filename=filename, folder=folder, default=self.name, ext='py', sanitize=True)
#        
##        if datasheetpath is None:
##            spreadsheetpath = self.name+'.xlsx'
##            self.createDatabook(filename=spreadsheetpath, folder=folder) ## TODO: first need to make sure that data can be written back to excel
##            printv('Generated spreadsheet from project %s and saved to file %s' % (self.name, spreadsheetpath), 2, verbose)
#
#        output = "'''\nSCRIPT TO GENERATE PROJECT %s\n" %(self.name)
#        output += "Created %s\n\n\n" %(today())
#        output += "THIS METHOD IS NOT FUNCTIONAL YET'''\n\n\n"
#
#        f = open(fullpath, 'w')
#        f.write( output )
#        f.close()
#        printv('Saved project %s to script file %s' % (self.name, fullpath), 2, verbose)
#        return None

        
        