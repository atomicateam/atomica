from optimacore.system import SystemSettings as SS

from optimacore.system import applyToAllMethods, logUsage, accepts, OptimaException

from collections import OrderedDict

class SemanticUnknownException(OptimaException):
    def __init__(self, term, attribute = None, **kwargs):
        extra_message = ""
        if not attribute is None: extra_message = ", attribute {0},".format(attribute)
        message = "Term '{0}'{1} is not recognised by the project.".format(term, extra_message)
        return super().__init__(message, **kwargs)

@applyToAllMethods(logUsage)
class CoreProjectStructure(object):
    """ A base object that contains details relating to instantiated items of types defined in relevant settings classes. """
    
    def __init__(self):
        """ Initialize the core project structure. """
        self.name = str()
        self.specs = dict()
        
        # Keep a dictionary linking any user-provided term with a reference to the appropriate specifications.
        self.semantics = dict()

    def createItem(self, item_name, item_type, superitem_type_name_pairs = None):
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
        if depth > 0: item_type += SS.DEFAULT_SUFFIX_PLURAL
        if item_type not in target_specs: target_specs[item_type] = OrderedDict()
        target_specs[item_type][item_name] = dict()

        key_list = [elem for pair in superitem_type_name_pairs for elem in pair]
        if key_list is None: key_list = []
        key_list.extend([item_type,item_name])
        self.createSemantic(term = item_name, item_type = item_type, item_name = item_name, attribute = "name", key_list = key_list)
        
    def addSpecAttribute(self, term, attribute, value, subkey = None):
        spec = self.getSpec(term)
        if subkey is None: spec[attribute] = value
        else:
            if not attribute in spec: spec[attribute] = dict()
            spec[attribute][subkey] = value
        if attribute in ["label"]:
            item_name = self.getSpecName(term)
            self.createSemantic(term = value, item_name = item_name, attribute = attribute)

    def extendSpecAttribute(self, term, attribute, value, subkey = None):
        """
        Creates a list for a specification attribute if currently nonexistent, then extends or appends it by a value.
        Attribute can be treated as a dictionary with key 'subkey'.
        """
        spec = self.getSpec(term)
        if subkey is None: 
            if attribute not in spec: spec[attribute] = []
            try: spec[attribute].extend(value)
            except:
                try: spec[attribute].append(value)
                except: raise OptimaException("Attribute '{0}' for specification associated with term '{1}' "
                                              "can neither be extended nor appended by value '{2}'.".format(attribute, term, value))
        else:
            if not attribute in spec: spec[attribute] = dict()
            if not subkey in spec[attribute]: spec[attribute][subkey] = []
            try: spec[attribute][subkey].extend(value)
            except:
                try: spec[attribute][subkey].append(value)
                except: raise OptimaException("Attribute '{0}', key '{1}', for specification associated with term '{2}' "
                                              "can neither be extended nor appended by value '{3}'.".format(attribute, subkey, term, value))


    def getSpecName(self, term):
        return self.getSemanticValue(term = term, attribute = "name")

    def getSpecType(self, term):
        """
        Return the type of item that this specification belongs to.
        Item type, like the referencing key list, is stored only in semantic structures keyed with item names.
        """
        return self.getSemanticValue(term = self.getSpecName(term), attribute = "type")

    def getSpec(self, term):
        semantic = self.getSemantic(self.getSpecName(term))
        try:
            key_list = semantic["key_list"]
            spec = self.specs
            for key in key_list:
                spec = spec[key]
            return spec
        except: raise OptimaException("The item corresponding to term '{0}' could not be located in the semantics dictionary.".format(term))

    def createSemantic(self, term, item_name, attribute, item_type = None, key_list = None):
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
        try: return self.semantics[term]
        except: raise SemanticUnknownException(term = term)

    def getSemanticValue(self, term, attribute):
        semantic = self.getSemantic(term)
        try: return semantic[attribute]
        except: raise SemanticUnknownException(term = term, attribute = attribute)

    def completeSpecs(self):
        """
        An overloaded method for completing specifications that is called at the end of a file import.
        This delay is because some specifications rely on other definitions and values existing in the specs dictionary.
        """
        pass
