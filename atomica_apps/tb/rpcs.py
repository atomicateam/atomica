"""
rpcs.py -- code related to HealthPrior project management
    
Last update: 2018jun04 by cliffk
"""

#
# Imports
#

import os
from zipfile import ZipFile
from flask_login import current_user
import mpld3

import sciris.corelib.fileio as fileio
import sciris.weblib.user as user
import sciris.core as sc
import sciris.web as sw

import atomica.ui as au
from . import projects as prj

# Dictionary to hold all of the registered RPCs in this module.
RPC_dict = {}

# RPC registration decorator factory created using call to make_register_RPC().
register_RPC = sw.make_register_RPC(RPC_dict)

        
#
# Other functions (mostly helpers for the RPCs)
#
    

def load_project_record(project_id, raise_exception=True):
    """
    Return the project DataStore reocord, given a project UID.
    """ 
    
    # Load the matching prj.ProjectSO object from the database.
    project_record = prj.proj_collection.get_object_by_uid(project_id)

    # If we have no match, we may want to throw an exception.
    if project_record is None:
        if raise_exception:
            raise Exception('ProjectDoesNotExist(id=%s)' % project_id)
            
    # Return the Project object for the match (None if none found).
    return project_record

def load_project(project_id, raise_exception=True):
    """
    Return the Nutrition Project object, given a project UID, or None if no 
    ID match is found.
    """ 
    
    # Load the project record matching the ID passed in.
    project_record = load_project_record(project_id, 
        raise_exception=raise_exception)
    
    # If there is no match, raise an exception or return None.
    if project_record is None:
        if raise_exception:
            raise Exception('ProjectDoesNotExist(id=%s)' % project_id)
        else:
            return None
        
    # Return the found project.
    return project_record.proj

def load_project_summary_from_project_record(project_record):
    """
    Return the project summary, given the DataStore record.
    """ 
    
    # Return the built project summary.
    return project_record.get_user_front_end_repr()
  
def load_current_user_project_summaries2():
    """
    Return project summaries for all projects the user has to the client.
    """ 
    
    # Get the prj.ProjectSO entries matching the user UID.
    project_entries = prj.proj_collection.get_project_entries_by_user(current_user.get_id())
    
    # Grab a list of project summaries from the list of prj.ProjectSO objects we 
    # just got.
    return {'projects': map(load_project_summary_from_project_record, 
        project_entries)}
                
def get_unique_name(name, other_names=None):
    """
    Given a name and a list of other names, find a replacement to the name 
    that doesn't conflict with the other names, and pass it back.
    """
    
    # If no list of other_names is passed in, load up a list with all of the 
    # names from the project summaries.
    if other_names is None:
        other_names = [p['project']['name'] for p in load_current_user_project_summaries2()['projects']]
      
    # Start with the passed in name.
    i = 0
    unique_name = name
    
    # Try adding an index (i) to the name until we find one that no longer 
    # matches one of the other names in the list.
    while unique_name in other_names:
        i += 1
        unique_name = "%s (%d)" % (name, i)
        
    # Return the found name.
    return unique_name

def save_project(proj):
    """
    Given a Project object, wrap it in a new prj.ProjectSO object and put this 
    in the project collection (either adding a new object, or updating an 
    existing one)  skip_result lets you null out saved results in the Project.
    """ 
    
    # Load the project record matching the UID of the project passed in.
    project_record = load_project_record(proj.uid)
    
    # Copy the project, only save what we want...
    new_project = sc.dcp(proj)
         
    # Create the new project entry and enter it into the ProjectCollection.
    # Note: We don't need to pass in project.uid as a 3rd argument because 
    # the constructor will automatically use the Project's UID.
    projSO = prj.ProjectSO(new_project, project_record.owner_uid)
    prj.proj_collection.update_object(projSO)
    

