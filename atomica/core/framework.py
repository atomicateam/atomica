# -*- coding: utf-8 -*-
"""
Atomica project-framework file.
Contains all information describing the context of a project.
This includes a description of the Markov chain network underlying project dynamics.
"""
import sciris.core as sc
from .structure import CoreProjectStructure, get_quantity_type_list
from .structure_settings import FrameworkSettings as FS, DataSettings as DS, TableTemplate
from .system import SystemSettings as SS, apply_to_all_methods, log_usage, logger, AtomicaException
from .workbook_export import make_instructions, write_workbook
from .workbook_import import read_workbook
from .parser_function import parse_function


@apply_to_all_methods(log_usage)
class ProjectFramework(CoreProjectStructure):
    """ The object that defines the transition-network structure of models generated by a project. """

    def __init__(self, filepath=None, **kwargs):
        """ Initialize the framework. """
        super(ProjectFramework, self).__init__(structure_key=SS.STRUCTURE_KEY_FRAMEWORK, **kwargs)

        # Set up a filter for quickly iterating through items of a certain group.
        self.filter = {FS.TERM_FUNCTION + FS.KEY_PARAMETER: [],
                       "stages": []}

        # Load framework file if provided.
        if filepath:
            self.read_from_file(filepath=filepath)

    def complete_specs(self, **kwargs):
        """
        A method for completing specifications that is called at the end of a file import.
        This delay is because some specifications rely on other definitions and values existing in the specs dictionary.
        """
        self.parse_parameter_specs()
        self.parse_cascade_specs()
        self.create_databook_specs()  # Establish specifications for constructing a databook.
        self.validate_specs()

    def parse_parameter_specs(self):
        """ Run through parsed parameters and apply special functions as required. """
        self.filter[FS.TERM_FUNCTION + FS.KEY_PARAMETER] = []
        for item_key in self.specs[FS.KEY_PARAMETER].keys():
            # If any parameters are associated with functions, store those functions as strings plus a dependency list.
            if not self.get_spec_value(item_key, FS.TERM_FUNCTION) is None:
                self.filter[FS.TERM_FUNCTION + FS.KEY_PARAMETER].append(item_key)
                fcn_str = self.get_spec_value(item_key, FS.TERM_FUNCTION).replace(" ", "")
                _, dependencies = parse_function(fcn_str)
                self.set_spec_value(item_key, attribute=FS.TERM_FUNCTION, value=fcn_str)
                self.set_spec_value(item_key, attribute="dependencies", value=dependencies)
            # # If any parameters are flagged as interactions, convert them into actual interaction items.
            # if self.get_spec_value(item_key, "is_" + FS.KEY_INTERACTION):
            #     spec = sc.dcp(self.get_spec(term=item_key))     # Get copy of parameter specs before deleting original.
            #     self.delete_item_riskily(term=item_key)
            #     self.create_item(item_name=item_key, item_type=FS.KEY_INTERACTION)
            #     for attribute in FS.ITEM_TYPE_SPECS[FS.KEY_PARAMETER]["attributes"]:
            #         if attribute in FS.ITEM_TYPE_SPECS[FS.KEY_INTERACTION]["attributes"] and not attribute == "name":
            #             value = spec[attribute]
            #             content_type = None
            #             att_specs = FS.ITEM_TYPE_SPECS[FS.KEY_INTERACTION]["attributes"][attribute]
            #             if "content_type" in att_specs:
            #                 content_type = att_specs["content_type"]
            #             self.set_spec_value(term=item_key, attribute=attribute, value=value, content_type=content_type)

    def parse_cascade_specs(self):
        """ If any compartments/characteristics are marked as cascade stages, sort them into a quick refence list. """
        temp_keys = []
        temp_stages = []
        for item_type in [FS.KEY_COMPARTMENT, FS.KEY_CHARACTERISTIC]:
            for item_key in self.specs[item_type]:
                if not self.get_spec_value(item_key, "cascade_stage") is None:
                    temp_keys.append(item_key)
                    temp_stages.append(self.get_spec_value(item_key, "cascade_stage"))
        self.filter["stages"] = [x for _, x in sorted(zip(temp_stages, temp_keys))]

    def create_databook_specs(self):
        """
        Generates framework-dependent databook settings.
        These are a fusion of static databook settings and dynamic framework specifics.
        They are the ones that databook construction processes use when deciding layout.
        """
        # Copy page keys from databook settings into framework datapage objects.
        for page_key in reversed(DS.PAGE_KEYS):
            position = 0
            if page_key in [DS.KEY_CHARACTERISTIC, DS.KEY_PARAMETER]:
                position = None
            self.create_item(item_name=page_key, item_type=FS.KEY_DATAPAGE, position=position)

        # Do a scan over page tables in default databook settings.
        # If templated, i.e. duplicated per item type instance, tables must be copied and duplicated where necessary.
        for page_key in DS.PAGE_KEYS:
            copy_over = False
            for table in DS.PAGE_SPECS[page_key]["tables"]:
                if isinstance(table, TableTemplate):
                    copy_over = True
                    break

            if copy_over:
                for page_attribute in DS.PAGE_SPECS[page_key]:
                    if not page_attribute == "tables":
                        self.set_spec_value(term=page_key, attribute=page_attribute,
                                            value=DS.PAGE_SPECS[page_key][page_attribute])
                    else:
                        for table in DS.PAGE_SPECS[page_key]["tables"]:
                            if isinstance(table, TableTemplate) and table.template_item_type is not None:
                                item_type = table.template_item_type
                                # If the template item type does not exist in the framework...
                                # Delay duplication of the template to databook construction, but pass it along.
                                if item_type not in self.specs:
                                    self.append_spec_value(term=page_key, attribute="tables", value=sc.dcp(table))
                                # Otherwise, apply the duplication later.
                                else:
                                    for item_key in self.specs[item_type]:
                                        # Do not create tables for items that are marked not to be shown in a datapage.
                                        # Warn if they should be.
                                        if "datapage_order" in self.get_spec(item_key) and \
                                                self.get_spec_value(item_key, "datapage_order") == -1:
                                            if ("setup_weight" in self.get_spec(item_key) and
                                                    not self.get_spec_value(item_key, "setup_weight") == 0.0):
                                                logger.warning("Item '{0}' of type '{1}' is associated with a non-zero "
                                                               "setup weight of '{2}' but a databook ordering of '-1'. "
                                                               "Users will not be able to supply important "
                                                               "values.".format(item_key, item_type,
                                                                                self.get_spec_value(item_key,
                                                                                                    "setup_weight")))
                                        # Otherwise create the tables.
                                        else:
                                            actual_page_key = page_key
                                            if FS.KEY_DATAPAGE in self.specs[item_type][item_key] and \
                                                    not self.specs[item_type][item_key][FS.KEY_DATAPAGE] is None:
                                                actual_page_key = self.specs[item_type][item_key][FS.KEY_DATAPAGE]
                                            instantiated_table = sc.dcp(table)
                                            instantiated_table.template_item_key = item_key
                                            self.append_spec_value(term=actual_page_key, attribute="tables",
                                                                   value=instantiated_table)
                            else:
                                self.append_spec_value(term=page_key, attribute="tables", value=table)
            # Keep framework specifications minimal by referring to settings when possible.
            # TODO: Reconsider. Does not save much space as attribute dictionary is constructed by self.create_item().
            else:
                self.set_spec_value(term=page_key, attribute="refer_to_settings", value=True)

    def validate_specs(self):
        """ Check that framework specifications make sense. """
        for item_key in self.specs[FS.KEY_COMPARTMENT]:
            special_comp_tags = [self.get_spec_value(item_key, "is_source"),
                                 self.get_spec_value(item_key, "is_sink"),
                                 self.get_spec_value(item_key, "is_junction")]
            if special_comp_tags.count(True) > 1:
                raise AtomicaException("Compartment '{0}' can only be a source, sink or junction, "
                                       "not a combination of two or more.".format(item_key))
            if special_comp_tags[0:2].count(True) > 0:
                if not self.get_spec_value(item_key, "setup_weight") == 0.0:
                    raise AtomicaException(
                        "Compartment '{0}' cannot be a source or sink and also have a nonzero setup weight. "
                        "Check that setup weight was explicitly set to '0'.".format(item_key))
                if not self.get_spec_value(item_key, "datapage_order") == -1:
                    raise AtomicaException(
                        "Compartment '{0}' cannot be a source or sink and not have a '-1' databook ordering. "
                        "It must be explicitly excluded from querying its population size in a databook.".format(
                            item_key))
        for item_key in self.specs[FS.KEY_PARAMETER]:
            # Validate transition-matrix and parameter matching.
            if self.get_spec_value(item_key, "label") is None:
                raise AtomicaException("Parameter '{0}' has no label. This is likely because it was used to mark a "
                                       "link in a transition matrix but was left undefined on the parameters "
                                       "page of a framework file.".format(item_key))
            # Make sure functional parameters have a specified format.
            links = self.get_spec_value(item_key, "links")
            if len(links) > 0:
                if (not self.get_spec_value(item_key, FS.TERM_FUNCTION) is None and
                        not self.get_spec_value(item_key, "format") in get_quantity_type_list(include_absolute=True,
                                                                                              include_relative=True,
                                                                                              include_special=True)):
                    raise AtomicaException("Parameter '{0}' is associated with transitions and is expressed as "
                                           "a custom function of other parameters. "
                                           "A format must be specified for it in a framework file.".format(item_key))
            initial_comps = {}
            for link in links:
                # Avoid discussions about how to disaggregate parameters with multiple links from the same compartment.
                if link[0] in initial_comps:
                    raise AtomicaException("Parameter '{0}' cannot be associated with two or more transitions "
                                           "from the same compartment '{1}'.".format(item_key, link[0]))
                initial_comps[link[0]] = True
                # Validate parameter-related transitions with source/sink compartments.
                if self.get_spec_value(link[0], "is_sink"):
                    raise AtomicaException("Parameter '{0}' cannot be associated with a transition from "
                                           "compartment '{1}' to '{2}'. Compartment '{1}' is strictly "
                                           "a sink compartment.".format(item_key, link[0], link[-1]))
                if self.get_spec_value(link[-1], "is_source"):
                    raise AtomicaException("Parameter '{0}' cannot be associated with a transition from "
                                           "compartment '{1}' to '{2}'. Compartment '{2}' is strictly "
                                           "a source compartment.".format(item_key, link[0], link[-1]))
                if self.get_spec_value(link[0], "is_source"):
                    if self.get_spec_value(link[-1], "is_sink"):
                        raise AtomicaException("Parameter '{0}' should not be associated with a transition from "
                                               "compartment '{1}' to '{2}'. This is a pointless flow from "
                                               "source to sink compartment.".format(item_key, link[0], link[-1]))
                    if len(links) > 1:
                        raise AtomicaException("Parameter '{0}' is associated with a transition from "
                                               "source compartment '{1}' to '{2}'. This restricts any other "
                                               "transitions being marked '{0}' due to flow disaggregation "
                                               "ambiguity.".format(item_key, link[0], link[-1]))
                    if not self.get_spec_value(item_key, "format") in get_quantity_type_list(include_absolute=True):
                        quantity_types_string = "' or '".join(get_quantity_type_list(include_absolute=True))
                        raise AtomicaException("Parameter '{0}' is associated with a "
                                               "transition from source compartment '{1}' to '{2}'. "
                                               "The format of the parameter must thus be specified as: "
                                               "'{3}'".format(item_key, link[0], link[-1], quantity_types_string))
                # Validate parameter-related transitions with junction compartments.
                if self.get_spec_value(link[0], "is_junction"):
                    if len(links) > 1:
                        # TODO: Avoid repetitive exception code. Encapsulate all exceptions.
                        raise AtomicaException("Parameter '{0}' is associated with a transition from junction "
                                               "compartment '{1}' to '{2}'. This restricts any other transitions "
                                               "being marked '{0}' due to flow disaggregation "
                                               "ambiguity.".format(item_key, link[0], link[-1]))
                    if not self.get_spec_value(item_key, "format") == FS.QUANTITY_TYPE_PROPORTION:
                        raise AtomicaException("Parameter '{0}' is associated with a transition from junction "
                                               "compartment '{1}' to '{2}'. The format of the parameter must thus be "
                                               "specified as: '{3}'".format(item_key, link[0], link[-1],
                                                                            FS.QUANTITY_TYPE_PROPORTION))
                if self.get_spec_value(item_key, "format") == FS.QUANTITY_TYPE_PROPORTION:
                    if not self.get_spec_value(link[0], "is_junction"):
                        raise AtomicaException("Parameter '{0}' is associated with a transition from non-junction "
                                               "compartment '{1}' to '{2}'. It is also incorrectly given a "
                                               "'proportion' format which can only describe transitions from "
                                               "junctions.".format(item_key, link[0], link[-1]))

    @classmethod
    def create_template(cls, path, num_comps=None, num_characs=None, num_pars=None, num_datapages=None):
        """ Convenience class method for template creation in the absence of an instance. """
        framework_instructions, _ = make_instructions(workbook_type=SS.STRUCTURE_KEY_FRAMEWORK)
        if num_comps is not None:  # Set the number of compartments.
            framework_instructions.update_number_of_items(FS.KEY_COMPARTMENT, num_comps)
        if num_characs is not None:  # Set the number of characteristics.
            framework_instructions.update_number_of_items(FS.KEY_CHARACTERISTIC, num_characs)
        if num_pars is not None:  # Set the number of parameters.
            framework_instructions.update_number_of_items(FS.KEY_PARAMETER, num_pars)
        if num_datapages is not None:  # Set the number of custom databook pages.
            framework_instructions.update_number_of_items(FS.KEY_DATAPAGE, num_datapages)

        write_workbook(workbook_path=path, instructions=framework_instructions,
                       workbook_type=SS.STRUCTURE_KEY_FRAMEWORK)
        return path

    def write_to_file(self, filename, data=None, instructions=None):
        """ Export a framework to file. """
        # TODO: modify write_workbook so it can write framework specs to an excel file???
        pass

    def read_from_file(self, filepath=None):
        """ Import a framework from file. """
        read_workbook(workbook_path=filepath, framework=self,
                      workbook_type=SS.STRUCTURE_KEY_FRAMEWORK)
        self.workbook_load_date = sc.today()
        self.modified = sc.today()
