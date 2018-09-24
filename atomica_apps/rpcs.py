'''
Atomica remote procedure calls (RPCs)
    
Last update: 2018sep23
'''

###############################################################
### Imports
##############################################################

import os
import socket
import psutil
import numpy as np
import pylab as pl
import mpld3
import sciris as sc
import scirisweb as sw
import atomica.ui as au
from matplotlib.legend import Legend
pl.rc('font', size=14)

# Globals
RPC_dict = {} # Dictionary to hold all of the registered RPCs in this module.
RPC = sw.RPCwrapper(RPC_dict) # RPC registration decorator factory created using call to make_RPC().
datastore = None # Populated by find_datastore(), which has to be called before any of the other functions


###############################################################
### Helper functions
###############################################################

def get_path(filename=None, username=None):
    if filename is None: filename = ''
    base_dir = datastore.tempfolder
    user_id = str(get_user(username).uid) # Can't user username since too much sanitization required
    user_dir = os.path.join(base_dir, user_id)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    fullpath = os.path.join(user_dir, sc.sanitizefilename(filename)) # Generate the full file name with path.
    return fullpath


@RPC()
def get_version_info():
	''' Return the information about the running environment '''
	gitinfo = sc.gitinfo(__file__)
	version_info = {
	       'version':   au.version,
	       'date':      au.versiondate,
	       'gitbranch': gitinfo['branch'],
	       'githash':   gitinfo['hash'],
	       'gitdate':   gitinfo['date'],
            'server':    socket.gethostname(),
            'cpu':       '%0.1f%%' % psutil.cpu_percent(),
	}
	return version_info
      

def get_user(username=None):
    ''' Ensure it's a valid user -- which for Atomica means has lists for projects and frameworks '''
    user = datastore.loaduser(username)
    dosave = False
    if not hasattr(user, 'projects'):
        user.projects = []
        dosave = True
    if not hasattr(user, 'frameworks'):
        user.frameworks = []
        dosave = True
    if dosave:
        datastore.saveuser(user)
    return user


def find_datastore(config):
    '''
    Ensure the datastore is loaded -- note, must be called externally since config 
    is required as an input argument.
    '''
    global datastore
    if datastore is None:
        datastore = sw.get_datastore(config=config)
    return datastore # So can be used externally


def CursorPosition():
    ''' Add the cursor position plugin to all plots '''
    plugin = mpld3.plugins.MousePosition(fontsize=12, fmt='.4r')
    return plugin


def LineLabels(line=None, label=None):
    ''' Add the line label plugin to line plots '''
    plugin = mpld3.plugins.LineLabelTooltip(line, label=label)
    return plugin


def to_float(raw, blank_ok=False, die=False):
    ''' Convert something to a number. WARNING, I'm sure this already exists!! '''
    try:
        if sc.isstring(raw):
            raw = raw.replace(',','') # Remove commas, if present
            raw = raw.replace('$','') # Remove dollars, if present
        output = float(raw)
    except Exception as E:
        errormsg = 'NUMBER WARNING, number conversion on "%s" failed, returning None: %s' % (raw, str(E))
        if raw not in [None, ''] and not blank_ok: 
            if die: raise Exception(errormsg)
            else:   print(errormsg)
        output = None
    return output


def from_number(raw, sf=3, die=False):
    ''' Convert something to a reasonable FE representation '''
    if not sc.isnumber(raw):
        output = str(raw)
        errormsg = 'NUMBER WARNING, cannot convert %s from a number since it is of type %s' % (output, type(raw))
        if die: raise Exception(errormsg)
        else:   print(errormsg)
    try:
        output = sc.sigfig(raw, sigfigs=sf, sep=True, keepints=True)
    except Exception as E:
        output = str(raw)
        errormsg = 'NUMBER WARNING, number conversion on "%s" failed, returning raw: %s' % (output, str(E))
        if die: raise Exception(errormsg)
        else:   print(errormsg)
    return output




##################################################################################
### Datastore functions
##################################################################################
    
def load_project(project_key, die=None):
    output = datastore.loadblob(project_key, objtype='project', die=die)
    return output

def load_framework(framework_key, die=None):
    output = datastore.loadblob(framework_key, objtype='framework', die=die)
    return output

def load_result(result_key, die=False):
    output = datastore.loadblob(result_key, objtype='result', die=die)
    return output

def save_project(project, die=None): # NB, only for saving an existing project
    project.modified = sc.now()
    output = datastore.saveblob(obj=project, objtype='project', die=die, forcetype=True)
    return output

def save_framework(framework, die=None): # NB, only for saving an existing project
    framework.modified = sc.now()
    output = datastore.saveblob(obj=framework, objtype='framework', die=die, forcetype=True)
    return output

def save_result(result, key=None, die=None):
    output = datastore.saveblob(obj=result, objtype='result', key=key, die=die, forcetype=True)
    return output


def save_new_project(proj, username=None):
    '''
    If we're creating a new project, we need to do some operations on it to
    make sure it's valid for the webapp.
    ''' 
    # Preliminaries
    new_project = sc.dcp(proj) # Copy the project, only save what we want...
    new_project.uid = sc.uuid()
    
    # Get unique name
    user = get_user(username)
    current_project_names = []
    for project_key in user.projects:
        proj = load_project(project_key)
        current_project_names.append(proj.name)
    new_project_name = sc.uniquename(new_project.name, namelist=current_project_names)
    new_project.name = new_project_name
    
    # Ensure it's a valid webapp project
    if not hasattr(new_project, 'webapp'):
        new_project.webapp = sc.prettyobj()
        new_project.webapp.username = username
        new_project.webapp.tasks = []
    
    # Save all the things
    key = save_project(new_project)
    user.projects.append(key)
    datastore.saveuser(user)
    return key,new_project


def save_new_framework(framework, username=None):
    '''
    If we're creating a new framework, we need to do some operations on it to
    make sure it's valid for the webapp.
    ''' 
    # Preliminaries
    new_framework = sc.dcp(framework) # Copy the project, only save what we want...
    new_framework.uid = sc.uuid()
    
    # Get unique name
    user = get_user(username)
    current_framework_names = []
    for framework_key in user.frameworks:
        proj = load_framework(framework_key)
        current_framework_names.append(proj.name)
    new_framework_name = sc.uniquename(new_framework.name, namelist=current_framework_names)
    new_framework.name = new_framework_name
    
    # Ensure it's a valid webapp framework -- store username
    if not hasattr(new_framework, 'webapp'):
        new_framework.webapp = sc.prettyobj()
        new_framework.webapp.username = username
    
    # Save all the things
    key = save_framework(new_framework)
    user.frameworks.append(key)
    datastore.saveuser(user)
    return key,new_framework


@RPC() # Not usually called directly
def del_project(project_key, die=None):
    key = datastore.getkey(key=project_key, objtype='project', forcetype=False)
    project = load_project(key)
    user = get_user(project.webapp.username)
    output = datastore.delete(key)
    if not output:
        print('Warning: could not delete project %s, not found' % project_key)
    if key in user.projects:
        user.projects.remove(key)
    else:
        print('Warning: deleting project %s (%s), but not found in user "%s" projects' % (project.name, key, user.username))
    datastore.saveuser(user)
    return output


