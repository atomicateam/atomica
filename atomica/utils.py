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

        t = sc.promotetoarray(t) if t is not None else list()
        vals = sc.promotetoarray(vals) if vals is not None else list()

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

    def interpolate(self, t2):
        # Output is guaranteed to be of type np.array
        t2 = sc.promotetoarray(t2)  # Deal with case where user prompts for single time point

        if not self.has_data:
            return np.full(t2.shape, np.nan)
        elif not self.has_time_data:
            return np.full(t2.shape, self.assumption)

        t1, v1 = self.get_arrays()

        # Remove NaNs
        idx = ~np.isnan(t1) & ~np.isnan(v1)
        t1 = t1[idx]
        v1 = v1[idx]

        if t1.size == 0:
            raise Exception('No time points remained after removing NaNs from the TimeSeries')
        elif t1.size == 1:
            return np.full(t2.shape, v1[0])
        else:
            v2 = np.zeros(t2.shape)
            f = scipy.interpolate.PchipInterpolator(t1, v1, axis=0, extrapolate=False)
            v2[(t2 >= t1[0]) & (t2 <= t1[-1])] = f(t2[(t2 >= t1[0]) & (t2 <= t1[-1])])
            v2[t2 < t1[0]] = v1[0]
            v2[t2 > t1[-1]] = v1[-1]
            return v2

    def sample(self, t2):
        # This method might sample from the TimeSeries for the given years
        # e.g. `ts.interpolate([2011,2012])` would give the values without uncertainty
        # while `ts.sample([2011,2012])` would perturb the values depending on sigma
        # (and perhaps some other distribution information too)
        raise NotImplementedError()

def evaluate_plot_string(plot_string):
    # The plots in the framework are specified as strings - for example,
    #
    # plot_string = "{'New active DS-TB':['pd_div:flow','nd_div:flow']}"
    #
    # This needs to be (safely) evaluated so that the actual dict can be
    # used. This function evaluates a string like this and returns a
    # variable accordingly. For example
    #
    # x = evaluate_plot_string("{'New active DS-TB':['pd_div:flow','nd_div:flow']}")
    #
    # is the same as
    #
    # x = {'New active DS-TB':['pd_div:flow','nd_div:flow']}
    #
    # This will only happen if tokens associated with dicts and lists are present -
    # otherwise the original string will just be returned directly

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