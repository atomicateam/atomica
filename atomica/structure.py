from .system import AtomicaException
from bisect import bisect
import sciris as sc
import numpy as np
import scipy.interpolate

class FrameworkSettings(object):
    # Holds various constants naming things used throughout Atomica
    KEY_COMPARTMENT = "comp"
    KEY_CHARACTERISTIC = "charac"
    KEY_TRANSITION = "link"
    KEY_PARAMETER = "par"
    KEY_POPULATION = "pop"
    KEY_TRANSFER = "transfer"
    KEY_INTERACTION = "interpop"

    QUANTITY_TYPE_PROBABILITY = "probability"
    QUANTITY_TYPE_DURATION = "duration"
    QUANTITY_TYPE_NUMBER = "number"
    QUANTITY_TYPE_FRACTION = "fraction"
    QUANTITY_TYPE_PROPORTION = "proportion"
    DEFAULT_SYMBOL_INAPPLICABLE = "N.A."

    RESERVED_KEYWORDS = ['t','flow','all'] # A code_name in the framework cannot be equal to one of these values

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
    def __init__(self, t=None, vals=None, format=None, units=None,assumption=None):

        t = sc.promotetoarray(t) if t is not None else list()
        vals = sc.promotetoarray(vals) if vals is not None else list()

        assert len(t) == len(vals)

        self.t = []
        self.vals = []
        self.format = format # TODO - differentiate between format and unit. The format specifies how to scale, while the unit specifies the dimensions. For example, format='number' but unit='Number of people'
        self.units = units
        self.assumption = assumption
        self.sigma = None # Uncertainty value

        for tx, vx in zip(t,vals):
            self.insert(tx, vx)

    def __repr__(self):
        output = sc.prepr(self)
        return output

    @property
    def has_data(self):
        # Returns true if any time-specific data has been entered (not just an assumption)
        return self.assumption is not None or self.has_time_data

    @property
    def has_time_data(self):
        # Returns true if any time-specific data has been entered (not just an assumption)
        return len(self.t) > 0

    def insert(self, t, v):
        # Insert value v at time t maintaining sort order
        # To set the assumption, set t=None
        v = float(v) # Convert input to float

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

    def remove_between(self, t_remove):
        # t is a two element vector [min,max] such that
        # times > min and < max are removed
        # Note that the endpoints are not included!
        for tval in sc.dcp(self.t):
            if t_remove[0] < tval < t_remove[1]:
                self.remove(tval)

    def interpolate(self,t2):
        # Output is guaranteed to be of type np.array
        t2 = sc.promotetoarray(t2) # Deal with case where user prompts for single time point

        if not self.has_data:
            return np.full(t2.shape, np.nan)
        elif not self.has_time_data:
            return np.full(t2.shape, self.assumption)

        t1,v1 = self.get_arrays()

        # Remove NaNs
        idx = ~np.isnan(t1) & ~np.isnan(v1)
        t1 = t1[idx]
        v1 = v1[idx]

        if t1.size == 0:
            raise AtomicaException('No time points remained after removing NaNs from the TimeSeries')
        elif t1.size == 1:
            return np.full(t2.shape,v1[0])
        else:
            v2 = np.zeros(t2.shape)
            f = scipy.interpolate.PchipInterpolator(t1, v1, axis=0, extrapolate=False)
            v2[(t2>=t1[0]) & (t2<=t1[-1])] = f(t2[(t2>=t1[0]) & (t2<=t1[-1])])
            v2[t2<t1[0]] = v1[0]
            v2[t2>t1[-1]] = v1[-1]
            return v2

    def sample(self,t2):
        # This method might sample from the TimeSeries for the given years
        # e.g. `ts.interpolate([2011,2012])` would give the values without uncertainty
        # while `ts.sample([2011,2012])` would perturb the values depending on sigma
        # (and perhaps some other distribution information too)
        raise NotImplementedError()
