'''
Classes for handling projects as Sciris objects

Version: 2018jun04 by cliffk
'''

import sciris.scirisobjects as sobj
import sciris.datastore as ds
import nutrition as on
import sciris.user as user
import sciris.core as sc
import os


#
# Globals
#

# The ProjectCollection object for all of the app's projects.  Gets 
# initialized by and loaded by init_projects().
proj_collection = None


#
# Classes
#

class ProjectSO(sobj.ScirisObject):
    """
    A ScirisObject-wrapped Optima Nutrition Project object.
    
    Methods:
        __init__(proj: Project, owner_uid: UUID, uid: UUID [None]): 
            void -- constructor
        load_from_copy(other_object): void -- assuming other_object is another 
            object of our type, copy its contents to us (calls the 
            ScirisObject superclass version of this method also)   
        show(): void -- print the contents of the object
        get_user_front_end_repr(): dict -- get a JSON-friendly dictionary 
            representation of the object state the front-end uses for non-
            admin purposes  
        save_as_file(load_dir: str): str -- given a load dictionary, save the 
            project in a file there and return the file name
                    
    Attributes:
        proj (Project) -- the actual Project object being wrapped
        owner_uid (UUID) -- the UID of the User that owns the Project
        
    Usage:
        >>> my_project = ProjectSO(proj, owner_uid)                      
    """
    
    def  __init__(self, proj, owner_uid, uid=None):
        # NOTE: uid argument is ignored but kept here to not mess up
        # inheritance.
        
        # Make sure the owner UID argument is a valid UUID, converting a hex 
        # text to a UUID object, if needed.        
        valid_uuid = sc.uuid(owner_uid)
        
        # If we have a valid UUID...
        if valid_uuid is not None:       
            # Set superclass parameters.
            super(ProjectSO, self).__init__(proj.uid)
                                   
            # Set the project to the Optima Project that is passed in.
            self.proj = proj
            
            # Set the owner (User) UID.
            self.owner_uid = valid_uuid
        
    def load_from_copy(self, other_object):
        if type(other_object) == type(self):
            # Do the superclass copying.
            super(ProjectSO, self).load_from_copy(other_object)
            
            # Copy the Project object itself.
            self.proj = sc.dcp(other_object.proj)
            
            # Copy the owner UID.
            self.owner_uid = other_object.owner_uid
                
    def show(self):
        # Show superclass attributes.
        super(ProjectSO, self).show()  
        
        # Show the Optima defined display text for the project.
        print '---------------------'
        print 'Owner User UID: %s' % self.owner_uid.hex
        print 'Project Name: %s' % self.proj.name
        print 'Creation Time: %s' % self.proj.created
        print 'Update Time: %s' % self.proj.modified
            
    def get_user_front_end_repr(self):
        obj_info = {
            'project': {
                'id': self.uid,
                'name': self.proj.name,
                'userId': self.owner_uid,
                'creationTime': self.proj.created,
                'updatedTime': self.proj.modified     
            }
        }
        return obj_info
    
    def save_as_file(self, load_dir):
        # Create a filename containing the project name followed by a .prj 
        # suffix.
        file_name = '%s.prj' % self.proj.name
        
        # Generate the full file name with path.
        full_file_name = '%s%s%s' % (load_dir, os.sep, file_name)   
     
        # Write the object to a Gzip string pickle file.
        ds.object_to_gzip_string_pickle_file(full_file_name, self.proj)
        
        # Return the filename (not the full one).
        return self.proj.name + ".prj"
    
        
class ProjectCollection(sobj.ScirisCollection):
    """
    A collection of Projects.
    
    Methods:
        __init__(uid: UUID [None], type_prefix: str ['projectscoll'], 
            file_suffix: str ['.pc'], 
            instance_label: str ['Projects Collection']): void -- constructor  
        get_user_front_end_repr(owner_uid: UUID): list -- return a list of dicts 
            containing JSON-friendly project contents for each project that 
            is owned by the specified user UID
        get_project_entries_by_user(owner_uid: UUID): list -- return the ProjectSOs 
            that match the owning User UID in a list
        
    Usage:
        >>> proj_collection = ProjectCollection(uuid.UUID('12345678123456781234567812345678'))                      
    """
    
    def __init__(self, uid, type_prefix='projectscoll', file_suffix='.pc', 
        instance_label='Projects Collection'):
        # Set superclass parameters.
        super(ProjectCollection, self).__init__(uid, type_prefix, file_suffix, 
             instance_label)
            
    def get_user_front_end_repr(self, owner_uid):
        # Make sure the argument is a valid UUID, converting a hex text to a
        # UUID object, if needed.        
        valid_uuid = sc.uuid(owner_uid)
        
        # If we have a valid UUID...
        if valid_uuid is not None:               
            # Get dictionaries for each Project in the dictionary.
            projects_info = [self.obj_dict[key].get_user_front_end_repr() \
                for key in self.obj_dict \
                if self.obj_dict[key].owner_uid == valid_uuid]
            return projects_info
        
        # Otherwise, return an empty list.
        else:
            return []
        
    def get_project_entries_by_user(self, owner_uid):
        # Make sure the argument is a valid UUID, converting a hex text to a
        # UUID object, if needed.        
        valid_uuid = sc.uuid(owner_uid)
        
        # If we have a valid UUID...
        if valid_uuid is not None:    
            # Get ProjectSO entries for each Project in the dictionary.
            project_entries = [self.obj_dict[key] \
                for key in self.obj_dict \
                if self.obj_dict[key].owner_uid == valid_uuid]
            return project_entries
        
        # Otherwise, return an empty list.
        else:
            return []


#
# Initialization function
#

def init_projects(app):
    global proj_collection  # need this to allow modification within the module
    
    # Look for an existing ProjectCollection.
    proj_collection_uid = ds.data_store.get_uid_from_instance('projectscoll', 
        'Projects Collection')
    
    # Create the projects collection object.  Note, that if no match was found, 
    # this will be assigned a new UID.    
    proj_collection = ProjectCollection(proj_collection_uid)
    
    # If there was a match...
    if proj_collection_uid is not None:
        if app.config['LOGGING_MODE'] == 'FULL':
            print '>> Loading ProjectCollection from the DataStore.'
        proj_collection.load_from_data_store() 
    
    # Else (no match)...
    else:
        # Load the data path holding the Excel files.
        data_path = on.ONpath('data')
    
        if app.config['LOGGING_MODE'] == 'FULL':
            print('>> Creating a new ProjectCollection.') 
        proj_collection.add_to_data_store()
        
        if app.config['LOGGING_MODE'] == 'FULL':
            print('>> Starting a demo project.')
        proj = on.Project(name='Bangladesh 1')  
        projSO = ProjectSO(proj, user.get_scirisdemo_user())
        proj_collection.add_object(projSO)
        
    if app.config['LOGGING_MODE'] == 'FULL':
        # Show what's in the ProjectCollection.    
        proj_collection.show()