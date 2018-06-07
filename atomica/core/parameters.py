# Imports

import numpy as np
import sciris.core as sc
from atomica.core.interpolation import interpolate_func
from atomica.core.structure_settings import DataSettings as DS
from atomica.core.system import AtomicaException, logger
from atomica.core.utils import NamedItem

# Parameter class that stores one array of values converted from raw project data
class Parameter(NamedItem):
    """ Class to hold one set of parameter values disaggregated by populations. """

    def __init__(self, name, t=None, y=None, y_format=None, y_factor=None, autocalibrate=None):
        NamedItem.__init__(self,name)

        # These ordered dictionaries have population names as keys.
        if t             is None: t             = sc.odict()
        if y             is None: y             = sc.odict()
        if y_format      is None: y_format      = sc.odict()
        if y_factor      is None: y_factor      = sc.odict()
        if autocalibrate is None: autocalibrate = sc.odict()
        self.t = t  # Time data
        self.y = y  # Value data
        self.y_format = y_format  # Value format data (e.g. Probability, Fraction or Number).
        # TODO: Consider whether to support different transformations whether format is relative or absolute.
        self.y_factor = y_factor  # Scaling factor of data.
        # The following attribute determines whether this parameter can be autocalibrated.
        self.autocalibrate = autocalibrate  # A set of boolean flags corresponding to y_factor.

    @property
    def pops(self):
        return self.t.keys()

    def has_values(self, pop_name):
        # Returns True if this Parameter has values specified for the given population
        # If the Parameter has an assumption, then the time value will be nan but a
        # y-value will be present. If the Parameter normally has a function, then the
        # y-value will be None. If a function Parameter has a scenario overwrite applied
        # then actual values will be present. Essentially, if this function returns True,
        # then the `interpolate()` method will return usable values
        return (self.y[pop_name].size > 0) and self.y[pop_name][0] is not None

    def insert_value_pair(self, t, y, pop_name):
        """
        Check if the inserted t value already exists for the population parameter.
        If not, append y value. If so, overwrite y value.
        """
        # Make sure it stays sorted
        if t in self.t[pop_name]:
            self.y[pop_name][self.t[pop_name] == t] = y
        else:
            idx = np.searchsorted(self.t[pop_name], t)
            self.t[pop_name] = np.insert(self.t[pop_name], idx, t)
            self.y[pop_name] = np.insert(self.y[pop_name], idx, y)

    def remove_value_at(self, t, pop_name):
        """ Remove value at time point 't' and the time point itself if no other time point exists. """

        if t in self.t[pop_name]:
            if len(self.t[pop_name]) <= 1:
                return False
            else:
                idx = np.equal(self.t[pop_name], t).nonzero()[0][0]
                self.t[pop_name] = np.delete(self.t[pop_name], idx)
                self.y[pop_name] = np.delete(self.y[pop_name], idx)
                return True
        else:
            return True

    def remove_between(self, t_remove, pop_name):
        # t is a two element vector [min,max] such that
        # times > min and < max are removed
        # Note that the endpoints are not included!
        original_t = self.t[pop_name]
        for tval in original_t:
            if t_remove[0] < tval < t_remove[1]:
                self.remove_value_at(tval, pop_name)

    def interpolate(self, tvec=None, pop_name=None):  # , extrapolate_nan = False):
        """ Take parameter values and construct an interpolated array corresponding to the input time vector. """

        # Validate input.
        if pop_name not in self.t.keys():
            raise AtomicaException("Cannot interpolate parameter '{0}' "
                                   "without referring to a proper population name.".format(pop_name))
        if tvec is None:
            raise AtomicaException("Cannot interpolate parameter '{0}' "
                                   "without providing a time vector.".format(self.name))
        if not len(self.t[pop_name]) > 0:
            raise AtomicaException("There are no timepoint values for parameter '{0}', "
                                   "population '{1}'.".format(self.name, pop_name))
        if not len(self.t[pop_name]) == len(self.y[pop_name]):
            raise AtomicaException("Parameter '{0}', population '{1}', does not have corresponding values "
                                   "and timepoints.".format(self.name, pop_name))

        # if len(self.t[pop_name]) == 1 and not extrapolate_nan:
        #     # Do not bother running interpolation loops if constant. Good for performance.
        #    output = np.ones(len(tvec))*(self.y[pop_name][0]*np.abs(self.y_factor[pop_name]))
        # else:
        input_t = sc.dcp(self.t[pop_name])
        input_y = sc.dcp(self.y[pop_name])  # *np.abs(self.y_factor[pop_name])

        # Eliminate np.nan from value array before interpolation. Makes sure timepoints are appropriately constrained.
        cleaned_times = input_t[~np.isnan(input_y)]  # NB. numpy advanced indexing here results in a copy
        cleaned_vals = input_y[~np.isnan(input_y)]

        if len(cleaned_times) == 0:  # If there are no timepoints after cleaning, this may be a calculated parameter.
            output = np.ones(len(tvec)) * np.nan
        elif len(cleaned_times) == 1:
            output = np.ones(len(tvec)) * cleaned_vals[0]  # Don't bother running interpolation loops if constant.
        else:
            # Pad the input vectors for interpolation with minimum and maximum timepoint values.
            # This avoids extrapolated values blowing up.
            ind_min, t_min = min(enumerate(cleaned_times), key=lambda p: p[1])
            ind_max, t_max = max(enumerate(cleaned_times), key=lambda p: p[1])
            val_at_t_min = cleaned_vals[ind_min]
            val_at_t_max = cleaned_vals[ind_max]

            # This padding keeps edge values constant for desired time ranges larger than data-provided time ranges.
            if tvec[0] < t_min:
                cleaned_times = np.append(tvec[0], cleaned_times)
                cleaned_vals = np.append(val_at_t_min, cleaned_vals)
            if tvec[-1] > t_max:
                cleaned_times = np.append(cleaned_times, tvec[-1])
                cleaned_vals = np.append(cleaned_vals, val_at_t_max)

            output = interpolate_func(cleaned_times, cleaned_vals, tvec)

        # if not extrapolate_nan:
        #     # Pad the input vectors for interpolation with minimum and maximum timepoint values.
        #     # This avoids extrapolated values blowing up.
        #     ind_min, t_min = min(enumerate(self.t[pop_name]), key = lambda p: p[1])
        #     ind_max, t_max = max(enumerate(self.t[pop_name]), key = lambda p: p[1])
        #     y_at_t_min = self.y[pop_name][ind_min]
        #     y_at_t_max = self.y[pop_name][ind_max]
        #
        #     # This padding keeps edge values constant for desired time ranges larger than data-provided time ranges.
        #     if tvec[0] < t_min:
        #         input_t = np.append(tvec[0], input_t)
        #         input_y = np.append(y_at_t_min, input_y)
        #     if tvec[-1] > t_max:
        #         input_t = np.append(input_t, tvec[-1])
        #         input_y = np.append(input_y, y_at_t_max)
        #
        # # The interpolation function currently complains about single data points.
        # # This is the simplest hack for nan extrapolation.
        # elif len(input_t) == 1:
        #     input_t = np.append(input_t, input_t[-1] + 1e-12)
        #     input_y = np.append(input_y, input_y[-1])
        #
        # output = interpolate_func(x = input_t, y = input_y, xnew = tvec, extrapolate_nan = extrapolate_nan)

        return output

    def __repr__(self, *args, **kwargs):
        return "Parameter: {0}\n\nt\n{1}\ny\n{2}\ny_format\n{3}\ny_factor\n{4}\n".format(self.name, self.t, self.y,
                                                                                         self.y_format, self.y_factor)


