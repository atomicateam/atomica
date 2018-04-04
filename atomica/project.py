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

from atomica.system import SystemSettings as SS, applyToAllMethods, logUsage, AtomicaException, logger
from atomica.excel import ExcelSettings as ES
from atomica.framework import ProjectFramework
from atomica.data import ProjectData
from atomica.project_settings import ProjectSettings
from atomica.parameters import ParameterSet#, makesimpars
from atomica.programs import Programset
from atomica.model import runModel
from atomica.results import Result
from atomica.workbook_export import writeWorkbook
from atomica.workbook_import import readWorkbook
from atomica._version import __version__
from sciris.core import tic, toc, odict, today, makefilepath, printv, isnumber, promotetolist, gitinfo, getdate, objrepr, Link, dcp, saveobj, uuid

from numpy.random import seed, randint

@applyToAllMethods(logUsage)
class Project(object):
    def __init__(self, name = "default", framework=None, databook=None):
        """ Initialize the project. """

        self.name = name
        self.filename = None # Never saved to file
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
        self.settings = ProjectSettings() # Global settings

        ## Load spreadsheet, if available
        if framework and databook: # Should we somehow check if these are compatible? Or should a spreadsheet somehow dominate, maybe just loading a datasheet should be enough to generate a framework?
            self.loadDatabook(filename=databook)

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
    def createDatabook(self, databook_path=None, instructions=None, databook_type=SS.DATABOOK_DEFAULT_TYPE):
        """
        Generate an empty data-input Excel spreadsheet corresponding to the framework of this project.
        An object in the form of DatabookInstructions can optionally be passed in to describe how many databook items should be templated.
        """
        if databook_path is None: databook_path = "./databook_" + self.name + ES.FILE_EXTENSION
        writeWorkbook(workbook_path=databook_path, framework=self.framework, data=self.data, instructions=instructions, workbook_type=SS.STRUCTURE_KEY_DATA)
    

    def loadDatabook(self, filename=None, folder=None, name=None, overwrite=True, dorun=True, **kwargs):
        ''' Load a data spreadsheet'''
        ## Load spreadsheet and update metadata
        fullpath = makefilepath(filename=filename, folder=folder, default=self.name, ext='xlsx')
        databookout = readWorkbook(workbook_path=fullpath, framework=self.framework, data=self.data, workbook_type=SS.STRUCTURE_KEY_DATA)

        self.databookloaddate = today() # Update date when spreadsheet was last loaded
        self.modified = today()
        
        datayears = databookout['datayears']
        self.settings.datastart = datayears[0]
        self.settings.start = datayears[0]
        self.settings.dataend = datayears[-1]

        if name is None: name = 'default'
        self.makeParset(name=name)
#        self.makeparset(name=name, overwrite=overwrite)
        if dorun:
            self.runSim()
#            self.runsum()

        return None


    def makeParset(self, name = "default"):
        """ Transform project data into a set of parameters that can be used in model simulations. """

#        if not self.data: raise AtomicaException("ERROR: No data exists for project '{0}'.".format(self.name))
        self.parsets[name] = ParameterSet(name=name)
        self.parsets[name].makePars(self.data)
        return self.parsets[name]

