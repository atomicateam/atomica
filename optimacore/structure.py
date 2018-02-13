from optimacore.system import SystemSettings as SS

from optimacore.system import applyToAllMethods, logUsage, accepts, OptimaException

from collections import OrderedDict

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
        if item_type not in self.specs: target_specs[item_type] = OrderedDict()
        target_specs[item_type][item_name] = dict()

        key_list = [elem for pair in superitem_type_name_pairs for elem in pair]
        if key_list is None: key_list = []
        key_list.extend([item_type,item_name])
        self.semantics[item_name] = {"item_name":item_name, "attribute":"name", "key_list":key_list}
        #import pprint
        #print(item_type)
        #print(item_name)
        #pprint.pprint(self.specs)
        #pprint.pprint(self.semantics)

    def getSpec(self, term):
        try:
            key_list = self.semantics[term]["key_list"]
            spec = self.specs
            for key in key_list:
                spec = spec[key]
            return spec
        except:
            raise OptimaException("Specifications for term '{0}' cannot be found.".format(term))


    @accepts(str)
    def addTermToSemantics(self, term):
        """ Insert a user-provided term into the semantics dictionary maintained by the project framework and ensure it is unique. """
        if term in self.semantics:
            error_message = ("Optima Core notes a term '{0}' that was defined previously. "
                             "Duplicate terms are not allowed.".format(term))
            raise OptimaException(error_message)
        self.semantics[term] = dict()   # TODO: UPDATE THE VALUE WITH REFERENCES ONCE THE SPECS DICT IS COMPLETE.

    def completeSpecs(self):
        """
        An overloaded method for completing specifications that is called at the end of a file import.
        This delay is because some specifications rely on other definitions and values existing in the specs dictionary.
        """
        pass