# Parset class that contains one set of parameters converted from raw project data

class ParameterSet(NamedItem):
    """ Class to hold all parameters. """

    def __init__(self, name="default"):
        NamedItem.__init__(self,name)

        self.pop_names = []  # List of population names.
        # Names are used throughout the codebase as variable names (technically dict keys).
        self.pop_labels = []  # List of population labels.
        # Labels are used only for user interface and can be more elaborate than simple names.
        self.pars = sc.odict()
        self.pars["cascade"] = []
        self.pars["comps"] = []
        self.pars["characs"] = []
        self.par_ids = {"cascade": {}, "comps": {}, "characs": {}}

        self.transfers = sc.odict()  # Dictionary of inter-population transitions.
        self.contacts  = sc.odict()  # Dictionary of inter-population interaction weights.

        logger.info("Created ParameterSet: {0}".format(self.name))

    def copy(self,new_name=None):
        x = sc.dcp(self)
        if new_name is not None:
            x.name = new_name
        return x

    def set_scaling_factor(self, par_name, pop_name, scale):
        par = self.get_par(par_name)
        par.y_factor[pop_name] = scale

    def get_par(self, name):
        for par_type in ["cascade", "comps", "characs"]:
            if name in self.par_ids[par_type].keys():
                return self.pars[par_type][self.par_ids[par_type][name]]
        raise AtomicaException("Name '{0}' cannot be found in parameter set '{1}' as either a cascade parameter, "
                               "compartment or characteristic.".format(name, self.name))

    def make_pars(self, data):
        self.pop_names = data.specs[DS.KEY_POPULATION].keys()
        self.pop_labels = [data.get_spec(pop_name)["label"] for pop_name in self.pop_names]

        # Cascade parameter and characteristic extraction.
        for j in range(3):
            item_key = [DS.KEY_PARAMETER, DS.KEY_COMPARTMENT, DS.KEY_CHARACTERISTIC][j]
            item_group = ["cascade", "comps", "characs"][j]
            for k, name in enumerate(data.specs[item_key]):
                self.par_ids[item_group][name] = k
                self.pars[item_group].append(Parameter(name=name))
                popdata = data.get_spec_value(name, DS.TERM_DATA)
                for pop_id in popdata.keys():
                    tvec, yvec = popdata.get_arrays(pop_id)
                    self.pars[item_group][-1].t[pop_id] = tvec
                    self.pars[item_group][-1].y[pop_id] = yvec
                    self.pars[item_group][-1].y_format[pop_id] = popdata.get_format(pop_id)
                    # TODO: Consider exposing scaling factors in the databook.
                    self.pars[item_group][-1].y_factor[pop_id] = 1.0

        # Transfer extraction.
        for name in data.specs[DS.KEY_TRANSFER]:
            if name not in self.transfers:
                self.transfers[name] = sc.odict()
            for pop_link in data.specs[DS.KEY_TRANSFER][name][DS.KEY_POPULATION_LINKS]:
                source_pop = pop_link[0]
                target_pop = pop_link[1]
                if pop_link[0] not in self.transfers[name]:
                    self.transfers[name][source_pop] = Parameter(name = name + "_from_" + source_pop)
                transfer_data = data.get_spec_value(name, DS.TERM_DATA)
                tvec, yvec = transfer_data.get_arrays(pop_link)
                self.transfers[name][source_pop].t[target_pop] = tvec
                self.transfers[name][source_pop].y[target_pop] = yvec
                self.transfers[name][source_pop].y_format[target_pop] = transfer_data.get_format(pop_link)
                # TODO: Consider exposing scaling factors in the databook.
                self.transfers[name][source_pop].y_factor[target_pop] = 1.0

