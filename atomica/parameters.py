"""
Implements data-based model parameters (:class:`ParameterSet`)

A :class:`ParameterSet` (or 'parset') is an intermediate representation of
model parameters. The main role of the parset is to store the calibration
values that are used to scale model parameters. Therefore, every parameter
in the model appears in the parset, not just the parameters in the databook.

"""

from collections import defaultdict
import numpy as np
import sciris as sc
from .utils import NamedItem, TimeSeries
import scipy.interpolate


class Parameter(NamedItem):
    """
    Class to hold one set of parameter values disaggregated by populations.

    :param name: The name of the parameter (should match framework code name)
    :param ts: A dict where the key is population name and the value is a TimeSeries instance

    """

    def __init__(self, name: str, ts: dict):
        NamedItem.__init__(self, name)
        self.ts = ts  # : Population-specific data is stored in TimeSeries within this dict, keyed by population name
        self.y_factor = sc.odict.fromkeys(self.ts, 1.0)  # : Calibration scale factors for the parameter in each population
        self.meta_y_factor = 1.0  # : Calibration scale factor for all populations
        self.skip_function = sc.odict.fromkeys(self.ts, None)  # : This can be a range of years [start,stop] between which the parameter function will not be evaluated
        self._interpolation_method = 'linear'  #: Fallback interpolation method. It is _strongly_ recommended not to change this, but to call ``Parameter.smooth()` instead

    @property
    def pops(self):
        """
        Get populations contained in the Parameter

        :return: Generator/list of available populations

        """

        return self.ts.keys()

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

        if pop_name not in self.ts:
            return False
        elif self.ts[pop_name].has_data:
            return True
        else:
            return False

    def interpolate(self, tvec, pop_name: str) -> np.array:
        """
        Return interpolated parameter values for a given population

        The Parameter internally stores the interpolation method. The default is linear.
        It is possible to set it to 'pchip' or 'previous' or some other method. However,
        this would also also be applied to any parameter scenarios that have modified the
        parameter and require interpolation. Therefore, it is STRONGLY recommended not to
        modify the fallback interpolation method, but to instead call `Parameter.smooth()`
        in advance with the appropriate options, if the interpolation matters.

        :param tvec: A scalar, list, or array or time values
        :param pop_name: The population to interpolate data for
        :return: An array with the interpolated values

        """

        return self.ts[pop_name].interpolate(tvec, method=self._interpolation_method)

    def sample(self, constant: bool) -> None:
        """
        Perturb parameter based on uncertainties

        This function modifies the parameter in-place. It would normally be called via
        :meth:`ParameterSet.sample()` which is responsible for copying this instance first.

        :param constant: If True, time series will be perturbed by a single constant offset. If False,
                         an different perturbation will be applied to each time specific value independently.

        """

        for k, ts in self.ts.items():
            self.ts[k] = ts.sample(constant)

    def smooth(self, tvec, method='smoothinterp', pop_names=None, **kwargs):
        """
        Smooth the parameter's time values

        Normally, Parameter instances contain temporally-sparse values from the databook.
        These are then interpolated to get the input parameter values at all model time points.
        The default interpolation is linear. However, sometimes it may be desired to make specific
        assumptions about the parameter value at intermediate times. These could be added directly
        to the Parameter's underlying `TimeSeries`.

        This method applies a smoothing method to the Parameter, modifying the underlying TimeSeries
        in-place. The operation is

        - Interpolated or smoothed values are generated for the requested times
        - All existing time points between and including the minimum and maximum values of `tvec` are removed
        - The time values generated in this function are inserted

        For example, to apply pchip interpolation to generate intermediate values

        >>> Parameter.smooth(P.settings.tvec, method='pchip',**kwargs)

        As this goes through `TimeSeries.interpolate` the same rules apply for the conditions under which
        the interpolation function gets used - specifically, interpolation is used if there are at least two
        finite time values present, otherwise, the assumption or single value will be used.

        :param tvec: New time points to add to the TimeSeries
        :param method: Method for generation of smoothed/interpolated values, default uses sciris smoothinterp
        :param pop_names: Optionally specify a list of populations to modify
        :param kwargs: Optionally pass arguments to the generating function/class constructor
        :return:

        """

        pop_names = sc.promotetolist(pop_names)
        if not pop_names:
            pop_names = self.ts.keys()

        if sc.isstring(method):
            if method == 'smoothinterp':
                # Generating function for smooth-interp interpolator
                def smoothinterp(x1, y1, **kwargs):
                    def fcn(x2):
                        return sc.smoothinterp(x2, x1, y1, **kwargs)
                    return fcn
                method = smoothinterp
            elif method in ['pchip', 'linear', 'previous']:
                pass
            else:
                raise Exception('Unknown smoothing method')

        for pop in pop_names:
            ts = self.ts[pop]
            v2 = ts.interpolate(tvec, method=method, **kwargs)
            ts.remove_between((min(tvec), max(tvec)))
            for t, v in zip(tvec, v2):
                ts.insert(t, v)


