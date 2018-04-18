from atomica.system import SystemSettings as SS
from atomica.structure_settings import FrameworkSettings as FS, DatabookSettings as DS
from atomica.system import applyToAllMethods, logUsage, AtomicaException
from atomica._version import __version__
from sciris.core import odict, today, gitinfo, objrepr, getdate, uuid


import numpy as np

class SemanticUnknownException(AtomicaException):
    def __init__(self, term, attribute = None, **kwargs):
        extra_message = ""
        if not attribute is None: extra_message = ", attribute '{0}',".format(attribute)
        message = "Term '{0}'{1} is not recognised by the project.".format(term, extra_message)
        return super().__init__(message, **kwargs)
    
def getQuantityTypeList(include_absolute = False, include_relative = False):
    quantity_types = []
    if include_absolute: quantity_types += [FS.QUANTITY_TYPE_NUMBER]
    if include_relative: quantity_types += [FS.QUANTITY_TYPE_PROBABILITY, FS.QUANTITY_TYPE_DURATION]
    return quantity_types
    
def convertQuantity(value, initial_type, final_type, set_size = None, dt = 1.0):
    """
    Converts a quantity from one type to another and applies a time conversion if requested.
    All values must be provided with respect to the project unit of time, e.g. a year.
    Note: Time conversion should only be applied to rate-based quantities, not state variables.
    """
    absolute_types = [FS.QUANTITY_TYPE_NUMBER]
    relative_types = [FS.QUANTITY_TYPE_FRACTION, FS.QUANTITY_TYPE_PROBABILITY, FS.QUANTITY_TYPE_DURATION]
    initial_class = SS.QUANTITY_TYPE_ABSOLUTE if initial_type in absolute_types else SS.QUANTITY_TYPE_RELATIVE
    final_class = SS.QUANTITY_TYPE_ABSOLUTE if final_type in absolute_types else SS.QUANTITY_TYPE_RELATIVE
    value = float(value)    # Safety conversion for type.
    
    if not initial_type in absolute_types + relative_types: 
        raise AtomicaException("An attempt to convert a quantity between types was made, "
                               "but initial type '{0}' was not recognised.".format(initial_type))
    if not final_type in absolute_types + relative_types:
        raise AtomicaException("An attempt to convert a quantity between types was made, "
                               "but final type '{0}' was not recognised.".format(final_type))
        
    # Convert the value of all input quantities to standardised 'absolute' or 'relative' format.
    if initial_type == FS.QUANTITY_TYPE_DURATION:
        value = 1.0 - np.exp(-1.0/value)
    
    # Convert between standard 'absolute' and 'relative' formats, if applicable.
    if not initial_class == final_class:
        if set_size is None:
            raise AtomicaException("An attempt to convert a quantity between absolute and relative types was made, "
                                   "but no set size was provided as the denominator for conversion.")
        if initial_class == SS.QUANTITY_TYPE_ABSOLUTE: value = value/set_size
        else: value = value*set_size
        
    # Convert value from standardised 'absolute' or 'relative' formats to that which is requested.
    if final_type == FS.QUANTITY_TYPE_DURATION:
        value = -1.0/np.log(1.0 - value)

    # Convert to the corresponding timestep value.
    if not dt == 1.0:
        if final_type == FS.QUANTITY_TYPE_DURATION:
            value /= dt     # Average duration before transition in number of timesteps.
        elif final_type == FS.QUANTITY_TYPE_PROBABILITY:
            value = 1 - (1 - value)**dt
        elif final_type in [FS.QUANTITY_TYPE_NUMBER, FS.QUANTITY_TYPE_FRACTION]:
            value *= dt
        else: raise AtomicaException("Time conversion for type '{0}' is not known.".format(final_type))
    
    return value
    

