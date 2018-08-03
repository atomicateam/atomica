import numpy as np
import xlrd
import sciris.core as sc

from .system import AtomicaException

#%% COMPLETELY SEPARATE CODE TO READ IN A WORKBOOK WITH PROGRAMS DATA - NEEDS TO BE MERGED WITH THE ABOVE

def getyears(sheetdata):
    ''' Get years from a worksheet'''
    years = [] # Initialize epidemiology data years
    for col in range(sheetdata.ncols):
        thiscell = sheetdata.cell_value(1,col) # 1 is the 2nd row which is where the year data should be
        if thiscell=='' and len(years)>0: #  We've gotten to the end
            lastdatacol = col # Store this column number
            break # Quit
        elif thiscell != '': # Nope, more years, keep going
            years.append(float(thiscell)) # Add this year
    
    return lastdatacol, years
   
   
def blank2newtype(thesedata, newtype=None):
    ''' Convert a blank entry to another type, e.g. nan, None or zero'''
    if newtype is None or newtype=='nan': newval = np.nan # For backward compatability
    elif newtype=='None': newval = None
    elif newtype=='zero': newval = 0
    elif sc.isnumber(newtype): newval = newtype
    else: 
        errormsg = 'Cannot convert blanks to type %s, can only convert to types [''nan'', ''None'', ''zero''] or numbers' % (type(newtype)) 
        raise AtomicaException(errormsg)
    return [newval if thisdatum=='' else thisdatum for thisdatum in thesedata ]
    

def validatedata(thesedata, sheetname, thispar, row, checkupper=False, checklower=True, checkblank=True, startcol=0):
    ''' Do basic validation on the data: at least one point entered, between 0 and 1 or just above 0 if checkupper=False '''
    
    result = sc.odict()
    result['isvalid'] = 1
    # Check that only numeric data have been entered
    for column,datum in enumerate(thesedata):
        if not sc.isnumber(datum):
            errormsg = 'Invalid entry in sheet "%s", parameter "%s":\n' % (sheetname, thispar) 
            errormsg += 'row=%i, column=%s, value="%s"\n' % (row+1, xlrd.colname(column+startcol), datum)
            errormsg += 'Be sure all entries are numeric'
            if ' ' or '\t' in datum: errormsg +=' (there seems to be a space or tab)'
            raise AtomicaException(errormsg)
    
    # Now check integrity of data itself
    validdata = np.array(thesedata)[~np.isnan(thesedata)]
    if len(validdata):
        valid = np.array([True]*len(validdata)) # By default, set everything to valid
        if checklower: valid *= np.array(validdata)>=0
        if checkupper: valid *= np.array(validdata)<=1
        if not valid.all():
            invalid = validdata[valid==False]
            errormsg = 'Invalid entry in sheet "%s", parameter "%s":\n' % (sheetname, thispar) 
            errormsg += 'row=%i, invalid="%s", values="%s"\n' % (row+1, invalid, validdata)
            errormsg += 'Be sure that all values are >=0 (and <=1 if a probability)'
            result['isvalid'] = 0
            result['errormsg'] = errormsg
    elif checkblank: # No data entered
        errormsg = 'No data or assumption entered for sheet "%s", parameter "%s", row=%i' % (sheetname, thispar, row) 
        result['isvalid'] = 0
        result['errormsg'] = errormsg
    return result


def load_progbook(spreadsheet, blh_effects=False, verbose=False):
    '''
    Loads programs book (i.e. reads its contents into the data).

    INPUTS
    - spreadsheet: An AtomicaSpreadsheet instance
    '''
    ## Basic setup
    data = sc.odict() # Create structure for holding data

    ## Read in databook 
    workbook = xlrd.open_workbook(file_contents=spreadsheet.get_file().read()) # Open workbook

    ## Load program spend information
    sheetdata = workbook.sheet_by_name('Program targeting') # Load 
    data['progs'] = sc.odict()
    data['pars'] = sc.odict()
    data['progs']['short'] = []
    data['progs']['name'] = []
    data['progs']['label'] = []
    data['progs']['target_pops'] = []
    data['progs']['target_comps'] = []
    
    colindices = []
    if verbose: print('Reading program targeting data with %s rows' % sheetdata.nrows)
    for row in range(sheetdata.nrows): 

        # Get data
        thesedata = sheetdata.row_values(row, start_colx=2) 

        # Get metadata from first row
        if row==0:
            for col in range(2,sheetdata.ncols):
                cell_val = sheetdata.cell(row, col).value
                if cell_val!='': colindices.append(col-1)

        if row==1:
#            import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
            data['pops'] = thesedata[3:colindices[1]-2]
            data['comps'] = thesedata[colindices[1]-1:]

        else:
            if thesedata[0]:
                if verbose: print('  Reading row for program: %s' % thesedata[0])
                progname = str(thesedata[0])
                data['progs']['short'].append(progname)
                data['progs']['name'].append(str(thesedata[1])) # WARNING, don't need name and short
                data['progs']['label'].append(str(thesedata[1]))
                data['progs']['target_pops'].append(thesedata[3:colindices[0]])
                data['progs']['target_comps'].append(blank2newtype(thesedata[colindices[1]-1:],0))
                data[progname] = sc.odict()
                data[progname]['name'] = str(thesedata[1])
                data[progname]['target_pops'] = thesedata[3:colindices[0]]
                data[progname]['target_comps'] = blank2newtype(thesedata[colindices[1]-1:], 0)
                data[progname]['spend'] = []