def save_project_as_new(proj, user_id):
    """
    Given a Project object and a user UID, wrap the Project in a new prj.ProjectSO 
    object and put this in the project collection, after getting a fresh UID
    for this Project.  Then do the actual save.
    """ 
    
    # Set a new project UID, so we aren't replicating the UID passed in.
    proj.uid = sc.uuid()
    
    # Create the new project entry and enter it into the ProjectCollection.
    projSO = prj.ProjectSO(proj, user_id)
    prj.proj_collection.add_object(projSO)  

    # Display the call information.
    # TODO: have this so that it doesn't show when logging is turned off
    print(">> save_project_as_new '%s'" % proj.name)

    # Save the changed Project object to the DataStore.
    save_project(proj)
    
    return None

def get_burden_set_fe_repr(burdenset):
    obj_info = {
        'burdenset': {
            'name': burdenset.name,
            'uid': burdenset.uid,
            'creationTime': burdenset.created,
            'updateTime': burdenset.modified
        }
    }
    return obj_info

def get_interv_set_fe_repr(interv_set):
    obj_info = {
        'intervset': {
            'name': interv_set.name,
            'uid': interv_set.uid,
            'creationTime': interv_set.created,
            'updateTime': interv_set.modified
        }
    }
    return obj_info

def get_package_set_fe_repr(packageset):
    obj_info = {
        'packageset': {
            'name': packageset.name,
            'uid': packageset.uid,
            'creationTime': packageset.created,
            'updateTime': packageset.modified
        }
    }
    return obj_info

#
# RPC functions
#

# RPC definitions
@register_RPC()
def get_version_info():
	''' Return the information about the project. '''
	gitinfo = sc.gitinfo(__file__)
	version_info = {
	       'version':   au.version,
	       'date':      au.versiondate,
	       'gitbranch': gitinfo['branch'],
	       'githash':   gitinfo['hash'],
	       'gitdate':   gitinfo['date'],
	}
	return version_info


##
## Project RPCs
##
    
@register_RPC(validation_type='nonanonymous user')
def get_scirisdemo_projects():
    """
    Return the projects associated with the Sciris Demo user.
    """
    
    # Get the user UID for the _ScirisDemo user.
    user_id = user.get_scirisdemo_user()
   
    # Get the prj.ProjectSO entries matching the _ScirisDemo user UID.
    project_entries = prj.proj_collection.get_project_entries_by_user(user_id)

    # Collect the project summaries for that user into a list.
    project_summary_list = map(load_project_summary_from_project_record, 
        project_entries)
    
    # Sort the projects by the project name.
    sorted_summary_list = sorted(project_summary_list, 
        key=lambda proj: proj['project']['name']) # Sorts by project name
    
    # Return a dictionary holding the project summaries.
    output = {'projects': sorted_summary_list}
    return output

@register_RPC(validation_type='nonanonymous user')
def load_project_summary(project_id):
    """
    Return the project summary, given the Project UID.
    """ 
    
    # Load the project record matching the UID of the project passed in.
    project_entry = load_project_record(project_id)
    
    # Return a project summary from the accessed prj.ProjectSO entry.
    return load_project_summary_from_project_record(project_entry)

@register_RPC(validation_type='nonanonymous user')
def load_current_user_project_summaries():
    """
    Return project summaries for all projects the user has to the client.
    """ 
    
    return load_current_user_project_summaries2()

@register_RPC(validation_type='nonanonymous user')                
def load_all_project_summaries():
    """
    Return project summaries for all projects to the client.
    """ 
    
    # Get all of the prj.ProjectSO entries.
    project_entries = prj.proj_collection.get_all_objects()
    
    # Grab a list of project summaries from the list of prj.ProjectSO objects we 
    # just got.
    return {'projects': map(load_project_summary_from_project_record, 
        project_entries)}
            
@register_RPC(validation_type='nonanonymous user')    
def delete_projects(project_ids):
    """
    Delete all of the projects with the passed in UIDs.
    """ 
    
    # Loop over the project UIDs of the projects to be deleted...
    for project_id in project_ids:
        # Load the project record matching the UID of the project passed in.
        record = load_project_record(project_id, raise_exception=True)
        
        # If a matching record is found, delete the object from the 
        # ProjectCollection.
        if record is not None:
            prj.proj_collection.delete_object_by_uid(project_id)

