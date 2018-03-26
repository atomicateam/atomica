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
from optimacore.workbook_export import writeWorkbook
from optimacore.workbook_import import readWorkbook

from optima import odict, today, OptimaException, makefilepath, printv ## TODO: remove temporary imports from HIV

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

        
        