#    def makeparset(self, name='default', overwrite=False, dosave=True, die=False):
#        ''' Create or overwrite a parameter set '''
#        if not self.data: # TODO this is not the right check to be doing
#            raise AtomicaException('No data in project "%s"!' % self.name)
#        parset = Parameterset(name=name, project=self)
#        parset.makepars(self.data, framework=self.framework, start=self.settings.datastart, end=self.settings.dataend) # Create parameters
#
#        if dosave: # Save to the project if requested
#            if name in self.parsets and not overwrite: # and overwrite if requested
#                errormsg = 'Cannot make parset "%s" because it already exists (%s) and overwrite is off' % (name, self.parsets.keys())
#                if die: raise AtomicaException(errormsg) # Probably not a big deal, so...
#                else:   printv(errormsg, 3, verbose=self.settings.verbose) # ...don't even print it except with high verbose settings
#            else:
#                self.addparset(name=name, parset=parset, overwrite=overwrite) # Store parameters
#                self.modified = today()
#        return parset


    def makeprogset(self, name='default'):
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


    #######################################################################################################
    ### Methods to handle common tasks with structure lists
    #######################################################################################################


    def getwhat(self, item=None, what=None):
        '''
        Figure out what kind of structure list is being requested, e.g.
            structlist = getwhat('parameters')
        will return P.parset.
        '''
        if item is None and what is None: raise AtomicaException('No inputs provided')
        if what is not None: # Explicitly define the type
            if what in ['p', 'pars', 'parset', 'parameters']: structlist = self.parsets
            elif what in ['pr', 'progs', 'progset', 'progsets']: structlist = self.progsets 
            elif what in ['s', 'scen', 'scens', 'scenario', 'scenarios']: structlist = self.scens
            elif what in ['o', 'opt', 'opts', 'optim', 'optims', 'optimisation', 'optimization', 'optimisations', 'optimizations']: structlist = self.optims
            elif what in ['r', 'res', 'result', 'results']: structlist = self.results
            else: raise AtomicaException('Structure list "%s" not understood' % what)
        else: # Figure out the type based on the input
            if type(item)==Parameterset: structlist = self.parsets
            elif type(item)==Programset: structlist = self.progsets
            elif type(item)==Resultset: structlist = self.results
            else: raise AtomicaException('Structure list "%s" not understood' % str(type(item)))
        return structlist


    def checkname(self, what=None, checkexists=None, checkabsent=None, overwrite=True):
        ''' Check that a name exists if it needs to; check that a name doesn't exist if it's not supposed to '''
        if type(what)==odict: structlist=what # It's already a structlist
        else: structlist = self.getwhat(what=what)
        if isnumber(checkexists): # It's a numerical index
            try: checkexists = structlist.keys()[checkexists] # Convert from 
            except: raise AtomicaException('Index %i is out of bounds for structure list "%s" of length %i' % (checkexists, what, len(structlist)))
        if checkabsent is not None:
            if checkabsent in structlist:
                if overwrite==False:
                    raise AtomicaException('Structure list "%s" already has item named "%s"' % (what, checkabsent))
                else:
                    printv('Structure list already has item named "%s"' % (checkabsent), 3, self.settings.verbose)
                
        if checkexists is not None:
            if not checkexists in structlist:
                raise AtomicaException('Structure list has no item named "%s"' % (checkexists))
        return None


    def add(self, name=None, item=None, what=None, overwrite=True, consistentnames=True):
        ''' Add an entry to a structure list -- can be used as add('blah', obj), add(name='blah', item=obj), or add(item) '''
        if name is None:
            try: name = item.name # Try getting name from the item
            except: name = 'default' # If not, revert to default
        if item is None:
            if type(name)!=str: # Maybe an item has been supplied as the only argument
                try: 
                    item = name # It's actully an item, not a name
                    name = item.name # Try getting name from the item
                except: raise AtomicaException('Could not figure out how to add item with name "%s" and item "%s"' % (name, item))
            else: # No item has been supplied, add a default one
                if what=='parset':  
                    item = Parameterset(name=name, project=self)
                    item.makepars(self.data, verbose=self.settings.verbose) # Create parameters
                elif what=='progset': 
                    item = Programset(name=name, project=self)
#                elif what=='scen':
#                    item = Parscen(name=name)
#                elif what=='optim': 
#                    item = Optim(project=self, name=name)
                else:
                    raise AtomicaException('Unable to add item of type "%s", please supply explicitly' % what)
        structlist = self.getwhat(item=item, what=what)
        self.checkname(structlist, checkabsent=name, overwrite=overwrite)
        structlist[name] = item
        if consistentnames: structlist[name].name = name # Make sure names are consistent -- should be the case for everything except results, where keys are UIDs
#        if hasattr(structlist[name], 'projectref'): structlist[name].projectref = Link(self) # Fix project links
#        printv('Item "%s" added to "%s"' % (name, what), 3, self.settings.verbose)
        self.modified = today()
        return None


    def remove(self, what=None, name=None):
        ''' Remove an entry from a structure list by name '''
        if name is None: name = -1 # If no name is supplied, remove the last item
        structlist = self.getwhat(what=what)
        self.checkname(what, checkexists=name)
        structlist.pop(name)
