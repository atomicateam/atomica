"""
Define utility classes used throughout Atomica

"""

import inspect
import os
import ast
from bisect import bisect
import numpy as np
import scipy.interpolate
import sciris as sc
import itertools


def parent_dir():
    # Return the parent directory of the file that called this function
    return os.path.join(os.path.abspath(os.path.join(inspect.stack()[1][1], os.pardir)), '')


class NamedItem():
    def __init__(self, name:str=None):
        """
        NamedItem constructor

        A name must be a string

        :param name:
        """
        if name is None:
            name = '<unnamed>'
        self.name = name
        self.created = sc.now()
        self.modified = sc.now()

    def copy(self, name=None):
        x = sc.dcp(self)
        if name is not None:
            x.name = name
        return x

    def __repr__(self):
        return sc.prepr(self)


class NDict(sc.odict):
    """
    Store and sync items with a name property

    """

    def __init__(self, *args, **kwargs):
        sc.odict.__init__(self, *args, **kwargs)
        return None

    def __setitem__(self, key, item):
        # Store an item in the NDict with an explicitly provided key. If the item is a NamedItem
        # then the name of the item will be automatically synchronized - otherwise, it will just behave
        # like a normal odict
        sc.odict.__setitem__(self, key, item)

        # If it is a NamedItem, then synchronize the name of the object with the specified string key
        if sc.isstring(key) and isinstance(item, NamedItem):
            item.name = key
            item.modified = sc.now()
        return None

    def append(self, value):
        # Insert a NamedItem into the NDict by using the name of the item as the key. Of course this only
        # works for NamedItems, otherwise you have to explicitly provide the key
        if not isinstance(value, NamedItem):
            raise Exception('Can only automatically get the name from NamedItems. Instead of `x.append(y)` you need `x["name"]=y`')
        key = value.name
        sc.odict.append(self, key=key, value=value)
        return None

    def copy(self, old, new):
        """
        Copy an item and return the copy

        :param old: The key of the existing item
        :param new: The new name for the item
        :return: The copied item

        Example usage:
        >>> new_parset = proj.parsets.copy('old_name','new_name')

        """
        sc.odict.copy(self, old, new)
        if isinstance(self[new], NamedItem):
            self[new].name = new
        return self[new]