@register_RPC(call_type='download', validation_type='nonanonymous user')   
def download_project(project_id):
    """
    For the passed in project UID, get the Project on the server, save it in a 
    file, minus results, and pass the full path of this file back.
    """
    
    # Load the project with the matching UID.
    proj = load_project(project_id, raise_exception=True)
    
    # Use the downloads directory to put the file in.
    dirname = fileio.downloads_dir.dir_path
        
    # Create a filename containing the project name followed by a .prj 
    # suffix.
    file_name = '%s.prj' % proj.name
        
    # Generate the full file name with path.
    full_file_name = '%s%s%s' % (dirname, os.sep, file_name)
        
    # Write the object to a Gzip string pickle file.
    fileio.object_to_gzip_string_pickle_file(full_file_name, proj)
    
    # Display the call information.
    # TODO: have this so that it doesn't show when logging is turned off
    print(">> download_project %s" % (full_file_name))
    
    # Return the full filename.
    return full_file_name

@register_RPC(call_type='download', validation_type='nonanonymous user')
def load_zip_of_prj_files(project_ids):
    """
    Given a list of project UIDs, make a .zip file containing all of these 
    projects as .prj files, and return the full path to this file.
    """
    
    # Use the downloads directory to put the file in.
    dirname = fileio.downloads_dir.dir_path

    # Build a list of prj.ProjectSO objects for each of the selected projects, 
    # saving each of them in separate .prj files.
    prjs = [load_project_record(id).save_as_file(dirname) for id in project_ids]
    
    # Make the zip file name and the full server file path version of the same..
    zip_fname = '%s.zip' % str(sc.uuid())
    server_zip_fname = os.path.join(dirname, zip_fname)
    
    # Create the zip file, putting all of the .prj files in a projects 
    # directory.
    with ZipFile(server_zip_fname, 'w') as zipfile:
        for project in prjs:
            zipfile.write(os.path.join(dirname, project), 'projects/{}'.format(project))
            
    # Display the call information.
    # TODO: have this so that it doesn't show when logging is turned off
    print(">> load_zip_of_prj_files %s" % (server_zip_fname))

    # Return the server file name.
    return server_zip_fname

@register_RPC(validation_type='nonanonymous user')
def add_demo_project(user_id):
    """
    Add a demo Optima TB project
    """
    # Get a unique name for the project to be added.
    new_proj_name = get_unique_name('Demo project', other_names=None)
    
    # Create the project, loading in the desired spreadsheets.
    proj = au.demo(which='tb',do_plot=0) 
    proj.name = new_proj_name
    
    # Display the call information.
    # TODO: have this so that it doesn't show when logging is turned off
    print(">> add_demo_project %s" % (proj.name))    
    
    # Save the new project in the DataStore.
    save_project_as_new(proj, user_id)
    
    # Return the new project UID in the return message.
    return { 'projectId': str(proj.uid) }


@register_RPC(call_type='download', validation_type='nonanonymous user')
def create_new_project(user_id, proj_name, num_pops, data_start, data_end):
    """
    Create a new Optima Nutrition project.
    """
    
    args = {"num_pops":int(num_pops), "data_start":int(data_start), "data_end":int(data_end)}
    
    # Get a unique name for the project to be added.
    new_proj_name = get_unique_name(proj_name, other_names=None)
    
    # Create the project, loading in the desired spreadsheets.
    F = au.ProjectFramework(name='TB', filepath=au.atomica_path(['tests','frameworks'])+'framework_tb.xlsx')
    proj = au.Project(framework=F, name=new_proj_name)
    
    # Display the call information.
    # TODO: have this so that it doesn't show when logging is turned off
    print(">> create_new_project %s" % (proj.name))    
    
    # Save the new project in the DataStore.
    save_project_as_new(proj, user_id)
    
    # Use the downloads directory to put the file in.
    dirname = fileio.downloads_dir.dir_path
        
    # Create a filename containing the project name followed by a .prj 
    # suffix.
    file_name = '%s.xlsx' % proj.name
        
    # Generate the full file name with path.
    full_file_name = '%s%s%s' % (dirname, os.sep, file_name)
    
    # Return the databook
    proj.create_databook(databook_path=full_file_name, **args)
    
    print(">> download_databook %s" % (full_file_name))
    
    # Return the new project UID in the return message.
    return full_file_name


