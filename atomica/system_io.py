#############################################################################################################################
### Imports
#############################################################################################################################

import six

if six.PY2: 
#    import cPickle as pickle
    from cStringIO import StringIO
else: 
#    import pickle
    from io import StringIO as StringIO
    basestring = str
import dill
from gzip import GzipFile
from contextlib import closing
#from numpy import ones, zeros
#from atomica.system import OptimaException
from atomica.utils import makefilepath#, odict
#from xlrd import open_workbook
#import os
import atomica as op



#############################################################################################################################
### Basic I/O functions
#############################################################################################################################

def saveobj(filename=None, obj=None, compresslevel=5, verbose=True, folder=None):
    '''
    Save an object to file -- use compression 5 by default, since more is much slower but not much smaller.
    Once saved, can be loaded with loadobj() (q.v.).

    Usage:
		myobj = ['this', 'is', 'a', 'weird', {'object':44}]
		saveobj('myfile.obj', myobj)
    '''
    fullpath = makefilepath(filename=filename, folder=folder, sanitize=True)
    with GzipFile(fullpath, 'wb', compresslevel=compresslevel) as fileobj:
        fileobj.write(dill.dumps(obj, protocol=-1))
    if verbose: print('Object saved to "%s"' % fullpath)
    return fullpath


def loadobj(filename=None, folder=None, verbose=True):
    '''
    Load a saved file.

    Usage:
    	obj = loadobj('myfile.obj')
    '''
    # Handle loading of either filename or file object
    if isinstance(filename, basestring): 
        argtype = 'filename'
        filename = makefilepath(filename=filename, folder=folder) # If it is a file, validate the folder
    else: 
        argtype = 'fileobj'
    kwargs = {'mode': 'rb', argtype: filename}
    with GzipFile(**kwargs) as fileobj:
        obj = loadpickle(fileobj)
    if verbose: print('Object loaded from "%s"' % filename)
    return obj


def dumpstr(obj):
    ''' Write data to a fake file object,then read from it -- used on the FE '''
    result = None
    with closing(StringIO()) as output:
        with GzipFile(fileobj = output, mode = 'wb') as fileobj: 
            fileobj.write(dill.dumps(obj, protocol=-1))
        output.seek(0)
        result = output.read()
    return result


def loadstr(source):
    ''' Load data from a fake file object -- also used on the FE '''
    with closing(StringIO(source)) as output:
        with GzipFile(fileobj = output, mode = 'rb') as fileobj: 
            obj = loadpickle(fileobj)
    return obj


def loadpickle(fileobj, verbose=False):
    ''' Loads a pickled object -- need to define legacy classes here since they're needed for unpickling '''
    
    # Load the file string
    filestr = fileobj.read()
    
    try: # Try just loading it
        obj = dill.loads(filestr) # Actually load it
    except: # If that fails, create legacy classes and try again
        if verbose: print('Initial loading failed, trying again with legacy classes...')
        class EmptyClass(object): pass
        op._project.Spreadsheet = EmptyClass
        op._portfolio.GAOptim = EmptyClass
        obj = dill.loads(filestr) # Actually load it with legacy classes
        del op._project.Spreadsheet
        del op._portfolio.GAOptim
    
    return obj


