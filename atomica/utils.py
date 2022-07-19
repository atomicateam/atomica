"""
Define utility classes used throughout Atomica

"""

import ast
import inspect
import itertools
import logging
import os
import re
import time
import zlib
from bisect import bisect_right, bisect_left
from datetime import datetime
from functools import partial
from pathlib import Path

import numpy as np
import scipy.interpolate
from tqdm import tqdm

import sciris as sc
from .system import logger

__all__ = [
    "NamedItem",
    "NDict",
    "TimeSeries",
    "Quiet",
    "parent_dir",
    "evaluate_plot_string",
    "format_duration",
    "nested_loop",
    "fast_gitinfo",
    "datetime_to_year",
    "parallel_progress",
    "start_logging",
    "stop_logging",
]


def parent_dir() -> Path:
    """
    Return the parent directory of current file

    This function returns a Path object for the folder containing the file that called this function
    e.g. if the file on disk is `foo/bar/baz.py` and `baz.py` contains `x = at.parent_dir()` then
    `x` would be an absolute path corresponding to `Path('foo/bar')`

    :return: Path object to the directory containing calling file

    """

    return Path(inspect.stack()[1][1]).parent


class NamedItem:
    def __init__(self, name: str = None):
        """
        NamedItem constructor

        A name must be a string

        :param name:
        """
        if name is None:
            name = "<unnamed>"
        self.name = name
        self.created = sc.now(utc=True)
        self.modified = sc.now(utc=True)

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
            item.modified = sc.now(utc=True)
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


