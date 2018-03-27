from atomica.system import SystemSettings as SS
from atomica.structure_settings import FrameworkSettings as FS
from atomica.structure_settings import DatabookSettings as DS
from atomica.system import applyToAllMethods, logUsage, OptimaException

from atomica.utils import odict

#from collections import OrderedDict

class SemanticUnknownException(OptimaException):
    def __init__(self, term, attribute = None, **kwargs):
        extra_message = ""
        if not attribute is None: extra_message = ", attribute {0},".format(attribute)
        message = "Term '{0}'{1} is not recognised by the project.".format(term, extra_message)
        return super().__init__(message, **kwargs)

class TimeSeries(object):
    """ A custom object for storing values associated with time points. """
    def __init__(self, keys = None):
        self.keys = ["t"]
        self.values = list()

        self.key_id_map = {"t":0}
        if not keys is None:
            for id, key in enumerate(keys):
                if key == "t": raise OptimaException("The symbol 't' is already a reserved key for a TimeSeries object. "
                                                     "It cannot be in the following list provided during construction: '{0}'".format("', '".join(keys)))
                self.keys.append(key)
                self.key_id_map[key] = id + 1

        # Make an assumption tuple for the object, associated with a 't' value of 'None'.
        self.values.append([None]*len(self.key_id_map))
        self.t_id_map = {None:0}

    def getValue(self, key, t = None):
        try: return self.values[self.t_id_map[t]][self.key_id_map[key]]
        except: raise OptimaException("Cannot locate value for '{0}' at time '{1}'.".format(key,t))

    def setValue(self, key, value, t = None):
        if not key in self.key_id_map: raise OptimaException("TimeSeries object queried for value of nonexistent key '{0}'.".format(key))
        if t not in self.t_id_map:
            self.values.append([t]+[None]*(len(self.key_id_map)-1))
            self.t_id_map[t] = len(self.t_id_map)    
        self.values[self.t_id_map[t]][self.key_id_map[key]] = value

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
        """ Initialize the attribute structure relating to specifications for a new item within a target dictionary. """
        target_item_location[item_name] = odict()
        if not self.structure_key is None:
            item_type_specs = None
            if self.structure_key == SS.STRUCTURE_KEY_FRAMEWORK: item_type_specs = FS.ITEM_TYPE_SPECS
            elif self.structure_key == SS.STRUCTURE_KEY_DATA: item_type_specs = DS.ITEM_TYPE_SPECS
            if not item_type_specs is None:
                for attribute in item_type_specs[item_type]["attributes"]:
                    # Create space for all item attributes except 'name' as that is used as the key for specifications.
                    if attribute == "name": continue
                    target_item_location[item_name][attribute] = None
                    try: content_type = item_type_specs[item_type]["attributes"][attribute]["content_type"]
                    except: content_type = None
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
            raise OptimaException("Item creation of type '{0}', name '{1}', was supplied the following chain of keys, "
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
        
    def setSpecAttribute(self, term, attribute, value, subkey = None):
        spec = self.getSpec(term)
        if not attribute in spec: raise SemanticUnknownException(term = term, attribute = attribute)
        if subkey is None: spec[attribute] = value
        else:
            #if not attribute in spec: spec[attribute] = dict()
            spec[attribute][subkey] = value
        if attribute in ["label"]:
            item_name = self.getSpecName(term)
            self.createSemantic(term = value, item_name = item_name, attribute = attribute)

    def appendSpecAttribute(self, term, attribute, value, subkey = None):
        """
        Creates a list for a specification attribute if currently nonexistent, then extends or appends it by a value.
        Attribute can be treated as a dictionary with key 'subkey'.
        """
        spec = self.getSpec(term)
        if subkey is None: 
            try: spec[attribute].append(value)
            except: raise OptimaException("Attribute '{0}' for specification associated with term '{1}' "
                                          "can neither be extended nor appended by value '{2}'.".format(attribute, term, value))
        else:
            if not subkey in spec[attribute]: spec[attribute][subkey] = list()
            try: spec[attribute][subkey].append(value)
            except: raise OptimaException("Attribute '{0}', key '{1}', for specification associated with term '{2}' "
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

    def getSpec(self, term):
        """ Returns the item specification association with a term. """
        semantic = self.getSemantic(self.getSpecName(term))
        try:
            key_list = semantic["key_list"]
            spec = self.specs
            for key in key_list:
                spec = spec[key]
            return spec
        except: raise OptimaException("The item corresponding to term '{0}' could not be located in the semantics dictionary.".format(term))

    def createSemantic(self, term, item_name, attribute, item_type = None, key_list = None):
        """
        Creates a semantic link from a term to an item, noting what item attribute has the term as its value.
        Names as terms are particularly important as they also link to item type and the list of keys to access item specifications.
        """
        if term in self.semantics:
            other_attribute = self.semantics[term]["attribute"]
            other_name = self.semantics[term]["name"]
            raise OptimaException("The term '{0}' has been defined previously as the '{1}' of item '{2}'. "
                                  "Duplicate terms are not allowed.".format(term, other_attribute, other_name))
        else:
            self.semantics[term] = {"name":item_name, "attribute":attribute}
            if attribute == "name":
                if not term == item_name:
                    raise OptimaException("Term '{0}' has been declared as the name of item with name '{1}'. "
                                          "This is a contradiction.".format(term, item_name))
                if item_type is None:
                    raise OptimaException("Term '{0}' is an item name. It must be associated with an item type in a semantics "
                                          "dictionary for quick-reference purposes.".format(term))
                else: self.semantics[term]["type"] = item_type
                if key_list is None:
                    raise OptimaException("Term '{0}' is an item name. It must be associated with a key list in a semantics "
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

    def completeSpecs(self):
        """
        An overloaded method for completing specifications that is called at the end of a file import.
        This delay is because some specifications rely on other definitions and values existing in the specs dictionary.
        """
        pass