#def optimafolder(subfolder=None):
#    '''
#    A centralized place to get the correct paths for Optima.
#    
#    Usage:
#        folder = optimafolder() # Return code folder
#        folder = optimafolder('tests') # Returns the Optima tests folder
#    '''
#    if subfolder is None: subfolder = 'optima' # By default, use code directory
#    
#    parentfolder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
#    folder = os.path.join(parentfolder, subfolder, '') # Empty last part puts a /
#    
#    return folder
#
##############################################################################################################################
#### Functions to load the parameters and transitions
##############################################################################################################################
#
## Default filename for all the functions that read this spreadsheet
#default_filename = optimafolder('optima')+'model-inputs.xlsx' # Include the Optima folder
#
#
#def loadpartable(filename=None, folder=None):
#    '''  Function to parse the parameter definitions from the spreadsheet and return a structure that can be used to generate the parameters '''
#    sheetname = 'Model parameters'
#    fullpath = makefilepath(filename=filename, folder=folder, default=default_filename)
#    workbook = open_workbook(fullpath)
#    sheet = workbook.sheet_by_name(sheetname)
#
#    rawpars = []
#    for rownum in range(sheet.nrows-1):
#        rawpars.append({})
#        for colnum in range(sheet.ncols):
#            attr = sheet.cell_value(0,colnum)
#            rawpars[rownum][attr] = sheet.cell_value(rownum+1,colnum) if sheet.cell_value(rownum+1,colnum)!='None' else None
#            if sheet.cell_value(0,colnum) in ['limits']:
#                rawpars[rownum][attr] = eval(sheet.cell_value(rownum+1,colnum)) # Turn into actual values
#    return rawpars
#
#
#
#def loadtranstable(filename=None, folder=None, npops=None, verbose=2):
#    ''' Function to load the allowable transitions from the spreadsheet '''
#    sheetname = 'Transitions' # This will only change between Optima versions, so OK to have in body of function
#    if npops is None: npops = 1 # Use just one population if not told otherwise
#    fullpath = makefilepath(filename=filename, folder=folder, default=default_filename)
#    workbook = open_workbook(fullpath)
#    sheet = workbook.sheet_by_name(sheetname)
#    
#    if sheet.nrows != sheet.ncols:
#        errormsg = 'Transition matrix should have the same number of rows and columns (%i vs. %i)' % (sheet.nrows, sheet.ncols)
#        raise OptimaException(errormsg)
#    nstates = sheet.nrows-1 # First row is header
#
#    fromto = []
#    transmatrix = zeros((nstates,nstates,npops))
#    for rownum in range(nstates): # Loop over each health state: the from state
#        fromto.append([]) # Append two lists: the to state and the probability
#        for colnum in range(nstates): # ...and again
#            if sheet.cell_value(rownum+1,colnum+1):
#                fromto[rownum].append(colnum) # Append the to states
#                transmatrix[rownum,colnum,:] = ones(npops) # Append the probabilities
#    
#    return fromto, transmatrix
#
#
#
#def loaddatapars(filename=None, folder=None, verbose=2):
#    ''' Function to parse the data parameter definitions '''
#    inputsheets = ['Data inputs', 'Data constants']
#    fullpath = makefilepath(filename=filename, folder=folder, default=default_filename)
#    workbook = open_workbook(fullpath)
#    
#    pardefinitions = odict()
#    for inputsheet in inputsheets:
#        sheet = workbook.sheet_by_name(inputsheet)
#        rawpars = []
#        for rownum in range(sheet.nrows-1):
#            rawpars.append({})
#            for colnum in range(sheet.ncols):
#                attr = str(sheet.cell_value(0,colnum))
#                cellval = sheet.cell_value(rownum+1,colnum)
#                if cellval=='None': cellval = None
#                if type(cellval)==unicode: cellval = str(cellval)
#                rawpars[rownum][attr] = cellval
#        pardefinitions[inputsheet] = rawpars
#    
#    sheets = odict() # Lists of parameters in each sheet
#    sheettypes = odict() # The type of each sheet -- e.g. time parameters or matrices
#    checkupper = odict() # Whether or not the upper limit of the parameter should be checked
#    sheetcontent = odict()
#    for par in pardefinitions['Data inputs']:
#        if par['sheet'] not in sheets.keys(): # Create new list if sheet not encountered yet
#            sheets[par['sheet']] = [] # Simple structure for storing a list of parameter names, used in loadspreadsheet
#            sheetcontent[par['sheet']] = [] # Complex structure for storing all information, used in makespreadsheet
#        sheets[par['sheet']].append(par['short']) # All-important: append the parameter name
#        sheetcontent[par['sheet']].append(par) # Append entire dictionary
#        sheettypes[par['sheet']] = par['type'] # Figure out why kind of sheet this is
#        checkupper[par['short']] = True if par['rowformat'] in ['decimal', 'percentage'] else False # Whether or not to check the upper limit
#    
#    # Handle constants separately
#    sheets['Constants'] = []
#    for par in pardefinitions['Data constants']:
#        sheets['Constants'].append(par['short'])
#    sheettypes['Constants'] = 'constant' # Hard-code this
#    
#    # Store useful derivative information
#    pardefinitions['sheets'] = sheets
#    pardefinitions['sheetcontent'] = sheetcontent
#    pardefinitions['sheettypes'] = sheettypes
#    pardefinitions['checkupper'] = checkupper
#    
#    return pardefinitions