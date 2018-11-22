"""
Implements data-based model parameters (:py:class:`ParameterSet`)

A :py:class:`ParameterSet` (or 'parset') is an intermediate representation of
model parameters. The main role of the parset is to store the calibration
values that are used to scale model parameters. Therefore, every parameter
in the model appears in the parset, not just the parameters in the databook.

"""

from collections import defaultdict
import numpy as np
import sciris as sc
from .utils import NamedItem, TimeSeries


class Parameter(NamedItem):
    """
    Class to hold one set of parameter values disaggregated by populations.

    :param name: The name of the parameter (should match framework code name)
    :param ts: A dict where the key is population name and the value is a TimeSeries instance

    """

    def __init__(self, name: str, ts: dict):
        NamedItem.__init__(self, name)
        self.ts = ts #: Population-specific data is stored in TimeSeries within this dict, keyed by population name
        self.y_factor = sc.odict.fromkeys(self.ts,1.0) #: Calibration scale factors for the parameter in each population
        self.meta_y_factor = 1.0 #: Calibration scale factor for all populations


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

        if self.ts[pop_name].has_data:
            return True
        else:
            return False

    def interpolate(self, tvec, pop_name: str) -> np.array:
        """
        Return interpolated parameter values for a given population

        :param tvec: A scalar, list, or array or time values
        :param pop_name: The population to interpolate data for
        :return: An array with the interpolated values

        """

        return self.ts[pop_name].interpolate(tvec)


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
        self.pars = sc.odict() #: Stores the Parameter instances contained by this ParameterSet associated with framework comps, characs, and parameters
        self.transfers = sc.odict() #: Stores the Parameter instances contained by this ParameterSet associated with databook transfers, keyed by source population
        self.interactions = sc.odict() #: Stores the Parameter instances contained by this ParameterSet associated with framework interactions, keyed by source population

        # Instantiate all quantities that appear in the databook (compartments, characteristics, parameters)
        for name, tdve in data.tdve.items():
            for pop_name, ts in tdve.ts.items():
                units = framework.get_databook_units(name)
                if units != ts.units:
                    raise Exception('The units entered in the databook do not match the units entered in the framework')
            self.pars[name] = Parameter(name,sc.dcp(tdve.ts))

        # Instantiate parameters not in the databook
        for _, spec in framework.pars.iterrows():
            if spec.name not in self.pars:
                ts = dict()
                units = framework.get_databook_units(spec.name)
                for pop_name in self.pop_names:
                    ts[pop_name] = TimeSeries(units=units)
                self.pars[spec.name] = Parameter(spec.name, ts)

        # Instantiate parameters for transfers and interactions
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

            for source_pop,ts in ts_dict.items():
                item_storage[name][source_pop] = Parameter(name + "_from_" + source_pop, sc.dcp(ts))

    def all_pars(self):
        """
        A generator that returns an iterator over all Parameters

        This is useful because transfers and interaction Parameters are stored in
        nested dictionaries, so it's not trivial to iterate over all parameters

        :return: Generator over all Parameters

        """

        for par in self.pars.values():
            yield par
        for obj in self.transfers.values() + self.interactions.values():
            for par in obj.values():
                yield par

    def copy(self, new_name=None):
        """
        Deep copy the parameter set, optionally changing the name

        :param new_name:
        :return: A new ``ParameterSet`` instance

        """

        x = sc.dcp(self)
        if new_name is not None:
            x.name = new_name
        return x
