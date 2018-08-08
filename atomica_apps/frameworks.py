'''
Classes for handling frameworks as Sciris objects

Version: 2018jun04 by cliffk
'''

import os
import atomica.ui as au
import sciris.core as sc
import sciris.web as sw
import sciris.weblib.user as user
import sciris.weblib.datastore as ds
import sciris.corelib.fileio as fileio

#
# Globals
#

# The frameworkCollection object for all of the app's frameworks.  Gets 
# initialized by and loaded by init_frameworks().
frame_collection = None


#
# Classes
#

class FrameworkSO(sw.ScirisObject):
    """
    A ScirisObject-wrapped Framework object.
    
    Methods:
        __init__(frame: Framework, owner_uid: UUID, uid: UUID [None]): 
            void -- constructor
        load_from_copy(other_object): void -- assuming other_object is another 
            object of our type, copy its contents to us (calls the 
            ScirisObject superclass version of this method also)   
        show(): void -- print the contents of the object
        get_user_front_end_repr(): dict -- get a JSON-friendly dictionary 
            representation of the object state the front-end uses for non-
            admin purposes  
        save_as_file(load_dir: str): str -- given a load dictionary, save the 
            framework in a file there and return the file name
                    
    Attributes:
        frame (Framework) -- the actual Framework object being wrapped
        owner_uid (UUID) -- the UID of the User that owns the Framework
        
    Usage:
        >>> my_framework = FrameworkSO(frame, owner_uid)                      
    """
    
    def  __init__(self, frame, owner_uid, uid=None):
        # NOTE: uid argument is ignored but kept here to not mess up
        # inheritance.
        
        # Make sure the owner UID argument is a valid UUID, converting a hex 
        # text to a UUID object, if needed.        
        valid_uuid = sc.uuid(owner_uid)
        
        # If we have a valid UUID...
        if valid_uuid is not None:       
            # Set superclass parameters.
            super(FrameworkSO, self).__init__(frame.uid, type_prefix='framework', 
                 file_suffix='.frw', instance_label=frame.name)
                                   
            # Set the framework to the Framework that is passed in.
            self.frame = frame
            
            # Set the owner (User) UID.
            self.owner_uid = valid_uuid
        
    def load_from_copy(self, other_object):
        if type(other_object) == type(self):
            # Do the superclass copying.
            super(FrameworkSO, self).load_from_copy(other_object)
            
            # Copy the Framework object itself.
            self.frame = sc.dcp(other_object.frame)
            
            # Copy the owner UID.
            self.owner_uid = other_object.owner_uid
                
    def show(self):
        # Show superclass attributes.
        super(FrameworkSO, self).show()  
        
        # Show the defined display text for the framework.
        print '---------------------'
        print 'Owner User UID: %s' % self.owner_uid.hex
        print 'Framework Name: %s' % self.frame.name
        print 'Creation Time: %s' % self.frame.created
        print 'Update Time: %s' % self.frame.modified
            
    def get_user_front_end_repr(self):
        obj_info = {
            'framework': {
                'id': self.uid,
                'name': self.frame.name,
                'userId': self.owner_uid,
                'creationTime': self.frame.created,
                'updatedTime': self.frame.modified     
            }
        }
        return obj_info
    
    def save_as_file(self, load_dir):
        # Create a filename containing the framework name followed by a .frw 
        # suffix.
        file_name = '%s.frw' % self.frame.name
        
        # Generate the full file name with path.
        full_file_name = '%s%s%s' % (load_dir, os.sep, file_name)   
     
        # Write the object to a Gzip string pickle file.
        fileio.object_to_gzip_string_pickle_file(full_file_name, self.frame)
        
        # Return the filename (not the full one).
        return self.frame.name + ".frw"
    
        