# TODO: Clean this batch of comments once autocalibration tags are conclusively handled.
# self.pars["cascade"][-1].y_format[pop_id] = data[DS.KEY_PARAMETER][name][pop_id]["y_format"]
#                if data[DS.KEY_PARAMETER][name][pop_id]["y_factor"] == DO_NOT_SCALE:
#                    self.pars["cascade"][-1].y_factor[pop_id] = DEFAULT_YFACTOR
#                    self.pars["cascade"][-1].autocalibrate[pop_id] = False
#                else:
#                    self.pars["cascade"][-1].y_factor[pop_id] = data[DS.KEY_PARAMETER][name][pop_id]["y_factor"]
#                    self.pars["cascade"][-1].autocalibrate[pop_id] = True

#        # Characteristic parameters (e.g. popsize/prevalence).
#        # Despite being mostly data to calibrate against, is still stored in full so as to interpolate initial value.
#        for l, name in enumerate(data.specs[DS.KEY_CHARACTERISTIC]):
#            self.par_ids["characs"][name] = l
#            self.pars["characs"].append(Parameter(name = name))
#            for pop_id in data.get_spec_value(name, DS.TERM_DATA):
#                self.pars["characs"][l].t[pop_id] = data.get_spec_value(name, DS.TERM_DATA)[pop_id]["t"]
#                self.pars["characs"][l].y[pop_id] = data.get_spec_value(name, DS.TERM_DATA)[pop_id]["y"]
#                self.pars["characs"][l].y_format[pop_id] = data.get_spec(name)[DS.TERM_VALUE][pop_id]["y_format"]
#                if data[DS.KEY_CHARACTERISTIC][name][pop_id]["y_factor"] == DO_NOT_SCALE:
#                    self.pars["characs"][-1].y_factor[pop_id] = DEFAULT_YFACTOR
#                    self.pars["characs"][-1].autocalibrate[pop_id] = False
#                else:
#                    self.pars["characs"][-1].y_factor[pop_id] = data[DS.KEY_CHARACTERISTIC][name][pop_id]["y_factor"]
#                    self.pars["characs"][-1].autocalibrate[pop_id] = True

# TODO: Clean this batch of comments once interpopulation dynamics are conclusively handled.
#                    
#        self.contacts = dcp(data["contacts"])   # Simple copying of the contacts structure into data.
                    # No need to be an object.