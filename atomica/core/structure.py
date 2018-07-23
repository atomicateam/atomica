from .system import SystemSettings as SS
from .structure_settings import FrameworkSettings as FS, DataSettings as DS
from .system import apply_to_all_methods, log_usage, AtomicaException
from .version import version
from bisect import bisect
import sciris.core as sc
import numpy as np


class SemanticUnknownException(AtomicaException):
    def __init__(self, term, attribute=None, **kwargs):
        extra_message = ""
        if attribute is not None:
            extra_message = ", attribute '{0}',".format(attribute)
        message = "Term '{0}'{1} is not recognised by the project.".format(term, extra_message)
        super(SemanticUnknownException, self).__init__(message, **kwargs)


def get_quantity_type_list(include_absolute=False, include_relative=False, include_special=False):
    quantity_types = []
    if include_absolute:
        quantity_types += [FS.QUANTITY_TYPE_NUMBER]
    if include_relative:
        quantity_types += [FS.QUANTITY_TYPE_PROBABILITY, FS.QUANTITY_TYPE_DURATION]
    if include_special:
        quantity_types += [FS.QUANTITY_TYPE_PROPORTION]
    return quantity_types


# def convert_quantity(value, initial_type, final_type, set_size=None, dt=1.0):
#     """
#     Converts a quantity from one type to another and applies a time conversion if requested.
#     All values must be provided with respect to the project unit of time, e.g. a year.
#     Note: Time conversion should only be applied to rate-based quantities, not state variables.
#     """
#     absolute_types = [FS.QUANTITY_TYPE_NUMBER]
#     relative_types = [FS.QUANTITY_TYPE_FRACTION, FS.QUANTITY_TYPE_PROBABILITY, FS.QUANTITY_TYPE_DURATION]
#     initial_class = SS.QUANTITY_TYPE_ABSOLUTE if initial_type in absolute_types else SS.QUANTITY_TYPE_RELATIVE
#     final_class = SS.QUANTITY_TYPE_ABSOLUTE if final_type in absolute_types else SS.QUANTITY_TYPE_RELATIVE
#     value = float(value)  # Safety conversion for type.
#
#     if initial_type not in absolute_types + relative_types:
#         raise AtomicaException("An attempt to convert a quantity between types was made, "
#                                "but initial type '{0}' was not recognised.".format(initial_type))
#     if final_type not in absolute_types + relative_types:
#         raise AtomicaException("An attempt to convert a quantity between types was made, "
#                                "but final type '{0}' was not recognised.".format(final_type))
#
#     # Convert the value of all input quantities to standardised 'absolute' or 'relative' format.
#     if initial_type == FS.QUANTITY_TYPE_DURATION:
#         value = 1.0 - np.exp(-1.0 / value)
#
#     # Convert between standard 'absolute' and 'relative' formats, if applicable.
#     if not initial_class == final_class:
#         if set_size is None:
#             raise AtomicaException("An attempt to convert a quantity between absolute and relative types was made, "
#                                    "but no set size was provided as the denominator for conversion.")
#         if initial_class == SS.QUANTITY_TYPE_ABSOLUTE:
#             value = value / set_size
#         else:
#             value = value * set_size
#
#     # Convert value from standardised 'absolute' or 'relative' formats to that which is requested.
#     if final_type == FS.QUANTITY_TYPE_DURATION:
#         value = -1.0 / np.log(1.0 - value)
#
#     # Convert to the corresponding timestep value.
#     if not dt == 1.0:
#         if final_type == FS.QUANTITY_TYPE_DURATION:
#             value /= dt  # Average duration before transition in number of timesteps.
#         elif final_type == FS.QUANTITY_TYPE_PROBABILITY:
#             value = 1 - (1 - value) ** dt
#         elif final_type in [FS.QUANTITY_TYPE_NUMBER, FS.QUANTITY_TYPE_FRACTION]:
#             value *= dt
#         else:
#             raise AtomicaException("Time conversion for type '{0}' is not known.".format(final_type))
#
#     return value