class TimeSeries(object):
    """ 
    A custom object for storing values associated with time points. 
    The values for each timepoint are listed in order as the 'keys' that represent the series.
    For example:
        self.keys = ["a","b","c"]
        self.values = {2010.0:[1,1001,-15],
                       2020.0:[2,2001,-50]}
    Note: The values structure contains special lists for assumptions and formats.
    """
    def __init__(self, keys = None, default_format = None):
        self.keys = keys
        self.key_id_map = dict()
        for id, key in enumerate(self.keys):
            self.key_id_map[key] = id
        self.values = {None:[None]*len(self.keys),
                       "format":[default_format]*len(self.keys)}

    def getValue(self, key, t = None):
        try: return self.values[t][self.key_id_map[key]]
        except: raise AtomicaException("Cannot locate value for '{0}' at time '{1}'.".format(key,t))

    def setValue(self, key, value, t = None):
        if not key in self.key_id_map: raise AtomicaException("TimeSeries object queried for value of nonexistent key '{0}'.".format(key))
        if t not in self.values:
            self.values[t] = [None]*len(self.keys)   
        self.values[t][self.key_id_map[key]] = value
        
    def getFormat(self, key):
        try: return self.values["format"][self.key_id_map[key]]
        except: raise AtomicaException("Cannot locate format for time series values of '{0}'.".format(key))

    def setFormat(self, key, value_format):
        if not key in self.key_id_map: raise AtomicaException("TimeSeries object queried for value of nonexistent key '{0}'.".format(key))
        self.values["format"][self.key_id_map[key]] = value_format

    def __repr__(self, **kwargs):
        return "<TimeSeries Object, Keys: " + self.keys.__repr__(**kwargs) + ", Values: " + self.values.__repr__(**kwargs) + ">"




