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


def parent_dir():
    # Return the parent directory of the file that called this function
    return os.path.join(os.path.abspath(os.path.join(inspect.stack()[1][1], os.pardir)), '')


class NamedItem(object):
    def __init__(self, name=None):
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

        # If it is a NamedItem, then synchronize the name of the object with the specified key
        if isinstance(item, NamedItem):
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
        sc.odict.copy(self, old, new)
        if isinstance(self[new], NamedItem):
            self[new].name = new
        return None


class TimeSeries(object):
    def __init__(self, t=None, vals=None, units=None, assumption=None):

        t = sc.promotetolist(t) if t is not None else list()
        vals = sc.promotetolist(vals) if vals is not None else list()

        assert len(t) == len(vals)

        self.t = []
        self.vals = []
        self.units = units
        self.assumption = assumption
        self.sigma = None  # Uncertainty value

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
        return new

    def copy(self):
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
        # Insert value v at time t maintaining sort order
        # To set the assumption, set t=None

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

    def get(self, t):
        # To get the assumption, set t=None
        if t is None or len(self.t) == 0:
            return self.assumption
        elif t in self.t:
            return self.vals[self.t.index(t)]
        else:
            raise Exception('Item not found')

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

    def sample(self, t2):
        """
        Not yet implemented

        This method might sample from the TimeSeries for the given years
        e.g. `ts.interpolate([2011,2012])` would give the values without uncertainty
        while `ts.sample([2011,2012])` would perturb the values depending on sigma
        (and perhaps some other distribution information too)

        :param t2:
        :return: None

        """

        raise NotImplementedError()


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
    elif t >= 1/12:
        base_scale = 1/12
        timescale = 'month'
    elif t >= 1/26:
        base_scale = 1/26
        timescale = 'fortnight'
    elif t >= 1/52:
        base_scale = 1/52
        timescale = 'week'
    else:
        base_scale = 1/365
        timescale = 'day'

    # Then, work out how many of the base unit there are
    converted_t = t/base_scale

    # If there is only one of the base unit, then return the timescale as the final string
    if abs(converted_t-1.0) < 1e-5:
        return (timescale + 's') if pluralize else timescale
    elif converted_t%1 < 1e-3: # If it's sufficiently close to an integer, show it as an integer
        return '%d %ss' % (converted_t, timescale)
    else:
        return '%s %ss' % (sc.sigfig(converted_t, keepints=True,sigfigs=3), timescale)


def interpolate(x: np.array,y: np.array,x2: np.array, extrapolate=True) -> np.array:
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
            y2 = f(x2) # PchipInterpolator will return NaNs outside the domain
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