@register_RPC(call_type='upload', validation_type='nonanonymous user')
def upload_databook(databook_filename, project_id):
    """
    Upload a databook to a project.
    """
    
    # Display the call information.
    print(">> upload_databook '%s'" % databook_filename)
    
    proj = load_project(project_id, raise_exception=True)
    
    # Reset the project name to a new project name that is unique.
    proj.load_databook(databook_path=databook_filename)
    proj.modified = sc.today()
    
    # Save the new project in the DataStore.
    save_project(proj)
    
    # Return the new project UID in the return message.
    return { 'projectId': str(proj.uid) }


@register_RPC(validation_type='nonanonymous user')
def update_project_from_summary(project_summary):
    """
    Given the passed in project summary, update the underlying project 
    accordingly.
    """ 
    
    # Load the project corresponding with this summary.
    proj = load_project(project_summary['project']['id'])
       
    # Use the summary to set the actual project.
    proj.name = project_summary['project']['name']
    
    # Set the modified time to now.
    proj.modified = sc.today()
    
    # Save the changed project to the DataStore.
    save_project(proj)
    
@register_RPC(validation_type='nonanonymous user')    
def copy_project(project_id):
    """
    Given a project UID, creates a copy of the project with a new UID and 
    returns that UID.
    """
    
    # Get the Project object for the project to be copied.
    project_record = load_project_record(project_id, raise_exception=True)
    proj = project_record.proj
    
    # Make a copy of the project loaded in to work with.
    new_project = sc.dcp(proj)
    
    # Just change the project name, and we have the new version of the 
    # Project object to be saved as a copy.
    new_project.name = get_unique_name(proj.name, other_names=None)
    
    # Set the user UID for the new projects record to be the current user.
    user_id = current_user.get_id() 
    
    # Display the call information.
    # TODO: have this so that it doesn't show when logging is turned off
    print(">> copy_project %s" % (new_project.name)) 
    
    # Save a DataStore projects record for the copy project.
    save_project_as_new(new_project, user_id)
    
    # Remember the new project UID (created in save_project_as_new()).
    copy_project_id = new_project.uid

    # Return the UID for the new projects record.
    return { 'projectId': copy_project_id }

@register_RPC(call_type='upload', validation_type='nonanonymous user')
def create_project_from_prj_file(prj_filename, user_id):
    """
    Given a .prj file name and a user UID, create a new project from the file 
    with a new UID and return the new UID.
    """
    
    # Display the call information.
    print(">> create_project_from_prj_file '%s'" % prj_filename)
    
    # Try to open the .prj file, and return an error message if this fails.
    try:
        proj = fileio.gzip_string_pickle_file_to_object(prj_filename)
    except Exception:
        return { 'projectId': 'BadFileFormatError' }
    
    # Reset the project name to a new project name that is unique.
    proj.name = get_unique_name(proj.name, other_names=None)
    
    # Save the new project in the DataStore.
    save_project_as_new(proj, user_id)
    
    # Return the new project UID in the return message.
    return { 'projectId': str(proj.uid) }




# TODO: move this into the helper functions.  It's here now for testing 
# purposes.  Or, maybe remove dependency on this entirely, since it's a one-
# liner.
def make_mpld3_graph_dict(fig):
    mpld3_dict = mpld3.fig_to_dict(fig)
    return mpld3_dict


