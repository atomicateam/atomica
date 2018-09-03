# Imports

import numpy as np
import sciris as sc
from .interpolation import interpolate_func
from .structure import FrameworkSettings as FS
from .system import AtomicaException, logger
from .utils import NamedItem

# Parameter class that stores one array of values converted from raw project data
class Parameter(NamedItem):
    """ Class to hold one set of parameter values disaggregated by populations. """

    def __init__(self, name, t=None, y=None, y_format=None, y_factor=None, autocalibrate=None, meta_y_factor=1.0):
        NamedItem.__init__(self, name)

        # These ordered dictionaries have population names as keys.
        if t is None: t = sc.odict()
        if y is None: y = sc.odict()
        if y_format is None: y_format = sc.odict()
        if y_factor is None: y_factor = sc.odict()
        if autocalibrate is None: autocalibrate = sc.odict()
        self.t = t  # Time data
        self.y = y  # Value data
        self.y_format = y_format  # Value format data (e.g. Probability, Fraction or Number).
        # TODO: Consider whether to support different transformations whether format is relative or absolute.
        self.y_factor = y_factor  # Scaling factor of data.
        self.meta_y_factor = meta_y_factor
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
        tvec = sc.promotetoarray(tvec)
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

        return output

    def __repr__(self, *args, **kwargs):
        return "Parameter: {0}\n\nt\n{1}\ny\n{2}\ny_format\n{3}\ny_factor\n{4}\n".format(self.name, self.t, self.y,
                                                                                         self.y_format, self.y_factor)


# Parset class that contains one set of parameters converted from raw project data

class ParameterSet(NamedItem):
    """ Class to hold all parameters. """

    def __init__(self, name="default"):
        NamedItem.__init__(self, name)

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
        self.interactions = sc.odict()  # Dictionary of inter-population interactions.

        logger.debug("Created ParameterSet: {0}".format(self.name))

    def copy(self, new_name=None):
        x = sc.dcp(self)
        if new_name is not None:
            x.name = new_name
        return x

    def set_scaling_factor(self, par_name, pop_name, scale):
        par = self.get_par(par_name)
        par.y_factor[pop_name] = scale
        return None
    
    def get_scaling_factor(self,par_name,pop_name):
        return self.get_par(par_name).y_factor[pop_name]

    def get_par(self, name):
        for par_type in ["cascade", "comps", "characs"]:
            if name in self.par_ids[par_type].keys():
                return self.pars[par_type][self.par_ids[par_type][name]]
        raise AtomicaException("Name '{0}' cannot be found in parameter set '{1}' as either a cascade parameter, "
                               "compartment or characteristic.".format(name, self.name))

    def make_pars(self, framework, data):
        self.pop_names = data.pops.keys()
        self.pop_labels = [pop["label"] for pop in data.pops.values()]

        # Cascade parameter and characteristic extraction.
        group_remapping = {FS.KEY_PARAMETER:'cascade',FS.KEY_COMPARTMENT:'comps',FS.KEY_CHARACTERISTIC:'characs'}
        for name,tdve in data.tdve.items():
            _,item_type = framework.get_variable(name)
            item_group = group_remapping[item_type]

            self.par_ids[item_group][name] = len(self.pars[item_group])
            self.pars[item_group].append(Parameter(name=name))

            for pop_name,ts in tdve.ts.items():
                tvec, yvec = ts.get_arrays()
                self.pars[item_group][-1].t[pop_name] = tvec
                self.pars[item_group][-1].y[pop_name] = yvec
                if ts.format is not None and ts.format.upper().strip() != FS.DEFAULT_SYMBOL_INAPPLICABLE:
                    if ts.format.lower().strip() in FS.STANDARD_UNITS:
                        self.pars[item_group][-1].y_format[pop_name] = ts.format.lower().strip()
                    else:
                        self.pars[item_group][-1].y_format[pop_name] = ts.format.strip() # Preserve the case if it's not a standard unit
                else:
                    self.pars[item_group][-1].y_format[pop_name] = None
                self.pars[item_group][-1].y_factor[pop_name] = 1.0

        # We have just created Parameter objects for every parameter in the databook
        # However, we also need Parameter objects for dependent parameters not in the databook
        # This allows them to be used in transitions and also for the user to set y-factors for them
        for _,spec in framework.pars.iterrows():
            if spec.name not in self.par_ids['cascade']:
                self.par_ids['cascade'][spec.name] = len(self.pars['cascade'])
                self.pars['cascade'].append(Parameter(name=spec.name))

                for pop_name in self.pop_names:
                    self.pars['cascade'][-1].t[pop_name] = None
                    self.pars['cascade'][-1].y[pop_name] = None
                    self.pars['cascade'][-1].y_format[pop_name] = spec['format'].lower().strip() if spec['format'] is not None else None
                    self.pars['cascade'][-1].y_factor[pop_name] = 1.0

        # Transfer and interaction extraction.
        for tdc in data.transfers + data.interpops:
            if tdc.type == 'transfer':
                item_storage = self.transfers
            elif tdc.type == 'interaction':
                item_storage = self.interactions
            else:
                raise AtomicaException('Unknown time-dependent connection type')

            name = tdc.code_name # The name of this interaction e.g. 'age'
            if name not in item_storage:
                item_storage[name] = sc.odict()

            for pop_link,ts in tdc.ts.items():
                source_pop = pop_link[0]
                target_pop = pop_link[1]
                if pop_link[0] not in item_storage[name]:
                    item_storage[name][source_pop] = Parameter(name=name + "_from_" + source_pop)
                tvec, yvec = ts.get_arrays()
                item_storage[name][source_pop].t[target_pop] = tvec
                item_storage[name][source_pop].y[target_pop] = yvec
                item_storage[name][source_pop].y_format[target_pop] = ts.format
                item_storage[name][source_pop].y_factor[target_pop] = 1.0

        return


