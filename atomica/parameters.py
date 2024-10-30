"""
Implements data-based model parameters (:class:`ParameterSet`)

A :class:`ParameterSet` (or 'parset') is an intermediate representation of
model parameters. The main role of the parset is to store the calibration
values that are used to scale model parameters. Therefore, every parameter
in the model appears in the parset, not just the parameters in the databook.

"""

import io
from collections import defaultdict

import atomica.excel
import numpy as np
import pandas as pd

import sciris as sc
from .utils import NamedItem, TimeSeries
from .system import logger
import itertools
import json
import hashlib
from .version import version, gitinfo

__all__ = ["Parameter", "ParameterSet"]


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
        self._interpolation_method = "linear"  #: Fallback interpolation method. It is _strongly_ recommended not to change this, but to call ``Parameter.smooth()` instead

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
        this would also be applied to any parameter scenarios that have modified the
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
                         a different perturbation will be applied to each time specific value independently.

        """

        for k, ts in self.ts.items():
            self.ts[k] = ts.sample(constant)

    def smooth(self, tvec, method="smoothinterp", pop_names=None, **kwargs):
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
            if method == "smoothinterp":
                # Generating function for smooth-interp interpolator
                def smoothinterp(x1, y1, **kwargs):
                    def fcn(x2):
                        return sc.smoothinterp(x2, x1, y1, **kwargs)

                    return fcn

                method = smoothinterp
            elif method in ["pchip", "linear", "previous"]:
                pass
            else:
                raise Exception("Unknown smoothing method")

        for pop in pop_names:
            ts = self.ts[pop]
            v2 = ts.interpolate(tvec, method=method, **kwargs)
            ts.remove_between((min(tvec), max(tvec)))
            for t, v in zip(tvec, v2):
                ts.insert(t, v)


class Initialization:
    """
    This class stores initial compartment sizes

    In some cases it may be desirable to explicitly set initial compartment sizes rather than
    having them calculated based on the databook values/characteristics. An example of this could
    be wanting to initialize the model using steady-state compartment sizes computed from a
    prior model run. This class facilitates storing/applying the initial compartment sizes as well
    as capturing metadata for validation purposes.
    """

    def __init__(self, values=None, year=None, init_y_factor_hash=None, dt=None):
        """
        Construct an Initialization with explicit initial values

        This function can be used to explicitly set initial compartment sizes. More typically, the initial compartment
        sizes would be drawn from a previous model run. In that case, construct the ``Initialization`` using the
        ``Initialization.from_result()`` method, passing in the parset and result. For users, this is typically handled
        via ``ParameterSet.set_initialization(result)`` which allows easily passing a result into the ``ParameterSet``
        to set the initialization in one step.

        :param values: Provide a dictionary of values with compartment sizes. Keys should be tuples with
                       (comp_name,pop_name) and values should be either scalars (for normal compartments) or
                       arrays (for timed compartments). The size of the arrays for timed compartments will reflect
                       both the duration of the timed compartment and the simulation step size (noting that if timed
                       compartments are being used, the ``Initialization`` instance will not be reusable if the
                       simulation step size is subsequently changed, and will need to be re-created using the new
                       step size).
        :param year: Optionally specify the year used to generate the initialization (for provenance)
        :param init_y_factor_hash: Optionally specify the y-factor hash. If supplied, this will be checked against the parset when the initialization is applied
        :param dt: Optionally specify the timestep used to generate the initialization (for provenance)
        """
        self.year = year
        self.init_y_factor_hash = init_y_factor_hash
        self.dt = dt
        self.values = values

    @classmethod
    def from_result(cls, res, parset=None, year=None):
        """
        Construct an initialization based on a Result

        This method is used to create an ``Initialization`` instance when the initial compartment sizes are
        drawn from the state of a previously-run model. This facilitates initializing the model after numerically
        converging to a steady state or after an initial transient has passed.

        :param res: An Atomica ``Result`` instance
        :param parset: Optionally specify a ``ParameterSet`` instance containing y-factor values. If provided, subsequent
                       use of the initialization will check if the y-factors have changed since the initialization was
                       saved and display a warning if so.
        :param year: Optionally specify the year to draw compartment sizes from in the result. If not provided, the last
                     time point will be used. The year must exactly match a year contained in the result.
        :return: A new ``Initialization`` instance
        """

        from atomica.model import TimedCompartment  # Avoid circular import

        if year is None:
            year = res.model.t[-1]
        elif year not in res.model.t:
            raise Exception(f"Year {year} was not present in the result")

        idx = np.nonzero(res.model.t == year)[0][0]
        values = dict()  #: Dictionary of values with either {'comp':val} or {'comp':[vals]} depending on

        for pop in res.model.pops:
            for comp in pop.comps:
                if isinstance(comp, TimedCompartment):
                    values[(comp.name, pop.name)] = comp._vals[:, idx]
                else:
                    values[(comp.name, pop.name)] = comp.vals[idx]

        self = cls(values)
        self.year = year  #: Record year from which the initialization was originally computed
        self.init_y_factor_hash = None if parset is None else self.hash_y_factors(res.model.framework, parset)  # Record a hash of the Y-factors used for initialization
        self.dt = res.dt
        return self

    @staticmethod
    def hash_y_factors(framework, parset) -> str:
        """
        Hash y-factors used for initialization

        This method calculates a hash of the y-factors for the purpose of identifying if they have
        changed since the Initialization was originally created.

        :param framework: An ``at.Framework`` instance containing setup weights for compartments/characteristics
        :param parset: An ``at.ParameterSet`` instance containing y-factors
        :return: A hash computed from the y-factors used for normal compartment initialization
        """

        init_quantities = {k for k, v in framework.comps["setup weight"].to_dict().items() if v > 0}
        init_quantities.update(k for k, v in framework.characs["setup weight"].to_dict().items() if v > 0)

        d = {}
        for quantity in init_quantities:
            d[quantity] = dict(parset.pars[quantity].y_factor)
            d[quantity]["_meta_y_factor"] = parset.pars[quantity].meta_y_factor  # This might fail if there actually was a population called '_meta_y_factor' but that seems unlikely...

        return hashlib.sha256(json.dumps(d, sort_keys=True).encode("utf-8")).hexdigest()

    def apply(self, pop, framework=None, parset=None) -> None:
        """
        Insert saved values into compartments

        The Initialization may contain a hash of the y-factors for initialization compartments/characteristics that were
        used when the Initialization was generated, if the Initialization was generated based on a previous Result.
        When applying the initialization, if a framework and parset are provided, then the y-factors will be checked to
        determine if there are any differences in the initialization y-factors or not, and a warning will be displayed
        if so.

        :param pop: An at.model.Population instance
        :param framework: Optionally specify a framework object containing the specification of which comps/characs are used for initialization
        :param parset: Optionally specify the requested parset for initialization containing Y-factors to compare to the saved Y-factors
        """
        from atomica.model import TimedCompartment  # Avoid circular import

        # Check the y-factors
        if self.init_y_factor_hash is not None and framework is not None and parset is not None:
            init_y_factor_hash = self.hash_y_factors(framework, parset)
            if init_y_factor_hash != self.init_y_factor_hash:
                logger.warning("Y-factors used for initialization have changed since the saved initialization was generated. These Y-factors will have no effect because a saved initialization is being used. Remove the initialization by setting `Parset.initialization=None` to return to using the Y-factors to adjust the initialization.")

        for comp in pop.comps:
            if isinstance(comp, TimedCompartment):
                if (comp.name, pop.name) not in self.values:
                    comp._vals[:, 0] = 0
                else:
                    comp._vals[:, 0] = self.values[(comp.name, pop.name)]
            else:
                if (comp.name, pop.name) not in self.values:
                    comp.vals[0] = 0
                else:
                    comp.vals[0] = self.values[(comp.name, pop.name)]

    def to_excel(self, writer):
        max_len = max(len(v) if not np.isscalar(v) else 1 for v in self.values.values())
        d = {}
        for k, v in self.values.items():
            d[k] = np.full(max_len, fill_value=np.nan)
            if np.isscalar(v):
                d[k][0] = v
            else:
                d[k][: len(v)] = v

        values = pd.DataFrame(d).T

        metadata = {
            "year": self.year,
            "init_y_factor_hash": self.init_y_factor_hash,
            "dt": self.dt,
        }
        metadata = pd.DataFrame.from_dict(metadata, orient="index")

        metadata.to_excel(writer, sheet_name="Initialization", startcol=0, startrow=0, index=True, header=False)
        values.to_excel(writer, sheet_name="Initialization", startcol=0, startrow=len(metadata) + 1, index=True, header=False)

    def __repr__(self):
        return sc.prepr(self)

    @classmethod
    def from_excel(cls, excelfile: pd.ExcelFile):
        """
        Construct an initialization from saved spreadsheet

        :param excelfile: A ``pd.ExcelFile`` containing an 'Initialization' sheet
        :return:
        """
        # excelfile = spreadsheet.pandas()

        metadata, value_df = atomica.excel.read_dataframes(excelfile.book["Initialization"])

        values = {}
        for k, s in value_df.T.reset_index().T.set_index([0, 1]).iterrows():
            v = s.dropna().values
            values[k] = v[0] if len(v) == 1 else v

        self = cls(values)

        for k, v in metadata.T.reset_index().T.set_index(0)[1].to_dict().items():
            setattr(self, k, v)

        return self


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
          the difference in how they are formatted in the databook)

    :param framework: A :class:`ProjectFramework` instance
    :param data: A :class:`ProjectData` instance
    :param name: Optionally specify the name of the parset

    """

    def __init__(self, framework, data, name="default"):
        NamedItem.__init__(self, name)
        self.version = version  # Track versioning information
        self.gitinfo = gitinfo

        self.pop_names = data.pops.keys()  # : List of all population code names contained in the ``ParameterSet``
        self.pop_labels = [pop["label"] for pop in data.pops.values()]  # : List of corresponding full names for populations
        self.pop_types = [pop["type"] for pop in data.pops.values()]  # : List of corresponding population types

        self.pars = sc.odict()  # : Stores the Parameter instances contained by this ParameterSet associated with framework comps, characs, and parameters
        self.transfers = sc.odict()  # : Stores the Parameter instances contained by this ParameterSet associated with databook transfers, keyed by source population
        self.interactions = sc.odict()  # : Stores the Parameter instances contained by this ParameterSet associated with framework interactions, keyed by source population

        self.initialization = None  #: Optionally store an ``Initialization`` instance to explicitly set initial compartment sizes

        # Instantiate all quantities that appear in the databook (compartments, characteristics, parameters)
        for name, tdve in data.tdve.items():
            ts = sc.odict()
            units = framework.get_databook_units(name).strip().lower()

            # First check units for all quantities
            for k, v in tdve.ts.items():
                if units != v.units.strip().lower():
                    message = f'The units for quantity "{framework.get_label(name)}" in the databook do not match the units in the framework. Expecting "{units}" but the databook contained "{ts.units.strip().lower()}"'
                    raise Exception(message)

            # Then populate the parameter time series
            for k in self.pop_names:
                if k in tdve.ts:
                    ts[k] = tdve.ts[k].copy()
                elif "all" in tdve.ts:
                    ts[k] = tdve.ts["all"].copy()
                elif "All" in tdve.ts:
                    ts[k] = tdve.ts["All"].copy()

            self.pars[name] = Parameter(name, ts)  # Keep only valid populations (discard any extra ones here)

        # Instantiate compartments and characteristics that have a default value and do not appear in the databook
        # Note that the default value will be used in all populations of the appropriate type
        # For the moment, framework validation ensures the default value is 0 - to avoid the confusion of default values being invisibly inserted
        # This requirement could be dropped in future if the use cases end up being unambiguous
        for _, spec in itertools.chain(framework.comps.iterrows(), framework.characs.iterrows()):
            if pd.isna(spec["databook page"]) and not pd.isna(spec["default value"]):
                assert spec.name not in self.pars, f"Quantity '{spec.name}' is not marked in the framework as having a databook page and it has a default value, but it has been loaded into the ParameterSet as data. If the quantity needs to be populated from the databook, either provide a databook page or remove the default value"
                ts = dict()
                units = framework.get_databook_units(name).strip().lower()
                for pop_name in self.pop_names:
                    if data.pops[pop_name]["type"] == spec["population type"]:
                        ts[pop_name] = TimeSeries(units=units, assumption=spec["default value"])
                self.pars[spec.name] = Parameter(spec.name, ts)

        # Instantiate parameters not in the databook
        for _, spec in framework.pars.iterrows():
            if spec.name not in self.pars:
                ts = dict()
                units = framework.get_databook_units(spec.name).strip().lower()
                for pop_name in self.pop_names:
                    if data.pops[pop_name]["type"] == spec["population type"]:
                        ts[pop_name] = TimeSeries(units=units)
                self.pars[spec.name] = Parameter(spec.name, ts)

        # Instantiate parameters for transfers and interactions
        # As with TDVE quantities, these must be initialized from the databook
        for tdc in data.transfers + data.interpops:
            if tdc.type == "transfer":
                item_storage = self.transfers
            elif tdc.type == "interaction":
                item_storage = self.interactions
            else:
                raise Exception("Unknown time-dependent connection type")

            name = tdc.code_name  # The name of this interaction e.g. 'age'
            item_storage[name] = sc.odict()
            ts_dict = defaultdict(dict)

            for pop_link, ts in tdc.ts.items():
                ts_dict[pop_link[0]][pop_link[1]] = ts.copy()

            for source_pop, ts in ts_dict.items():
                item_storage[name][source_pop] = Parameter(name + "_from_" + source_pop, sc.dcp(ts))

    def __setstate__(self, d):
        from .migration import migrate

        self.__dict__ = d
        parset = migrate(self)
        self.__dict__ = parset.__dict__

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
            assert pd.isna(pop), f'"{name}" is a parameter so the ``pop`` should not be specified'
            return self.pars[name]
        elif name in self.transfers:
            assert not pd.isna(pop), f'"{name}" is a transfer, so the ``pop`` must be specified'
            return self.transfers[name][pop]
        elif name in self.interactions:
            assert not pd.isna(pop), f'"{name}" is an interaction, so the ``pop`` must be specified'
            return self.interactions[name][pop]
        else:
            raise KeyError(f'Parameter "{name}" not found')

    def sample(self, constant=True):
        """
        Return a sampled copy of the ParameterSet

        :param constant: If True, time series will be perturbed by a single constant offset. If False,
                         a different perturbation will be applied to each time specific value independently.
        :return: A new :class:`ParameterSet` with perturbed values

        """

        new = sc.dcp(self)
        for par in new.all_pars():
            par.sample(constant)
        return new

    def make_constant(self, year: float):
        """
        Return a constant copy of the ParameterSet

        This function will return a copy of the ParameterSet where all parameter time series have been replaced
        with temporally static versions.

        :param year: Year to use for interpolation
        :return: A copy of the ParameterSet with constant parameters
        """
        ps = self.copy(f"{self.name} (constant)")
        for par in ps.all_pars():
            for ts in par.ts.values():
                ts.insert(None, ts.interpolate(year))
                ts.t = []
                ts.vals = []
        return ps

    # SAVE AND LOAD CALIBRATION (Y-FACTORS)

    @property
    def y_factors(self) -> dict:
        """
        Return y-values in a dictionary

        Note that any missing populations reflect population types. For example, the
        dictionary for a parameter in one population type will not contain any entries
        for populations that belong to another type

        :return: Dictionary keyed by ``(par, pop)`` containing a dict of y-values
        """
        y_factors = {}

        for par_name, par in self.pars.items():
            y_factors[(par_name, None)] = sc.mergedicts({"meta_y_factor": par.meta_y_factor}, par.y_factor)

        for par_name, d in self.interactions.items() + self.transfers.items():
            for pop_name, par in d.items():
                y_factors[(par_name, pop_name)] = sc.mergedicts({"meta_y_factor": par.meta_y_factor}, par.y_factor)

        return y_factors

    def calibration_spreadsheet(self) -> sc.Spreadsheet:
        """
        Return y-values in a spreadsheet

        Note that the tabular structure contains missing entries for any interactions
        that don't exist (e.g. due to missing population types) - these can be identified
        with ``pd.isna``

        :return: Spreadsheet containing y-factors in tabular form
        """

        # Initialize the bytestream
        f = io.BytesIO()

        writer = pd.ExcelWriter(f, engine="xlsxwriter")
        # writer.book.set_properties({"category": "atomica:framework"})
        # standard_formats(writer.book)  # Apply formatting

        # worksheet = writer.book.add_worksheet("Y-factors")

        df = pd.DataFrame(self.y_factors).T
        df.index.set_names(["par", "pop"], inplace=True)
        df.to_excel(writer, sheet_name="Y-factors", merge_cells=False)  # Write index if present

        if self.initialization:
            self.initialization.to_excel(writer)

        # Close the workbook
        writer.close()

        return sc.Spreadsheet(f)

    def set_initialization(self, res, year=None):
        self.initialization = Initialization.from_result(res, parset=self, year=year)

    def apply_initialization(self, pop, framework=None) -> None:
        """

        :param pop: An ``at.Model.Population`` instance containing compartment objects that require initialization
        :param framework: A Framework containing a specification of which compartments/characteristics are ordinarily
                          used for initialization. If a framework is not provided, then the y-factors will not be
                          validated.
        :return:
        """
        if self.initialization is None:
            raise Exception("Attempted to apply an explicit compartment initialization but the parset does not contain an initialization")

        self.initialization.apply(pop, framework, self)

    def save_calibration(self, fname) -> None:
        """
        Save y-values to file

        :param fname: ``str`` or ``Path`` specifying location of file to save

        """
        ss = self.calibration_spreadsheet()
        ss.save(fname)

    def load_calibration(self, spreadsheet: sc.Spreadsheet) -> None:
        """
        Load calibration y-factors

        This function reads a spreadsheet created by ``ParameterSet.save_calibration()`` and
        inserts the y-factors. It is permissive in that

        - If y-factors are present in the spreadsheet and not in the ``ParameterSet`` then they
          will be skipped
        - If y-factors are missing in the spreadsheet, the existing values will be maintained

        :param spreadsheet:
        :return:
        """
        if not isinstance(spreadsheet, sc.Spreadsheet):
            spreadsheet = sc.Spreadsheet(spreadsheet)

        excelfile = spreadsheet.pandas()

        df = pd.read_excel(excelfile, "Y-factors" if "Y-factors" in excelfile.sheet_names else 0)
        df.set_index(["par", "pop"], inplace=True)

        if df.index.duplicated().any():
            msg = "The calibration file contained duplicate entries:"
            for par, pop in df.index[df.index.duplicated()].unique():
                msg += f'\n\t- {par} ({"meta/all populations" if pd.isna(pop) else pop})'
            raise Exception(msg)

        for (par_name, pop_name), values in df.to_dict(orient="index").items():
            try:
                par = self.get_par(par_name, pop_name)
            except KeyError:
                if pop_name:
                    logger.debug(f"{par.name} in {pop_name} was not found, ignoring y-factors for this quantity")
                else:
                    logger.debug(f"{par.name} was not found, ignoring y-factors for this quantity")
                continue

            for k, v in values.items():
                if pd.isna(v):
                    continue

                if k == "meta_y_factor":
                    par.meta_y_factor = v
                else:
                    if k in par.y_factor:
                        par.y_factor[k] = v
                    else:
                        logger.debug(f"The ParameterSet does not define a y-factor for {par.name} in the {k} population (e.g., because the population type does not match the parameter) - skipping")

        if "Initialization" in excelfile.sheet_names:
            self.initialization = Initialization.from_excel(excelfile)

        logger.debug("Loaded calibration from file")