class TimeSeries:
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

    # Use slots here to guarantee that __deepcopy__() and __eq__() only have to check these
    # specific fields - otherwise, would need to do a more complex recursive dict comparison
    __slots__ = ["t", "vals", "units", "assumption", "sigma", "_sampled"]

    def __init__(self, t=None, vals=None, units: str = None, assumption: float = None, sigma: float = None):

        self.t = []  #: Sorted array of time points. Normally interacted with via methods like :meth:`insert()`
        self.vals = []  #: Time-specific values - indices correspond to ``self.t``
        self.units = units  #: The units of the quantity
        self.assumption = assumption  #: The time-independent scalar assumption
        self.sigma = sigma  #: Uncertainty value, assumed to be a standard deviation
        self._sampled = False  #: Flag to indicate whether sampling has been performed. Once sampling has been performed, cannot sample again

        # Using insert() means that array/list inputs containing None or duplicate entries will
        # be sanitized via insert()
        self.insert(t, vals)

    def __repr__(self):
        output = sc.prepr(self)
        return output

    def __eq__(self, other):
        """
        Check TimeSeries equality

        Two TimeSeries instances are equal if all of their attributes are equal. This is easy to
        implement because `==` is directly defined for all of the attribute types (lists and scalars)
        and due to `__slots__` there are guaranteed not to be any other attributes

        :param other:
        :return:
        """

        return all(getattr(self, x) == getattr(other, x) for x in self.__slots__)

    def __deepcopy__(self, memodict={}):
        new = TimeSeries.__new__(TimeSeries)
        new.t = self.t.copy()
        new.vals = self.vals.copy()
        new.units = self.units
        new.assumption = self.assumption
        new.sigma = self.sigma
        new._sampled = self._sampled
        return new

    def __getstate__(self):
        return dict([(k, getattr(self, k, None)) for k in self.__slots__])

    def __setstate__(self, data):

        if "format" in data:
            # 'format' was changed to 'units' but the attribute was not dropped, however now this is a
            # hard error because of the switch to __slots__ so we need to make sure it gets removed.
            # This can't be done as a Migration because a Migration expects an instance of the
            data = sc.dcp(data)
            if "units" not in data:
                data["units"] = data["format"]
            del data["format"]

        for k, v in data.items():
            setattr(self, k, v)

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
        Insert a value or list of at a particular time

        If the value already exists in the ``TimeSeries``, it will be overwritten/updated.
        The arrays are internally sorted by time value, and this order will be maintained.

        :param t: Time value to insert or update. If ``None``, the value will be assigned to the assumption
        :param v: Value to insert. If ``None``, this function will return immediately without doing anything

        """

        # Check if inputs are iterable
        iterable_input = True
        try:
            assert len(t) == len(v), "Cannot insert non-matching lengths or types of time and values %s and %s" % (t, v)
        except TypeError:
            iterable_input = False

        # If inputs are iterable, call insert() for each zipped item
        if iterable_input:
            for ti, vi in zip(t, v):
                self.insert(ti, vi)
            return

        if v is None:  # Can't cast a None to a float, so just skip it
            return

        v = float(v)  # Convert input to float

        if t is None:  # Store the value in the assumption
            self.assumption = v
            return

        idx = bisect_left(self.t, t)
        if idx < len(self.t) and self.t[idx] == t:
            # Overwrite an existing entry
            self.vals[idx] = v
        else:
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

    def remove(self, t) -> None:
        """
        Remove single time point

        :param t: Time value to remove. Set to ``None`` to remove the assumption

        """
        # To remove the assumption, set t=None
        if t is None:
            self.assumption = None
        elif t in self.t:
            idx = self.t.index(t)
            del self.t[idx]
            del self.vals[idx]
        else:
            raise Exception("Item not found")

    def remove_before(self, t_remove) -> None:
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

    def remove_between(self, t_remove) -> None:
        """
        Remove a range of times

        Note that the endpoints are not included

        :param t_remove: two element iterable e.g. array, with [min,max] times

        """

        for tval in sc.dcp(self.t):
            if t_remove[0] < tval < t_remove[1]:
                self.remove(tval)

    def interpolate(self, t2: np.array, method="linear", **kwargs) -> np.array:
        """
        Return interpolated values

        This method returns interpolated values from the time series at time points `t2`
        according to a given interpolation method. There are 4 possibilities for the method

        - 'linear' - normal linear interpolation (with constant, zero-gradient extrapolation)
        - 'pchip' - legacy interpolation with some curvature between points (with constant, zero-gradient extrapolation)
        - 'previous' - stepped interpolation, maintain value until the next timepoint is reached (with constant, zero-gradient extrapolation)
        - Interpolation class or generator function

        That final option allows the use of arbitrary interpolation methods. The underlying call will be

            c = method(t1, v1, **kwargs)
            return c(t2)

        so for example, if you wanted to use the base Scipy pchip method with no extrapolation, then could pass in

            TimeSeries.interpolate(...,method=scipy.interpolate.PchipInterpolator)

        Note that the following special behaviours apply:

        - If there is no data at all, this function will return ``np.nan`` for all requested time points
        - If only an assumption exists, this assumption will be returned for all requested time points
        - Otherwise, arrays will be formed with all finite time values
            - If no finite time values remain, an error will be raised (in general, a TimeSeries should not store such values anyway)
            - If only one finite time value remains, then that value will be returned for all requested time points
            - Otherwise, the specified interpolation method will be used

        :param t2: float, list, or array, with times
        :param method: A string 'linear', 'pchip' or 'previous' OR a callable item that returns an Interpolator
        :return: array the same length as t2, with interpolated values

        """

        t2 = sc.promotetoarray(t2)  # Deal with case where user prompts for single time point

        # Deal with not having time-specific data first
        if not self.has_data:
            return np.full(t2.shape, np.nan)
        elif not self.has_time_data:
            return np.full(t2.shape, self.assumption)

        # Then, deal with having only 0 or 1 valid time points
        t1, v1 = self.get_arrays()
        idx = ~np.isnan(t1) & ~np.isnan(v1)
        t1, v1 = t1[idx], v1[idx]
        if t1.size == 0:
            raise Exception("No time points remained after removing NaNs from the TimeSeries")
        elif t1.size == 1:
            return np.full(t2.shape, v1[0])

        # # Finally, perform interpolation
        if sc.isstring(method):
            if method == "linear":
                # Default linear interpolation
                return np.interp(t2, t1, v1, left=v1[0], right=v1[-1])
            elif method == "pchip":
                # Legacy pchip interpolation
                f = scipy.interpolate.PchipInterpolator(t1, v1, axis=0, extrapolate=False)
                y2 = np.zeros(t2.shape)
                y2[(t2 >= t1[0]) & (t2 <= t1[-1])] = f(t2[(t2 >= t1[0]) & (t2 <= t1[-1])])
                y2[t2 < t1[0]] = v1[0]
                y2[t2 > t1[-1]] = v1[-1]
                return y2
            elif method == "previous":
                return scipy.interpolate.interp1d(t1, v1, kind="previous", copy=False, assume_sorted=True, bounds_error=False, fill_value=(v1[0], v1[-1]))(t2)
            else:
                raise Exception('Unknown interpolation type - must be one of "linear", "pchip", or "previous"')

        # Otherwise, `method` is a callable (class instance e.g. `scipy.interpolate.PchipInterpolator` or generating function) that
        # produces a callable function representation of the interpolation. This function is then called with the new time points
        interpolator = method(t1, v1, **kwargs)
        return interpolator(t2)

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
            raise Exception("Sampling has already been performed - can only sample once")

        new = self.copy()
        if self.sigma is not None:
            delta = self.sigma * np.random.randn(1)[0]
            if self.assumption is not None:
                new.assumption += delta

            if constant:
                # Use the same delta for all data points
                new.vals = [v + delta for v in new.vals]
            else:
                # Sample again for each data point
                for i, (v, delta) in enumerate(zip(new.vals, self.sigma * np.random.randn(len(new.vals)))):
                    new.vals[i] = v + delta

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

    if "{" in plot_string or "[" in plot_string:
        # Evaluate the string to set lists and dicts - do at least a little validation
        assert "__" not in plot_string, "Cannot use double underscores in functions"
        assert len(plot_string) < 1800  # Function string must be less than 1800 characters
        fcn_ast = ast.parse(plot_string, mode="eval")
        for node in ast.walk(fcn_ast):
            if not (node is fcn_ast):
                assert isinstance(node, ast.Dict) or isinstance(node, ast.Str) or isinstance(node, ast.List) or isinstance(node, ast.Load), "Only allowed to initialize lists and dicts of strings here"
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
        timescale = "year"
    elif t >= 1 / 12:
        base_scale = 1 / 12
        timescale = "month"
    elif t >= 1 / 26:
        base_scale = 1 / 26
        timescale = "fortnight"
    elif t >= 1 / 52:
        base_scale = 1 / 52
        timescale = "week"
    else:
        base_scale = 1 / 365
        timescale = "day"

    # Then, work out how many of the base unit there are
    converted_t = t / base_scale

    # If there is only one of the base unit, then return the timescale as the final string
    if abs(converted_t - 1.0) < 1e-5:
        return (timescale + "s") if pluralize else timescale
    elif converted_t % 1 < 1e-3:  # If it's sufficiently close to an integer, show it as an integer
        return "%d %ss" % (converted_t, timescale)
    else:
        return "%s %ss" % (sc.sigfig(converted_t, keepints=True, sigfigs=3), timescale)


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

    loop_order = list(loop_order)  # Convert to list, in case loop order was passed in as a generator e.g. from map()
    inputs = [inputs[i] for i in loop_order]
    iterator = itertools.product(*inputs)  # This is in the loop order
    for item in iterator:
        out = [None] * len(loop_order)
        for i in range(len(item)):
            out[loop_order[i]] = item[i]
        yield out


def fast_gitinfo(path):
    """
    Retrieve git info

    This function reads git branch and commit information from a .git directory.
    Given a path, it will check for a `.git` directory. If the path doesn't contain
    that directory, it will search parent directories for `.git` until it finds one.
    Then, the current information will be parsed.

    :param path: A folder either containing a ``.git`` directory, or with a parent that contains a ``.git`` directory

    """

    try:
        # First, get the .git directory
        curpath = os.path.abspath(path)
        while curpath:
            if os.path.exists(os.path.join(curpath, ".git")):
                gitdir = os.path.join(curpath, ".git")
                break
            else:
                parent, _ = os.path.split(curpath)
                if parent == curpath:
                    curpath = None
                else:
                    curpath = parent
        else:
            raise Exception("Could not find .git directory")

        # Then, get the branch and commit
        with open(os.path.join(gitdir, "HEAD"), "r") as f1:
            ref = f1.read()
            if ref.startswith("ref:"):
                refdir = ref.split(" ")[1].strip()  # The path to the file with the commit
                gitbranch = refdir.replace("refs/heads/", "")  # / is always used (not os.sep)
                with open(os.path.join(gitdir, refdir), "r") as f2:
                    githash = f2.read().strip()  # The hash of the commit
            else:
                gitbranch = "Detached head (no branch)"
                githash = ref.strip()

        # Now read the time from the commit
        compressed_contents = open(os.path.join(gitdir, "objects", githash[0:2], githash[2:]), "rb").read()
        decompressed_contents = zlib.decompress(compressed_contents).decode()
        for line in decompressed_contents.split("\n"):
            if line.startswith("author"):
                _re_actor_epoch = re.compile(r"^.+? (.*) (\d+) ([+-]\d+).*$")
                m = _re_actor_epoch.search(line)
                actor, epoch, offset = m.groups()
                t = time.gmtime(int(epoch))
                gitdate = time.strftime("%Y-%m-%d %H:%M:%S UTC", t)

    except Exception:
        gitbranch = "Git branch N/A"
        githash = "Git hash N/A"
        gitdate = "Git date N/A"

    output = {"branch": gitbranch, "hash": githash, "date": gitdate}  # Assemble outupt
    return output


def datetime_to_year(dt: datetime) -> float:
    """
    Convert a DateTime instance to decimal year

    For example, 1/7/2010 would be approximately 2010.5

    :param dt: The datetime instance to convert
    :return: Equivalent decimal year

    """
    # By Luke Davis from https://stackoverflow.com/a/42424261
    year_part = dt - datetime(year=dt.year, month=1, day=1)
    year_length = datetime(year=dt.year + 1, month=1, day=1) - datetime(year=dt.year, month=1, day=1)
    return dt.year + year_part / year_length


def _worker_init() -> None:
    """
    Suppress output on parallel workers

    A parallel worker should only ever print out warning output or higher
    This function gets passed as an initializer to `multiprocessing.Pool`
    to set the logger level locally on the workers

    """

    logger.setLevel(logging.WARNING)


def parallel_progress(fcn, inputs, num_workers=None, show_progress=True) -> list:
    """
    Run a function in parallel with a optional single progress bar

    The result is essentially equivalent to

    >>> list(map(fcn, inputs))

    But with execution in parallel and with a single progress bar being shown.
    The Atomica logger level will be changed to hide output below the
    WARNING level.

    :param fcn: Function object to call, accepting one argument, OR a function with zero arguments in which
                case inputs should be an integer
    :param inputs: A collection of inputs that will each be passed to (list, array, etc.)
                    OR a number, if the fcn() has no input arguments
    :param num_workers: Number of processes, defaults to the number of CPUs
    :return: An list of outputs

    """

    from multiprocessing import pool, cpu_count

    if num_workers is None:
        num_workers = min(cpu_count(), len(inputs))

    pool = pool.Pool(num_workers, initializer=_worker_init)

    results = [None]
    if sc.isnumber(inputs):
        results *= inputs
        pbar = tqdm(total=inputs) if show_progress else None
    else:
        results *= len(inputs)
        pbar = tqdm(total=len(inputs)) if show_progress else None

    def callback(result, idx):
        results[idx] = result
        if show_progress:
            pbar.update(1)

    jobs = []
    if sc.isnumber(inputs):
        for i in range(inputs):
            jobs.append(pool.apply_async(fcn, callback=partial(callback, idx=i)))
    else:
        for i, x in enumerate(inputs):
            jobs.append(pool.apply_async(fcn, args=(x,), callback=partial(callback, idx=i)))

    pool.close()
    pool.join()

    for job in jobs:
        job.get()  # This will raise any exceptions thrown from within the async task

    if show_progress:
        pbar.close()

    return results


class Quiet:
    """
    Atomica quiet context

    This object can be used in a `with/as` block to temporarily suppress
    Atomica output, with the logger level reset at the end of the block


    Example usage:

    >>> with at.Quiet():
    >>>     res = P.run_sim()

    """

    def __init__(self, show_warnings=True):
        """
        Initialize standard context

        Initialization captures the current logger level at the time the context is created.

        :param show_warnings: If True, logger will be temporarily set at WARNING level. If
                              False, all output will be suppressed by setting logger above CRITICAL
        """

        self.previous_level = logger.getEffectiveLevel()
        self.show_warnings = show_warnings

    def __enter__(self):
        if self.show_warnings:
            logger.setLevel(logging.WARNING)
        else:
            logger.setLevel(logging.CRITICAL + 1)

    def __exit__(self, *args):
        logger.setLevel(self.previous_level)


def start_logging(fname: str, reset=False) -> None:
    """
    Log Atomica output to a file

    This function automatically starts the file with a version record.

    The file logger will potentially handle any log level, from 0 upwards.
    Therefore both stdout and stderr can potentially be logged. The stdout
    messages will be gated by the log level of `at.logger`. In practice,
    this means that the log file generated here will replicate whatever is
    being printed to the screen by the main Atomica process.

    The key items that will NOT be captured in this file log are
        - Output generated by a `print` statement. Instead of using `print`, use
          `at.logger.info('message')` which will both print and log the output
        - Output generated by worker processes e.g. if using `run_sampled_sims(parallel=True)`
          This is because the workers can't all write to the same log file without overwriting
          each other. Normal log output is typically suppressed anyway - however, stderr messages
          from the workers will be printed to the console but not logged in the file. These messages
          would typically corrupt the progress bar in the console anyway.

    :param fname: File name to write log file to
    :param reset: If True, the previous file handler will be cleared and a new one opened. If the new log file
                  has the same name as the old log file, the file will be cleared.
    """

    if reset:
        stop_logging()

    for handler in logger.handlers:
        if handler.name == "atomica_file_handler":
            # Logging has already been started, so we can return immediately
            # Otherwise, output could be logged multiple times
            return

    from .version import gitinfo, version, versiondate  # Avoid circular import

    sc.makefilepath(fname)
    h = logging.FileHandler(fname, mode="w")
    h.set_name("atomica_file_handler")
    fmt = logging.Formatter("%(asctime)-20s %(message)s", datefmt="%d-%m-%y %H:%M:%S")
    h.setFormatter(fmt)

    logger.addHandler(h)

    logger.critical(f"Atomica log file: {os.path.abspath(fname)}")
    logger.critical("-" * 80)
    logger.critical("Atomica %s (%s) -- (c) the Atomica development team" % (version, versiondate))  # Log with the highest level to make sure it appears in the log
    if gitinfo["branch"] != "N/A":
        logger.critical("git branch: %s (%s)" % (gitinfo["branch"], gitinfo["hash"][0:8]))
    logger.critical(datetime.now())
    logger.critical("-" * 80)

    # We also want uncaught exceptions (in the main process) to appear in the log
    # Based on https://stackoverflow.com/a/57587758 by Nabs
    def log_exception(exctype, value, traceback):
        logger.error("UNCAUGHT EXCEPTION", exc_info=(exctype, value, traceback))

    def attach_hook(hook_func, run_func):
        def inner(*args, **kwargs):
            local_args = run_func()
            hook_func(*local_args)
            return run_func(*args, **kwargs)

        return inner

    if not reset:  # do not double up on error messages
        import sys

        sys.exc_info = attach_hook(log_exception, sys.exc_info)
        sys.excepthook = log_exception


def stop_logging() -> None:
    """
    Stop logging output to file

    This function will clear the `atomica_file_handler` and close
    the last-opened log file. If file logging has not started, this
    function will return normally without raising an error

    """

    for handler in logger.handlers:
        if handler.name == "atomica_file_handler":
            handler.close()
            logger.removeHandler(handler)
            # Don't terminate the loop, if by some change there is more than one handler
            # (not supposed to happen though) then we would want to close them all