class TimeSeries(object):
    """
    Class to store time-series data

    Internally values are stored as lists rather than numpy arrays because
    insert/remove operations on lists tend to be faster (and working with sparse
    data is a key role of TimeSeries objects). Note that methods like :meth:`interpolate()`
    return numpy arrays, so the output types from such functions should generally match up
    with what is required by the calling function.

    :param t: Optionally specify a scalar, list, or array of time values
    :param vals: Optionally specify a scalar, list, or array of values (must be same size as ``t``)
    :param units: Optionally specify units (as a string)
    :param assumption: Optionally specify a scalar assumption
    :param sigma: Optionally specify a scalar uncertainty

    """

    def __init__(self, t=None, vals=None, units: str = None, assumption: float = None, sigma: float = None):
        t = sc.promotetolist(t) if t is not None else list()
        vals = sc.promotetolist(vals) if vals is not None else list()

        assert len(t) == len(vals)

        self.t = []  #: Sorted array of time points. Normally interacted with via methods like :meth:`insert()`
        self.vals = []  #: Time-specific values - indices correspond to ``self.t``
        self.units = units  #: The units of the quantity
        self.assumption = assumption  #: The time-independent scalar assumption
        self.sigma = sigma  #: Uncertainty value, assumed to be a standard deviation
        self._sampled = False  #: Flag to indicate whether sampling has been performed. Once sampling has been performed, cannot sample again

        for tx, vx in zip(t, vals):
            self.insert(tx, vx)

    def __repr__(self):
        output = sc.prepr(self)
        return output

    def __deepcopy__(self, memodict={}):
        new = TimeSeries.__new__(TimeSeries)
        new.t = self.t.copy()
        new.vals = self.vals.copy()
        new.units = self.units
        new.assumption = self.assumption
        new.sigma = self.sigma
        new._sampled = self._sampled
        return new

    # The operators for + and * below are prototypes but haven't been added
    # The reason is because they add a lot of complexity to the usage of the class
    # but it's not clear whether that complexity is worth it for the benefits it brings.
    # Part of the problem is also that propagation of uncertainty requires the time series
    # values which means that propagation of uncertainty is time dependent. So it's hard
    # to come up with intuitive behaviour for them.
    #
    # def __add__(self, other):
    #     """
    #     Add a constant or TimeSeries
    #
    #     If adding a constant, it is simply added onto the assumption and time values.
    #
    #     If adding another TimeSeries:
    #
    #         - The units must match
    #         - The assumption will be None if either TimeSeries has no assumption
    #         - The output times will be the union of times in both TimeSeries and they will
    #           be interpolated onto those times before adding. This preserves commutativity
    #           of addition
    #         - Uncertainties will be formally propagated
    #
    #     :param other: A TimeSeries or a scalar (float)
    #     :return: A new TimeSeries
    #
    #     """
    #
    #     if type(other) == type(self):
    #         # If we are operating on another TimeSeries
    #         if self.units is None:
    #             assert other.units is None, 'TimeSeries units must match for addition'
    #         else:
    #             assert self.units == other.units, 'TimeSeries units must match for addition'
    #
    #         new = self.copy()
    #
    #         # Add time values
    #         if self.t == other.t:
    #             new.t = [x+y for x,y in zip(self.vals, other.vals)]
    #         else:
    #             # Interpolate and add the time values
    #             t_out = sorted(set(self.t).union(set(other.t)))
    #             new.t = t_out
    #             new.vals = (self.interpolate(t_out) + other.interpolate(t_out)).tolist()
    #
    #         # Add the assumption
    #         if (self.assumption is None) or (other.assumption is None):
    #             new.assumption = None
    #         else:
    #             new.assumption = self.assumption + other.assumption
    #
    #         # Propagate uncertainty
    #         self_sigma = self.sigma if self.sigma else 0
    #         other_sigma = other.sigma if other.sigma else 0
    #
    #         if self_sigma or other_sigma:
    #             new.sigma = np.sqrt(self_sigma**2 + other_sigma**2)
    #     else:
    #         # Should be a numeric type
    #         new = self.copy()
    #         new.vals = [x+other for x in self.vals]
    #         new.assumption = self.assumption+other if self.assumption is not None else None
    #
    #     return new
    #
    # def __mul__(self, other):
    #     """
    #     Multiply by a constant or TimeSeries
    #
    #     If multiplying by a constant, it is simply operated on the assumption,
    #     values, and uncertainty.
    #
    #     If adding another TimeSeries:
    #
    #         - The units must match
    #         - The assumption will be None if either TimeSeries has no assumption
    #         - The output times will be the union of times in both TimeSeries and they will
    #           be interpolated onto those times before multiplying. This preserves commutativity
    #           of multiplication
    #         - Uncertainties will be formally propagated
    #
    #     :param other: A TimeSeries or a scalar (float)
    #     :return: A new TimeSeries
    #
    #     """
    #
    #     if type(other) == type(self):
    #         # If we are operating on another TimeSeries
    #         if self.units is None:
    #             assert other.units is None, 'TimeSeries units must match for addition'
    #         else:
    #             assert self.units == other.units, 'TimeSeries units must match for addition'
    #
    #         new = self.copy()
    #
    #         # Add time values
    #         if self.t == other.t:
    #             new.t = [x+y for x,y in zip(self.vals, other.vals)]
    #         else:
    #             # Interpolate and add the time values
    #             t_out = sorted(set(self.t).union(set(other.t)))
    #             new.t = t_out
    #             new.vals = (self.interpolate(t_out) * other.interpolate(t_out)).tolist()
    #
    #         # Add the assumption
    #         if (self.assumption is None) or (other.assumption is None):
    #             new.assumption = None
    #         else:
    #             new.assumption = self.assumption * other.assumption
    #
    #         # Propagate uncertainty
    #         if (self.sigma is None) or (other.sigma is None):
    #             new.sigma = None
    #         else:
    #             raise NotImplementedError # Proper propagation is time dependent
    #
    #     else:
    #         # Should be a numeric type
    #         new = self.copy()
    #         new.vals = [x*other for x in self.vals]
    #         new.assumption = self.assumption*other if self.assumption is not None else None
    #         new.assumption = self.sigma*other if self.sigma is not None else None
    #
    #     return new

    def copy(self):
        """
        Return a copy of the ``TimeSeries``

        :return: An independent copy of the ``TimeSeries``
        """

        return self.__deepcopy__(self)

    @property
    def has_data(self) -> bool:
        """
        Check if any data has been provided

        :return: ``True`` if any data has been entered (assumption or time-specific)

        """
        return self.assumption is not None or self.has_time_data

    @property
    def has_time_data(self) -> bool:
        """
        Check if time-specific data has been provided

        Unlike ``has_data``, this will return ``False`` if only an assumption has been entered

        :return: ``True`` if any time-specific data has been entered

        """
        # Returns true if any time-specific data has been entered (not just an assumption)
        return len(self.t) > 0

    def insert(self, t, v) -> None:
        """
        Insert a value at a particular time

        If the value already exists in the ``TimeSeries``, it will be overwritten/updated.
        The arrays are internally sorted by time value, and this order will be maintained.

        :param t: Time value to insert or update. If ``None``, the value will be assigned to the assumption
        :param v: Value to insert. If ``None``, this function will return immediately without doing anything

        """

        if v is None:  # Can't cast a None to a float, just skip it
            return

        v = float(v)  # Convert input to float

        if t is None:
            self.assumption = v
        elif t in self.t:
            idx = self.t.index(t)
            self.vals[idx] = v
        else:
            idx = bisect(self.t, t)
            self.t.insert(idx, t)
            self.vals.insert(idx, v)

    def get(self, t) -> float:
        """
        Retrieve value at a particular time

        This function will automatically retrieve the value of the assumption if
        no time specific values have been provided, or if any time specific values
        are provided, will return the value entered at that time. If time specific
        values have been entered and the requested time is not explicitly present,
        an error will be raised.

        This function may be deprecated in future because generally it is more useful
        to either call ``TimeSeries.interpolate()`` if interested in getting values at
        arbitrary times, or ``TimeSeries.get_arrays()`` if interested in retrieving
        values that have been entered.

        :param t: A time value. If ``None``, will return assumption regardless of whether
                  time data has been entered or not
        :return: The value at the corresponding time. Returns None if the value no value present
        """

        if t is None or len(self.t) == 0:
            return self.assumption
        elif t in self.t:
            return self.vals[self.t.index(t)]
        else:
            return None

    def get_arrays(self):
        """
        Return arrays with the contents of this TimeSeries

        The TimeSeries instance may have time values, or may simply have
        an assumption. If obtaining raw arrays is desired, this function will
        return arrays with values extracted from the appropriate attribute of the
        TimeSeries. However, in general, it is usually `.interpolate()` that is
        desired, rather than `.get_arrays()`

        :return: Tuple with two arrays - the first item is times (with a single NaN if
                 the TimeSeries only has an assumption) and the second item is values

        """
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
            raise Exception('Item not found')

    def remove_before(self,t_remove) -> None:
        """
        Remove times from start

        :param tval: Remove times up to but not including this time
        """

        for tval in sc.dcp(self.t):
            if tval < t_remove:
                self.remove(tval)

    def remove_after(self, t_remove) -> None:
        """
        Remove times from start

        :param tval: Remove times up to but not including this time
        """

        for tval in sc.dcp(self.t):
            if tval > t_remove:
                self.remove(tval)

    def remove_between(self, t_remove):
        # t is a two element vector [min,max] such that
        # times > min and < max are removed
        # Note that the endpoints are not included!
        for tval in sc.dcp(self.t):
            if t_remove[0] < tval < t_remove[1]:
                self.remove(tval)

    def interpolate(self, t2: np.array) -> np.array:
        """
        Return interpolated values

        :param t2: float, list, or array, with times
        :return: array the same length as t2, with interpolated values

        """

        t2 = sc.promotetoarray(t2)  # Deal with case where user prompts for single time point

        if not self.has_data:
            return np.full(t2.shape, np.nan)
        elif not self.has_time_data:
            return np.full(t2.shape, self.assumption)

        t1, v1 = self.get_arrays()
        return interpolate(t1, v1, t2)

    def sample(self, constant=True):
        """
        Return a sampled copy of the TimeSeries

        This method returns a copy of the TimeSeries in which the values have been
        perturbed based on the uncertainty value.

        :param constant: If True, time series will be perturbed by a single constant offset. If False,
                         an different perturbation will be applied to each time specific value independently.
        :return: A copied ``TimeSeries`` with perturbed values

        """

        if self._sampled:
            raise Exception('Sampling has already been performed - can only sample once')

        new = self.copy()
        if self.sigma is not None:
            delta = self.sigma * np.random.randn(1)[0]
            if self.assumption is not None:
                new.assumption += delta

            if constant:
                # Use the same delta for all data points
                new.vals = [v+delta for v in new.vals]
            else:
                # Sample again for each data point
                for i, (v, delta) in enumerate(zip(new.vals, self.sigma * np.random.randn(len(new.vals)))):
                    new.vals[i] = v+delta

        # Sampling flag only needs to be set if the TimeSeries had data to change
        if new.has_data:
            new._sampled = True

        return new