class ParameterSet(NamedItem):
    """
    Collection of model parameters to run a simulation

    A ParameterSet contains a collection of Parameters required to run the simulation.
    The parameters contain scale factors used for calibration, so often a project will
    contain multiple ParameterSets corresponding to different calibrations.

    Although parameters are constructed from ProjectData, there are two key differences

        - The ParameterSet contains calibration scale factors
        - The ParameterSet expands transfers and interactions into per-population parameters
          so they are stored on an equal basis (whereas ProjectData segregates them in
          :class:`TimeDependentValuesEntry` and :class:`TimeDependentConnections` due to
          the difference in how they are formatted in the databook

    :param framework: A :class:`ProjectFramework` instance
    :param data: A :class:`ProjectData` instance
    :param name: Optionally specify the name of the parset

    """

    def __init__(self, framework, data, name="default"):
        NamedItem.__init__(self, name)

        self.pop_names = data.pops.keys()  # : List of all population code names contained in the ``ParameterSet``
        self.pop_labels = [pop["label"] for pop in data.pops.values()]  # : List of corresponding full names for populations
        self.pop_types = [pop['type'] for pop in data.pops.values()]  # : List of corresponding population types

        self.pars = sc.odict()  # : Stores the Parameter instances contained by this ParameterSet associated with framework comps, characs, and parameters
        self.transfers = sc.odict()  # : Stores the Parameter instances contained by this ParameterSet associated with databook transfers, keyed by source population
        self.interactions = sc.odict()  # : Stores the Parameter instances contained by this ParameterSet associated with framework interactions, keyed by source population

        # Instantiate all quantities that appear in the databook (compartments, characteristics, parameters)
        for name, tdve in data.tdve.items():
            units = framework.get_databook_units(name).strip().lower()
            for pop_name, ts in tdve.ts.items():  # The TDVE has already been validated to contain any required populations (although it might also contain extra ones)
                if units != ts.units.strip().lower():
                    message = f'The units for quantity "{framework.get_label(name)}" in the databook do not match the units in the framework. Expecting "{units}" but the databook contained "{ts.units.strip().lower()}"'
                    raise Exception(message)
            self.pars[name] = Parameter(name, sc.odict({k: v.copy() for k, v in tdve.ts.items() if k in self.pop_names}))  # Keep only valid populations (discard any extra ones here)

        # Instantiate parameters not in the databook
        for _, spec in framework.pars.iterrows():
            if spec.name not in self.pars:
                ts = dict()
                units = framework.get_databook_units(spec.name)
                for pop_name in self.pop_names:
                    if data.pops[pop_name]['type'] == spec['population type']:
                        ts[pop_name] = TimeSeries(units=units)
                self.pars[spec.name] = Parameter(spec.name, ts)

        # Instantiate parameters for transfers and interactions
        # As with TDVE quantities, these must be initialized from the databook
        for tdc in data.transfers + data.interpops:
            if tdc.type == 'transfer':
                item_storage = self.transfers
            elif tdc.type == 'interaction':
                item_storage = self.interactions
            else:
                raise Exception('Unknown time-dependent connection type')

            name = tdc.code_name  # The name of this interaction e.g. 'age'
            item_storage[name] = sc.odict()
            ts_dict = defaultdict(dict)

            for pop_link, ts in tdc.ts.items():
                ts_dict[pop_link[0]][pop_link[1]] = ts.copy()

            for source_pop, ts in ts_dict.items():
                item_storage[name][source_pop] = Parameter(name + "_from_" + source_pop, sc.dcp(ts))

    def all_pars(self):
        """
        Return an iterator over all Parameters

        This is useful because transfers and interaction :class:`Parameter` instances are stored in
        nested dictionaries, so it's not trivial to iterate over all of them.

        :return: Generator over all :class:`Parameter` instances contained in the ``ParameterSet``

        """

        for par in self.pars.values():
            yield par
        for obj in self.transfers.values() + self.interactions.values():
            for par in obj.values():
                yield par

    def get_par(self, name: str, pop: str = None) -> Parameter:
        """
        Retrieve parameter instance

        The parameter values for interactions and transfers are stored keyed by
        the source/from population. Thus, if the quantity name is an interaction
        or transfer, it is also necessary to specify the source population in order
        to return a :class:`Parameter` instance.

        :param name: The code name of a parameter, interaction, or transfer
        :param pop:
        :return: A :class:`Parameter` instance
        """

        if name in self.pars:
            assert pop is None, f'"{name}" is a parameter so the ``pop`` should not be specified'
            return self.pars[name]
        elif name in self.transfers:
            assert pop is not None, f'"{name}" is a transfer, so the ``pop`` must be specified'
            return self.transfers[name][pop]
        elif name in self.interactions:
            assert pop is not None, f'"{name}" is an interaction, so the ``pop`` must be specified'
            return self.interactions[name][pop]
        else:
            raise Exception(f'Parameter "{name}" not found')

    def sample(self, constant=True):
        """
        Return a sampled copy of the ParameterSet

        :param constant: If True, time series will be perturbed by a single constant offset. If False,
                         an different perturbation will be applied to each time specific value independently.
        :return: A new :class:`ParameterSet` with perturbed values

        """

        new = sc.dcp(self)
        for par in new.all_pars():
            par.sample(constant)
        return new
