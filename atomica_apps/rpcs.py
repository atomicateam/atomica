"""
Atomica remote procedure calls (RPCs)
    
Last update: 2018sep09
"""

###############################################################
### Imports
##############################################################

import time
import os
import re
import numpy as np
import pylab as pl
import mpld3
from zipfile import ZipFile
from flask_login import current_user
import sciris as sc
import scirisweb as sw
import atomica.ui as au
import atomica as at
from . import projects as prj
from . import frameworks as frw
from matplotlib.legend import Legend
pl.rc('font', size=14)



RPC_dict = {} # Dictionary to hold all of the registered RPCs in this module.
RPC = sw.makeRPCtag(RPC_dict) # RPC registration decorator factory created using call to make_RPC().


def CursorPosition():
    plugin = mpld3.plugins.MousePosition(fontsize=12, fmt='.4r')
    return plugin

def LineLabels(line=None, label=None):
    plugin = mpld3.plugins.LineLabelTooltip(line, label=label)
    return plugin


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.2f ms' %  (method.__name__, (te - ts) * 1000))
        return result

    return timed


def to_number(raw):
    ''' Convert something to a number. WARNING, I'm sure this already exists!! '''
    try:
        if sc.isstring(raw):
            raw = raw.replace(',','') # Remove commas, if present
            raw = raw.replace('$','') # Remove dollars, if present
        output = float(raw)
    except Exception as E:
        if raw is None:
            output = None
        else:
            raise E
    return output


def get_path(filename, online=True):
    if online:
        dirname = sw.globalvars.downloads_dir.dir_path # Use the downloads directory to put the file in.
        fullpath = '%s%s%s' % (dirname, os.sep, filename) # Generate the full file name with path.
    else:
        fullpath = filename
    return fullpath

###############################################################
### Results global and classes
##############################################################
    

# Global for the results cache.
results_cache = None


class ResultSet(sw.Blob):

    def __init__(self, uid, result_set, set_label):
        super(ResultSet, self).__init__(uid, type_prefix='resultset', 
            file_suffix='.rst', instance_label=set_label)
        self.result_set = result_set  # can be single Result or list of Results
        
    def show(self):
        # Show superclass attributes.
        super(ResultSet, self).show()  
        
        # Show the defined display text for the project.
        print('---------------------')
        print('Result set contents: ')
        print(self.result_set)


class ResultsCache(sw.BlobDict):

    def __init__(self, uid):
        super(ResultsCache, self).__init__(uid, type_prefix='resultscache', 
            file_suffix='.rca', instance_label='Results Cache', 
            objs_within_coll=False)
        
        # Create the Python dict to hold the hashes from cache_ids to the UIDs.
        self.cache_id_hashes = {}
        
    def load_from_copy(self, other_object):
        if type(other_object) == type(self):
            # Do the superclass copying.
            super(ResultsCache, self).load_from_copy(other_object)
            
            self.cache_id_hashes = other_object.cache_id_hashes
            
    def retrieve(self, cache_id):
        print('>> ResultsCache.retrieve() called') 
        print('>>   cache_id = %s' % cache_id)
        
        # Get the UID for the blob corresponding to the cache ID (if any).
        result_set_blob_uid = self.cache_id_hashes.get(cache_id, None)
        
        # If we found no match, return None.
        if result_set_blob_uid is None:
            print('>> ERROR: ResultSet %s not in cache_id_hashes' % result_set_blob_uid)
            return None
        
        # Otherwise, return the object found.
        else:
            obj = self.get_object_by_uid(result_set_blob_uid)
            if obj is None:
                print('>> ERROR: ResultSet %s not in DataStore handle_dict' % result_set_blob_uid)
                return None
            else:
                return self.get_object_by_uid(result_set_blob_uid).result_set
    
    def store(self, cache_id, result_set):
        print('>> ResultsCache.store() called')
        print('>>   cache_id = %s' % cache_id)
        print('>>   result_set contents:')
        print(result_set)
        
        # If there already is a cache entry for this, update the object there.
        if cache_id in self.cache_id_hashes.keys():
            result_set_blob = ResultSet(self.cache_id_hashes[cache_id], 
                result_set, cache_id)
            print('>> Running update_object()')
            self.update_object(result_set_blob)
            
        # Otherwise, update the cache ID hashes and add the new object.
        else:
            print('>> Running add_object()')
            result_set_blob = ResultSet(None, result_set, cache_id)
            self.cache_id_hashes[cache_id] = result_set_blob.uid
            self.add_object(result_set_blob)
    
    def delete(self, cache_id):
        print('>> ResultsCache.delete()')
        print('>>   cache_id = %s' % cache_id)
        
        # Get the UID for the blob corresponding to the cache ID (if any).
        result_set_blob_uid = self.cache_id_hashes.get(cache_id, None)
        
        # If we found no match, give an error.
        if result_set_blob_uid is None:
            print('>> ERROR: ResultSet not in cache_id_hashes')
            
        # Otherwise, delete the object found.
        else:
            del self.cache_id_hashes[cache_id] 
            self.delete_object_by_uid(result_set_blob_uid)
        
    def delete_all(self):
        print('>> ResultsCache.delete_all() called')
        # Reset the hashes from cache_ids to UIDs.
        self.cache_id_hashes = {}
        
        # Do the rest of the deletion process.
        self.delete_all_objects()
        
    def delete_by_project(self, project_uid):
        print('>> ResultsCache.delete_by_project() called')
        print('>>   project_uid = %s' % project_uid)
        
        # Build a list of the keys that match the given project.
        matching_cache_ids = []
        for cache_id in self.cache_id_hashes.keys():
            cache_id_project = re.sub(':.*', '', cache_id)
            if cache_id_project == project_uid:
                matching_cache_ids.append(cache_id)
        
        # For each matching key, delete the entry.
        for cache_id in matching_cache_ids:
            self.delete(cache_id)
            
    def show(self):
        super(sw.BlobDict, self).show()   # Show superclass attributes.
        if self.objs_within_coll: print('Objects stored within dict?: Yes')
        else:                     print('Objects stored within dict?: No')
        print('Cache ID dict contents: ')
        print(self.cache_id_hashes)         
        print('---------------------')
        print('Contents')
        print('---------------------')
        
        if self.objs_within_coll: # If we are storing things inside the obj_dict...
            for key in self.obj_dict: # For each key in the dictionary...
                obj = self.obj_dict[key] # Get the object pointed to.
                obj.show() # Show the handle contents.
        else: # Otherwise, we are using the UUID set.
            for uid in self.ds_uuid_set: # For each item in the set...
                obj = sw.globalvars.data_store.retrieve(uid)
                if obj is None:
                    print('--------------------------------------------')
                    print('ERROR: UID %s object failed to retrieve' % uid)
                else:
                    obj.show() # Show the object with that UID in the DataStore.
        print('--------------------------------------------')
 

###############################################################
### Framework functions
##############################################################
    

def load_framework_record(framework_id, raise_exception=True):
    """
    Return the framework DataStore reocord, given a framework UID.
    """ 
    
    # Load the matching frw.FrameworkSO object from the database.
    framework_record = frw.frame_collection.get_object_by_uid(framework_id)

    # If we have no match, we may want to throw an exception.
    if framework_record is None:
        if raise_exception:
            raise Exception('FrameworkDoesNotExist(id=%s)' % framework_id)
            
    # Return the Framework object for the match (None if none found).
    return framework_record