@applyToAllMethods(logUsage)
class CoreProjectStructure(object):
    """ A base object that contains details relating to instantiated items of types defined in relevant settings classes. """
    
    def __init__(self, structure_key = None):
        """ Initialize the core project structure. """
        self.name = str()
        self.specs = odict()

        # Keep a dictionary linking any user-provided term with a reference to the appropriate specifications.
        self.semantics = odict()
        
        # Record what type of structure this is for specification initialization purposes.
        self.structure_key = structure_key

        self.initSpecs()
        
        # Standard metadata.
        self.uid = uuid()
        self.created = today()
        self.modified = today()
        self.version = __version__
        self.git_info = gitinfo()
        self.workbook_load_date = "N.A."

    def __repr__(self):
        output = objrepr(self)
        output += self.getMetadataString()
        output += "="*60 + "\n"
        return output
    
    def getMetadataString(self):
        meta =  "   Atomica version: %s\n"    % self.version
        meta += "      Date created: %s\n"    % getdate(self.created)
        meta += "     Date modified: %s\n"    % getdate(self.modified)
        meta += "   Workbook loaded: %s\n"    % getdate(self.workbook_load_date)
        meta += "        Git branch: %s\n"    % self.git_info['branch']
        meta += "          Git hash: %s\n"    % self.git_info['hash']
        meta += "               UID: %s\n"    % self.uid
        return meta

    def initSpecs(self):
        """ Initialize the uppermost layer of structure specifications (i.e. base item types) according to corresponding settings. """
        if not self.structure_key is None:
            item_type_specs = None
            if self.structure_key == SS.STRUCTURE_KEY_FRAMEWORK: item_type_specs = FS.ITEM_TYPE_SPECS
            elif self.structure_key == SS.STRUCTURE_KEY_DATA: item_type_specs = DS.ITEM_TYPE_SPECS
            if not item_type_specs is None:
                for item_type in item_type_specs:
                    if item_type_specs[item_type]["superitem_type"] is None: self.specs[item_type] = odict()

    def initItem(self, item_name, item_type, target_item_location):
        """
        Initialize the attribute structure relating to specifications for a new item within a target dictionary.
        Should not be called directly as it is part of item creation.
        """
        target_item_location[item_name] = odict()
        if not self.structure_key is None:
            item_type_specs = None
            if self.structure_key == SS.STRUCTURE_KEY_FRAMEWORK: item_type_specs = FS.ITEM_TYPE_SPECS
            elif self.structure_key == SS.STRUCTURE_KEY_DATA: item_type_specs = DS.ITEM_TYPE_SPECS
            if not item_type_specs is None:
                for attribute in item_type_specs[item_type]["attributes"]:
                    # Create space for all item attributes except 'name' as that is used as the key for specifications.
                    if attribute == "name": continue
                    content_type = None
                    if "content_type" in item_type_specs[item_type]["attributes"][attribute]:
                        content_type = item_type_specs[item_type]["attributes"][attribute]["content_type"]
                    # Set up a default value if available.
                    value = None
                    if (not content_type is None) and not content_type.default_value is None: 
                        value = self.enforceValue(value = content_type.default_value, content_type = content_type)
                    target_item_location[item_name][attribute] = value
                    # If the attribute itself references another item type in settings, prepare it as a container for corresponding items in specifications.
                    if "ref_item_type" in item_type_specs[item_type]["attributes"][attribute]:
                        target_item_location[item_name][attribute] = odict()
                    # If the content type for the attribute is marked as a list, instantiate that list.
                    elif (not content_type is None) and content_type.is_list:
                        target_item_location[item_name][attribute] = list()

    def createItem(self, item_name, item_type, superitem_type_name_pairs = None):
        """
        Instantiates item type in specs with item name as key, initializing its attribute structure as well.
        If the item is not top-level, a list of superitem type-name pairs must be provided to point to the intended item location in specs.
        """
        item_name = str(item_name)  # Hard-coded type-enforcement for name.
        # Move down the specs dictionary according to superitem type-name pair list.
        target_specs = self.specs
        depth = 0
        if superitem_type_name_pairs is None: superitem_type_name_pairs = []
        try:
            for pair in superitem_type_name_pairs:
                super_type = pair[0]
                super_name = pair[-1]
                if depth > 0: super_type += SS.DEFAULT_SUFFIX_PLURAL
                target_specs = target_specs[super_type][super_name]
                depth += 1
        except:
            raise AtomicaException("Item creation of type '{0}', name '{1}', was supplied the following chain of keys, "
                                  "which does not exist in specifications: '{2}'".format(item_type, item_name, "', '".join([elem for pair in superitem_type_name_pairs for elem in pair])))
        
        # Initialize item in specifications dictionary.
        # Subitem types are pluralized when used as keys in the specs structure.
        item_type_key = item_type
        if depth > 0: item_type_key += SS.DEFAULT_SUFFIX_PLURAL
        self.initItem(item_name = item_name, item_type = item_type, target_item_location = target_specs[item_type_key])

        # Flatten superitem type-name pairs into a flat list, if available, and extend it with the type and name of the current item.
        key_list = [elem for pair in superitem_type_name_pairs for elem in pair]
        if key_list is None: key_list = []
        key_list.extend([item_type_key, item_name])
        # Create a semantic link between the name of the item and its specifications.
        self.createSemantic(term = item_name, item_type = item_type, item_name = item_name, attribute = "name", key_list = key_list)
        
    def enforceValue(self, value, content_type):
        """ Enforces value type according to content specifications. """
        def identity(x): return x
        intermediate_type = identity
        # All content subclasses from ContentType, which may specify type enforcement for a value and whether it is a list.
        # If so, apply the enforcement.
        if not content_type is None:
            if not content_type.default_value is None:
                if content_type.is_list: value = [content_type.default_value if x is None else x for x in value]
                else: value = content_type.default_value if value is None else value
            if not content_type.enforce_type is None:
                if content_type.enforce_type == int: intermediate_type = float  # Handles str to int conversion.
                if content_type.is_list: value = [content_type.enforce_type(intermediate_type(x)) if not x is None else None for x in value]
                else: value = content_type.enforce_type(intermediate_type(value)) if not value is None else None
        return value
        
    def setSpecValue(self, term, attribute, value, subkey = None, content_type = None):
        if not content_type is None:
            try: value = self.enforceValue(value, content_type)
            except: raise AtomicaException("Attribute '{0}' for specification associated with term '{1}' "
                                           "has been assigned a value that cannot be enforced as type '{2}'. "
                                           "The value is: {3}".format(attribute, term, content_type.enforce_type, value))
        spec = self.getSpec(term)
        if not attribute in spec: raise SemanticUnknownException(term = term, attribute = attribute)
        if subkey is None: spec[attribute] = value
        else:
            #if not attribute in spec: spec[attribute] = dict()
            spec[attribute][subkey] = value
        if attribute in ["label"]:
            item_name = self.getSpecName(term)
            self.createSemantic(term = value, item_name = item_name, attribute = attribute)

    def appendSpecValue(self, term, attribute, value, subkey = None, content_type = None):
        """
        Creates a list for a specification attribute if currently nonexistent, then extends or appends it by a value.
        Attribute can be treated as a dictionary with key 'subkey'.
        """
        if not content_type is None:
            try: value = self.enforceValue(value, content_type)
            except: raise AtomicaException("Attribute '{0}' for specification associated with term '{1}' "
                                           "has been assigned a value that cannot be enforced as type '{2}'. "
                                           "The value is: {3}".format(attribute, term, content_type.enforce_type, value))
        spec = self.getSpec(term)
        if subkey is None: 
            try: spec[attribute].append(value)
            except: raise AtomicaException("Attribute '{0}' for specification associated with term '{1}' "
                                          "can neither be extended nor appended by value '{2}'.".format(attribute, term, value))
        else:
            if not subkey in spec[attribute]: spec[attribute][subkey] = list()
            try: spec[attribute][subkey].append(value)
            except: raise AtomicaException("Attribute '{0}', key '{1}', for specification associated with term '{2}' "
                                          "can neither be extended nor appended by value '{3}'.".format(attribute, subkey, term, value))

    def getSpecName(self, term):
        """ Returns the name corresponding to a provided term. """
        return self.getSemanticValue(term = term, attribute = "name")

    def getSpecType(self, term):
        """
        Returns the type of item that this specification belongs to.
        Item type, like the referencing key list, is stored only in semantic structures keyed with item names.
        """
        return self.getSemanticValue(term = self.getSpecName(term), attribute = "type")

    def getSpecValue(self, term, attribute):
        """ Returns the value of an attribute for a provided term. """
        spec = self.getSpec(term = term)
        try: return spec[attribute]
        except: raise AtomicaException("The item corresponding to term '{0}' does not have attribute '{1}' to query value of.".format(term, attribute))

    def getSpec(self, term):
        """ Returns the item specification association with a term. """
        semantic = self.getSemantic(self.getSpecName(term))
        try:
            key_list = semantic["key_list"]
            spec = self.specs
            for key in key_list:
                spec = spec[key]
            return spec
        except: raise AtomicaException("The item corresponding to term '{0}' could not be located in the semantics dictionary.".format(term))

    def createSemantic(self, term, item_name, attribute, item_type = None, key_list = None):
        """
        Creates a semantic link from a term to an item, noting what item attribute has the term as its value.
        Names as terms are particularly important as they also link to item type and the list of keys to access item specifications.
        """
        if term in self.semantics:
            other_attribute = self.semantics[term]["attribute"]
            other_name = self.semantics[term]["name"]
            raise AtomicaException("The term '{0}' has been defined previously as the '{1}' of item '{2}'. "
                                  "Duplicate terms are not allowed.".format(term, other_attribute, other_name))
        else:
            self.semantics[term] = {"name":item_name, "attribute":attribute}
            if attribute == "name":
                if not term == item_name:
                    raise AtomicaException("Term '{0}' has been declared as the name of item with name '{1}'. "
                                          "This is a contradiction.".format(term, item_name))
                if item_type is None:
                    raise AtomicaException("Term '{0}' is an item name. It must be associated with an item type in a semantics "
                                          "dictionary for quick-reference purposes.".format(term))
                else: self.semantics[term]["type"] = item_type
                if key_list is None:
                    raise AtomicaException("Term '{0}' is an item name. It must be associated with a key list in a semantics "
                                          "dictionary that points to where the item sits in a specifications dictionary.".format(term))
                else: self.semantics[term]["key_list"] = key_list

    def getSemantic(self, term):
        """ Returns a dictionary of item name, attribute and possibly item type plus spec-referencing key list corresponding to a term. """
        try: return self.semantics[term]
        except: raise SemanticUnknownException(term = term)

    def getSemanticValue(self, term, attribute):
        """ Convenience function to return the value of a semantic attribute, such as 'name', 'attribute', 'type' and 'key_list'. """
        semantic = self.getSemantic(term)
        try: return semantic[attribute]
        except: raise SemanticUnknownException(term = term, attribute = attribute)

    def completeSpecs(self, **kwargs):
        """
        An overloaded method for completing specifications that is called at the end of a file import.
        This delay is because some specifications rely on other definitions and values existing in the specs dictionary.
        """
        pass
