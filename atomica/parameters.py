"""
Implements data-based model parameters (:py:class:`ParameterSet`)

A :py:class:`ParameterSet` (or 'parset') is an intermediate representation of
model parameters. The main role of the parset is to store the calibration
values that are used to scale model parameters. Therefore, every parameter
in the model appears in the parset, not just the parameters in the databook.

"""

import numpy as np
import sciris as sc
from .interpolation import interpolate_func
from .system import FrameworkSettings as FS
from .system import logger
from .utils import NamedItem

# Parameter class that stores one array of values converted from raw project data


class Parameter(NamedItem):
    """ Class to hold one set of parameter values disaggregated by populations. """

    def __init__(self, name, t=None, y=None, y_format=None, y_factor=None, autocalibrate=None, meta_y_factor=1.0):
        NamedItem.__init__(self, name)

        # These ordered dictionaries have population names as keys.
        if t is None:
            t = sc.odict()
        if y is None:
            y = sc.odict()
        if y_format is None:
            y_format = sc.odict()
        if y_factor is None:
            y_factor = sc.odict()
        if autocalibrate is None:
            autocalibrate = sc.odict()
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

    def has_values(self, pop_name: str) -> bool:
        """
        Check if any values are present

        Returns True if this Parameter has values specified for the given population
        If the Parameter has an assumption, then the time value will be nan but a
        y-value will be present. If the Parameter normally has a function, then the
        y-value will be None. If a function Parameter has a scenario overwrite applied
        then actual values will be present. Essentially, if this function returns True,
        then the `interpolate()` method will return usable values

        :param pop_name: The code name of a population
        :return: ``True`` if any values are present for specified population, otherwise ``False``

        """

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

    def interpolate(self, tvec, pop_name):  # , extrapolate_nan = False):
        """ Take parameter values and construct an interpolated array corresponding to the input time vector. """

        # Validate input.
        if pop_name not in self.t.keys():
            raise Exception("Cannot interpolate parameter '{0}' "
                            "without referring to a proper population name.".format(pop_name))
        if tvec is None:
            raise Exception("Cannot interpolate parameter '{0}' "
                            "without providing a time vector.".format(self.name))

        if not self.has_values(pop_name):
            raise Exception('Parameter "%s" contains no data for pop "%s", and thus cannot be interpolated' % (self.name, pop_name))

        tvec = sc.promotetoarray(tvec)
        if not len(self.t[pop_name]) > 0:
            raise Exception("There are no timepoint values for parameter '{0}', "
                            "population '{1}'.".format(self.name, pop_name))
        if not len(self.t[pop_name]) == len(self.y[pop_name]):
            raise Exception("Parameter '{0}', population '{1}', does not have corresponding values "
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
    """ Collection of model parameters to run a simulation

    A ParameterSet contains a collection of Parameters required to run the simulation.
    The parameters contain scale factors used for calibration, so often a project will
    contain multiple ParameterSets corresponding to different calibrations.

    Although parameters are constructed from ProjectData, there are two key differences

        - The ParameterSet contains calibration scale factors
        - The ParameterSet expands transfers and interactions into per-population parameters
          so they are stored on an equal basis (whereas ProjectData segregates them in
          :py:class:`TimeDependentValuesEntry` and :py:class:`TimeDependentConnections` due to
          the difference in how they are formatted in the databook

    :param framework: A :py:class:`ProjectFramework` instance
    :param data: A :py:class:`ProjectData` instance
    :param name: Optionally specify the name of the parset

    """

    def __init__(self, framework, data, name="default"):
        NamedItem.__init__(self, name)

        self.pop_names = data.pops.keys() #: List of all population code names contained in the ``ParameterSet``
        self.pop_labels = [pop["label"] for pop in data.pops.values()] #: List of corresponding full names for populations

        # Instantiate all quantities that appear in the databook (compartments, characteristics, parameters)
        for name, tdve in data.tdve.items():
            par = Parameter(name=name)
            self.pars[name] = par
            spec, _ = framework.get_variable(name)
            units = framework.get_databook_units(name) # Note that in general, we EITHER have a base unit and timescale, or a unit string with a timescale suffix

            for pop_name, ts in tdve.ts.items():
                tvec, yvec = ts.get_arrays()
                par.t[pop_name] = tvec
                par.y[pop_name] = yvec
                par.y_format = units
                par.y_factor[pop_name] = 1.0

        # Instantiate parameters not in the databook
        for _, spec in framework.pars.iterrows():
            if spec.name not in self.pars:
                par = Parameter(name=spec.name)
                self.pars[spec.name] = par
                units = framework.get_databook_units(spec.name)

                for pop_name in self.pop_names:
                    par.t[pop_name] = None
                    par.y[pop_name] = None
                    par.y_format[pop_name] = units
                    par.y_factor[pop_name] = 1.0

        # Instantiate parameters for transfers and interactions
        for tdc in data.transfers + data.interpops:
            if tdc.type == 'transfer':
                item_storage = self.transfers
            elif tdc.type == 'interaction':
                item_storage = self.interactions
            else:
                raise Exception('Unknown time-dependent connection type')

            name = tdc.code_name  # The name of this interaction e.g. 'age'
            if name not in item_storage:
                item_storage[name] = sc.odict()

            for pop_link, ts in tdc.ts.items():
                source_pop = pop_link[0]
                target_pop = pop_link[1]
                if pop_link[0] not in item_storage[name]:
                    item_storage[name][source_pop] = Parameter(name=name + "_from_" + source_pop)
                tvec, yvec = ts.get_arrays()
                item_storage[name][source_pop].t[target_pop] = tvec
                item_storage[name][source_pop].y[target_pop] = yvec
                item_storage[name][source_pop].y_format[target_pop] = ts.units # The user can set the units in TDCs in the databook (unlike the TDVEs used above)
                item_storage[name][source_pop].y_factor[target_pop] = 1.0

    def copy(self, new_name=None):
        x = sc.dcp(self)
        if new_name is not None:
            x.name = new_name
        return x

    def set_scaling_factor(self, par_name, pop_name, scale):
        par = self.get_par(par_name)
        par.y_factor[pop_name] = scale
        return None

    def get_scaling_factor(self, par_name, pop_name):
        return self.get_par(par_name).y_factor[pop_name]

    def get_par(self, name):
        if name in self.pars:
            return self.pars[name]
        else:
            raise Exception("Name '{0}' cannot be found in parameter set '{1}'".format(name, self.name))