def evaluate_plot_string(plot_string: str):
    """
    Evaluate a plotting output specification

    The plots in the framework are specified as strings - for example,

    >>> plot_string = "{'New active DS-TB':['pd_div:flow','nd_div:flow']}"

    This needs to be (safely) evaluated so that the actual dict can be
    used. This function evaluates a string like this and returns a
    variable accordingly. For example

    >>> x = evaluate_plot_string("{'New active DS-TB':['pd_div:flow','nd_div:flow']}")

    is the same as

    >>> x = {'New active DS-TB':['pd_div:flow','nd_div:flow']}

    This will only happen if tokens associated with dicts and lists are present -
    otherwise the original string will just be returned directly

    :param plot_string: A string representation of Python structures (e.g., lists, dicts)
    :return: Evaluated expression, the same as if it has originally been entered in a .py file
    """

    if '{' in plot_string or '[' in plot_string:
        # Evaluate the string to set lists and dicts - do at least a little validation
        assert '__' not in plot_string, 'Cannot use double underscores in functions'
        assert len(plot_string) < 1800  # Function string must be less than 1800 characters
        fcn_ast = ast.parse(plot_string, mode='eval')
        for node in ast.walk(fcn_ast):
            if not (node is fcn_ast):
                assert isinstance(node, ast.Dict) or isinstance(node, ast.Str) or isinstance(node, ast.List) or isinstance(node, ast.Load), 'Only allowed to initialize lists and dicts of strings here'
        compiled_code = compile(fcn_ast, filename="<ast>", mode="eval")
        return eval(compiled_code)
    else:
        return plot_string