class TimeSeries(object):
    def __init__(self, t=None, vals=None, format=None, units=None):

        t = t if t is not None else list()
        vals = vals if vals is not None else list()

        assert len(t) == len(vals)

        self.t = []
        self.vals = []
        self.format = format # TODO - what's the difference between format and units?!
        self.units = units
        self.assumption = None

        for tx, vx in zip(t, vals):
            self.insert(tx, vx)

    @property
    def has_data(self):
        # Returns true if any time-specific data has been entered (not just an assumption)
        return len(self.t) > 0

    def insert(self, t, v):
        # Insert value v at time t maintaining sort order
        # To set the assumption, set t=None
        if t is None:
            self.assumption = v
        elif t in self.t:
            idx = self.t.index(t)
            self.vals[idx] = v
        else:
            idx = bisect(self.t, t)
            self.t.insert(idx, t)
            self.vals.insert(idx, v)

    def get(self, t):
        # To get the assumption, set t=None
        if t is None or len(self.t) == 0:
            return self.assumption
        elif t in self.t:
            return self.vals[self.t.index(t)]
        else:
            raise AtomicaException('Item not found')

    def get_arrays(self):
        if len(self.t) == 0:
            t = np.array([np.nan])
            v = np.array([self.assumption])
        else:
            t = np.array(self.t)
            v = np.array(self.vals)
        return t, v

    def remove(self, t):
        # To remove the assumption, set t=None
        if t is None:
            self.assumption = None
        elif t in self.t:
            idx = self.t.index(t)
            del self.t[idx]
            del self.vals[idx]
        else:
            raise AtomicaException('Item not found')

            # Todo - unit conversion (should it return a new instance?)
            # Todo - interpolation/expansion