@RPC() # Not usually called directly
def del_framework(framework_key, die=None):
    key = datastore.getkey(key=framework_key, objtype='framework', forcetype=False)
    framework = load_framework(key)
    user = get_user(framework.webapp.username)
    output = datastore.delete(key)
    if not output:
        print('Warning: could not delete framework %s, not found' % framework_key)
    if key in user.frameworks:
        user.frameworks.remove(key)
    else:
        print('Warning: deleting framework %s (%s), but not found in user "%s" frameworks' % (framework.name, key, user.username))
    datastore.saveuser(user)
    return output

@RPC()
def del_result(result_key, project_key, die=None):
    key = datastore.getkey(key=result_key, objtype='result', forcetype=False)
    output = datastore.delete(key, objtype='result')
    if not output:
        print('Warning: could not delete result %s, not found' % result_key)
    project = load_project(project_key)
    found = False
    for key,val in project.results.items():
        if result_key in [key, val]: # Could be either, depending on results caching
            project.results.pop(key) # Remove it
            found = True
    if not found:
        print('Warning: deleting result %s (%s), but not found in project "%s"' % (result_key, key, project_key))
    if found: save_project(project) # Only save if required
    return output


@RPC()
def delete_projects(project_keys):
    ''' Delete one or more projects '''
    project_keys = sc.promotetolist(project_keys)
    for project_key in project_keys:
        del_project(project_key)
    return None


@RPC()
def delete_frameworks(framework_keys):
    ''' Delete one or more frameworks '''
    framework_keys = sc.promotetolist(framework_keys)
    for framework_key in framework_keys:
        del_framework(framework_key)
    return None



##################################################################################
### Project RPCs
##################################################################################

@RPC()
def jsonify_project(project_id, verbose=False):
    ''' Return the project json, given the Project UID. ''' 
    proj = load_project(project_id) # Load the project record matching the UID of the project passed in.
    try:    
        framework_name = proj.framework.name
    except: 
        print('Could not load framework name for project')
        framework_name = 'N/A'
    try:
        n_pops = len(proj.data.pops)
        pop_pairs = [[key, val['label']] for key, val in proj.data.pops.items()]  # Pull out population keys and names
    except: 
        print('Could not load populations for project')
        n_pops = 'N/A'
        pop_pairs = []
    json = {
        'project': {
                'id':           str(proj.uid),
                'name':         proj.name,
                'username':     proj.webapp.username,
                'creationTime': sc.getdate(proj.created),
                'updatedTime':  sc.getdate(proj.modified),
                'hasData':      proj.data is not None,
                'hasPrograms':  len(proj.progsets)>0,
                'n_pops':       n_pops,
                'sim_start':    proj.settings.sim_start,
                'sim_end':      proj.settings.sim_end,
                'data_start':   proj.data.start_year if proj.data else None,
                'data_end':     proj.data.end_year if proj.data else None,
                'framework':    framework_name,
                'pops':         pop_pairs,
                'n_results':    len(proj.results),
                'n_tasks':      len(proj.webapp.tasks)
            }
    }
    if verbose: sc.pp(json)
    return json
    

@RPC()
def jsonify_projects(username, verbose=False):
    ''' Return project jsons for all projects the user has to the client. ''' 
    output = {'projects':[]}
    user = get_user(username)
    for project_key in user.projects:
        json = jsonify_project(project_key)
        output['projects'].append(json)
    if verbose: sc.pp(output)
    return output


@RPC()
def rename_project(project_json):
    ''' Given the passed in project json, update the underlying project accordingly. ''' 
    proj = load_project(project_json['project']['id']) # Load the project corresponding with this json.
    proj.name = project_json['project']['name'] # Use the json to set the actual project.
    save_project(proj) # Save the changed project to the DataStore.
    return None


@RPC()
def get_demo_project_options():
    '''
    Return the available demo frameworks
    '''
    options = au.default_project(show_options=True).values()
    return options


@RPC()
def add_demo_project(username, project_name=None, tool=None):
    '''
    Add a demo project
    '''
    if tool == 'tb':
        if project_name is None: project_name = 'Demo project'
        proj = au.demo(which='tb', do_run=False, do_plot=False, sim_dt=0.5)  # Create the project, loading in the desired spreadsheets.
    else:
        if project_name is None: project_name = 'default'
        proj = au.demo(which=project_name, do_run=False, do_plot=False)  # Create the project, loading in the desired spreadsheets.
    proj.name = project_name
    key,proj = save_new_project(proj, username) # Save the new project in the DataStore.
    print('Added demo project %s/%s' % (username, proj.name))
    return {'projectID': str(proj.uid)} # Return the new project UID in the return message.


@RPC(call_type='download')
def create_new_project(username, framework_id, proj_name, num_pops, num_progs, data_start, data_end, tool=None):
    '''
    Create a new project.
    '''
    if tool == 'tb': sim_dt = 0.5
    else:            sim_dt = None
    if tool is None or tool == 'cascade': # Optionally select by tool rather than frame
        frame = load_framework(framework_id, die=True) # Get the Framework object for the framework to be copied.
    elif tool == 'tb': # Or get a pre-existing one by the tool name
        frame = au.demo(kind='framework', which='tb')

    if tool == 'tb': args = {"num_pops":int(num_pops), "data_start":int(data_start), "data_end":int(data_end), "num_transfers":1}
    else:            args = {"num_pops":int(num_pops), "data_start":int(data_start), "data_end":int(data_end)}
    proj = au.Project(framework=frame, name=proj_name, sim_dt=sim_dt) # Create the project, loading in the desired spreadsheets.
    print(">> create_new_project %s" % (proj.name))
    file_name = '%s.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, username=username) # Generate the full file name with path.
    data = proj.create_databook(databook_path=full_file_name, **args) # Return the databook
    proj.databook = data.to_spreadsheet()
    save_new_project(proj, username) # Save the new project in the DataStore.
    print(">> download_databook %s" % (full_file_name))
    return full_file_name # Return the filename


@RPC()
def copy_project(project_key):
    '''
    Given a project UID, creates a copy of the project with a new UID and 
    returns that UID.
    '''
    proj = load_project(project_key, die=True) # Get the Project object for the project to be copied.
    new_project = sc.dcp(proj) # Make a copy of the project loaded in to work with.
    print(">> copy_project %s" % (new_project.name))  # Display the call information.
    key,new_project = save_new_project(new_project, proj.webapp.username) # Save a DataStore projects record for the copy project.
    copy_project_id = new_project.uid # Remember the new project UID (created in save_project_as_new()).
    return { 'projectID': copy_project_id } # Return the UID for the new projects record.



##################################################################################
### Project upload/download RPCs
##################################################################################

@RPC(call_type='upload')
def upload_project(prj_filename, username):
    '''
    Given a .prj file name and a user UID, create a new project from the file 
    with a new UID and return the new UID.
    '''
    print(">> create_project_from_prj_file '%s'" % prj_filename) # Display the call information.
    try: # Try to open the .prj file, and return an error message if this fails.
        proj = sc.loadobj(prj_filename)
    except Exception:
        return { 'error': 'BadFileFormatError' }
    key,proj = save_new_project(proj, username) # Save the new project in the DataStore.
    return {'projectID': str(proj.uid)} # Return the new project UID in the return message.