def format_duration(t: float, pluralize=False) -> str:
    """
    User-friendly string format of a duration

    This helper function is used when displaying durations in plots. It takes in
    a duration in units of years, and returns a string representation in user-friendly
    units. This function is mainly intended to be used to format denominators
    e.g., going from 'probability' and '1/365' to 'probability/day'

    :param t: A duration in units of years
    :param pluralize: Always return a plural suffix
    :return: A string

    Example usage:

    >>> format_duration(1)
    'year'
    >>> format_duration(1, pluralize=True)
    'years'
    >>> format_duration(1/365)
    'day'
    >>> format_duration(2/365)
    '2 days'
    >>> format_duration(1.5/52)
    '1.5 weeks'
    >>> format_duration(2/52)
    'fortnight'
    >>> format_duration(2.5/12)
    '2.5 months'

    """

    # First decide the base units
    if t >= 1.0:
        base_scale = 1
        timescale = 'year'
    elif t >= 1 / 12:
        base_scale = 1 / 12
        timescale = 'month'
    elif t >= 1 / 26:
        base_scale = 1 / 26
        timescale = 'fortnight'
    elif t >= 1 / 52:
        base_scale = 1 / 52
        timescale = 'week'
    else:
        base_scale = 1 / 365
        timescale = 'day'

    # Then, work out how many of the base unit there are
    converted_t = t / base_scale

    # If there is only one of the base unit, then return the timescale as the final string
    if abs(converted_t - 1.0) < 1e-5:
        return (timescale + 's') if pluralize else timescale
    elif converted_t % 1 < 1e-3:  # If it's sufficiently close to an integer, show it as an integer
        return '%d %ss' % (converted_t, timescale)
    else:
        return '%s %ss' % (sc.sigfig(converted_t, keepints=True, sigfigs=3), timescale)