#                    data[progname]['basespend'] = []
                data[progname]['capacity'] = []
                data[progname]['unitcost'] = sc.odict()

    ## Calculate columns for which data are entered, and store the year ranges
    sheetdata = workbook.sheet_by_name('Spending data') # Load this workbook
    lastdatacol, data['years'] = getyears(sheetdata)
    assumptioncol = lastdatacol + 1 # Figure out which column the assumptions are in; the "OR" space is in between

    namemap = {'Total spend': 'spend',
#               'Base spend':'basespend',
               'Unit cost':'unitcost',
               'Capacity constraints': 'capacity'}

    validunitcosts = sc.odict()
    if verbose: print('Reading spending data with %s rows' % sheetdata.nrows)
    for row in range(sheetdata.nrows):
        sheetname = sheetdata.cell_value(row,0) # Sheet name
        progname = sheetdata.cell_value(row, 1) # Get the name of the program

        if progname != '': # The first column is blank: it's time for the data
            if verbose: print('  Reading row for program: %s' % progname)
            validunitcosts[progname] = []
            thesedata = blank2newtype(sheetdata.row_values(row, start_colx=3, end_colx=lastdatacol)) # Data starts in 3rd column, and ends lastdatacol-1
            assumptiondata = sheetdata.cell_value(row, assumptioncol)
            if assumptiondata != '': # There's an assumption entered
                # TODO: Check if it is valid to just treat an assumption as the first value of the data list.
                thesedata[0] = assumptiondata
            if sheetdata.cell_value(row, 2) in namemap.keys(): # It's a regular variable without ranges
                thisvar = namemap[sheetdata.cell_value(row, 2)]  # Get the name of the indicator
                data[progname][thisvar] = thesedata # Store data
            else:
                thisvar = namemap[sheetdata.cell_value(row, 2).split(': ')[0]]  # Get the name of the indicator
                thisestimate = sheetdata.cell_value(row, 2).split(': ')[1]
                data[progname][thisvar][thisestimate] = thesedata # Store data
#            checkblank = False if thisvar in ['basespend','capacity'] else True # Don't check optional indicators, check everything else
            checkblank = False if thisvar in ['capacity'] else True # Don't check optional indicators, check everything else
            result = validatedata(thesedata, sheetname, thisvar, row, checkblank=checkblank)
            if thisvar in namemap.keys():
                if result['isvalid']==0: raise AtomicaException(result['errormsg'])
            elif thisvar=='unitcost': # For some variables we need to compare several
                if result['isvalid']==0: validunitcosts.append(result['isvalid'])
    
    for progname in data['progs']['short']:
        if validunitcosts[progname] in [[0,0,0],[0,0,1],[0,1,0]]:
            errormsg = 'You need to enter either best+low+high, best, or low+high values for the unit costs. Values are incorrect for program %s' % (progname) 
            raise AtomicaException(errormsg)

    ## Load parameter information
    sheetdata = workbook.sheet_by_name('Program effects') # Load 
    if verbose: print('Reading program effects data with %s rows' % sheetdata.nrows)
    for row in range(sheetdata.nrows): # Even though it loops over every row, skip all except the best rows
        if sheetdata.cell_value(row, 1)!='': # Data row
            par_name = sheetdata.cell_value(row, 1) # Get the name of the parameter
            if blh_effects:
                pop_name = sheetdata.cell_value(row, 2).split(': ')[0]
                est_name = sheetdata.cell_value(row, 2).split(': ')[1]
                if est_name == 'best':
                    if verbose: print('  Reading data for row %s (%s/%s/%s): ' % (row, par_name, pop_name, est_name))
                    if par_name not in data['pars']: data['pars'][par_name] = sc.odict() # Initialize only if it doesn't exist yet
                    if pop_name not in data['pars'][par_name]: data['pars'][par_name][pop_name] = sc.odict()  # Initialize only if it doesn't exist yet
                    data['pars'][par_name][pop_name]['npi_val'] = [sheetdata.cell_value(row+i, 3) if sheetdata.cell_value(row+i, 3)!='' else np.nan for i in range(3)]
                    data['pars'][par_name][pop_name]['prog_vals'] = [blank2newtype(sheetdata.row_values(row+i, start_colx=5, end_colx=5+len(data['progs']['short'])) ) for i in range(3)]
            else:
                pop_name = sheetdata.cell_value(row, 2)
                if verbose: print('  Reading data for row %s (%s/%s/): ' % (row, par_name, pop_name))
                if par_name not in data['pars']: data['pars'][par_name] = sc.odict() # Initialize only if it doesn't exist yet
                if pop_name not in data['pars'][par_name]: data['pars'][par_name][pop_name] = sc.odict()  # Initialize only if it doesn't exist yet
                data['pars'][par_name][pop_name]['npi_val'] = [sheetdata.cell_value(row, 3) if sheetdata.cell_value(row, 3)!='' else np.nan]
                data['pars'][par_name][pop_name]['prog_vals'] = [blank2newtype(sheetdata.row_values(row, start_colx=5, end_colx=5+len(data['progs']['short'])) )]
        else:
            if verbose: print('Not reading data for row %s, row is blank' % row)
    
    if verbose: print('Done with load_progbook().')
    return data