def load_framework(framework_id, raise_exception=True):
    """
    Return the Nutrition Framework object, given a framework UID, or None if no 
    ID match is found.
    """ 
    
    # Load the framework record matching the ID passed in.
    framework_record = load_framework_record(framework_id, 
        raise_exception=raise_exception)
    
    # If there is no match, raise an exception or return None.
    if framework_record is None:
        if raise_exception:
            raise Exception('FrameworkDoesNotExist(id=%s)' % framework_id)
        else:
            return None
        
    # Return the found framework.
    return framework_record.frame


def load_framework_summary_from_framework_record(framework_record):
    """
    Return the framework summary, given the DataStore record.
    """ 
    
    # Return the built framework summary.
    return framework_record.get_user_front_end_repr()
  
                
def save_framework(frame):
    """
    Given a Framework object, wrap it in a new frw.FrameworkSO object and put this 
    in the framework collection (either adding a new object, or updating an 
    existing one)  skip_result lets you null out saved results in the Framework.
    """ 
    
    # Load the framework record matching the UID of the framework passed in.
    framework_record = load_framework_record(frame.uid)
    
    # Copy the framework, only save what we want...
    new_framework = sc.dcp(frame)
    new_framework.modified = sc.now()
         
    # Create the new framework entry and enter it into the FrameworkCollection.
    # Note: We don't need to pass in framework.uid as a 3rd argument because 
    # the constructor will automatically use the Framework's UID.
    frameSO = frw.FrameworkSO(new_framework, framework_record.owner_uid)
    frw.frame_collection.update_object(frameSO)
    

def save_framework_as_new(frame, user_id):
    """
    Given a Framework object and a user UID, wrap the Framework in a new frw.FrameworkSO 
    object and put this in the framework collection, after getting a fresh UID
    for this Framework.  Then do the actual save.
    """ 
    frame.uid = sc.uuid() # Set a new framework UID, so we aren't replicating the UID passed in.
    frameSO = frw.FrameworkSO(frame, user_id) # Create the new framework entry and enter it into the FrameworkCollection.
    frw.frame_collection.add_object(frameSO)  
    print(">> save_framework_as_new '%s'" % frame.name) # Display the call information.
    save_framework(frame) # Save the changed Framework object to the DataStore.
    return None

    
##############################################################
### Project functions
##############################################################
    

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


@timeit
def load_project(project_id, raise_exception=True, online=True):
    """
    Return the Nutrition Project object, given a project UID, or None if no 
    ID match is found.
    """ 
    if not online:  return project_id # If running offline, just return the project
    project_record = load_project_record(project_id, raise_exception=raise_exception) # Load the project record matching the ID passed in.
    if project_record is None: # If there is no match, raise an exception or return None.
        if raise_exception: raise Exception('ProjectDoesNotExist(id=%s)' % project_id)
        else:               return None
    return project_record.proj # Return the found project.


@timeit
def load_project_summary_from_project_record(project_record):
    """
    Return the project summary, given the DataStore record.
    """ 
    
    # Return the built project summary.
    return project_record.get_user_front_end_repr()


@timeit
def get_unique_name(name, other_names=None):
    """
    Given a name and a list of other names, find a replacement to the name 
    that doesn't conflict with the other names, and pass it back.
    """
    
    # If no list of other_names is passed in, load up a list with all of the 
    # names from the project summaries.
    if other_names is None:
        other_names = [p['project']['name'] for p in load_current_user_project_summaries()['projects']]
      
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


@timeit
def save_project(proj, online=True):
    """
    Given a Project object, wrap it in a new prj.ProjectSO object and put this 
    in the project collection (either adding a new object, or updating an 
    existing one)  skip_result lets you null out saved results in the Project.
    """ 
    # If offline, just save to a file and return
    if not online:
        proj.save()
        return None
    
    # Load the project record matching the UID of the project passed in.

    ts = time.time()
    project_record = load_project_record(proj.uid)
    print('Loaded project record - elapsed time %.2f' % ((time.time()-ts)*1000))

    # Create the new project entry and enter it into the ProjectCollection.
    # Note: We don't need to pass in project.uid as a 3rd argument because 
    # the constructor will automatically use the Project's UID.
    projSO = prj.ProjectSO(proj, project_record.owner_uid)
    print('ProjectSO constructor - elapsed time %.2f' % ((time.time()-ts)*1000))
    prj.proj_collection.update_object(projSO)
    print('Collection update object - elapsed time %.2f' % ((time.time()-ts)*1000))
    return None


@timeit
def save_project_as_new(proj, user_id, uid=None):
    """
    Given a Project object and a user UID, wrap the Project in a new prj.ProjectSO 
    object and put this in the project collection, after getting a fresh UID
    for this Project.  Then do the actual save.
    """ 
    proj.uid = sc.uuid(uid=uid) # Set a new project UID, so we aren't replicating the UID passed in.
    projSO = prj.ProjectSO(proj, user_id) # Create the new project entry and enter it into the ProjectCollection.
    prj.proj_collection.add_object(projSO)  
    print(">> save_project_as_new '%s' [<%s> %s]" % (proj.name, user_id, proj.uid)) # Display the call information.
    save_project(proj) # Save the changed Project object to the DataStore.
    return proj.uid


# RPC definitions
@RPC()
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


##################################################################################
### Framework RPCs
##################################################################################


@RPC()
def get_framework_options():
    """
    Return the available demo frameworks
    """
    options = au.default_framework(show_options=True).values()
    return options
    
    
@RPC()
def get_scirisdemo_frameworks():
    """
    Return the frameworks associated with the Sciris Demo user.
    """
    
    # Get the user UID for the _ScirisDemo user.
    user_id = sw.get_scirisdemo_user()
   
    # Get the frw.FrameworkSO entries matching the _ScirisDemo user UID.
    framework_entries = frw.frame_collection.get_framework_entries_by_user(user_id)

    # Collect the framework summaries for that user into a list.
    framework_summary_list = map(load_framework_summary_from_framework_record, 
        framework_entries)
    
    # Sort the frameworks by the framework name.
    sorted_summary_list = sorted(framework_summary_list, 
        key=lambda frame: frame['framework']['name']) # Sorts by framework name
    
    # Return a dictionary holding the framework summaries.
    output = {'frameworks': sorted_summary_list}
    return output


@RPC()
def load_framework_summary(framework_id):
    """
    Return the framework summary, given the Framework UID.
    """ 
    
    # Load the framework record matching the UID of the framework passed in.
    framework_entry = load_framework_record(framework_id)
    
    # Return a framework summary from the accessed frw.FrameworkSO entry.
    return load_framework_summary_from_framework_record(framework_entry)


@RPC()
def load_current_user_framework_summaries():
    """
    Return framework summaries for all frameworks the user has to the client. -- WARNING, fix!
    """ 
    
    # Get the frw.FrameworkSO entries matching the user UID.
    framework_entries = frw.frame_collection.get_framework_entries_by_user(current_user.get_id())
    
    # Grab a list of framework summaries from the list of frw.FrameworkSO objects we 
    # just got.
    return {'frameworks': map(load_framework_summary_from_framework_record, framework_entries)}


@RPC()                
def load_all_framework_summaries():
    """
    Return framework summaries for all frameworks to the client.
    """ 
    
    # Get all of the frw.FrameworkSO entries.
    framework_entries = frw.frame_collection.get_all_objects()
    
    # Grab a list of framework summaries from the list of frw.FrameworkSO objects we 
    # just got.
    return {'frameworks': map(load_framework_summary_from_framework_record, 
        framework_entries)}

       