def interpolate(x: np.array, y: np.array, x2: np.array, extrapolate=True) -> np.array:
    """
    pchip interpolation with constant extrapolation

    Atomica's standard interpolation routine is based on the pchip method. However, when
    extrapolation is desired (such as when interpolating parameters), it is most useful to
    assume the derivative is zero outside the original range of the function, rather than
    the default pchip behaviour of extrapolating with constant gradient.

    :param x: Original x values
    :param y: Original function values
    :param x2: New desired x values
    :param extrapolate: If True, use constant interpolation outside the original domain. Otherwise,
                        the function value will be NaN. Note that in general, model outputs
                        should not be extrapolated
    :return: Array the same size as ``x2`` with interpolated values

    """

    # Remove NaNs - note that advanced indexing means that the variable is copied
    idx = ~np.isnan(x) & ~np.isnan(y)
    x = x[idx]
    y = y[idx]

    if x.size == 0:
        raise Exception('No time points remained after removing NaNs from the TimeSeries')
    elif x.size == 1:
        return np.full(x2.shape, y[0])
    else:
        f = scipy.interpolate.PchipInterpolator(x, y, axis=0, extrapolate=False)
        if extrapolate:
            y2 = np.zeros(x2.shape)
            y2[(x2 >= x[0]) & (x2 <= x[-1])] = f(x2[(x2 >= x[0]) & (x2 <= x[-1])])
            y2[x2 < x[0]] = y[0]
            y2[x2 > x[-1]] = y[-1]
        else:
            y2 = f(x2)  # PchipInterpolator will return NaNs outside the domain
        return y2


def floor_interpolator(x, y):
    """
    Stepped (single-sided nearest neighbour) interpolation

    This returns a function that does interpolation where the return value
    corresponds to the nearest smaller neighbour (and NaN if extrapolating)

    :param x: Original x values
    :param y: Original y values
    :return: Function object `f(x)` that performs interpolation

    Example usage:

    >>> f = floor_interpolator([1,2,3,4],[1,2,3,4])
    >>> (f(0.5) )
    [nan]
    >>> (f(1))
    [1.]
    >>> (f(1.5))
    [1.]
    >>> (f(2))
    [2.]
    >>> (f(4))
    [4.]
    >>> (f(5))
    [nan]
    >>> (f([0.5,1,1.5,2,4,5]))
    [nan  1.  1.  2.  4. nan]

    """
    # Return a function that returns the floor interpolation for given values (and NaN if out of range)
    x = sc.promotetoarray(x)
    y = sc.promotetoarray(y)

    idx = np.argsort(x)
    x = x[idx]
    y = y[idx]

    def f(x2):
        x2 = sc.promotetoarray(x2)
        out = np.full(x2.shape, np.nan)
        for i, v in enumerate(x2):
            if v > x[-1]:
                continue

            flt = np.where(x <= v)[0]
            if not len(flt):
                continue

            out[i] = y[flt[-1]]

        return out

    return f


def nested_loop(inputs, loop_order):
    """
    Zip list of lists in order

    This is used in :func:`plot_bars` to control whether 'times' or 'results' are the
    outer grouping. This function takes in a list of lists to iterate over, and their
    nesting order. It then yields tuples of items in the given order. Only tested
    for two levels (which are all that get used in :func:`plot_bars` but in theory
    supports an arbitrary number of items.

    :param inputs: List of lists. All lists should have the same length
    :param loop_order: Nesting order for the lists
    :return: Generator yielding tuples of items, one for each list

    Example usage:

    >>> list(nested_loop([['a','b'],[1,2]],[0,1]))
    [['a', 1], ['a', 2], ['b', 1], ['b', 2]]

    Notice how the first two items have the same value for the first list
    while the items from the second list vary. If the `loop_order` is
    reversed, then:

    >>> list(nested_loop([['a','b'],[1,2]],[1,0]))
    [['a', 1], ['b', 1], ['a', 2], ['b', 2]]

    Notice now how now the first two items have different values from the
    first list but the same items from the second list.

    """

    loop_order = list(loop_order) # Convert to list, in case loop order was passed in as a generator e.g. from map()
    inputs = [inputs[i] for i in loop_order]
    iterator = itertools.product(*inputs)  # This is in the loop order
    for item in iterator:
        out = [None] * len(loop_order)
        for i in range(len(item)):
            out[loop_order[i]] = item[i]
        yield out