#        printv('%s "%s" removed' % (what, name), 3, self.settings.verbose)
        self.modified = today()
        return None


    def copy(self, what=None, orig=None, new=None, overwrite=True):
        ''' Copy an entry in a structure list '''
        if orig is None: orig = -1
        if new  is None: new = 'new'
        structlist = self.getwhat(what=what)
        self.checkname(what, checkexists=orig, checkabsent=new, overwrite=overwrite)
        structlist[new] = dcp(structlist[orig])
        structlist[new].name = new  # Update name
        structlist[new].created = today() # Update dates
        structlist[new].modified = today() # Update dates
#        if hasattr(structlist[new], 'projectref'): structlist[new].projectref = Link(self) # Fix project links
#        printv('%s "%s" copied to "%s"' % (what, orig, new), 3, self.settings.verbose)
        self.modified = today()
        return None


    def rename(self, what=None, orig=None, new=None, overwrite=True):
        ''' Rename an entry in a structure list '''
        if orig is None: orig = -1
        if new  is None: new = 'new'
        structlist = self.getwhat(what=what)
        self.checkname(what, checkexists=orig, checkabsent=new, overwrite=overwrite)
        structlist.rename(oldkey=orig, newkey=new)
        structlist[new].name = new # Update name
#        printv('%s "%s" renamed "%s"' % (what, orig, new), 3, self.settings.verbose)
        self.modified = today()
        return None
        

    def addparset(self,   name=None, parset=None,   overwrite=True): self.add(what='parset',   name=name, item=parset,  overwrite=overwrite)
    def addprogset(self,  name=None, progset=None,  overwrite=True): self.add(what='progset',  name=name, item=progset, overwrite=overwrite)
    def addscen(self,     name=None, scen=None,     overwrite=True): self.add(what='scen',     name=name, item=scen,    overwrite=overwrite)
    def addoptim(self,    name=None, optim=None,    overwrite=True): self.add(what='optim',    name=name, item=optim,   overwrite=overwrite)

    def rmparset(self,   name=None): self.remove(what='parset',   name=name)
    def rmprogset(self,  name=None): self.remove(what='progset',  name=name)
    def rmscen(self,     name=None): self.remove(what='scen',     name=name)
    def rmoptim(self,    name=None): self.remove(what='optim',    name=name)


    def copyparset(self,  orig=None, new=None, overwrite=True): self.copy(what='parset',   orig=orig, new=new, overwrite=overwrite)
    def copyprogset(self, orig=None, new=None, overwrite=True): self.copy(what='progset',  orig=orig, new=new, overwrite=overwrite)
    def copyscen(self,    orig=None, new=None, overwrite=True): self.copy(what='scen',     orig=orig, new=new, overwrite=overwrite)
    def copyoptim(self,   orig=None, new=None, overwrite=True): self.copy(what='optim',    orig=orig, new=new, overwrite=overwrite)

    def renameparset(self,  orig=None, new=None, overwrite=True): self.rename(what='parset',   orig=orig, new=new, overwrite=overwrite)
    def renameprogset(self, orig=None, new=None, overwrite=True): self.rename(what='progset',  orig=orig, new=new, overwrite=overwrite)
    def renamescen(self,    orig=None, new=None, overwrite=True): self.rename(what='scen',     orig=orig, new=new, overwrite=overwrite)
    def renameoptim(self,   orig=None, new=None, overwrite=True): self.rename(what='optim',    orig=orig, new=new, overwrite=overwrite)

    #######################################################################################################
    ### Utilities
    #######################################################################################################

    def restorelinks(self):
        ''' Loop over all objects that have links back to the project and restore them '''
        for item in self.parsets.values()+self.progsets.values()+self.scens.values()+self.optims.values()+self.results.values():
            if hasattr(item, 'projectref'):
                item.projectref = Link(self)
        return None


    def pars(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest active set of parameters, i.e. self.parsets[-1].pars '''
        try:    return self.parsets[key].pars
        except: return printv('Warning, parameters dictionary not found!', 1, verbose) # Returns None
    
    def parset(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest active parameters set, i.e. self.parsets[-1] '''
        try:    return self.parsets[key]
        except: return printv('Warning, parameter set not found!', 1, verbose) # Returns None
    
    def programs(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest active set of programs '''
        try:    return self.progsets[key].programs
        except: return printv('Warning, programs not found!', 1, verbose) # Returns None

    def progset(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest active program set, i.e. self.progsets[-1]'''
        try:    return self.progsets[key]
        except: return printv('Warning, program set not found!', 1, verbose) # Returns None
    
    def scen(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest scenario, i.e. self.scens[-1]'''
        try:    return self.scens[key]
        except: return printv('Warning, scenario not found!', 1, verbose) # Returns None

    def optim(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest optimization, i.e. self.optims[-1]'''
        try:    return self.optims[key]
        except: return printv('Warning, optimization not found!', 1, verbose) # Returns None

    def result(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest active results, i.e. self.results[-1]'''
        try:    return self.results[key]
        except: return printv('Warning, results set not found!', 1, verbose) # Returns None


    #######################################################################################################
    ### Methods to perform major tasks
    #######################################################################################################


    def runSim(self, parset=None, parset_name='default', progset=None, progset_name=None, options=None, plot=False, debug=False, store_results=True, result_type=None, result_name=None):
        """ Run model using a selected parset and store/return results. """

        if parset is None:
            if len(self.parsets) < 1:
                raise AtomicaException("ERROR: Project '{0}' appears to have no parameter sets. Cannot run model.".format(self.name))
            else:
                try: parset = self.parsets[parset_name]
                except: raise AtomicaException("ERROR: Project '{0}' is lacking a parset named '{1}'. Cannot run model.".format(self.name, parset_name))

        if progset is None:
            try: progset = self.progsets[progset_name]
            except: logger.info("Initiating a standard run of project '{0}' (i.e. without the influence of programs).".format(self.name))
        if progset is not None:
            if options is None:
                logger.info("Program set '{0}' will be ignored while running project '{1}' due to no options specified.".format(progset.name, self.name))
                progset = None

        tm = tic()

#        # results = runModel(settings = self.settings, parset = parset)
        results = runModel(settings=self.settings, framework=self.framework, parset=parset, progset=progset, options=options)

        toc(tm, label="running '{0}' model".format(self.name))

#        if plot:
#            tp = tic()
#            self.plotResults(results=results)
#            toc(tp, label='plotting %s' % self.name)

        if store_results:
            if result_name is None:
                result_name = "parset_" + parset.name
                if not progset is None:
                    result_name = result_name + "_progset_" + progset.name
                if result_type is not None:
                    result_name = result_type + "_" + result_name
                k = 1
                while k > 0:
                    result_name_attempt = result_name + "_" + str(k)
                    k = k + 1
                    if result_name_attempt not in self.results:
                        result_name = result_name_attempt
                        k = 0
            self.results[result_name] = results

        return results

#    def runsim(self, name=None, pars=None, simpars=None, start=None, end=None, dt=None, tvec=None, 
#               budget=None, coverage=None, budgetyears=None, data=None, n=1, sample=None, tosample=None, randseed=None,
#               addresult=True, overwrite=True, keepraw=False, doround=True, die=True, debug=False, verbose=None, 
#               parsetname=None, progsetname=None, resultname=None, label=None, **kwargs):
#        ''' 
#        This function runs a single simulation, or multiple simulations if n>1. This is the
#        core function for actually running the model!!!!!!
#        
#        Version: 2018jan13
#        '''
#        if dt      is None: dt      = self.settings.dt # Specify the timestep
#        if verbose is None: verbose = self.settings.verbose
#        
#        # Extract parameters either from a parset stored in project or from input
#        if parsetname is None:
#            if name is not None: parsetname = name # This is mostly for backwards compatibility -- allow the first argument to set the parset
#            else:                parsetname = -1 # Set default name
#            if pars is None:
#                pars = self.parsets[parsetname].pars
#                resultname = 'parset-'+self.parsets[parsetname].name
#            else:
#                printv('Model was given a pardict and a parsetname, defaulting to use pardict input', 3, self.settings.verbose)
#                if resultname is None: resultname = 'pardict'
#        else:
#            if pars is not None:
#                printv('Model was given a pardict and a parsetname, defaulting to use pardict input', 3, self.settings.verbose)
#                if resultname is None: resultname = 'pardict'
#            else:
#                if resultname is None: resultname = 'parset-'+self.parsets[parsetname].name
#                pars = self.parsets[parsetname].pars
#        if label is None: # Define the label
#            if name is None: label = '%s' % parsetname
#            else:            label = name
#            
#        # Get the parameters sorted
#        if simpars is None: # Optionally run with a precreated simpars instead
#            simparslist = [] # Needs to be a list
#            if n>1 and sample is None: sample = 'new' # No point drawing more than one sample unless you're going to use uncertainty
#            if randseed is not None: seed(randseed) # Reset the random seed, if specified
#            if start is None: 
#                try:    start = self.parsets[parsetname].start # Try to get start from parameter set, but don't worry if it doesn't exist
#                except: start = self.settings.start # Else, specify the start year from the project
#                try:    end   = self.parsets[parsetname].end # Ditto
#                except: end   = self.settings.end # Ditto
#            for i in range(n):
#                maxint = 2**31-1 # See https://en.wikipedia.org/wiki/2147483647_(number)
#                sampleseed = randint(0,maxint) 
#                simparslist.append(makesimpars(pars, start=start, end=end, dt=dt, tvec=tvec, settings=self.settings, name=parsetname, sample=sample, tosample=tosample, randseed=sampleseed))
#        else:
#            simparslist = promotetolist(simpars)
#
##        # Run the model!
##        rawlist = []
##        for ind,simpars in enumerate(simparslist):
##            raw = model(simpars, self.settings, die=die, debug=debug, verbose=verbose, label=self.name, **kwargs) # ACTUALLY RUN THE MODEL
##            rawlist.append(raw)
##
##        # Store results if required
##        results = Resultset(name=resultname, pars=pars, parsetname=parsetname, progsetname=progsetname, raw=rawlist, simpars=simparslist, budget=budget, coverage=coverage, budgetyears=budgetyears, project=self, keepraw=keepraw, doround=doround, data=data, verbose=verbose) # Create structure for storing results
##        if addresult:
##            keyname = self.addresult(result=results, overwrite=overwrite)
##            if parsetname is not None:
##                self.parsets[parsetname].resultsref = keyname # If linked to a parset, store the results
##            self.modified = today() # Only change the modified date if the results are stored
##        
#        return simparslist #TEMP: return interpolated parameters


    def calibrate(self):
        ''' Function to perform automatic calibration '''
        pass
    
    def outcome(self):
        ''' Function to get the outcome for a particular sim and objective'''
        pass
    
    def runscenarios(self):
        '''Run the specified scenarios'''
        pass
    
    def optimize(self):
        '''Run an optimization'''
    
    
    def save(self, filename=None, folder=None, verbose=2):
        ''' Save the current project.'''
        fullpath = makefilepath(filename=filename, folder=folder, ext='prj', sanitize=True)
        self.filename = fullpath # Store file path
        saveobj(fullpath, self, verbose=verbose)
        return fullpath


    def export(self, filename=None, folder=None, datasheetpath=None, verbose=2):
        '''
        Export a script that, when run, generates this project.
        '''
        
        fullpath = makefilepath(filename=filename, folder=folder, default=self.name, ext='py', sanitize=True)
        
#        if datasheetpath is None:
#            spreadsheetpath = self.name+'.xlsx'
#            self.createDatabook(filename=spreadsheetpath, folder=folder) ## TODO: first need to make sure that data can be written back to excel
#            printv('Generated spreadsheet from project %s and saved to file %s' % (self.name, spreadsheetpath), 2, verbose)

        output = "'''\nSCRIPT TO GENERATE PROJECT %s\n" %(self.name)
        output += "Created %s\n\n\n" %(today())
        output += "THIS METHOD IS NOT FUNCTIONAL YET'''\n\n\n"

        f = open(fullpath, 'w')
        f.write( output )
        f.close()
        printv('Saved project %s to script file %s' % (self.name, fullpath), 2, verbose)
        return None

        
        