@RPC()    
def delete_frameworks(framework_ids):
    """
    Delete all of the frameworks with the passed in UIDs.
    """ 
    
    # Loop over the framework UIDs of the frameworks to be deleted...
    for framework_id in framework_ids:
        # Load the framework record matching the UID of the framework passed in.
        record = load_framework_record(framework_id, raise_exception=True)
        
        # If a matching record is found, delete the object from the 
        # FrameworkCollection.
        if record is not None:
            frw.frame_collection.delete_object_by_uid(framework_id)


@RPC(call_type='download')   
def download_framework(framework_id):
    """
    For the passed in framework UID, get the Framework on the server, save it in a 
    file, minus results, and pass the full path of this file back.
    """
    frame = load_framework(framework_id, raise_exception=True) # Load the framework with the matching UID.
    dirname = sw.globalvars.downloads_dir.dir_path # Use the downloads directory to put the file in.
    file_name = '%s.xlsx' % frame.name # Create a filename containing the framework name followed by a .frw suffix.
    full_file_name = '%s%s%s' % (dirname, os.sep, file_name) # Generate the full file name with path.
    frame.save(full_file_name) # Write the object to a Gzip string pickle file.
    print(">> download_framework %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download')
def load_zip_of_frw_files(framework_ids):
    """
    Given a list of framework UIDs, make a .zip file containing all of these 
    frameworks as .frw files, and return the full path to this file.
    """
    dirname = sw.globalvars.downloads_dir.dir_path # Use the downloads directory to put the file in.
    frws = [load_framework_record(id).save_as_file(dirname) for id in framework_ids] # Build a list of frw.FrameworkSO objects for each of the selected frameworks, saving each of them in separate .frw files.
    zip_fname = 'Frameworks %s.zip' % sc.getdate() # Make the zip file name and the full server file path version of the same..
    server_zip_fname = os.path.join(dirname, sc.sanitizefilename(zip_fname))
    with ZipFile(server_zip_fname, 'w') as zipfile: # Create the zip file, putting all of the .frw files in a frameworks directory.
        for framework in frws:
            zipfile.write(os.path.join(dirname, framework), 'frameworks/{}'.format(framework))
    print(">> load_zip_of_frw_files %s" % (server_zip_fname)) # Display the call information.
    return server_zip_fname # Return the server file name.


@RPC()
def add_demo_framework(user_id, framework_name):
    """
    Add a demo framework
    """
    other_names = [frw['framework']['name'] for frw in load_current_user_framework_summaries()['frameworks']]
    new_frame_name = sc.uniquename(framework_name, namelist=other_names) # Get a unique name for the framework to be added.
    frame = au.demo(kind='framework', which=framework_name)  # Create the framework, loading in the desired spreadsheets.
    frame.name = new_frame_name
    print(">> add_demo_framework %s" % (frame.name))    
    save_framework_as_new(frame, user_id) # Save the new framework in the DataStore.
    return { 'frameworkId': str(frame.uid) } # Return the new framework UID in the return message.


@RPC(call_type='download')
def create_new_framework(advanced=False):
    """
    Create a new framework.
    """
    if advanced: filename = 'framework_template_advanced.xlsx'
    else:        filename = 'framework_template.xlsx'
    filepath = au.atomica_path('atomica')+filename
    print(">> download_framework %s" % (filepath))
    return filepath # Return the filename


@RPC(call_type='upload')
def upload_frameworkbook(databook_filename, framework_id):
    """
    Upload a databook to a framework.
    """
    print(">> upload_frameworkbook '%s'" % databook_filename)
    frame = load_framework(framework_id, raise_exception=True)
    frame.read_from_file(filepath=databook_filename, overwrite=True) # Reset the framework name to a new framework name that is unique.
    frame.modified = sc.now()
    save_framework(frame) # Save the new framework in the DataStore.
    return { 'frameworkId': str(frame.uid) }


@RPC()
def update_framework_from_summary(framework_summary):
    """
    Given the passed in framework summary, update the underlying framework accordingly.
    """ 
    frame = load_framework(framework_summary['framework']['id']) # Load the framework corresponding with this summary.
    frame_uid = sc.uuid(framework_summary['framework']['id']).hex # Use the summary to set the actual framework, checking to make sure that the framework name is unique.
    other_names = [frw['framework']['name'] for frw in load_current_user_framework_summaries()['frameworks'] if (frw['framework']['id'].hex != frame_uid)]
    frame.name = sc.uniquename(framework_summary['framework']['name'], namelist=other_names)
    frame.modified = sc.now() # Set the modified time to now.
    save_framework(frame) # Save the changed framework to the DataStore.
    return None


@RPC()    
def copy_framework(framework_id):
    """
    Given a framework UID, creates a copy of the framework with a new UID and returns that UID.
    """
    framework_record = load_framework_record(framework_id, raise_exception=True) # Get the Framework object for the framework to be copied.
    frame = framework_record.frame
    new_framework = sc.dcp(frame) # Make a copy of the framework loaded in to work with.
    other_names = [frw['framework']['name'] for frw in load_current_user_framework_summaries()['frameworks']] # Just change the framework name, and we have the new version of the Framework object to be saved as a copy
    new_framework.name = sc.uniquename(frame.name, namelist=other_names)
    user_id = current_user.get_id()  # Set the user UID for the new frameworks record to be the current user.
    print(">> copy_framework %s" % (new_framework.name))  # Display the call information.
    save_framework_as_new(new_framework, user_id) # Save a DataStore frameworks record for the copy framework.
    copy_framework_id = new_framework.uid # Remember the new framework UID (created in save_framework_as_new()).
    return { 'frameworkId': copy_framework_id } # Return the UID for the new frameworks record.


@RPC(call_type='upload')
def create_framework_from_file(filename, user_id=None):
    """
    Given an .xlsx file name and a user UID, create a new framework from the file.
    """
    print(">> create_framework_from_frw_file '%s'" % filename)
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
    other_names = [frw['framework']['name'] for frw in load_current_user_framework_summaries()['frameworks']] # Reset the framework name to a new framework name that is unique.
    frame.name = sc.uniquename(frame.name, namelist=other_names)
    save_framework_as_new(frame, user_id) # Save the new framework in the DataStore.
    print('Created new framework:')
    print(frame)
    return { 'frameworkId': str(frame.uid) }


##################################################################################
### Project RPCs
##################################################################################


@RPC()
def get_demo_project_options():
    """
    Return the available demo frameworks
    """
    options = au.default_project(show_options=True).values()
    return options
    
    
@RPC()
def get_scirisdemo_projects():
    """ Return the projects associated with the Sciris Demo user. """
    user_id = sw.get_scirisdemo_user() # Get the user UID for the _ScirisDemo user.
    project_entries = prj.proj_collection.get_project_entries_by_user(user_id) # Get the prj.ProjectSO entries matching the _ScirisDemo user UID.
    project_summary_list = map(load_project_summary_from_project_record, project_entries) # Collect the project summaries for that user into a list.
    sorted_summary_list = sorted(project_summary_list, key=lambda proj: proj['project']['name']) # Sorts by project name
    output = {'projects': sorted_summary_list} # Return a dictionary holding the project summaries.
    return output


@RPC()
def load_project_summary(project_id):
    """ Return the project summary, given the Project UID. """ 
    project_entry = load_project_record(project_id) # Load the project record matching the UID of the project passed in.
    return load_project_summary_from_project_record(project_entry) # Return a project summary from the accessed prj.ProjectSO entry.


@timeit
@RPC()
def load_current_user_project_summaries():
    """ Return project summaries for all projects the user has to the client. """ 
    project_entries = prj.proj_collection.get_project_entries_by_user(current_user.get_id()) # Get the prj.ProjectSO entries matching the user UID.
    return {'projects': map(load_project_summary_from_project_record, project_entries)}# Grab a list of project summaries from the list of prj.ProjectSO objects we just got.


@RPC()
def load_all_project_summaries():
    """ Return project summaries for all projects to the client. """ 
    project_entries = prj.proj_collection.get_all_objects() # Get all of the prj.ProjectSO entries.
    return {'projects': map(load_project_summary_from_project_record, project_entries)} # Grab a list of project summaries from the list of prj.ProjectSO objects we just got.


@RPC()    
def delete_projects(project_ids):
    """
    Delete all of the projects with the passed in UIDs.
    """ 
    
    # Loop over the project UIDs of the projects to be deleted...
    for project_id in project_ids:
        # Load the project record matching the UID of the project passed in.
        record = load_project_record(project_id, raise_exception=True)
        
        # If a matching record is found...
        if record is not None:
            # Delete the object from the ProjectCollection.
            prj.proj_collection.delete_object_by_uid(project_id)
            
#            sw.globalvars.data_store.load()  # should not be needed so long as Celery worker does not change handle_dict
            
            # Delete any TaskRecords associated with the Project.
            tasks_delete_by_project(project_id)
            
            # Load the latest ResultsCache state from persistent store.
            results_cache.load_from_data_store()
            
            # Delete all cache entries with this project ID.
            results_cache.delete_by_project(project_id)


@RPC(call_type='download')   
def download_project(project_id):
    """
    For the passed in project UID, get the Project on the server, save it in a 
    file, minus results, and pass the full path of this file back.
    """
    proj = load_project(project_id, raise_exception=True) # Load the project with the matching UID.
    file_name = '%s.prj' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name) # Generate the full file name with path.
    sc.saveobj(full_file_name, proj) # Write the object to a Gzip string pickle file.
    print(">> download_project %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download')   
def download_framework_from_project(project_id):
    """
    Download the framework Excel file from a project
    """
    proj = load_project(project_id, raise_exception=True) # Load the project with the matching UID.
    file_name = '%s_framework.xlsx' % proj.name
    full_file_name = get_path(file_name) # Generate the full file name with path.
    proj.framework.save(full_file_name)
    print(">> download_framework %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download')   
def download_databook(project_id):
    """
    Download databook
    """
    proj = load_project(project_id, raise_exception=True) # Load the project with the matching UID.
    file_name = '%s_databook.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = get_path(file_name) # Generate the full file name with path.
    proj.databook.save(full_file_name)
    print(">> download_databook %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.


@RPC(call_type='download')   
def download_progbook(project_id):
    """ Download program book """
    proj = load_project(project_id, raise_exception=True) # Load the project with the matching UID.
    dirname = sw.globalvars.downloads_dir.dir_path # Use the downloads directory to put the file in.
    file_name = '%s_program_book.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = '%s%s%s' % (dirname, os.sep, file_name) # Generate the full file name with path.
    proj.progbook.save(full_file_name)
    print(">> download_progbook %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.
  
    
@RPC(call_type='download')   
def create_progbook(project_id, num_progs):
    """ Create program book """
    proj = load_project(project_id, raise_exception=True) # Load the project with the matching UID.
    dirname = sw.globalvars.downloads_dir.dir_path # Use the downloads directory to put the file in.
    file_name = '%s_program_book.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = '%s%s%s' % (dirname, os.sep, file_name) # Generate the full file name with path.
    proj.make_progbook(progbook_path=full_file_name, progs=int(num_progs))
    print(">> download_progbook %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.    
    

@RPC(call_type='download')
def load_zip_of_prj_files(project_ids):
    """
    Given a list of project UIDs, make a .zip file containing all of these 
    projects as .prj files, and return the full path to this file.
    """
    dirname = sw.globalvars.downloads_dir.dir_path # Use the downloads directory to put the file in.
    prjs = [load_project_record(id).save_as_file(dirname) for id in project_ids] # Build a list of prj.ProjectSO objects for each of the selected projects, saving each of them in separate .prj files.
    zip_fname = 'Projects %s.zip' % sc.getdate() # Make the zip file name and the full server file path version of the same..
    server_zip_fname = os.path.join(dirname, sc.sanitizefilename(zip_fname))
    with ZipFile(server_zip_fname, 'w') as zipfile: # Create the zip file, putting all of the .prj files in a projects directory.
        for project in prjs:
            zipfile.write(os.path.join(dirname, project), 'projects/{}'.format(project))
    print(">> load_zip_of_prj_files %s" % (server_zip_fname)) # Display the call information.
    return server_zip_fname # Return the server file name.


@RPC()
def add_demo_project(user_id, project_name='default'):
    """
    Add a demo project
    """
    if project_name == 'default':
        new_proj_name = get_unique_name('Demo project', other_names=None) # Get a unique name for the project to be added
        proj = au.demo(which='tb', do_run=False, do_plot=False, sim_dt=0.5)  # Create the project, loading in the desired spreadsheets.
        proj.name = new_proj_name
    else:
        new_proj_name = get_unique_name(project_name, other_names=None) # Get a unique name for the project to be added.
        proj = au.demo(which=project_name, do_run=False, do_plot=False)  # Create the project, loading in the desired spreadsheets.
        proj.name = new_proj_name
        print('Adding demo project %s/%s...' % (project_name, new_proj_name))

    save_project_as_new(proj, user_id) # Save the new project in the DataStore.
    print(">> add_demo_project %s" % (proj.name))    
    return { 'projectId': str(proj.uid) } # Return the new project UID in the return message.


@RPC(call_type='download')
def create_new_project(user_id, framework_id, proj_name, num_pops, num_progs, data_start, data_end, tool=None):
    """
    Create a new project.
    """
    if tool == 'tb': sim_dt = 0.5
    else:            sim_dt = None
    if tool is None: # Optionally select by tool rather than frame
        framework_record = load_framework_record(framework_id, raise_exception=True) # Get the Framework object for the framework to be copied.
        frame = framework_record.frame
    else: # Or get a pre-existing one by the tool name
        frame = au.demo(kind='framework', which=tool, sim_dt=sim_dt)
    args = {"num_pops":int(num_pops), "data_start":int(data_start), "data_end":int(data_end)}
    new_proj_name = get_unique_name(proj_name, other_names=None) # Get a unique name for the project to be added.
    proj = au.Project(framework=frame, name=new_proj_name, sim_dt=sim_dt) # Create the project, loading in the desired spreadsheets.
    print(">> create_new_project %s" % (proj.name))
    dirname = sw.globalvars.downloads_dir.dir_path # Use the downloads directory to put the file in.
    file_name = '%s.xlsx' % proj.name # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = '%s%s%s' % (dirname, os.sep, file_name) # Generate the full file name with path.
    data = proj.create_databook(databook_path=full_file_name, **args) # Return the databook
    proj.databook = data.to_spreadsheet()
    save_project_as_new(proj, user_id) # Save the new project in the DataStore.
    print(">> download_databook %s" % (full_file_name))
    return full_file_name # Return the filename


@RPC(call_type='upload')
def upload_databook(databook_filename, project_id):
    """ Upload a databook to a project. """
    print(">> upload_databook '%s'" % databook_filename)
    proj = load_project(project_id, raise_exception=True)
    proj.load_databook(databook_path=databook_filename) 
    proj.modified = sc.now()
    save_project(proj) # Save the new project in the DataStore.
    return { 'projectId': str(proj.uid) } # Return the new project UID in the return message.


@RPC(call_type='upload')
def upload_progbook(progbook_filename, project_id):
    """
    Upload a program book to a project.
    """
    print(">> upload_progbook '%s'" % progbook_filename)
    proj = load_project(project_id, raise_exception=True)
    proj.load_progbook(progbook_path=progbook_filename) 
    proj.modified = sc.now()
    save_project(proj)
    return { 'projectId': str(proj.uid) }


@RPC()
def update_project_from_summary(project_summary):
    """ Given the passed in project summary, update the underlying project accordingly. """ 
    proj = load_project(project_summary['project']['id']) # Load the project corresponding with this summary.
    proj.name = project_summary['project']['name'] # Use the summary to set the actual project.
    proj.modified = sc.now() # Set the modified time to now.
    save_project(proj) # Save the changed project to the DataStore.
    return None
    
@RPC()
def copy_project(project_id):
    """
    Given a project UID, creates a copy of the project with a new UID and 
    returns that UID.
    """
    # Get the Project object for the project to be copied.
    project_record = load_project_record(project_id, raise_exception=True)
    proj = project_record.proj
    new_project = sc.dcp(proj) # Make a copy of the project loaded in to work with.
    new_project.name = get_unique_name(proj.name, other_names=None) # Just change the project name, and we have the new version of the Project object to be saved as a copy.
    user_id = current_user.get_id() # Set the user UID for the new projects record to be the current user.
    print(">> copy_project %s" % (new_project.name))  # Display the call information.
    save_project_as_new(new_project, user_id) # Save a DataStore projects record for the copy project.
    copy_project_id = new_project.uid # Remember the new project UID (created in save_project_as_new()).
    return { 'projectId': copy_project_id } # Return the UID for the new projects record.


@RPC(call_type='upload')
def create_project_from_prj_file(prj_filename, user_id):
    """
    Given a .prj file name and a user UID, create a new project from the file 
    with a new UID and return the new UID.
    """
    print(">> create_project_from_prj_file '%s'" % prj_filename) # Display the call information.
    try: # Try to open the .prj file, and return an error message if this fails.
        proj = sc.loadobj(prj_filename)
    except Exception:
        return { 'error': 'BadFileFormatError' }
    proj.name = get_unique_name(proj.name, other_names=None) # Reset the project name to a new project name that is unique.
    save_project_as_new(proj, user_id) # Save the new project in the DataStore.
    return { 'projectId': str(proj.uid) } # Return the new project UID in the return message.


@RPC()
def get_y_factors(project_id, parsetname=-1):
    print('Getting y factors for parset %s...' % parsetname)
    TEMP_YEAR = 2018 # WARNING, hard-coded!
    y_factors = []
    proj = load_project(project_id, raise_exception=True)
    parset = proj.parsets[parsetname]
    count = 0
    for par_type in ["cascade", "comps", "characs"]:
        for parname in parset.par_ids[par_type].keys():
            this_par = parset.get_par(parname)
            # TODO - do something with this_par.meta_y_factor here
            this_spec = proj.framework.get_variable(parname)[0]
            if 'calibrate' in this_spec and this_spec['calibrate'] is not None:
                for popname,y_factor in this_par.y_factor.items():
                    count += 1
                    parlabel = this_spec['display name']
                    popindex = parset.pop_names.index(popname)
                    poplabel = parset.pop_labels[popindex]
                    try:    
                        interp_val = this_par.interpolate([TEMP_YEAR],popname)[0]
                        if not np.isfinite(interp_val):
                            interp_val = 1
                        if sc.approx(interp_val, 0):
                            interp_val = 1
                    except: 
                        interp_val = 1
                    dispvalue = interp_val*y_factor
                    thisdict = {'index':count, 'parname':parname, 'popname':popname, 'value':y_factor, 'dispvalue':dispvalue, 'parlabel':parlabel, 'poplabel':poplabel}
                    y_factors.append(thisdict)
                    print(thisdict)
    print('Returning %s y-factors' % len(y_factors))
    return y_factors


##################################################################################
#%% Parset functions and RPCs
##################################################################################


@RPC() 
def get_parset_info(project_id):
    print('Returning parset info...')
    proj = load_project(project_id, raise_exception=True)
    parset_names = proj.parsets.keys()
    return parset_names


@RPC() 
def rename_parset(project_id, parsetname=None, new_name=None):
    print('Renaming parset from %s to %s...' % (parsetname, new_name))
    proj = load_project(project_id, raise_exception=True)
    proj.parsets.rename(parsetname, new_name)
    print('Saving project...')
    save_project(proj)
    return None


@RPC() 
def copy_parset(project_id, parsetname=None):
    print('Copying parset %s...' % parsetname)
    proj = load_project(project_id, raise_exception=True)
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
    proj = load_project(project_id, raise_exception=True)
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
    """
    For the passed in project UID, get the Project on the server, save it in a 
    file, minus results, and pass the full path of this file back.
    """
    proj = load_project(project_id, raise_exception=True) # Load the project with the matching UID.
    parset = proj.parsets[parsetname]
    dirname = sw.globalvars.downloads_dir.dir_path # Use the downloads directory to put the file in.
    file_name = '%s - %s.par' % (proj.name, parsetname) # Create a filename containing the project name followed by a .prj suffix.
    full_file_name = '%s%s%s' % (dirname, os.sep, file_name) # Generate the full file name with path.
    sc.saveobj(full_file_name, parset) # Write the object to a Gzip string pickle file.
    print(">> download_parset %s" % (full_file_name)) # Display the call information.
    return full_file_name # Return the full filename.
    
    
@RPC(call_type='upload')   
def upload_parset(parset_filename, project_id):
    """
    For the passed in project UID, get the Project on the server, save it in a 
    file, minus results, and pass the full path of this file back.
    """
    proj = load_project(project_id, raise_exception=True) # Load the project with the matching UID.
    parset = sc.loadobj(parset_filename)
    parsetname = sc.uniquename(parset.name, namelist=proj.parsets.keys())
    parset.name = parsetname # Reset the name
    proj.parsets[parsetname] = parset
    proj.modified = sc.now()
    save_project(proj) # Save the new project in the DataStore.
    return parsetname # Return the new project UID in the return message.


##################################################################################
#%% Progset functions and RPCs
##################################################################################


@RPC() 
def get_progset_info(project_id):
    print('Returning progset info...')
    proj = load_project(project_id, raise_exception=True)
    progset_names = proj.progsets.keys()
    return progset_names


@RPC() 
def rename_progset(project_id, progsetname=None, new_name=None):
    print('Renaming progset from %s to %s...' % (progsetname, new_name))
    proj = load_project(project_id, raise_exception=True)
    proj.progsets.rename(progsetname, new_name)
    print('Saving project...')
    save_project(proj)
    return None


@RPC() 
def copy_progset(project_id, progsetname=None):
    print('Copying progset %s...' % progsetname)
    proj = load_project(project_id, raise_exception=True)
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
    proj = load_project(project_id, raise_exception=True)
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
### Plotting functions and RPCs
##################################################################################


def supported_plots_func(framework):
    '''
    Return a dict of supported plots extracted from the framework.

    Input:
        framework : a ProjectFramework instance
    Output:
        {name:quantities}: a dict with all of the plot quantities in the framework keyed by name
    '''
    if 'plots' not in framework.sheets:
        return dict()
    else:
        df = framework.sheets['plots'][0]
        plots = sc.odict()
        for name,output in zip(df['name'], df['quantities']):
            plots[name] = at.results.evaluate_plot_string(output)
        return plots


@RPC()    
def get_supported_plots(project_id, only_keys=False):
    proj = load_project(project_id, raise_exception=True)
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


def savefigs(allfigs, online=True, die=False):
#    if online: folder = sw.globalvars.downloads_dir.dir_path
    if online: 
        # Look for an existing downloads_dir UID.
        downloads_dir_uid = sw.globalvars.data_store.get_uid('filesavedir', 
            'Downloads Directory')        
        folder = sw.globalvars.data_store.retrieve(downloads_dir_uid).dir_path    
    else:      folder = os.getcwd()
    filepath = sc.savefigs(allfigs, filetype='singlepdf', filename='figures.pdf', folder=folder)
    return filepath


@RPC(call_type='download')
def download_graphs():
    dirname = sw.globalvars.downloads_dir.dir_path # Use the downloads directory to put the file in.
    file_name = 'figures.pdf' # Create a filename containing the framework name followed by a .frw suffix.
    full_file_name = '%s%s%s' % (dirname, os.sep, file_name) # Generate the full file name with path.
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
            if isinstance(output.values()[0],list):
                plotdata = au.PlotData(results, outputs=output, project=proj, pops=pops)
            else:
                plotdata = au.PlotData(results, outputs=output.values()[0], project=proj, pops=pops) # Pass string in directly so that it is not treated as a function aggregation

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
                pl.close(fig)
            print('Plot %s succeeded' % (output))
        except Exception as E:
            print('WARNING: plot %s failed (%s)' % (output, repr(E)))
    output = {'graphs':allfigjsons, 'legends':alllegendjsons}
    return output, allfigs, alllegends


def make_plots(proj, results, tool=None, year=None, pops=None, cascade=None, plot_options=None, dosave=None, calibration=False, online=True, plot_budget=False, outputfigs=False):
    
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
        pops = 'aggregate' # make sure it's lowercase
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
    if dosave:
        savefigs(allfigs, online=online)  
    if outputfigs: return output, allfigs, alllegends
    else:          return output


def customize_fig(fig=None, output=None, plotdata=None, xlims=None, figsize=None, is_legend=False):
    if is_legend:
        pass # Put legend customizations here
    else:
        if figsize is None: figsize = (5,3)
        fig.set_size_inches(figsize)
        ax = fig.get_axes()[0]
        ax.set_position([0.25,0.15,0.70,0.75])
        ax.set_facecolor('none')
        ax.set_title(output.keys()[0]) # This is in a loop over outputs, so there should only be one output present
        ax.set_ylabel(plotdata.series[0].units) # All outputs should have the same units (one output for each pop/result)
        if xlims is not None: ax.set_xlim(xlims)
        try:
            legend = fig.findobj(Legend)[0]
            if len(legend.get_texts())==1:
                legend.remove() # Can remove the legend if it only has one entry
        except:
            pass
        mpld3.plugins.connect(fig, CursorPosition())
        for l,line in enumerate(fig.axes[0].lines):
            mpld3.plugins.connect(fig, LineLabels(line, label=line.get_label()))
    
    graph_dict = sw.mpld3ify(fig, jsonify=False) # Convert to mpld3
    return graph_dict
    

def get_program_plots(results,year,budget=True,coverage=True):
    # Generate program related plots
    # INPUTS
    # - proj : Project instance
    # - results : Result or list of Results
    # - year : If making a budget bar plot, it will be displayed for this year
    # - budget : True/False flag for whether to include budget bar plot
    # - coverage : True/False flag for whether to include program coverage figures

    figs = []
    if budget:
        d = au.PlotData.programs(results, quantity='spending')
        d.interpolate(year)
        budget_figs = au.plot_bars(d, stack_outputs='all', legend_mode='together', outer='times', show_all_labels=False, orientation='horizontal')

        ax = budget_figs[0].axes[0]
        ax.set_xlabel('Spending ($/year)')

        # The legend is too big for the figure -- WARNING, think of a better solution
        #        budget_figs[1].set_figheight(8.9)
        #        budgetfigs[1].set_figwidth(8.7)

        figs += budget_figs
        print('Budget plot succeeded')

    if coverage:
        d = au.PlotData.programs(results,quantity='coverage_fraction')
        coverage_figs = au.plot_series(d, axis='results')
        for fig,(output_name,output_label) in zip(coverage_figs,d.outputs.items()):
            fig.axes[0].set_title(output_label)
            series = d[d.results.keys()[0],d.pops.keys()[0],output_name]
            fig.axes[0].set_ylabel(series.units)
        figs += coverage_figs
        print('Coverage plots succeeded')

    graphs = []
    for fig in figs:
        graph_dict = mpld3.fig_to_dict(fig)
        graph_dict = sc.sanitizejson(graph_dict) # This shouldn't be necessary, but it is...
        graphs.append(graph_dict)
        pl.close(fig)
    output = {'graphs':graphs}
    return output, figs

def get_cascade_plot(proj, results=None, pops=None, year=None, cascade=None, plot_budget=False):
    
    if results is None: results = proj.results[-1]
    if year is None: year = proj.settings.sim_end # Needed for plot_budget
    
    figs = []
    legends = []
    figjsons = []
    legendjsons = []
    years = sc.promotetolist(year)
    for y in range(len(years)):
        years[y] = float(years[y]) # Ensure it's a float

    fig,table = au.plot_cascade(results, cascade=cascade, pops=pops, year=years, data=proj.data, show_table=False)
    figs.append(fig)
    legends.append(sc.emptyfig()) # No figure, but still useful to have a plot
    
    if plot_budget:
        
        d = au.PlotData.programs(results, quantity='spending')
        d.interpolate(year)
        budgetfigs = au.plot_bars(d, stack_outputs='all', legend_mode='together', outer='times', show_all_labels=False, orientation='vertical')
        budgetlegends = [sc.emptyfig()]
        
        ax = budgetfigs[0].axes[0]
        ax.set_xlabel('Spending ($/year)')
        
        figs    += budgetfigs
        legends += budgetlegends
        print('Budget plot succeeded')
    
    for fig in figs:
        ax = fig.get_axes()[0]
        ax.set_facecolor('none')
        mpld3.plugins.connect(fig, CursorPosition())
        graph_dict = sw.mpld3ify(fig, jsonify=False) # These get jsonified later
        figjsons.append(graph_dict)
        pl.close(fig)
    
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
    # Return all data to render cascade in FE, for multiple results
    #
    # INPUTS
    # - results - A Result, or list of Results
    # - data - A ProjectData instance (e.g. proj.data)
    #
    # OUTPUTS
    # - dict/json containing the data required to make the cascade plot on the FE
    #   The dict has the following structure. Suppose we have
    #
    #   cascade_data = get_json_cascade(results,data)
    #
    #   Then the output of this function is (JSON equivalent of?):
    #
    #   cascade_data['results'] - List of names of all results included (could render as checkboxes)
    #   cascade_data['pops'] - List of names of all pops included (could render as checkboxes)
    #   cascade_data['cascades'] - List of names of all cascades included (could render as dropdown)
    #   cascade_data['stages'][cascade_name] - List of the names of the stages in a given cascade
    #   cascade_data['t'][result_name] - Array of time values for the given result
    #   cascade_data['model'][result_name][cascade_name][pop_name][stage_name] - Array of values, same size as cascade_data['t'][result_name] (this contains the values that end up in the bar)
    #   cascade_data['data_t'] - Array of time values for the data
    #   cascade_data['data'][cascade_name][pop_name][stage_name] - Array of values, same size as cascade_data['data_t'] (this contains the values to be plotted as scatter points)
    #
    #   Note - the data values entered in the databook are sparse (typically there isn't a data point at every time). The arrays all have
    #   the same size as cascade_data['data_t'], but contain `NaN` if the data was missing

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


@timeit
@RPC()  
def manual_calibration(project_id, cache_id, parsetname=-1, y_factors=None, plot_options=None, plotyear=None, pops=None, tool=None, cascade=None, dosave=True):
    print('>> DEBUGGING STUFF:')
    print(plot_options)
    print('Setting y factors for parset %s...' % parsetname)
    TEMP_YEAR = 2018 # WARNING, hard-coded!
    proj = load_project(project_id, raise_exception=True)
    parset = proj.parsets[parsetname]
    for pardict in y_factors:
        parname   = pardict['parname']
        dispvalue = float(pardict['dispvalue'])
        popname   = pardict['popname']
        thispar   = parset.get_par(parname)
        try:    
            interp_val = thispar.interpolate([TEMP_YEAR],popname)[0]
            if not np.isfinite(interp_val):
                interp_val = 1
            if sc.approx(interp_val, 0):
                interp_val = 1
        except: 
            interp_val = 1
        y_factor  = dispvalue/interp_val
        parset.get_par(parname).y_factor[popname] = y_factor
        # TODO - set thispar.meta_y_factor here
        if not sc.approx(y_factor, 1):
            print('Modified: %s (%s)' % (parname, y_factor))
    
    proj.modified = sc.now()
    result = proj.run_sim(parset=parsetname, store_results=False)
    put_results_cache_entry(cache_id, result)

    output = make_plots(proj, result, tool=tool, year=plotyear, pops=pops, cascade=cascade, plot_options=plot_options, dosave=dosave, calibration=True)

    return output


@RPC()    
def automatic_calibration(project_id, cache_id, parsetname=-1, max_time=20, saveresults=True, plot_options=None, tool=None, plotyear=None, pops=None,cascade=None, dosave=True):
    print('Running automatic calibration for parset %s...' % parsetname)
    proj = load_project(project_id, raise_exception=True)
    proj.calibrate(parset=parsetname, max_time=float(max_time)) # WARNING, add kwargs!
    
    print('Rerunning calibrated model...')
    
    print('Resultsets before run: %s' % len(proj.results))
    if saveresults:
        result = proj.run_sim(parset=parsetname, store_results=True)
        save_project(proj)
    else:
        result = proj.run_sim(parset=parsetname, store_results=False) 
#        store_result_separately(proj, result)
    put_results_cache_entry(cache_id, result)    
    print('Resultsets after run: %s' % len(proj.results))

    output = make_plots(proj, result, tool=tool, year=plotyear, pops=pops, cascade=cascade, plot_options=plot_options, dosave=dosave, calibration=True)

    return output


##################################################################################
### Scenario functions and RPCs
##################################################################################


def py_to_js_scen(py_scen, project=None):
    ''' Convert a Python to JSON representation of a scenario. The Python scenario might be a dictionary or an object. '''
    js_scen = {}
    attrs = ['name', 'active', 'parsetname', 'progsetname', 'start_year'] 
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
    py_scen['start_year'] = float(js_scen['start_year']) # Convert to number
    py_scen['alloc'] = sc.odict()
    for item in js_scen['alloc']:
        prog_name = item[0]
        budget = item[1]
        if sc.isstring(budget):
            try:
                budget = to_number(budget)
            except Exception as E:
                raise Exception('Could not convert budget to number: %s' % repr(E))
        if sc.isiterable(budget):
            if len(budget)>1:
                raise Exception('Budget should only have a single element in it, not %s' % len(budget))
            else:
                budget = budget[0] # If it's not a scalar, pull out the first element -- WARNING, KLUDGY
        py_scen['alloc'][prog_name] = to_number(budget)
    return py_scen
    

@RPC()
def get_scen_info(project_id, online=True):
    print('Getting scenario info...')
    proj = load_project(project_id, raise_exception=True, online=online)
    scenario_summaries = []
    for py_scen in proj.scens.values():
        js_scen = py_to_js_scen(py_scen, project=proj)
        scenario_summaries.append(js_scen)
    print('JavaScript scenario info:')
    sc.pp(scenario_summaries)

    return scenario_summaries


@RPC()
def set_scen_info(project_id, scenario_summaries, online=True):
    print('Setting scenario info...')
    proj = load_project(project_id, raise_exception=True, online=online)
    proj.scens.clear()
    for j,js_scen in enumerate(scenario_summaries):
        print('Setting scenario %s of %s...' % (j+1, len(scenario_summaries)))
        py_scen = js_to_py_scen(js_scen)
        print('Python scenario info for scenario %s:' % (j+1))
        print(py_scen)
        proj.make_scenario(which='budget', json=py_scen)
    print('Saving project...')
    save_project(proj, online=online)
    return None


@RPC()    
def get_default_budget_scen(project_id):
    print('Creating default scenario...')
    proj = load_project(project_id, raise_exception=True)
    py_scen = proj.demo_scenarios(doadd=False)
    js_scen = py_to_js_scen(py_scen, project=proj)
    print('Created default JavaScript scenario:')
    sc.pp(js_scen)
    return js_scen


@RPC()    
def run_scenarios(project_id, cache_id, plot_options, saveresults=True, tool=None, plotyear=None, pops=None,cascade=None, dosave=True):
    print('Running scenarios...')
    proj = load_project(project_id, raise_exception=True)
    results = proj.run_scenarios(store_results=False)
    if len(results) < 1:  # Fail if we have no results (user didn't pick a scenario)
        return {'error': 'No scenario selected'}
    put_results_cache_entry(cache_id, results)
    output = make_plots(proj, results, tool=tool, year=plotyear, pops=pops, cascade=cascade, plot_options=plot_options, dosave=dosave, calibration=False, plot_budget=True)
    print('Saving project...')
    save_project(proj)
    return output




##################################################################################
### Optimization functions and RPCs
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
        json[key] = to_number(json[key]) # Convert to a number
    for subkey in json['objective_weights'].keys():
        json['objective_weights'][subkey] = to_number(json['objective_weights'][subkey])
    for subkey in json['prog_spending'].keys():
        this = json['prog_spending'][subkey]
        json['prog_spending'][subkey] = (to_number(this['min']), to_number(this['max']))
    return json
    

@RPC()    
def get_optim_info(project_id, online=True):
    print('Getting optimization info...')
    proj = load_project(project_id, raise_exception=True, online=online)
    optim_summaries = []
    for py_optim in proj.optims.values():
        js_optim = py_to_js_optim(py_optim, project=proj)
        optim_summaries.append(js_optim)
    print('JavaScript optimization info:')
    print(optim_summaries)
    return optim_summaries


@RPC()
def get_default_optim(project_id, tool=None, online=True):
    print('Getting default optimization...')
    proj = load_project(project_id, raise_exception=True, online=online)
    py_optim = proj.demo_optimization(tool=tool)
    js_optim = py_to_js_optim(py_optim, project=proj)
    print('Created default optimization:')
    print(js_optim)
    return js_optim


@RPC()    
def set_optim_info(project_id, optim_summaries, online=True):
    print('Setting optimization info...')
    proj = load_project(project_id, raise_exception=True, online=online)
    proj.optims.clear()
    for j,js_optim in enumerate(optim_summaries):
        print('Setting optimization %s of %s...' % (j+1, len(optim_summaries)))
        json = js_to_py_optim(js_optim)
        print('Python optimization info for optimization %s:' % (j+1))
        print(json)
        proj.make_optimization(json=json)
    print('Saving project...')
    save_project(proj, online=online)   
    return None


# This is the function we should use on occasions when we can't use Celery.
@RPC()
def run_optimization(project_id, cache_id, optim_name=None, plot_options=None, maxtime=None, tool=None, plotyear=None, pops=None, cascade=None, dosave=True, online=True):
    print('Running Cascade optimization...')
    sc.printvars(locals(), ['project_id', 'optim_name', 'plot_options', 'maxtime', 'tool', 'plotyear', 'pops', 'cascade', 'dosave', 'online'], color='blue')
    if online: # Assume project_id is actually an ID
        proj = load_project(project_id, raise_exception=True)
    else: # Otherwise try using it as a project
        proj = project_id
        
    # Actually run the optimization and get its results (list of baseline and 
    # optimized Result objects).
    results = proj.run_optimization(optim_name, maxtime=float(maxtime), store_results=False)
    
    # Put the results into the ResultsCache.
    put_results_cache_entry(cache_id, results)

    # Plot the results.    
    output = make_plots(proj, results, tool=tool, year=plotyear, pops=pops, cascade=cascade, plot_options=plot_options, dosave=dosave, online=online, plot_budget=True)
    return output


##############################################################
### Task functions and RPCs
##############################################################
    

def tasks_delete_by_project(project_uid):
    print('>> tasks_delete_by_project() called')
    print('>>   project_uid = %s' % project_uid)
    
    # Look for an existing tasks dictionary.
    task_dict_uid = sw.globalvars.data_store.get_uid('taskdict', 'Task Dictionary')
    
    # Create the task dictionary object.
    task_dict = sw.TaskDict(task_dict_uid)
    
    # Load the TaskDict tasks from Redis.
    task_dict.load_from_data_store()

    # Build a list of the keys that match the given project.
    matching_task_ids = []
    for task_id in task_dict.task_id_hashes.keys():
        task_id_project = re.sub(':.*', '', task_id)
        if task_id_project == project_uid:
            matching_task_ids.append(task_id)
            
    print('>> Task IDs to be deleted:')
    print(matching_task_ids)
    
    # For each matching key, delete the task, aborting it in Celery also.
    for task_id in matching_task_ids:
        sw.delete_task(task_id)
            

##############################################################
### Results / ResultSet functions and RPCs
##############################################################
    

def init_results_cache(app):
    global results_cache
    
    # Look for an existing ResultsCache.
    results_cache_uid = sw.globalvars.data_store.get_uid('resultscache', 'Results Cache')
    
    # Create the results cache object.  Note, that if no match was found, 
    # this will be assigned a new UID.    
    results_cache = ResultsCache(results_cache_uid)  
    
    # If there was a match...
    if results_cache_uid is not None:
#        if app.config['LOGGING_MODE'] == 'FULL':
#            print('>> Loading ResultsCache from the DataStore.')
        results_cache.load_from_data_store()
        
    # Else (no match)...
    else:
        if app.config['LOGGING_MODE'] == 'FULL':
            print('>> Creating a new ResultsCache.') 
        results_cache.add_to_data_store()
        
    # Uncomment this to delete all the entries in the cache.
#    results_cache.delete_all()
    
    if app.config['LOGGING_MODE'] == 'FULL':
        # Show what's in the ResultsCache.    
        results_cache.show()
        print('>> Loaded results cache with %s results' % len(results_cache.keys()))

        
def apptasks_load_results_cache():
    # Look for an existing ResultsCache.
    results_cache_uid = sw.globalvars.data_store.get_uid('resultscache', 'Results Cache')
    
    # Create the results cache object.  Note, that if no match was found, 
    # this will be assigned a new UID.    
    results_cache = ResultsCache(results_cache_uid)
    
    # If there was a match...
    if results_cache_uid is not None:
        # Load the cache from the persistent storage.
        results_cache.load_from_data_store()
        
        # Return the cache state to the Celery worker.
        return results_cache
        
    # Else (no match)...
    else: 
        print('>>> ERROR: RESULTS CACHE NOT IN DATASTORE')
        return None  


def fetch_results_cache_entry(cache_id):
    # Reload the whole data_store (handle_dict), just in case a Celery worker 
    # has modified handle_dict, for example, by adding a new ResultsCache 
    # entry.
    # NOTE: It is possible this line can be removed if Celery never writes  
    # to handle_dict.
    sw.globalvars.data_store.load()
    
    # Load the latest results_cache from persistent store.
    results_cache.load_from_data_store()
    
    # Retrieve and return the results from the cache..
    return results_cache.retrieve(cache_id)


def put_results_cache_entry(cache_id, results, apptasks_call=False):
    global results_cache
    
    # If a Celery worker has made the call...
    if apptasks_call:
        # Load the latest ResultsCache from persistent storage.  It is likely 
        # to have changed because the webapp process added a new cache entry.
        results_cache = apptasks_load_results_cache()
        
        # If we have no cache, give an error.
        if not (cache_id in results_cache.cache_id_hashes.keys()):
            print('>>> WARNING: A NEW CACHE ENTRY IS BEING ADDED BY CELERY, WHICH IS POTENTIALLY UNSAFE.  YOU SHOULD HAVE THE WEBAPP CALL make_results_cache_entry(cache_id) FIRST TO AVOID THIS')
            
    else:      
        # Load the latest results_cache from persistent store.
        results_cache.load_from_data_store()
    
    # Reload the whole data_store (handle_dict), just in case a Celery worker 
    # has modified handle_dict, for example, by adding a new ResultsCache 
    # entry.
    # NOTE: It is possible this line can be removed if Celery never writes  
    # to handle_dict.    
    sw.globalvars.data_store.load()
    
    # Actually, store the results in the cache.
    results_cache.store(cache_id, results)


@RPC() 
def check_results_cache_entry(cache_id):
    print('Checking for cached results...')
    # Load the results from the cache and check if we got a result.
    results = fetch_results_cache_entry(cache_id)   
    return { 'found': (results is not None) }


# NOTE: This function should be called by the Optimizations FE pages before the 
# call is made to launch_task().  That is because we want to avoid the Celery 
# workers adding new cache entries through its own call to ResultsCache.store()
# because that is unsafe due to conflicts over the DataStore handle_dict.
@RPC()
def make_results_cache_entry(cache_id):
    # TODO: We might want to have a check here to see if this is a new entry 
    # in the cache, and if it isn't, just exit out, so the store doesn't 
    # overwrite the already-stored result.  However, this may not really be an 
    # issue because "Plot results" is disabled during the running of a task.
    results_cache.store(cache_id, None)

    
@RPC()
def delete_results_cache_entry(cache_id):
    results_cache.delete(cache_id)
    
    
@RPC() 
def plot_results_cache_entry(project_id, cache_id, plot_options, tool=None, plotyear=None, pops=None, cascade=None, dosave=True, plotbudget=False, calibration=False):
    print('Plotting cached results...')
    proj = load_project(project_id, raise_exception=True)

    # Load the results from the cache and check if we got a result.
    results = fetch_results_cache_entry(cache_id)
    if results is None:
        return { 'error': 'Failed to load plot results from cache' }
    
    output = make_plots(proj, results, tool=tool, year=plotyear, pops=pops, cascade=cascade, plot_options=plot_options, dosave=dosave, plot_budget=plotbudget, calibration=calibration)
    return output
    

@RPC(call_type='download')
def export_results(cache_id):
    print('Exporting results...')
    
    # Load the result from the cache and check if we got a result.
    result = fetch_results_cache_entry(cache_id)
    if result is None:
        return { 'error': 'Failed to load plot results from cache' }
    
#    if isinstance(result, ResultPlaceholder):
#        print('Getting actual result...')
#        result = result.get()
    
    dirname = sw.globalvars.downloads_dir.dir_path 
    file_name = '%s.xlsx' % result.name 
    full_file_name = os.path.join(dirname, file_name)
    result.export(full_file_name)
    print(">> export_results %s" % (full_file_name))
    return full_file_name # Return the filename  