class FrameworkCollection(sw.ScirisCollection):
    """
    A collection of Frameworks.
    
    Methods:
        __init__(uid: UUID [None], type_prefix: str ['frameworkscoll'], 
            file_suffix: str ['.pc'], 
            instance_label: str ['Frameworks Collection']): void -- constructor  
        get_user_front_end_repr(owner_uid: UUID): list -- return a list of dicts 
            containing JSON-friendly framework contents for each framework that 
            is owned by the specified user UID
        get_framework_entries_by_user(owner_uid: UUID): list -- return the FrameworkSOs 
            that match the owning User UID in a list
        
    Usage:
        >>> frame_collection = FrameworkCollection(uuid.UUID('12345678123456781234567812345678'))                      
    """
    
    def __init__(self, uid, type_prefix='frameworkscoll', file_suffix='.fc', 
        instance_label='Frameworks Collection'):
        # Set superclass parameters.
        super(FrameworkCollection, self).__init__(uid, type_prefix, file_suffix, 
             instance_label, objs_within_coll=False)
            
    def get_user_front_end_repr(self, owner_uid):
        # Make sure the argument is a valid UUID, converting a hex text to a
        # UUID object, if needed.        
        valid_uuid = sc.uuid(owner_uid)
        
        # If we have a valid UUID...
        if valid_uuid is not None:    
            # If we are storing things inside the obj_dict...
            if self.objs_within_coll: 
                # Get dictionaries for each Framework in the dictionary.
                frameworks_info = [self.obj_dict[key].get_user_front_end_repr() \
                    for key in self.obj_dict \
                    if self.obj_dict[key].owner_uid == valid_uuid]
                return frameworks_info
            
            # Otherwise, we are using the UUID set.
            else:
                frameworks_info = []
                for uid in self.ds_uuid_set:
                    obj = ds.data_store.retrieve(uid)
                    if obj.owner_uid == valid_uuid:
                        frameworks_info.append(obj.get_user_front_end_repr())
                return frameworks_info
            
        # Otherwise, return an empty list.
        else:
            return []
        
    def get_framework_entries_by_user(self, owner_uid):
        # Make sure the argument is a valid UUID, converting a hex text to a
        # UUID object, if needed.        
        valid_uuid = sc.uuid(owner_uid)
        
        # If we have a valid UUID...
        if valid_uuid is not None:    
            # If we are storing things inside the obj_dict...
            if self.objs_within_coll:             
                # Get FrameworkSO entries for each Framework in the dictionary.
                framework_entries = [self.obj_dict[key] \
                    for key in self.obj_dict \
                    if self.obj_dict[key].owner_uid == valid_uuid]
                return framework_entries
            
            # Otherwise, we are using the UUID set.
            else:
                framework_entries = []
                for uid in self.ds_uuid_set:
                    obj = ds.data_store.retrieve(uid)
                    if obj.owner_uid == valid_uuid:
                        framework_entries.append(obj)
                return framework_entries
            
        # Otherwise, return an empty list.
        else:
            return []


#
# Initialization function
#

def init_frameworks(app):
    global frame_collection  # need this to allow modification within the module
    
    # Look for an existing FrameworkCollection.
    frame_collection_uid = ds.data_store.get_uid_from_instance('frameworkscoll', 
        'Frameworks Collection')
    
    # Create the frameworks collection object.  Note, that if no match was found, 
    # this will be assigned a new UID.    
    frame_collection = FrameworkCollection(frame_collection_uid)
    
    # If there was a match...
    if frame_collection_uid is not None:
        if app.config['LOGGING_MODE'] == 'FULL':
            print '>> Loading FrameworkCollection from the DataStore.'
        frame_collection.load_from_data_store() 
    
    # Else (no match)...
    else:
        # Load the data path holding the Excel files.
        #data_path = on.ONpath('data')
    
        if app.config['LOGGING_MODE'] == 'FULL':
            print('>> Creating a new FrameworkCollection.') 
        frame_collection.add_to_data_store()
        
        if app.config['LOGGING_MODE'] == 'FULL':
            print('>> Starting a demo framework.')
        frame = au.ProjectFramework(name='Test 1')  
        frameSO = FrameworkSO(frame, user.get_scirisdemo_user())
        frame_collection.add_object(frameSO)
        
    if app.config['LOGGING_MODE'] == 'FULL':
        # Show what's in the FrameworkCollection.    
        frame_collection.show()