@apply_to_all_methods(log_usage)
class CoreProjectStructure(object):
    """ Base object that contains details for instantiated items of types defined in relevant settings classes. """

    def __init__(self, name=None, structure_key=None):
        """ Initialize the core project structure. """
        if name is None:
            self.name = str()
        else:
            self.name = name
        self.specs = sc.odict()

        # Keep a dictionary linking any user-provided term with a reference to the appropriate specifications.
        self.semantics = sc.odict()

        # Record what type of structure this is for specification initialization purposes.
        self.structure_key = structure_key

        self.init_specs()

        # Standard metadata.
        self.uid = sc.uuid()
        self.created = sc.today()
        self.modified = sc.today()
        self.version = version
        self.git_info = sc.gitinfo(__file__)
        self.workbook_load_date = "N.A."

    def __repr__(self):
        output = sc.objrepr(self)
        output += self.get_metadata_string()
        output += "=" * 60 + "\n"
        return output

    def get_metadata_string(self):
        meta = "   Atomica version: %s\n" % self.version
        meta += "      Date created: %s\n" % sc.getdate(self.created)
        meta += "     Date modified: %s\n" % sc.getdate(self.modified)
        meta += "   Workbook loaded: %s\n" % sc.getdate(self.workbook_load_date)
        meta += "        Git branch: %s\n" % self.git_info['branch']
        meta += "          Git hash: %s\n" % self.git_info['hash']
        meta += "               UID: %s\n" % self.uid
        return meta

    def init_specs(self):
        """
        Initialize the uppermost layer of structure specifications (i.e. base item types).
        Do so according to corresponding settings.
        """
        if self.structure_key is not None:
            item_type_specs = None
            if self.structure_key == SS.STRUCTURE_KEY_FRAMEWORK:
                item_type_specs = FS.ITEM_TYPE_SPECS
            elif self.structure_key == SS.STRUCTURE_KEY_DATA:
                item_type_specs = DS.ITEM_TYPE_SPECS
            if item_type_specs is not None:
                for item_type in item_type_specs:
                    if item_type_specs[item_type]["superitem_type"] is None:
                        self.specs[item_type] = sc.odict()

    def init_item(self, item_name, item_type, target_item_location, position=None):
        """
        Initialize the attribute structure relating to specifications for a new item within a target dictionary.
        Should not be called directly as it is part of item creation.
        """
        #        target_item_location[item_name] = sc.odict()
        if position is None:
            target_item_location[item_name] = sc.odict()
        else:
            target_item_location.insert(pos=position, key=item_name,
                                        value=sc.odict())  # Note: cannot initialize as an odict since this will create a linked version

        if self.structure_key is not None:
            item_type_specs = None
            if self.structure_key == SS.STRUCTURE_KEY_FRAMEWORK:
                item_type_specs = FS.ITEM_TYPE_SPECS
            elif self.structure_key == SS.STRUCTURE_KEY_DATA:
                item_type_specs = DS.ITEM_TYPE_SPECS
            if item_type_specs is not None:
                for attribute in item_type_specs[item_type]["attributes"]:
                    # Create space for all item attributes except 'name' as that is used as the key for specifications.
                    if attribute == "name":
                        continue
                    content_type = None
                    if "content_type" in item_type_specs[item_type]["attributes"][attribute]:
                        content_type = item_type_specs[item_type]["attributes"][attribute]["content_type"]
                    # Set up a default value if available.
                    value = None
                    if content_type is not None and content_type.default_value is not None:
                        value = self.enforce_value(value=content_type.default_value, content_type=content_type)
                    target_item_location[item_name][attribute] = value
                    # If the attribute itself references another item type in settings, prepare it as a container.
                    # The container itself is for storing those corresponding items in specifications.
                    if "ref_item_type" in item_type_specs[item_type]["attributes"][attribute]:
                        target_item_location[item_name][attribute] = sc.odict()
                    # If the content type for the attribute is marked as a list, instantiate that list.
                    elif content_type is not None and content_type.is_list:
                        target_item_location[item_name][attribute] = list()

    def create_item(self, item_name, item_type, superitem_type_name_pairs=None, position=None):
        """
        Instantiates item type in specs with item name as key, initializing its attribute structure as well.
        If the item is not top-level, a list of superitem type-name pairs must be provided.
        These must point to the intended item location in specs.
        Position is an integer corresponding to the index of the ordered dictionary in which the item should be created.
        """
        item_name = str(item_name)  # Hard-coded type-enforcement for name.
        # Move down the specs dictionary according to superitem type-name pair list.
        target_specs = self.specs
        depth = 0
        if superitem_type_name_pairs is None:
            superitem_type_name_pairs = []
        try:
            for pair in superitem_type_name_pairs:
                super_type = pair[0]
                super_name = pair[-1]
                if depth > 0:
                    super_type += SS.DEFAULT_SUFFIX_PLURAL
                target_specs = target_specs[super_type][super_name]
                depth += 1
        except Exception:
            raise AtomicaException("Item creation of type '{0}', name '{1}', was supplied the following chain of keys, "
                                   "which does not exist in specifications: "
                                   "'{2}'".format(item_type, item_name,
                                                  "', '".join([elem for pair in superitem_type_name_pairs
                                                               for elem in pair])))

        # Initialize item in specifications dictionary.
        # Subitem types are pluralized when used as keys in the specs structure.
        item_type_key = item_type
        if depth > 0:
            item_type_key += SS.DEFAULT_SUFFIX_PLURAL
        self.init_item(item_name=item_name, item_type=item_type, target_item_location=target_specs[item_type_key],
                       position=position)

        # Flatten superitem type-name pairs into a list, if available, and extend with type and name of current item.
        key_list = [elem for pair in superitem_type_name_pairs for elem in pair]
        if key_list is None:
            key_list = []
        key_list.extend([item_type_key, item_name])
        # Create a semantic link between the name of the item and its specifications.
        self.create_semantic(term=item_name, item_type=item_type, item_name=item_name, attribute="name",
                             key_list=key_list)

    # TODO: Develop a more robust item deletion method that is aware of subitems, either deleting them or validating.
    #       Refactor the name to delete_item once this is done.
    def delete_item_riskily(self, term):
        """
        Deletes the item from specs as well as associated semantics entries.
        This item must have no subitems, otherwise...
        - Their specifications will be deleted as part of the superitem spec.
        - Their semantics will not be deleted.
        However, the original design only introduced subitems for population attributes and program types.
        Provided neither are implemented or, if implemented, items are not deleted with this method, risk is controlled.
        """
        semantic = self.get_semantic(self.get_spec_name(term))
        key_list = semantic["key_list"]
        check_keys = key_list[:-1]
        last_key = key_list[-1]
        # Clear semantics.
        try:
            label = self.get_spec_value(term=term, attribute="label")
            del self.semantics[label]
        except AtomicaException:
            pass
        name = self.get_spec_name(term)
        del self.semantics[name]
        # Delete spec.
        spec = self.specs
        for key in check_keys:
            spec = spec[key]
        del spec[last_key]

    @staticmethod
    def enforce_value(value, content_type):
        """ Enforces value type according to content specifications. """

        def identity(x):
            return x

        intermediate_type = identity
        # All content subclasses from ContentType, which may specify value type enforcement and whether it is a list.
        # If so, apply the enforcement.
        if content_type is not None:
            if content_type.default_value is not None:
                if content_type.is_list:
                    value = [content_type.default_value if x is None else x for x in value]
                else:
                    value = content_type.default_value if value is None else value
            if content_type.enforce_type is not None:
                if content_type.enforce_type == int:
                    intermediate_type = float  # Handles str to int conversion.
                if content_type.is_list:
                    value = [content_type.enforce_type(intermediate_type(x)) if x is not None else None for x in value]
                else:
                    value = content_type.enforce_type(intermediate_type(value)) if value is not None else None
        return value

    def set_spec_value(self, term, attribute, value, content_type=None):
        if content_type is not None:
            try:
                value = self.enforce_value(value, content_type)
            except Exception:
                raise AtomicaException("Attribute '{0}' for specification associated with term '{1}' "
                                       "has been assigned a value that cannot be enforced as type '{2}'. "
                                       "The value is: {3}".format(attribute, term, content_type.enforce_type, value))
        spec = self.get_spec(term)
        if attribute not in spec:
            raise SemanticUnknownException(term=term, attribute=attribute)
        spec[attribute] = value
        # Labels are special; construct a label-keyed semantic link to item specifications here.
        if attribute in ["label"]:
            item_name = self.get_spec_name(term)
            self.create_semantic(term=value, item_name=item_name, attribute=attribute)

    def append_spec_value(self, term, attribute, value, content_type=None):
        """
        Creates a list for a specification attribute if currently nonexistent, then extends or appends it by a value.
        """
        if content_type is not None:
            try:
                value = self.enforce_value(value, content_type)
            except Exception:
                raise AtomicaException("Attribute '{0}' for specification associated with term '{1}' "
                                       "has been assigned a value that cannot be enforced as type '{2}'. "
                                       "The value is: {3}".format(attribute, term, content_type.enforce_type, value))
        spec = self.get_spec(term)
        if attribute not in spec:
            raise SemanticUnknownException(term=term, attribute=attribute)
        try:
            spec[attribute].append(value)
        except Exception:
            raise AtomicaException("Attribute '{0}' for specification associated with term '{1}' can neither be "
                                   "extended nor appended by value '{2}'.".format(attribute, term, value))

    def get_spec_name(self, term):
        """ Returns the name corresponding to a provided term. """
        return self.get_semantic_value(term=term, attribute="name")

    def get_spec_type(self, term):
        """
        Returns the type of item that this specification belongs to.
        Item type, like the referencing key list, is stored only in semantic structures keyed with item names.
        """
        return self.get_semantic_value(term=self.get_spec_name(term), attribute="type")

    def get_spec_value(self, term, attribute):
        """ Returns the value of an attribute for a provided term. """
        spec = self.get_spec(term=term)
        try:
            return spec[attribute]
        except Exception:
            raise AtomicaException("The item corresponding to term '{0}' does not have attribute '{1}' "
                                   "to query value of.".format(term, attribute))

    def get_spec(self, term):
        """ Returns the item specification association with a term. """
        semantic = self.get_semantic(self.get_spec_name(term))
        try:
            key_list = semantic["key_list"]
            spec = self.specs
            for key in key_list:
                spec = spec[key]
            return spec
        except Exception:
            raise AtomicaException(
                "The item corresponding to term '{0}' could not be located in the semantics dictionary.".format(term))

    def create_semantic(self, term, item_name, attribute, item_type=None, key_list=None):
        """
        Creates a semantic link from a term to an item, noting what item attribute has the term as its value.
        Names as terms are important; they link to item type and the list of keys to access item specifications.
        """
        if term in self.semantics:
            other_attribute = self.semantics[term]["attribute"]
            other_name = self.semantics[term]["name"]
            other_type = self.get_spec_type(term)
            this_type = "'" + item_type + "'" if item_type is not None else ""
            raise AtomicaException("The {0} term '{1}' has been defined previously as the '{2}' of '{3}' item '{4}'. "
                                   "Duplicate terms are not allowed.".format(this_type, term, other_attribute,
                                                                             other_type, other_name))
        else:
            self.semantics[term] = {"name": item_name, "attribute": attribute}
            if attribute == "name":
                if not term == item_name:
                    raise AtomicaException("Term '{0}' has been declared as the name of item with name '{1}'. "
                                           "This is a contradiction.".format(term, item_name))
                if item_type is None:
                    raise AtomicaException(
                        "Term '{0}' is an item name. It must be associated with an item type in a semantics "
                        "dictionary for quick-reference purposes.".format(term))
                else:
                    self.semantics[term]["type"] = item_type
                if key_list is None:
                    raise AtomicaException(
                        "Term '{0}' is an item name. It must be associated with a key list in a semantics "
                        "dictionary that points to where the item sits in a specifications dictionary.".format(term))
                else:
                    self.semantics[term]["key_list"] = key_list

    def get_semantic(self, term):
        """
        Returns a dictionary of item name, attribute and possibly item type.
        Spec-referencing key list corresponding to a term is also included.
        """
        try:
            return self.semantics[term]
        except Exception:
            raise SemanticUnknownException(term=term)

    def get_semantic_value(self, term, attribute):
        """ Convenient function to return semantic attribute value, e.g. 'name', 'attribute', 'type' and 'key_list'. """
        semantic = self.get_semantic(term)
        try:
            return semantic[attribute]
        except Exception:
            raise SemanticUnknownException(term=term, attribute=attribute)

    def complete_specs(self, **kwargs):
        """
        An overloaded method for completing specifications that is called at the end of a file import.
        This delay is because some specifications rely on other definitions and values existing in the specs dictionary.
        """
        pass

    def save(self, filepath):
        """ Save the current project structure to a relevant object file. """
        file_extension = None
        if self.structure_key == SS.STRUCTURE_KEY_FRAMEWORK:
            file_extension = SS.OBJECT_EXTENSION_FRAMEWORK
        if self.structure_key == SS.STRUCTURE_KEY_DATA:
            file_extension = SS.OBJECT_EXTENSION_DATA
        filepath = sc.makefilepath(filename=filepath, ext=file_extension, sanitize=True)  # Enforce file extension.
        sc.saveobj(filepath, self)

    @classmethod
    def load(cls, filepath):
        """ Convenience class method for loading a project structure in the absence of an instance. """
        return sc.loadobj(filepath)