def supported_plots_func():
    
    supported_plots = {
            'Population size':'alive',
            'Latent infections':'lt_inf',
            'Active TB':'ac_inf',
            'Active DS-TB':'ds_inf',
            'Active MDR-TB':'mdr_inf',
            'Active XDR-TB':'xdr_inf',
            'New active DS-TB':{'New active DS-TB':['pd_div:flow','nd_div:flow']},
            'New active MDR-TB':{'New active MDR-TB':['pm_div:flow','nm_div:flow']},
            'New active XDR-TB':{'New active XDR-TB':['px_div:flow','nx_div:flow']},
            'Smear negative active TB':'sn_inf',
            'Smear positive active TB':'sp_inf',
            'Latent diagnoses':{'Latent diagnoses':['le_treat:flow','ll_treat:flow']},
            'New active TB diagnoses':{'Active TB diagnoses':['pd_diag:flow','pm_diag:flow','px_diag:flow','nd_diag:flow','nm_diag:flow','nx_diag:flow']},
            'New active DS-TB diagnoses':{'Active DS-TB diagnoses':['pd_diag:flow','nd_diag:flow']},
            'New active MDR-TB diagnoses':{'Active MDR-TB diagnoses':['pm_diag:flow','nm_diag:flow']},
            'New active XDR-TB diagnoses':{'Active XDR-TB diagnoses':['px_diag:flow','nx_diag:flow']},
            'Latent treatment':'ltt_inf',
            'Active treatment':'num_treat',
            'TB-related deaths':':ddis',
            }
    
    return supported_plots


@register_RPC(validation_type='nonanonymous user')    
def get_supported_plots(only_keys=False):
    
    supported_plots = supported_plots_func()
    
    if only_keys:
        return supported_plots.keys()
    else:
        return supported_plots


def get_plots(project_id, plot_names=None, pops='all'):
    
    import pylab as pl
    
    supported_plots = supported_plots_func() 
    
    if plot_names is None: plot_names = supported_plots.keys()

    proj = load_project(project_id, raise_exception=True)
    
    plot_names = sc.promotetolist(plot_names)
    result = proj.results[-1]

    figs = []
    graphs = []
    for plot_name in plot_names:
        try:
            plotdata = au.PlotData([result], outputs=supported_plots[plot_name], project=proj, pops=pops)
            figs += au.plot_series(plotdata, data=proj.data) # Todo - customize plot formatting here
            pl.gca().set_facecolor('none')
            print('Plot %s succeeded' % (plot_name))
        except Exception as E:
            print('WARNING: plot %s failed (%s)' % (plot_name, repr(E)))
    
    for f,fig in enumerate(figs):
        graph_dict = make_mpld3_graph_dict(fig)
        graphs.append(graph_dict)
        print('Converted figure %s of %s' % (f+1, len(figs)))

    return {'graphs':graphs}


@register_RPC(validation_type='nonanonymous user')    
def get_y_factors(project_id, parsetname=-1):
    print('Getting y factors...')
    y_factors = []
    proj = load_project(project_id, raise_exception=True)
    parset = proj.parsets[parsetname]
    for par_type in ["cascade", "comps", "characs"]:
        for parname in parset.par_ids[par_type].keys():
            thispar = parset.get_par(parname)
            for popname,y_factor in thispar.y_factor.items():
                thisdict = {'parname':parname, 'popname':popname, 'value':y_factor}
                y_factors.append(thisdict)
                print(thisdict)
    print('Returning %s y-factors' % len(y_factors))
    return y_factors


@register_RPC(validation_type='nonanonymous user')    
def set_y_factors(project_id, y_factors, parsetname=-1):
    print('Setting y factors...')
    proj = load_project(project_id, raise_exception=True)
    parset = proj.parsets[parsetname]
    for par in y_factors:
        value = float(par['value'])
        parset.get_par(par['parname']).y_factor[par['popname']] = value
        if value != 1:
            print(par)
    
    proj.modified = sc.today()
    proj.run_sim(parset=parsetname, store_results=True)
    save_project(proj)    
    output = get_plots(proj.uid)
    return output