@RPC(call_type='download')   
def download_project(project_id):
    '''
    For the passed in project UID, get the Project on the server, save it in a 
    file, minus results, and pass the full path of this file back.
    '''
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    file_name = '%s.prj' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, proj.webapp.username) # Generate the full file name with path.
    sc.saveobj(full_file_name, proj) # Write the object to a Gzip string pickle file.
    print(">> download_project %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download')
def download_projects(project_keys, username):
    '''
    Given a list of project UIDs, make a .zip file containing all of these 
    projects as .prj files, and return the full path to this file.
    '''
    basedir = get_path('', username) # Use the downloads directory to put the file in.
    project_paths = []
    for project_key in project_keys:
        proj = load_project(project_key)
        project_path = proj.save(folder=basedir)
        project_paths.append(project_path)
    zip_fname = 'Projects %s.zip' % sc.getdate() # Make the zip file name and the full server file path version of the same..
    server_zip_fname = get_path(zip_fname, username)
    server_zip_fname = sc.savezip(server_zip_fname, project_paths)
    print(">> download_projects %s" % (server_zip_fname)) # Display the call information.
    return server_zip_fname # Return the server file name.


@RPC(call_type='download')   
def download_framework_from_project(project_id):
    ''' Download the framework Excel file from a project '''
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    file_name = '%s_framework.xlsx' % proj.name
    full_file_name = get_path(file_name, username=proj.webapp.username) # Generate the full file name with path.
    proj.framework.save(full_file_name)
    print(">> download_framework %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download')   
def download_databook(project_id):
    ''' Download databook '''
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    file_name = '%s_databook.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, username=proj.webapp.username) # Generate the full file name with path.
    proj.databook.save(full_file_name)
    print(">> download_databook %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download')   
def download_progbook(project_id):
    ''' Download program book '''
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    file_name = '%s_program_book.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, username=proj.webapp.username) # Generate the full file name with path.
    proj.progbook.save(full_file_name)
    print(">> download_progbook %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.
  
    
@RPC(call_type='download')   
def create_progbook(project_id, num_progs):
    ''' Create program book '''
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    file_name = '%s_program_book.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, username=proj.webapp.username) # Generate the full file name with path.
    proj.make_progbook(progbook_path=full_file_name, progs=int(num_progs))
    print(">> download_progbook %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.    


@RPC(call_type='upload')
def upload_databook(databook_filename, project_id):
    ''' Upload a databook to a project. '''
    print(">> upload_databook '%s'" % databook_filename)
    proj = load_project(project_id, die=True)
    proj.load_databook(databook_path=databook_filename) 
    save_project(proj) # Save the new project in the DataStore.
    return { 'projectID': str(proj.uid) } # Return the new project UID in the return message.


@RPC(call_type='upload')
def upload_progbook(progbook_filename, project_id):
    ''' Upload a program book to a project. '''
    print(">> upload_progbook '%s'" % progbook_filename)
    proj = load_project(project_id, die=True)
    proj.load_progbook(progbook_path=progbook_filename) 
    save_project(proj)
    return { 'projectID': str(proj.uid) }



##################################################################################
### Framework RPCs
##################################################################################

@RPC()
def jsonify_framework(framework_id, verbose=False):
    ''' Return the framework json, given the framework UID. ''' 
    frame = load_framework(framework_id) # Load the framework record matching the UID of the framework passed in.
    json = {
        'framework': {
            'id':           str(frame.uid),
            'name':         frame.name,
            'username':     frame.webapp.username,
            'creationTime': frame.created,
            'updatedTime':  frame.modified,
        }
    }
    if verbose: sc.pp(json)
    return json
    

@RPC()
def jsonify_frameworks(username, verbose=False):
    ''' Return framework jsons for all frameworks the user has to the client. ''' 
    output = {'frameworks':[]}
    user = get_user(username)
    for framework_key in user.frameworks:
        json = jsonify_framework(framework_key)
        output['frameworks'].append(json)
    if verbose: sc.pp(output)
    return output


@RPC()
def get_framework_options():
    ''' Return the available demo frameworks '''
    options = au.default_framework(show_options=True).values()
    return options


@RPC()
def add_demo_framework(username, framework_name):
    ''' Add a demo framework '''
    frame = au.demo(kind='framework', which=framework_name)  # Create the framework, loading in the desired spreadsheets.
    save_new_framework(frame, username) # Save the new framework in the DataStore.
    print(">> add_demo_framework %s" % (frame.name))  
    return {'frameworkID': str(frame.uid) } # Return the new framework UID in the return message.


@RPC()
def rename_framework(framework_json):
    ''' Given the passed in framework summary, update the underlying framework accordingly. ''' 
    frame = load_framework(framework_json['framework']['id']) # Load the framework corresponding with this summary.
    frame.name = framework_json['framework']['name']
    save_framework(frame) # Save the changed framework to the DataStore.
    return None


@RPC()    
def copy_framework(framework_id):
    ''' Given a framework UID, creates a copy of the framework with a new UID and returns that UID. '''
    frame = load_framework.frame
    new_framework = sc.dcp(frame) # Make a copy of the framework loaded in to work with.
    key,new_framework = save_new_framework(new_framework, username=new_framework.webapp.username) # Save a DataStore frameworks record for the copy framework.
    print(">> copy_framework %s" % (new_framework.name))  # Display the call information.
    return {'frameworkID': str(new_framework.uid)} # Return the UID for the new frameworks record.



@RPC(call_type='download')   
def download_framework(framework_id):
    ''' Download the framework Excel file from a project '''
    frame = load_framework(framework_id, die=True) # Load the project with the matching UID.
    file_name = '%s.xlsx' % frame.name
    full_file_name = get_path(file_name, username=frame.webapp.username) # Generate the full file name with path.
    frame.save(full_file_name)
    print(">> download_framework %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download')
def download_frameworks(framework_keys, username):
    '''
    Given a list of framework UIDs, make a .zip file containing all of these 
    frameworks as .frw files, and return the full path to this file.
    '''
    basedir = get_path('', username) # Use the downloads directory to put the file in.
    framework_paths = []
    for framework_key in framework_keys:
        frame = load_framework(framework_key)
        framework_path = frame.save(folder=basedir)
        framework_paths.append(framework_path)
    zip_fname = 'Frameworks %s.zip' % sc.getdate() # Make the zip file name and the full server file path version of the same..
    server_zip_fname = get_path(zip_fname, username)
    server_zip_fname = sc.savezip(server_zip_fname, framework_paths)
    print(">> download_frameworks %s" % (server_zip_fname)) # Display the call information.
    return server_zip_fname # Return the server file name.


@RPC(call_type='download')
def download_new_framework(advanced=False):
    ''' Create a new framework. '''
    if advanced: filename = 'framework_template_advanced.xlsx'
    else:        filename = 'framework_template.xlsx'
    filepath = au.atomica_path('atomica')+filename
    print(">> download_framework %s" % (filepath))
    return filepath # Return the filename


@RPC(call_type='upload')
def upload_frameworkbook(databook_filename, framework_id):
    ''' Upload a databook to a framework. '''
    print(">> upload_frameworkbook '%s'" % databook_filename)
    frame = load_framework(framework_id, die=True)
    frame.read_from_file(filepath=databook_filename, overwrite=True) # Reset the framework name to a new framework name that is unique.
    save_framework(frame) # Save the new framework in the DataStore.
    return {'frameworkID': str(frame.uid)}


@RPC(call_type='upload')
def upload_new_frameworkbook(filename, username):
    '''
    Given an .xlsx file name and a user UID, create a new framework from the file.
    '''
    frame = au.ProjectFramework(filename)
    if not frame.cascades:
        au.validate_cascade(frame, None)
    else:
        for cascade in frame.cascades:
            au.validate_cascade(frame, cascade)
    if frame.name is None: 
        frame.name = os.path.basename(filename) # Ensure that it's not None
        if frame.name.endswith('.xlsx'):
            frame.name = frame.name[:-5]
    save_new_framework(frame, username) # Save the new framework in the DataStore.
    print('Created new framework: %s' % frame.name)
    return { 'frameworkID': str(frame.uid) }



##################################################################################
### Calibration RPCs
##################################################################################

@RPC()
def get_y_factors(project_id, parsetname=-1, verbose=False):
    print('Getting y factors for parset %s...' % parsetname)
    print('Warning, year hard coded!')
    TEMP_YEAR = 2018 # WARNING, hard-coded!
    y_factors = []
    proj = load_project(project_id, die=True)
    parset = proj.parsets[parsetname]
    count = 0
    for par_type in ["cascade", "comps", "characs"]:
        for par in parset.pars[par_type]:
            parname = par.name
            this_par = parset.get_par(parname)
            this_spec = proj.framework.get_variable(parname)[0]
            if 'calibrate' in this_spec and this_spec['calibrate'] is not None:
                count += 1
                parlabel = this_spec['display name']
                y_factors.append({'index':count, 'parname':parname, 'parlabel':parlabel, 'meta_y_factor':this_par.meta_y_factor, 'pop_y_factors':[]}) 
                for p,popname,y_factor in this_par.y_factor.enumitems():
                    popindex = parset.pop_names.index(popname)
                    poplabel = parset.pop_labels[popindex]
                    try:    
                        interp_val = this_par.interpolate([TEMP_YEAR],popname)[0]
                        if not np.isfinite(interp_val):
                            print('NUMBER WARNING, value for %s %s is not finite' % (parlabel, poplabel))
                            interp_val = 1
                        if sc.approx(interp_val, 0):
                            interp_val = 0.0
                    except Exception as E: 
                        print('NUMBER WARNING, value for %s %s is not convertible: %s' % (parlabel, poplabel, str(E)))
                        interp_val = 1
                    dispvalue = from_number(interp_val*y_factor)
                    thisdict = {'popcount':p, 'popname':popname, 'dispvalue':dispvalue, 'origdispvalue':dispvalue, 'poplabel':poplabel}
                    y_factors[-1]['pop_y_factors'].append(thisdict)
    if verbose: sc.pp(y_factors)
    print('Returning %s y-factors for %s' % (len(y_factors), parsetname))
    return {'parlist':y_factors, 'poplabels':parset.pop_labels}


@RPC()
def set_y_factors(project_id, parsetname=-1, parlist=None, verbose=False):
    print('Setting y factors for parset %s...' % parsetname)
    print('Warning, year hard coded!')
    TEMP_YEAR = 2018 # WARNING, hard-coded!
    proj = load_project(project_id, die=True)
    parset = proj.parsets[parsetname]
    for newpar in parlist:
        parname = newpar['parname']
        this_par = parset.get_par(parname)
        this_par.meta_y_factor = to_float(newpar['meta_y_factor'])
        for newpoppar in newpar['pop_y_factors']:
            popname = newpoppar['popname']
            try:    
                interp_val = this_par.interpolate([TEMP_YEAR],popname)[0]
                if not np.isfinite(interp_val):
                    print('NUMBER WARNING, value for %s %s is not finite' % (parname, popname))
                    interp_val = 1
                if sc.approx(interp_val, 0):
                    interp_val = 0.0
            except Exception as E: 
                print('NUMBER WARNING, value for %s %s is not convertible: %s' % (parname, popname, str(E)))
                interp_val = 1
            dispvalue     = to_float(newpoppar['dispvalue'])
            origdispvalue = to_float(newpoppar['origdispvalue'])
            changed = (dispvalue != origdispvalue)
            if changed:
                print('Parameter %10s %10s UPDATED! %s -> %s' % (parname, popname, origdispvalue, dispvalue))
            else:
                print('Note: parameter %10s %10s stayed the same! %s -> %s' % (parname, popname, origdispvalue, dispvalue))
            orig_y_factor = this_par.y_factor[popname]
            if not sc.approx(origdispvalue, 0):
                y_factor_change = dispvalue/origdispvalue
                y_factor        = orig_y_factor*y_factor_change
            elif not sc.approx(interp_val, 0):
                y_factor = dispvalue/(1e-6+interp_val)
            else:
                if changed: print('NUMBER WARNING, everything is 0 for %s %s: %s %s %s %s' % (parname, popname, origdispvalue, dispvalue, interp_val, orig_y_factor))
                y_factor = orig_y_factor
            this_par.y_factor[popname] = y_factor
    if verbose: sc.pp(parlist)
    print('Setting %s y-factors for %s' % (len(parlist), parsetname))
    print('Saving project...')
    save_project(proj)
    return None


@RPC(call_type='download')   
def reconcile(project_id, parsetname=None, progsetname=-1, year=2018, unit_cost_bounds=0.2, outcome_bounds=0.2):
    ''' Reconcile parameter set and program set '''
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    reconciled_progset, progset_comparison, parameter_comparison = au.reconcile(project=proj, parset=parsetname, progset=progsetname, reconciliation_year=year,unit_cost_bounds=unit_cost_bounds, outcome_bounds=outcome_bounds)
    file_name = '%s_reconciled_program_book.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, username=proj.webapp.username) # Generate the full file name with path.
    reconciled_progset.save(full_file_name)
    print(">> download_progbook %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


##################################################################################
### Parameter set RPCs
##################################################################################

@RPC() 
def get_parset_info(project_id):
    print('Returning parset info...')
    proj = load_project(project_id, die=True)
    parset_names = proj.parsets.keys()
    return parset_names


@RPC() 
def rename_parset(project_id, parsetname=None, new_name=None):
    print('Renaming parset from %s to %s...' % (parsetname, new_name))
    proj = load_project(project_id, die=True)
    proj.parsets.rename(parsetname, new_name)
    print('Saving project...')
    save_project(proj)
    return None


@RPC() 
def copy_parset(project_id, parsetname=None):
    print('Copying parset %s...' % parsetname)
    proj = load_project(project_id, die=True)
    print('Number of parsets before copy: %s' % len(proj.parsets))
    new_name = sc.uniquename(parsetname, namelist=proj.parsets.keys())
    print('Old name: %s; new name: %s' % (parsetname, new_name))
    proj.parsets[new_name] = sc.dcp(proj.parsets[parsetname])
    print('Number of parsets after copy: %s' % len(proj.parsets))
    print('Saving project...')
    save_project(proj)
    return new_name


@RPC() 
def delete_parset(project_id, parsetname=None):
    print('Deleting parset %s...' % parsetname)
    proj = load_project(project_id, die=True)
    print('Number of parsets before delete: %s' % len(proj.parsets))
    if len(proj.parsets)>1:
        proj.parsets.pop(parsetname)
    else:
        raise Exception('Cannot delete last parameter set')
    print('Number of parsets after delete: %s' % len(proj.parsets))
    print('Saving project...')
    save_project(proj)
    return None


@RPC(call_type='download')   
def download_parset(project_id, parsetname=None):
    '''
    For the passed in project UID, get the Project on the server, save it in a 
    file, minus results, and pass the full path of this file back.
    '''
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    parset = proj.parsets[parsetname]
    file_name = '%s - %s.par' % (proj.name, parsetname) # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name, username=proj.webapp.username) # Generate the full file name with path.
    sc.saveobj(full_file_name, parset) # Write the object to a Gzip string pickle file.
    print(">> download_parset %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.
    
    
@RPC(call_type='upload')   
def upload_parset(parset_filename, project_id):
    '''
    For the passed in project UID, get the Project on the server, save it in a 
    file, minus results, and pass the full path of this file back.
    '''
    proj = load_project(project_id, die=True) # Load the project with the matching UID.
    parset = sc.loadobj(parset_filename)
    parsetname = sc.uniquename(parset.name, namelist=proj.parsets.keys())
    parset.name = parsetname # Reset the name
    proj.parsets[parsetname] = parset
    save_project(proj) # Save the new project in the DataStore.
    return parsetname # Return the new project UID in the return message.


##################################################################################
### Program set RPCs
##################################################################################


@RPC() 
def get_progset_info(project_id):
    print('Returning progset info...')
    proj = load_project(project_id, die=True)
    progset_names = proj.progsets.keys()
    return progset_names


@RPC() 
def rename_progset(project_id, progsetname=None, new_name=None):
    print('Renaming progset from %s to %s...' % (progsetname, new_name))
    proj = load_project(project_id, die=True)
    proj.progsets.rename(progsetname, new_name)
    print('Saving project...')
    save_project(proj)
    return None


@RPC() 
def copy_progset(project_id, progsetname=None):
    print('Copying progset %s...' % progsetname)
    proj = load_project(project_id, die=True)
    print('Number of progsets before copy: %s' % len(proj.progsets))
    new_name = sc.uniquename(progsetname, namelist=proj.progsets.keys())
    print('Old name: %s; new name: %s' % (progsetname, new_name))
    proj.progsets[new_name] = sc.dcp(proj.progsets[progsetname])
    print('Number of progsets after copy: %s' % len(proj.progsets))
    print('Saving project...')
    save_project(proj)
    return None


@RPC() 
def delete_progset(project_id, progsetname=None):
    print('Deleting progset %s...' % progsetname)
    proj = load_project(project_id, die=True)
    print('Number of progsets before delete: %s' % len(proj.progsets))
    if len(proj.progsets)>1:
        proj.progsets.pop(progsetname)
    else:
        raise Exception('Cannot delete last program set')
    print('Number of progsets after delete: %s' % len(proj.progsets))
    print('Saving project...')
    save_project(proj)
    return None


##################################################################################
### Plotting RPCs
##################################################################################


def supported_plots_func(framework):
    '''
    Return a dict of supported plots extracted from the framework.
        Input:  framework :        a ProjectFramework instance
        Output: {name:quantities}: a dict with all of the plot quantities in the framework keyed by name
    '''
    if 'plots' not in framework.sheets:
        return sc.odict()
    else:
        df = framework.sheets['plots'][0]
        plots = sc.odict()
        for name,output in zip(df['name'], df['quantities']):
            plots[name] = au.evaluate_plot_string(output)
        return plots


@RPC()    
def get_supported_plots(project_id, only_keys=False):
    proj = load_project(project_id, die=True)
    supported_plots = supported_plots_func(proj.framework)
    if only_keys:
        plot_names = supported_plots.keys()
        vals = np.ones(len(plot_names))
        output = []
        for plot_name,val in zip(plot_names,vals):
            this = {'plot_name':plot_name, 'active':val}
            output.append(this)
        return output
    else:
        return supported_plots


def savefigs(allfigs, username, die=False):
    filepath = sc.savefigs(allfigs, filetype='singlepdf', filename='Figures.pdf', folder=get_path('', username=username))
    return filepath


@RPC(call_type='download')
def download_graphs(username):
    file_name = 'Figures.pdf' # Create a filename containing the framework name followed by a .frw suffix.
    full_file_name = get_path(file_name, username=username) # Generate the full file name with path.
    return full_file_name


def get_atomica_plots(proj, results=None, plot_names=None, plot_options=None, pops='all', outputs=None, do_plot_data=None, replace_nans=True, stacked=False, xlims=None, figsize=None, calibration=False):
    results = sc.promotetolist(results)
    supported_plots = supported_plots_func(proj.framework)
    if plot_names is None: 
        if plot_options is not None:
            plot_names = []
            for item in plot_options:
                if item['active']: plot_names.append(item['plot_name'])
        else:
            plot_names = supported_plots.keys()
    plot_names = sc.promotetolist(plot_names)
    if outputs is None:
        outputs = [{plot_name:supported_plots[plot_name]} for plot_name in plot_names]
    allfigs = []
    alllegends = []
    allfigjsons = []
    alllegendjsons = []
    data = proj.data if do_plot_data is True else None # Plot data unless asked not to
    for output in outputs:
        try:
            plotdata = au.PlotData(results, outputs=output.values()[0], project=proj, pops=pops)
            nans_replaced = 0
            for series in plotdata.series:
                if replace_nans and any(np.isnan(series.vals)):
                    nan_inds = sc.findinds(np.isnan(series.vals))
                    for nan_ind in nan_inds:
                        if nan_ind>0: # Skip the first point
                            series.vals[nan_ind] = series.vals[nan_ind-1]
                            nans_replaced += 1
            if nans_replaced: print('Warning: %s nans were replaced' % nans_replaced)

            if calibration:
               if stacked: figs,legends = au.plot_series(plotdata, axis='pops', plot_type='stacked', legend_mode='separate')
               else:       figs,legends = au.plot_series(plotdata, axis='pops', data=proj.data, legend_mode='separate') # Only plot data if not stacked
            else:
               if stacked: figs,legends = au.plot_series(plotdata, axis='pops', data=data, plot_type='stacked', legend_mode='separate')
               else:       figs,legends = au.plot_series(plotdata, axis='results', data=data, legend_mode='separate')
            for fig,legend in zip(figs, legends):
                allfigjsons.append(customize_fig(fig=fig, output=output, plotdata=plotdata, xlims=xlims, figsize=figsize))
                alllegendjsons.append(customize_fig(fig=legend, output=output, plotdata=plotdata, xlims=xlims, figsize=figsize, is_legend=True))
                allfigs.append(fig)
                alllegends.append(legend)
            print('Plot %s succeeded' % (output))
        except Exception as E:
            print('WARNING: plot %s failed (%s)' % (output, repr(E)))
    output = {'graphs':allfigjsons, 'legends':alllegendjsons}
    return output, allfigs, alllegends


def make_plots(proj, results, tool=None, year=None, pops=None, cascade=None, plot_options=None, dosave=True, calibration=False, plot_budget=False, outputfigs=False):
    
    # Handle inputs
    if sc.isstring(year): year = float(year)
    if pops is None:      pops = 'all'
    results = sc.promotetolist(results)

    # Decide what to do
    if calibration and pops.lower() == 'all':
        # For calibration plot, 'all' pops means that they should all be disaggregated and visible
        # But for scenarios and optimizations, 'all' pops means aggregated over all pops
        pops = 'all'  # pops=None means aggregate all pops in get_cascade_plot, and plots all pops _without_ aggregating in calibration
    elif pops.lower() == 'all':
        pops = 'total' # make sure it's lowercase
    else:
        pop_labels = {y:x for x,y in zip(results[0].pop_names,results[0].pop_labels)}
        pops = pop_labels[pops]

    cascadeoutput,cascadefigs,cascadelegends = get_cascade_plot(proj, results, year=year, pops=pops, cascade=cascade, plot_budget=plot_budget)
    if tool == 'cascade': # For Cascade Tool
        output = cascadeoutput
        allfigs = cascadefigs
        alllegends = cascadelegends
    else: # For Optima TB
        if calibration: output, allfigs, alllegends = get_atomica_plots(proj, results=results, pops=pops, plot_options=plot_options, calibration=True, stacked=False)
        else:           output, allfigs, alllegends = get_atomica_plots(proj, results=results, pops=pops, plot_options=plot_options, calibration=False)
        output['table'] = cascadeoutput['table'] # Put this back in -- warning kludgy! -- also not used for Optima TB...
        for key in ['graphs','legends']:
            output[key] = cascadeoutput[key] + output[key]
        allfigs = cascadefigs + allfigs
        alllegends = cascadelegends + alllegends
    try:                   savefigs(allfigs, username=proj.webapp.username) # WARNING, dosave ignored fornow
    except Exception as E: print('Could not save figures: %s' % str(E))
    if outputfigs: return output, allfigs, alllegends
    else:          return output


def customize_fig(fig=None, output=None, plotdata=None, xlims=None, figsize=None, is_legend=False, is_epi=True):
    if is_legend:
        pass # Put legend customizations here
    else:
        ax = fig.get_axes()[0]
        ax.set_facecolor('none')
        if is_epi: 
            if figsize is None: figsize = (5,3)
            fig.set_size_inches(figsize)
            ax.set_position([0.25,0.18,0.70,0.72])
            ax.set_title(output.keys()[0]) # This is in a loop over outputs, so there should only be one output present
        y_max = ax.get_ylim()[1]
        labelpad = 7
        if y_max < 1e-3: labelpad = 15
        if y_max > 1e3:  labelpad = 15
        if y_max > 1e6:  labelpad = 25
        if y_max > 1e7:  labelpad = 30
        if y_max > 1e8:  labelpad = 35
        if y_max > 1e9:  labelpad = 40
        if is_epi:
            ylabel = plotdata.series[0].units
            if ylabel == 'probability': ylabel = 'Probability'
            if ylabel == '':            ylabel = 'Proportion'
        else:
            ylabel = ax.get_ylabel()
        ax.set_ylabel(ylabel, labelpad=labelpad) # All outputs should have the same units (one output for each pop/result)
        if xlims is not None: ax.set_xlim(xlims)
        try:
            legend = fig.findobj(Legend)[0]
            if len(legend.get_texts())==1:
                legend.remove() # Can remove the legend if it only has one entry
        except:
            pass
        mpld3.plugins.connect(fig, CursorPosition())
        if is_epi:
            for l,line in enumerate(fig.axes[0].lines):
                mpld3.plugins.connect(fig, LineLabels(line, label=line.get_label()))
    graph_dict = sw.mpld3ify(fig, jsonify=False) # Convert to mpld3
    pl.close(fig)
    return graph_dict
    

#def get_program_plots(results,year,budget=True,coverage=True):
#    # Generate program related plots
#    # INPUTS
#    # - proj : Project instance
#    # - results : Result or list of Results
#    # - year : If making a budget bar plot, it will be displayed for this year
#    # - budget : True/False flag for whether to include budget bar plot
#    # - coverage : True/False flag for whether to include program coverage figures
#
#    figs = []
#    if budget:
#        d = au.PlotData.programs(results, quantity='spending')
#        d.interpolate(year)
#        budget_figs = au.plot_bars(d, stack_outputs='all', legend_mode='together', outer='times', show_all_labels=False, orientation='horizontal')
#
#        ax = budget_figs[0].axes[0]
#        ax.set_xlabel('Spending ($/year)')
#
#        # The legend is too big for the figure -- WARNING, think of a better solution
#        #        budget_figs[1].set_figheight(8.9)
#        #        budgetfigs[1].set_figwidth(8.7)
#
#        figs += budget_figs
#        print('Budget plot succeeded')
#
#    if coverage:
#        d = au.PlotData.programs(results,quantity='coverage_fraction')
#        coverage_figs = au.plot_series(d, axis='results')
#        for fig,(output_name,output_label) in zip(coverage_figs,d.outputs.items()):
#            fig.axes[0].set_title(output_label)
#            series = d[d.results.keys()[0],d.pops.keys()[0],output_name]
#            fig.axes[0].set_ylabel(series.units.title())
#        figs += coverage_figs
#        print('Coverage plots succeeded')
#
#    graphs = []
#    for fig in figs:
#        graph_dict = mpld3.fig_to_dict(fig)
#        graph_dict = sc.sanitizejson(graph_dict) # This shouldn't be necessary, but it is...
#        graphs.append(graph_dict)
#        pl.close(fig)
#    output = {'graphs':graphs}
#    return output, figs

def get_cascade_plot(proj, results=None, pops=None, year=None, cascade=None, plot_budget=False):
    
    if results is None: results = proj.results[-1]
    if year    is None: year    = proj.settings.sim_end # Needed for plot_budget
    
    figs = []
    legends = []
    figjsons = []
    legendjsons = []
    years = sc.promotetolist(year)
    for y in range(len(years)):
        years[y] = float(years[y]) # Ensure it's a float

    fig,table = au.plot_cascade(results, cascade=cascade, pops=pops, year=years, data=proj.data, show_table=False)
    figjsons.append(customize_fig(fig=fig, output=None, plotdata=None, xlims=None, figsize=None, is_epi=False))
    figs.append(fig)
    legends.append(sc.emptyfig()) # No figure, but still useful to have a plot
    
    if plot_budget:
        d = au.PlotData.programs(results, quantity='spending')
        d.interpolate(year)
        budgetfigs = au.plot_bars(d, stack_outputs='all', legend_mode='together', outer='times', show_all_labels=False, orientation='vertical')
        figjsons.append(customize_fig(fig=budgetfigs[0], output=None, plotdata=None, xlims=None, figsize=None, is_epi=False))
        budgetlegends = [sc.emptyfig()]
        
        ax = budgetfigs[0].axes[0]
        ax.set_xlabel('Spending ($/year)')
        
        figs    += budgetfigs
        legends += budgetlegends
        print('Budget plot succeeded')
    
    for fig in legends: # Different enough to warrant its own block, although ugly
        try:
            ax = fig.get_axes()[0]
            ax.set_facecolor('none')
        except:
            pass
        graph_dict = sw.mpld3ify(fig, jsonify=False)
        legendjsons.append(graph_dict)
        pl.close(fig)
        
    output = {'graphs':figjsons, 'legends':legendjsons, 'table':table}
    print('Cascade plot succeeded with %s plots and %s legends and %s table' % (len(figjsons), len(legendjsons), bool(table)))
    return output, figs, legends


def get_json_cascade(results,data):
    '''
    Return all data to render cascade in FE, for multiple results
   
    INPUTS
    - results - A Result, or list of Results
    - data - A ProjectData instance (e.g. proj.data)
   
    OUTPUTS
    - dict/json containing the data required to make the cascade plot on the FE
      The dict has the following structure. Suppose we have
   
      cascade_data = get_json_cascade(results,data)
   
      Then the output of this function is (JSON equivalent of?):
   
      cascade_data['results'] - List of names of all results included (could render as checkboxes)
      cascade_data['pops'] - List of names of all pops included (could render as checkboxes)
      cascade_data['cascades'] - List of names of all cascades included (could render as dropdown)
      cascade_data['stages'][cascade_name] - List of the names of the stages in a given cascade
      cascade_data['t'][result_name] - Array of time values for the given result
      cascade_data['model'][result_name][cascade_name][pop_name][stage_name] - Array of values, same size as cascade_data['t'][result_name] (this contains the values that end up in the bar)
      cascade_data['data_t'] - Array of time values for the data
      cascade_data['data'][cascade_name][pop_name][stage_name] - Array of values, same size as cascade_data['data_t'] (this contains the values to be plotted as scatter points)
   
      Note - the data values entered in the databook are sparse (typically there isn't a data point at every time). The arrays all have
      the same size as cascade_data['data_t'], but contain `NaN` if the data was missing
    '''

    results = sc.promotetolist(results)

    cascade_data = sc.odict()
    cascade_data['pops'] = results[0].pop_labels
    cascade_data['results'] = [x.name for x in results]

    # Extract the cascade values
    if results[0].framework.cascades:
        cascade_data['cascades'] = list(results[0].framework.cascades.keys()) # Available cascades
        cascades = cascade_data['cascades']
    else:
        cascade_data['cascades'] = ['Default'] # Available cascades
        cascades = [None]

    cascade_data['model'] = sc.odict()
    cascade_data['t'] = sc.odict()
    cascade_data['stages'] = sc.odict()

    for result in results:
        cascade_data['model'][result.name] = sc.odict()
        for name, cascade in zip(cascade_data['cascades'],cascades):
            cascade_data['model'][result.name][name] = sc.odict()
            for pop_name, pop_label in zip(result.pop_names,result.pop_labels):
                cascade_data['model'][result.name][name][pop_label],t = au.get_cascade_vals(result,cascade=cascade,pops=pop_name)
            cascade_data['stages'][name] = list(cascade_data['model'][result.name][name][pop_label].keys())
        cascade_data['t'][result.name] = t

    # Extract the data values
    cascade_data['data'] = sc.odict()
    for name, cascade in zip(cascade_data['cascades'], cascades):
        cascade_data['data'][name] = sc.odict()
        for pop_name, pop_label in zip(results[0].pop_names, results[0].pop_labels):
            cascade_data['data'][name][pop_label],t = au.get_cascade_data(data,results[0].framework, cascade=cascade,pops=pop_name)
    cascade_data['data_t'] = t
    
    output = sc.sanitizejson(cascade_data)
    
    return output


@RPC()  
def manual_calibration(project_id, cache_id, parsetname=-1, plot_options=None, plotyear=None, pops=None, tool=None, cascade=None, dosave=True):
    print('Running "manual calibration"...')
    print(plot_options)
    proj = load_project(project_id, die=True)
    result = proj.run_sim(parset=parsetname, store_results=False)
    cache_result(proj, result, cache_id)
    output = make_plots(proj, result, tool=tool, year=plotyear, pops=pops, cascade=cascade, plot_options=plot_options, dosave=dosave, calibration=True)
    return output


@RPC()    
def automatic_calibration(project_id, cache_id, parsetname=-1, max_time=20, saveresults=True, plot_options=None, tool=None, plotyear=None, pops=None,cascade=None, dosave=True):
    print('Running automatic calibration for parset %s...' % parsetname)
    proj = load_project(project_id, die=True)
    proj.calibrate(parset=parsetname, max_time=float(max_time)) # WARNING, add kwargs!
    result = proj.run_sim(parset=parsetname, store_results=False)
    cache_result(proj, result, cache_id)
    output = make_plots(proj, result, tool=tool, year=plotyear, pops=pops, cascade=cascade, plot_options=plot_options, dosave=dosave, calibration=True)
    return output



##################################################################################
### Scenario RPCs
##################################################################################

def py_to_js_scen(py_scen, project=None):
    ''' Convert a Python to JSON representation of a scenario. The Python scenario might be a dictionary or an object. '''
    js_scen = {}
    attrs = ['name', 'active', 'parsetname', 'progsetname', 'alloc_year']
    for attr in attrs:
        if isinstance(py_scen, dict):
            js_scen[attr] = py_scen[attr] # Copy the attributes directly
        else:
            js_scen[attr] = getattr(py_scen, attr) # Copy the attributes into a dictionary
            
    js_scen['alloc'] = []
    if isinstance(py_scen, dict): alloc = py_scen['alloc']
    else:                         alloc = py_scen.alloc
    for prog_name,budget in alloc.items():
        prog_label = project.progset().programs[prog_name].label
        if sc.isiterable(budget):
            if len(budget)>1:
                raise Exception('Budget should only have a single element in it, not %s' % len(budget))
            else:
                budget = budget[0] # If it's not a scalar, pull out the first element -- WARNING, KLUDGY
        budgetstr = format(int(round(float(budget))), ',')
        js_scen['alloc'].append([prog_name,budgetstr, prog_label])
    return js_scen


def js_to_py_scen(js_scen):
    ''' Convert a Python to JSON representation of a scenario '''
    py_scen = sc.odict()
    attrs = ['name', 'active', 'parsetname', 'progsetname']
    for attr in attrs:
        py_scen[attr] = js_scen[attr] # Copy the attributes into a dictionary
    py_scen['alloc_year'] = float(js_scen['alloc_year']) # Convert to number
    py_scen['start_year'] = py_scen['alloc_year'] # Normally, the start year will be set by the set_scen_info() RPC but this is a fallback to ensure the scenario is still usable even if that step is omitted
    py_scen['alloc'] = sc.odict()
    for item in js_scen['alloc']:
        prog_name = item[0]
        budget = item[1]
        if sc.isstring(budget):
            try:
                budget = to_float(budget)
            except Exception as E:
                raise Exception('Could not convert budget to number: %s' % repr(E))
        if sc.isiterable(budget):
            if len(budget)>1:
                raise Exception('Budget should only have a single element in it, not %s' % len(budget))
            else:
                budget = budget[0] # If it's not a scalar, pull out the first element -- WARNING, KLUDGY
        py_scen['alloc'][prog_name] = to_float(budget)
    return py_scen
    

@RPC()
def get_scen_info(project_id, verbose=True):
    print('Getting scenario info...')
    proj = load_project(project_id, die=True)
    scenario_jsons = []
    for py_scen in proj.scens.values():
        js_scen = py_to_js_scen(py_scen, project=proj)
        scenario_jsons.append(js_scen)
    if verbose:
        print('JavaScript scenario info:')
        sc.pp(scenario_jsons)

    return scenario_jsons


@RPC()
def set_scen_info(project_id, scenario_jsons, verbose=True):
    print('Setting scenario info...')
    proj = load_project(project_id, die=True)
    proj.scens.clear()
    for j,js_scen in enumerate(scenario_jsons):
        print('Setting scenario %s of %s...' % (j+1, len(scenario_jsons)))
        py_scen = js_to_py_scen(js_scen)
        py_scen['start_year'] = proj.data.end_year # The scenario program start year is the same as the end year
        if verbose: 
            print('Python scenario info for scenario %s:' % (j+1))
            sc.pp(py_scen)
        proj.make_scenario(which='budget', json=py_scen)
    print('Saving project...')
    save_project(proj)
    return None


@RPC()    
def get_default_budget_scen(project_id):
    print('Creating default scenario...')
    proj = load_project(project_id, die=True)
    py_scen = proj.demo_scenarios(doadd=False)
    js_scen = py_to_js_scen(py_scen, project=proj)
    print('Created default JavaScript scenario:')
    sc.pp(js_scen)
    return js_scen


@RPC()    
def run_scenarios(project_id, cache_id, plot_options, saveresults=True, tool=None, plotyear=None, pops=None,cascade=None, dosave=True):
    print('Running scenarios...')
    proj = load_project(project_id, die=True)
    results = proj.run_scenarios(store_results=False)
    if len(results) < 1:  # Fail if we have no results (user didn't pick a scenario)
        return {'error': 'No scenario selected'}
    cache_result(proj, results, cache_id)
    output = make_plots(proj, results, tool=tool, year=plotyear, pops=pops, cascade=cascade, plot_options=plot_options, dosave=dosave, calibration=False, plot_budget=True)
    print('Saving project...')
    save_project(proj)
    return output




##################################################################################
### Optimization RPCs
##################################################################################


def py_to_js_optim(py_optim, project=None):
    js_optim = sc.sanitizejson(py_optim.json)
    if 'objective_labels' not in js_optim:
        js_optim['objective_labels'] = {key:key for key in js_optim['objective_weights'].keys()} # Copy keys if labels not available
    for prog_name in js_optim['prog_spending']:
        prog_label = project.progset().programs[prog_name].label
        this_prog = js_optim['prog_spending'][prog_name]
        this_prog.append(prog_label)
        js_optim['prog_spending'][prog_name] = {'min':this_prog[0], 'max':this_prog[1], 'label':prog_label}
    return js_optim


def js_to_py_optim(js_optim):
    json = js_optim
    for key in ['start_year', 'end_year', 'budget_factor', 'maxtime']:
        json[key] = to_float(json[key]) # Convert to a number
    for subkey in json['objective_weights'].keys():
        json['objective_weights'][subkey] = to_float(json['objective_weights'][subkey], blank_ok=True)
    for subkey in json['prog_spending'].keys():
        this = json['prog_spending'][subkey]
        json['prog_spending'][subkey] = (to_float(this['min']), to_float(this['max']))
    return json
    

@RPC()    
def get_optim_info(project_id, verbose=True):
    print('Getting optimization info...')
    proj = load_project(project_id, die=True)
    optim_jsons = []
    for py_optim in proj.optims.values():
        js_optim = py_to_js_optim(py_optim, project=proj)
        optim_jsons.append(js_optim)
    if verbose: sc.pp(optim_jsons)
    return optim_jsons


@RPC()
def get_default_optim(project_id, tool=None, optim_type=None, verbose=True):
    print('Getting default optimization...')
    proj = load_project(project_id, die=True)
    py_optim = proj.demo_optimization(tool=tool, optim_type=optim_type)
    js_optim = py_to_js_optim(py_optim, project=proj)
    if verbose: sc.pp(js_optim)
    return js_optim


@RPC()    
def set_optim_info(project_id, optim_jsons, verbose=True):
    print('Setting optimization info...')
    proj = load_project(project_id, die=True)
    proj.optims.clear()
    for j,js_optim in enumerate(optim_jsons):
        if verbose: print('Setting optimization %s of %s...' % (j+1, len(optim_jsons)))
        json = js_to_py_optim(js_optim)
        if verbose: sc.pp(json)
        proj.make_optimization(json=json)
    print('Saving project...')
    save_project(proj)   
    return None


# This is the function we should use on occasions when we can't use Celery.
@RPC()
def run_optimization(project_id, cache_id, optim_name=None, plot_options=None, maxtime=None, tool=None, plotyear=None, pops=None, cascade=None, dosave=True):
    print('Running Cascade optimization...')
    sc.printvars(locals(), ['project_id', 'optim_name', 'plot_options', 'maxtime', 'tool', 'plotyear', 'pops', 'cascade', 'dosave'], color='blue')
    proj = load_project(project_id, die=True)
        
    # Actually run the optimization and get its results (list of baseline and optimized Result objects).
    results = proj.run_optimization(optim_name, maxtime=float(maxtime), store_results=False)
    cache_result(proj, results, cache_id)
    output = make_plots(proj, results, tool=tool, year=plotyear, pops=pops, cascade=cascade, plot_options=plot_options, dosave=dosave, plot_budget=True) # Plot the results.   
    save_project(proj)
    return output



##################################################################################
### Results RPCs
##################################################################################

def cache_result(project=None, result=None, key=None, die=False, verbose=False):
    if verbose: print('Cache result inputs:\nProject:\n%s\nResult:\n%s\nKey:\n%s' % (project, result, key))
    if not sc.isstring(result):
        result_key = save_result(result, key=key)
        if result_key != key:
            errormsg = 'Warning: supplied database key had to be changed (%s -> %s)' % (key, result_key)
            if die: raise Exception(errormsg)
            else:   print(errormsg)
        project.results[key] = result_key # In most cases, these will match, e.g. project.results['result::4e6efc39-94ef'] = 'result::4e6efc39-94ef'
        save_project(project)
    return result_key


def cache_results(proj, verbose=True):
    ''' Store the results of the project in Redis '''
    for key,result in proj.results.items():
        if not sc.isstring(result):
            result_key = save_result(result)
            proj.results[key] = result_key
            if verbose: print('Cached result "%s" to "%s"' % (key, result_key))
    save_project(proj)
    return proj


def retrieve_results(proj, verbose=True):
    ''' Retrieve the results from the database back into the project '''
    for key,result_key in proj.results.items():
        if sc.isstring(result_key):
            result = load_result(result_key)
            proj.results[key] = result
            if verbose: print('Retrieved result "%s" from "%s"' % (key, result_key))
    return proj

    
@RPC() 
def plot_results(project_id, cache_id, plot_options, tool=None, plotyear=None, pops=None, cascade=None, dosave=True, plotbudget=False, calibration=False):
    print('Plotting cached results...')
    proj = load_project(project_id, die=True)
    results = load_result(cache_id) # Load the results from the cache and check if we got a result.
    if results is None:
        return { 'error': 'Failed to load plot results from cache' }
    output = make_plots(proj, results, tool=tool, year=plotyear, pops=pops, cascade=cascade, plot_options=plot_options, dosave=dosave, plot_budget=plotbudget, calibration=calibration)
    return output
    

@RPC(call_type='download')
def export_results(cache_id, username):
    print('Exporting results...')
    results = load_result(cache_id) # Load the result from the cache and check if we got a result.
    if results is None:
        return { 'error': 'Failed to load plot results from cache' }
    file_name = 'results.zip'
    full_file_name = get_path(file_name, username=username)
    au.export_results(results, full_file_name)
    print(">> export_results %s" % (full_file_name))
    return full_file_name # Return the filename  