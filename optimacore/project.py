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

from optimacore.system import SystemSettings as SS
from optimacore.excel import ExcelSettings as ES

from optimacore.system import applyToAllMethods, logUsage, accepts
from optimacore.framework import ProjectFramework
from optimacore.data import ProjectData
from optimacore.project_settings import ProjectSettings
from optimacore.parameters import Parameterset
from optimacore.programs import Programset
from optimacore.results import Resultset
from optimacore.workbook_export import writeWorkbook
from optimacore.workbook_import import readWorkbook

from optima import odict, dcp, today, OptimaException, makefilepath, printv, isnumber ## TODO: remove temporary imports from HIV

@applyToAllMethods(logUsage)
class Project(object):
    def __init__(self, name = "default", framework=None, databook=None):
        """ Initialize the project. """

        if isinstance(name, str): self.name = name
        self.framework = framework if framework else ProjectFramework()
        self.data = ProjectData()
        
        ## Define the structure sets
        self.parsets  = odict()
        self.progsets = odict()
        self.scens    = odict()
        self.optims   = odict()
        self.results  = odict()

        ## Define metadata
        self.created = today()
        self.modified = today()
        self.databookdate = 'Databook never loaded'
        self.settings = ProjectSettings() # Global settings

        ## Load spreadsheet, if available
        if framework and databook: # Should we somehow check if these are compatible? Or should a spreadsheet somehow dominate, maybe just loading a datasheet should be enough to generate a framework?
            self.loadDatabook(filename=databook)

        return None


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
    

    def loadDatabook(self, filename=None, folder=None, name=None, overwrite=True, **kwargs):
        ''' Load a data spreadsheet'''
        ## Load spreadsheet and update metadata
        fullpath = makefilepath(filename=filename, folder=folder, default=self.name, ext='xlsx')
        databookout = readWorkbook(workbook_path=fullpath, framework=self.framework, data=self.data, workbook_type=SS.STRUCTURE_KEY_DATA)

        self.databookdate = today() # Update date when spreadsheet was last loaded
        self.modified = today()
        
        self.datayears = databookout['datayears']
        self.datastart = self.datayears[0]
        self.dataend = self.datayears[-1]

        if name is None: name = 'default'
        self.makeparset(name=name, overwrite=overwrite)

        return None


    def makeparset(self, name='default', overwrite=False, dosave=True, die=False):
        ''' Create or overwrite a parameter set '''
        if not self.data: # TODO this is not the right check to be doing
            raise OptimaException('No data in project "%s"!' % self.name)
        parset = Parameterset(name=name, project=self)
#        import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
        parset.makepars(self.data, framework=self.framework, start=self.datastart, end=self.dataend) # Create parameters

        if dosave: # Save to the project if requested
            if name in self.parsets and not overwrite: # and overwrite if requested
                errormsg = 'Cannot make parset "%s" because it already exists (%s) and overwrite is off' % (name, self.parsets.keys())
                if die: raise OptimaException(errormsg) # Probably not a big deal, so...
                else:   printv(errormsg, 3, verbose=self.settings.verbose) # ...don't even print it except with high verbose settings
            else:
                self.addparset(name=name, parset=parset, overwrite=overwrite) # Store parameters
                self.modified = today()
        return parset


    #######################################################################################################
    ### Methods to handle common tasks with structure lists
    #######################################################################################################


    def getwhat(self, item=None, what=None):
        '''
        Figure out what kind of structure list is being requested, e.g.
            structlist = getwhat('parameters')
        will return P.parset.
        '''
        if item is None and what is None: raise OptimaException('No inputs provided')
        if what is not None: # Explicitly define the type
            if what in ['p', 'pars', 'parset', 'parameters']: structlist = self.parsets
            elif what in ['pr', 'progs', 'progset', 'progsets']: structlist = self.progsets 
            elif what in ['s', 'scen', 'scens', 'scenario', 'scenarios']: structlist = self.scens
            elif what in ['o', 'opt', 'opts', 'optim', 'optims', 'optimisation', 'optimization', 'optimisations', 'optimizations']: structlist = self.optims
            elif what in ['r', 'res', 'result', 'results']: structlist = self.results
            else: raise OptimaException('Structure list "%s" not understood' % what)
        else: # Figure out the type based on the input
            if type(item)==Parameterset: structlist = self.parsets
            elif type(item)==Programset: structlist = self.progsets
            elif type(item)==Resultset: structlist = self.results
            else: raise OptimaException('Structure list "%s" not understood' % str(type(item)))
        return structlist


    def checkname(self, what=None, checkexists=None, checkabsent=None, overwrite=True):
        ''' Check that a name exists if it needs to; check that a name doesn't exist if it's not supposed to '''
        if type(what)==odict: structlist=what # It's already a structlist
        else: structlist = self.getwhat(what=what)
        if isnumber(checkexists): # It's a numerical index
            try: checkexists = structlist.keys()[checkexists] # Convert from 
            except: raise OptimaException('Index %i is out of bounds for structure list "%s" of length %i' % (checkexists, what, len(structlist)))
        if checkabsent is not None:
            if checkabsent in structlist:
                if overwrite==False:
                    raise OptimaException('Structure list "%s" already has item named "%s"' % (what, checkabsent))
                else:
                    printv('Structure list already has item named "%s"' % (checkabsent), 3, self.settings.verbose)
                
        if checkexists is not None:
            if not checkexists in structlist:
                raise OptimaException('Structure list has no item named "%s"' % (checkexists))
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
                except: raise OptimaException('Could not figure out how to add item with name "%s" and item "%s"' % (name, item))
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
                    raise OptimaException('Unable to add item of type "%s", please supply explicitly' % what)
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
    ### Utilities
    #######################################################################################################

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



        
        