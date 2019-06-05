"""
Implements the Atomica computational graph

Fundamentally, models in Atomica can be represented as a graph, with
nodes corresponding to compartments, and edges corresponding to transitions/links.
This module implements the graph representation of the Framework in a form that can
be numerically integrated. It also implements the methods to actually perform the integration.

"""


from .system import NotFoundError
from .system import logger
from .system import FrameworkSettings as FS
from .results import Result
from .function_parser import parse_function
from .version import version, gitinfo
from collections import defaultdict
import sciris as sc
import numpy as np
import matplotlib.pyplot as plt
from .programs import ProgramSet

model_settings = dict()
model_settings['tolerance'] = 1e-6
model_settings['iteration_limit'] = 100


class BadInitialization(Exception):
    """
    Error for invalid conditions

    This error gets raised if the simulation exited due to a bad initialization, specifically
    due to negative initial popsizes or an excessive residual. This commonly happens if the
    initial conditions are being programatically varied and thus may be an expected error.
    This error can then be caught and dealt with appropriately. For example:

    - calibration will catch this error and instruct ASD to reject the proposed parameters
    - ``Ensemble.run_sims`` catches this error and tries another sample

    """

    pass


class Variable(object):
    """
    Integration object to manage compartments, characteristics, parameters, and links

    This is a lightweight abstract class to store arrays of values at each simulation time step. It includes
    functionality that is common to all integration objects, and defines the interface to be implemented
    by derived classes.

        :param pop: A :class:`Population` instance. This allows references back to the population containing an object
                    (which facilitates a number of operations such as those that require the population's size)
        :param id: ID is a tuple that uniquely identifies the Variable within a model.
                    By convention, this is a ``population:code_name`` tuple
                    (but in the case of links, there are additional terms)
    """

    def __init__(self, pop, id):
        self.id = id  #: Unique identifier for the integration object
        self.t = None #: Array of time values. This should be a reference to the base array stored in a :class:`model` object
        self.dt = None #: Time step size
        if 'vals' not in dir(self):
            self.vals = None #: The fundamental values stored by this object. Note that Characteristics implement this as a property method
        self.units = 'unknown'  #: The units for the quantity, used for plotting and for validation. Note that the default ``'unknown'`` units are distinct to dimensionless units, which have value ``''``
        self.pop = pop  #: Reference back to the Population containing this object

    @property
    def name(self) -> str:
        """
        Variable code name

        This is implemented as a property method because the ``id`` of the ``Variable`` is a
        tuple containing the population name and the variable code name, so this property
        method returns just the variable code name portion. That way, storage does not need
        to be duplicated.

        :return: A code name

        """

        return self.id[-1]

    def preallocate(self, tvec: np.array, dt: float) -> None:
        """
        Preallocate data storage

        This method gets called just before integration, once the final sizes of the arrays are known.
        Performance is improved by preallocating the arrays. The ``tvec`` attribute is assigned
        as-is, so it is typically a reference to the array stored in the parent ``Model`` object. Thus,
        there is no duplication of storage there, and ``Variable.tvec`` is mainly for convenience when
        interpolating or plotting.

        This method may be overloaded in derived classes to preallocate other variables specific
        to those classes.

        :param tvec: An array of time values
        :param dt: Time step size

        """
        self.t = tvec
        self.dt = dt
        self.vals = np.ones(tvec.shape) * np.nan

    def plot(self) -> None:
        """
        Produce a time series plot

        This is a quick function to make a basic line plot of this ``Variable``. Mainly
        intended for debugging. Production-ready plots should be generated using the
        plotting library functions instead

        """

        plt.figure()
        plt.plot(self.t, self.vals, label=self.name)
        plt.legend()
        plt.xlabel('Year')
        plt.ylabel("%s (%s)" % (self.name, self.units))

    def update(self, ti: int) -> None:
        """
        Update the value at a given time index

        This method performs any required computations to update the value
        of the variable at a given time index. For example, Parameters may require
        their update function to be called, while characteristics need their
        source compartments to be added up.

        This method generally must be overloaded in derived classes e.g. :meth:`Parameter.update`

        :param ti: Time index to update

        """

        return

    def set_dynamic(self, **kwargs) -> None:
        """
        Make the variable a dependency

        For Compartments and Links, this does nothing. For Characteristics and
        Parameters, it will set the dynamic flag, but in addition, any validation constraints e.g. a Parameter
        that depends on Links cannot itself be dynamic, will be enforced.

        This method generally must be overloaded in derived classes e.g. :meth:`Parameter.set_dynamic`

        """

        return

    def unlink(self):
        self.pop = self.pop.name

    def relink(self, objs):
        self.pop = objs[self.pop]

    def __repr__(self):
        return '%s "%s" %s' % (self.__class__.__name__, self.name, self.id)


class Compartment(Variable):
    """ A class to wrap up data for one compartment within a cascade network. """

    def __init__(self, pop, name):
        Variable.__init__(self, pop=pop, id=(pop.name, name))
        self.units = 'Number of people'
        self.tag_birth = False  # Tag for whether this compartment contains unborn people.
        self.tag_dead = False  # Tag for whether this compartment contains dead people.
        self.is_junction = False
        self.vals = None

        self.outlinks = []
        self.inlinks = []

    def unlink(self):
        Variable.unlink(self)
        self.outlinks = [x.id for x in self.outlinks]
        self.inlinks = [x.id for x in self.inlinks]

    def relink(self, objs):
        Variable.relink(self, objs)
        self.outlinks = [objs[x] for x in self.outlinks]
        self.inlinks = [objs[x] for x in self.inlinks]

    @property
    def outflow(self):
        # Return the outflow at each timestep - for a junction, this is equal to the number
        # of people that were in the junction
        x = np.zeros(self.t.shape)
        if self.outlinks:
            for link in self.outlinks:
                x += link.vals
        return x

    def expected_duration(self, ti=None):
        # Returns the expected number of years that an individual is expected to remain
        # in this compartment for, if the outgoing flow rates are maintained
        if ti is None:
            ti = np.arange(0, len(self.t))

        outflow_probability = 0  # Outflow probability at this timestep
        for link in self.outlinks:

            if link.parameter.units == FS.QUANTITY_TYPE_DURATION:
                x = 1.0 - np.exp(-1.0 / link.parameter.vals[ti])
                outflow_probability += 1 - (1 - link.parameter.vals[ti]) ** self.dt  # A formula for converting from yearly fraction values to the dt equivalent.
            elif link.parameter.units == FS.QUANTITY_TYPE_PROBABILITY:
                outflow_probability += 1 - (1 - link.parameter.vals[ti]) ** self.dt  # A formula for converting from yearly fraction values to the dt equivalent.
            elif link.parameter.units == FS.QUANTITY_TYPE_NUMBER:
                outflow_probability += link.parameter.vals[ti] * self.dt / self.vals[ti]
            elif link.parameter.units == FS.QUANTITY_TYPE_PROPORTION:
                outflow_probability += link.parameter.vals[ti]
            else:
                raise Exception('Unknown parameter units')

        remain_probability = 1 - outflow_probability

        # This is the algorithm - we calculate the probability of leaving after a specific number of time steps, and then
        # take the expectation value. The example below shows a discrete numerical calculation as well as a closed-form
        # approximation which is what actually gets used
        # remain_probability = 0.99
        # x = np.arange(0,1000)
        # y = (remain_probability**x)*(1-remain_probability)
        # numerical = np.sum((x+1) * y) * self.dt # x+1 because if we leave at the first timestep, we are considered to have stayed for dt units of time
        # analytic = (1 - (1. / np.log(remain_probability) ** 2) * (remain_probability - 1)) * self.dt
        # print('numerical=%.2f, analytic=%.2f' % (numerical,analytic))

        dur = (1 - (1. / np.log(remain_probability) ** 2) * (remain_probability - 1)) * self.dt
        return dur

    def expected_outflow(self, ti):
        # After 1 year, where are people expected to be? If people would leave in less than a year,
        # then the numbers correspond to when the compartment is empty
        popsize = self.vals[ti]  # This is the number of people who are leaving

        outflow = {link.dest.name: popsize * link.vals[ti] / self.dt for link in self.outlinks}
        rescale = popsize / sum([y for _, y in outflow.items()])
        for x in outflow.keys():
            outflow[x] *= rescale
        outflow[self.name] = popsize - sum([y for _, y in outflow.items()])

        return outflow


class Characteristic(Variable):
    """ A characteristic represents a grouping of compartments. """

    def __init__(self, pop, name):
        # includes is a list of Compartments, whose values are summed
        # the denominator is another Characteristic that normalizes this one
        # All passed by reference so minimal performance impact
        Variable.__init__(self, pop=pop, id=(pop.name, name))
        self.units = 'Number of people'
        self.includes = []
        self.denominator = None
        # The following flag indicates if another variable depends on this one.
        # This indicates a value needs computation during integration.
        self._is_dynamic = False
        self._vals = None

    def preallocate(self, tvec, dt):
        # Note that we don't use Variable.preallocate() here because we cannot
        # preallocate self.vals because it is a property method
        self.t = tvec
        self.dt = dt
        self._vals = np.ones(tvec.shape) * np.nan

    def get_included_comps(self):
        includes = []
        for inc in self.includes:
            if isinstance(inc, Characteristic):
                includes += inc.get_included_comps()
            else:
                includes.append(inc)
        return includes

    @property
    def vals(self):
        if self._vals is None:
            vals = np.zeros(self.t.shape)

            for comp in self.includes:
                vals += comp.vals

            if self.denominator is not None:
                denom = self.denominator.vals
                vals_zero = vals < model_settings['tolerance']
                vals[denom > 0] /= denom[denom > 0]
                vals[vals_zero] = 0.0
                vals[(denom <= 0) & (~vals_zero)] = np.inf

            return vals
        else:
            return self._vals

    def set_dynamic(self, **kwargs):
        self._is_dynamic = True

        for inc in self.includes:
            inc.set_dynamic()

        if self.denominator is not None:
            self.denominator.set_dynamic()

    def unlink(self):
        Variable.unlink(self)
        self.includes = [x.id for x in self.includes]
        self.denominator = self.denominator.id if self.denominator is not None else None

    def relink(self, objs):
        # Given a dictionary of objects, restore the internal references
        Variable.relink(self, objs)
        self.includes = [objs[x] for x in self.includes]
        self.denominator = objs[self.denominator] if self.denominator is not None else None

    def add_include(self, x):
        assert isinstance(x, Compartment) or isinstance(x, Characteristic)
        self.includes.append(x)

    def add_denom(self, x):
        assert isinstance(x, Compartment) or isinstance(x, Characteristic)
        self.denominator = x
        self.units = ''

    def update(self, ti):
        self._vals[ti] = 0
        for comp in self.includes:
            self._vals[ti] += comp.vals[ti]
        if self.denominator is not None:
            denom = self.denominator.vals[ti]
            if denom > 0:
                self._vals[ti] /= denom
            elif self._vals[ti] < model_settings['tolerance']:
                self._vals[ti] = 0  # Given a zero/zero case, make the answer zero.
            else:
                self._vals[ti] = np.inf  # Given a non-zero/zero case, keep the answer infinite.


class Parameter(Variable):
    """
    Integration object to represent Parameters

    A parameter is a Variable that can have a value computed via an fcn_str and a list of
    dependent Variables. This is a Parameter in the cascade.xlsx sense - there is one Parameter object for every item in the
    Parameters sheet. A parameter that maps to multiple transitions (e.g. ``doth_rate``) will have one parameter
    and multiple Link instances that depend on the same Parameter instance

    :param pop: A :class:`Population` instance corresponding to the population that will contain this parameter
    :param name: The code name for this parameter

    """

    def __init__(self, pop, name):

        Variable.__init__(self, pop=pop, id=(pop.name, name))
        self.limits = None  #: Can be a two element vector [min,max]
        self.pop_aggregation = None  #: If not None, stores list of population aggregation information (special function, which weighting comp/charac and which interaction term to use)
        self.scale_factor = 1.0  #: This should be set to the product of the population-specific ``y_factor`` and the ``meta_y_factor`` from the ParameterSet
        self.links = []  #: References to links that derive from this parameter
        self._source_popsize_cache_time = None #: Internal cache for the time at which the source popsize was previously computed
        self._source_popsize_cache_val = None #: Internal cache for the last previously computed source popsize
        self.fcn_str = None  #: String representation of parameter function
        self.deps = dict()  #: Dict of dependencies containing lists of integration objects
        self._fcn = None  #: Internal cache for parsed parameter function (this will be dropped when pickled)
        self._precompute = False #: If True, the parameter function will be computed in a vector operation prior to integration
        self._is_dynamic = False #: If True, this parameter will be updated during integration. Note that `precompute` and `dynamic` are mutually exclusive
        self.derivative = False #: If True, the parameter function will be treated as a derivative and the value added on to the end
        self.skip_function = None #: Can optionally be set to a (start,stop) tuple of times. Between these times, the parameter will not be updated so the parset value will be left unchanged

        #: For transition parameters, the ``vals`` stored by the parameter is effectively a rate. The ``timescale``
        #: attribute informs the time period corresponding to the units in which the rate has been provided.
        #: If the units are ``number`` or ``probability`` then the ``timescale`` corresponds to the denominator of the units
        #: e.g. probability/day (with ``timescale=1/365``).
        #: If the units are ``duration`` then the timescale stores the units in which the duration has been specified
        #: e.g. ``duration=1`` with ``timescale=1/52`` is the same as ``duration=7`` with ``timescale=1/365``
        #: The effective duration used in the simulation is ``duration*timescale`` with units of years (so it will behave correctly if
        #: one wanted to use 1/365.25 instead of 1/365)
        self.timescale = 1.0

    def set_fcn(self, framework, fcn_str, progset) -> None:
        """
        Add a function to this parameter

        This method adds a function to the parameter. The following steps are carried out

            - The function is parsed and stored in the ``._fcn`` attribute (until the Parameter is pickled)
            - The dependencies are extracted, and are stored as references to the actual integration objects
              to increase performance during integration
            - If this is a transition parameter, then dependencies will have their `dynamic` flag updated

        :param framework: A py:class:`ProjectFramework` instance, used to identify and retrieve interaction terms
        :param fcn_str: The string containing the function to add
        :param progset: A py:class:`ProgramSet` instance, used to identify parameters that will be overwritten

        """

        assert sc.isstring(fcn_str), "Parameter function must be supplied as a string"
        self.fcn_str = fcn_str
        self._fcn, dep_list = parse_function(self.fcn_str)
        if fcn_str.startswith("SRC_POP_AVG") or fcn_str.startswith("TGT_POP_AVG") or fcn_str.startswith("SRC_POP_SUM") or fcn_str.startswith("TGT_POP_SUM"):
            # The function is like 'SRC_POP_AVG(par_name,interaction_name,charac_name)'
            # self.pop_aggregation will be ['SRC_POP_AVG',par_name,interaction_name,charac_object]
            special_function, temp_list = self.fcn_str.split("(")
            function_args = temp_list.rstrip(")").split(',')
            function_args = [x.strip() for x in function_args]
            self.pop_aggregation = [special_function] + function_args
        else:
            for dep_name in dep_list:
                if not (dep_name in ['t', 'dt']):  # There are no integration variables associated with the interactions, as they are treated as a special matrix
                    self.deps[dep_name] = self.pop.get_variable(dep_name) # nb. this lookup will fail if the user has a function that depends on a quantity outside this population

        # If this Parameter has links and a function, it must be updated during computation
        # Similarly, if it is a derivative then it should be vector-computed
        # (for simplicity in implementation)
        if (self.links and self.fcn_str) or self.derivative:
            self.set_dynamic(progset)

    def set_dynamic(self, progset=None) -> None:
        """
        Mark this parameter as needing evaluation for integration

        If a parameter has a function and `set_dynamic()` has been called, that means the
        result of the function is required to drive a transition in the model. In this context,
        'dynamic' means that the parameter depends on values that are only known during integration
        (i.e. compartment sizes). It could also depend on compartment sizes indirectly, if
        it depends on characteristics, or if it depends on parameters that depend on compartments
        or characteristics. If none of these are true, then the parameter function can be evaluated
        before integration starts, taking advantage of vector operations.

        If a parameter is overwritten by a program in this simulation, then its value may change
        during integration, and we again need to make this parameter dynamic. Note that this doesn't
        apply to the parameter *being* overwritten - if it gets overwritten, that has no bearing on
        when its function gets evaluated. But if a parameter depends on a value that has changed, then
        the function must be re-evaluated. Technically this only needs to be done after the time index
        where programs turn on, but it's simpler just to mark it as dynamic for the entire simulation,
        the gains aren't large enough to justify the extra complexity otherwise.

        :param progset: A ``ProgramSet`` instance (the one contained in the Model containing this Parameter)

        """

        if self.fcn_str is None or self._is_dynamic or self._precompute:
            # Only parameters with functions need to be made dynamic
            # If the parameter is marked dynamic or precompute, that means this parameter and any of its
            # dependencies have already been checked
            return

        if self.pop_aggregation or self.derivative: # Pop aggregations and derivatives are handled in `update_pars()` so must be done incrementally during integration
            self._is_dynamic = True

        if self.deps: # If there are no dependencies, then we know that this is precompute-only
            for deps in self.deps.values(): # deps is {'dep_name':[dep_objects]}
                for dep in deps:
                    if isinstance(dep, Link):
                        raise Exception("A Parameter that depends on transition flow rates cannot be a dependency, it must be output only.")
                    elif isinstance(dep, Compartment) or isinstance(dep, Characteristic):
                        dep.set_dynamic()
                        self._is_dynamic = True
                    elif isinstance(dep, Parameter):
                        dep.set_dynamic() # Run `set_dynamic()` on the parameter which will descend further to see if the Parameter depends on comps/characs or on overwritten parameters
                        if dep._is_dynamic or (progset and dep.name in progset.pars):
                            self._is_dynamic = True
                    else:
                        raise Exception('Unexpected dependency type')

        # If not dynamic, then we need to precompute the function because the value is required for a transition
        if not self._is_dynamic:
            self._precompute = True

    def unlink(self):
        Variable.unlink(self)
        self.links = [x.id for x in self.links]
        if self.deps is not None:
            for dep_name in self.deps:
                self.deps[dep_name] = [x.id for x in self.deps[dep_name]]
        if self._fcn is not None:
            self._fcn = None

    def relink(self, objs):
        # Given a dictionary of objects, restore the internal references
        Variable.relink(self, objs)
        self.links = [objs[x] for x in self.links]
        if self.deps is not None:
            for dep_name in self.deps:
                self.deps[dep_name] = [objs[x] for x in self.deps[dep_name]]
        if self.fcn_str:
            self._fcn = parse_function(self.fcn_str)[0]

    def constrain(self, ti=None) -> None:
        """
        Constrain the parameter value to allowed range

        If ``Parameter.limits`` is not None, then the parameter values at the specified
        time will be clipped to the limits. If no time index is provided, clipping will
        be performed on all values in a vectorized operation. Vector clipping is used
        for data parameters that are not evaluated during integration, while index-specific
        clipping is used for dependencies that are calculated during integration.

        :param ti: An integer index, or None (to operate on all time points)

        """

        if self.limits is not None:
            if ti is None:
                self.vals = np.clip(self.vals,self.limits[0],self.limits[1])
            else:
                if self.vals[ti] < self.limits[0]:
                    self.vals[ti] = self.limits[0]
                if self.vals[ti] > self.limits[1]:
                    self.vals[ti] = self.limits[1]

    def update(self, ti=None) -> None:
        """
        Update the value of this Parameter

        If the parameter contains a function, this entails evaluating the function.
        Typically this is done at a single time point during integration, or over all
        time points for precomputing and postcomputing

        :param ti: An ``int``, or a numpy array with index values. If ``None``, all time values will be used

        """

        if not self._fcn or self.pop_aggregation:
            return

        if ti is None:
            if self.derivative:
                raise Exception('Cannot perform a vector update of a derivative parameter (these parameters intrinsically require integration to be computed)')
            ti = np.arange(0, self.vals.size)  # This corresponds to every time point

        if self.derivative and ti == 0:
            return

        if self.skip_function:
            # If we don't want to overwrite the parameter in certain years, those years need to be excluded
            if hasattr(ti, '__len__'):
                # Filter out years outside the excluded range
                ti = ti[np.where((self.t[ti] < self.skip_function[0]) | (self.t[ti] > self.skip_function[1]))]
                if ti.size == 0: # If all times were removed
                    return
            else:
                # Dealing with a scalar ti
                if (self.t[ti] >= self.skip_function[0]) and (self.t[ti] <= self.skip_function[1]):
                    return

        dep_vals = dict.fromkeys(self.deps, 0.0)
        for dep_name, deps in self.deps.items():
            for dep in deps:
                if isinstance(dep, Link):
                    dep_vals[dep_name] += dep.vals[ti] / dep.dt
                else:
                    dep_vals[dep_name] += dep.vals[ti]

        dep_vals['t'] = self.t[ti]
        dep_vals['dt'] = self.dt
        self.vals[ti] = self.scale_factor * self._fcn(**dep_vals)

    def source_popsize(self, ti):
        # Get the total number of people covered by this program
        # i.e. the sum of the source compartments of all links that
        # derive from this program. If the parameter has no links, return NaN
        # which disambiguates between a parameter whose source compartments are all
        # empty, vs a parameter that has no source compartments
        if ti == self._source_popsize_cache_time:
            return self._source_popsize_cache_val
        else:
            if self.links:
                n = 0
                for link in self.links:
                    n += link.source.vals[ti]
            else:
                raise Exception('Cannot retrieve source popsize for a non-transition parameter')
            self._source_popsize_cache_time = ti
            self._source_popsize_cache_val = n
            return n


class Link(Variable):
    """
    A Link is a Variable that maps to a transition between compartments. As
    such, it contains an inflow and outflow compartment.  A Link's value is
    drawn from a Parameter, and there may be multiple links that draw values
    from the same parameter. The values stored in this extended version of
    Variable refer to flow rates. If used in ModelPop, the Link references two
    cascade compartments within a single population.
    """

    #
    # *** Link values are always dt-based ***
    def __init__(self, pop, parameter, source, dest, tag=None):
        # Note that the Link's name is the transition tag
        Variable.__init__(self, pop=pop, id=(pop.name, source.name, dest.name, tag))  # A Link is only uniquely identified by (Pop,Source,Dest,Par)
        self.vals = None
        self.units = 'Number of people'

        # Source parameter where unscaled link value is drawn from (a single parameter may have multiple links).
        self.parameter = parameter

        self.source = source  # Compartment to remove people from
        self.dest = dest  # Compartment to add people to

        # Wire up references to this object
        self.parameter.links.append(self)
        self.source.outlinks.append(self)
        self.dest.inlinks.append(self)

    def unlink(self):
        Variable.unlink(self)
        self.parameter = self.parameter.id
        self.source = self.source.id
        self.dest = self.dest.id

    def relink(self, objs):
        # Given a dictionary of objects, restore the internal references
        Variable.relink(self, objs)
        self.parameter = objs[self.parameter]
        self.source = objs[self.source]
        self.dest = objs[self.dest]

    def __repr__(self, *args, **kwargs):
        return "Link %s (parameter %s) - %s to %s" % (self.name, self.parameter.name, self.source.name, self.dest.name)

    def plot(self):
        Variable.plot(self)
        plt.title('Link %s to %s' % (self.source.name, self.dest.name))


class Population(object):
    """
    A class to wrap up data for one population within model.
    Each model population must contain a set of compartments with equivalent names.
    """

    def __init__(self, framework, name: str, label:str, progset:ProgramSet, pop_type:str):
        """
        Construct a Population

        This function constructs a population instance. Aside from creating the Population, it also
        instantiates all of the integration objects defined in the Framework. Note that transfers
        and interactions aren't added at this point - because they transcend populations, they are
        instantiated one level higher up, in ``model.build()``

        :param framework: A ProjectFramework
        :param name: The code name of the population
        :param label: The full name of the population
        :param progset: A ProgramSet instance
        """

        self.name = name  #: The code name of the population
        self.label = label  #: The full name/label of the population
        self.type = pop_type #: The population's type

        self.comps = list()  #: List of Compartment objects
        self.characs = list() #: List of Characteristic objects
        self.links = list()  #: List of Link objects
        self.pars = list() #: List of Parameter objects

        self.comp_lookup = dict()  #: Maps name of a compartment to a Compartment
        self.charac_lookup = dict() #: Maps name of a compartment to a Characteristic
        self.par_lookup = dict() #: Maps name of a parameter to a Parameter
        self.link_lookup = dict()  #: Maps name of link to a list of Links with that name

        self.gen_cascade(framework=framework, progset=progset)  # Convert compartmental cascade into lists of compartment and link objects.

        self.popsize_cache_time = None
        self.popsize_cache_val = None

        self.is_linked = True  # Flag to manage double unlinking/relinking

    def __repr__(self):
        return '%s "%s"' % (self.__class__.__name__, self.name)

    def unlink(self):
        if not self.is_linked:
            return
        for obj in self.comps + self.characs + self.pars + self.links:
            obj.unlink()
        self.comp_lookup = None
        self.charac_lookup = None
        self.par_lookup = None
        self.link_lookup = None
        self.is_linked = False

    def relink(self, objs):
        if self.is_linked:
            return
        for obj in self.comps + self.characs + self.pars + self.links:
            obj.relink(objs)
        self.comp_lookup = {comp.name: comp for comp in self.comps}
        self.charac_lookup = {charac.name: charac for charac in self.characs}
        self.par_lookup = {par.name: par for par in self.pars}
        link_names = set([link.name for link in self.links])
        self.link_lookup = {name: [link for link in self.links if link.name == name] for name in link_names}
        self.is_linked = True

    def popsize(self, ti=None):
        # A population's popsize is the sum of all of the people in its compartments, excluding
        # birth and death compartments
        if ti is None:
            return np.sum([comp.vals for comp in self.comps if (not comp.tag_birth and not comp.tag_dead)], axis=0)

        if ti == self.popsize_cache_time:
            return self.popsize_cache_val
        else:
            n = 0
            for comp in self.comps:
                if not comp.tag_birth and not comp.tag_dead:
                    n += comp.vals[ti]

            return n

    def get_variable(self, name: str) -> list:
        """
        Return list of variables given code name

        At the moment, names are unique across object types and within object
        types except for links, but if that logic changes, simple modifications can
        be made here

        Link names in Atomica end in 'par_name:flow' so passing in a code name of this form
        will return links. Links can also be identified by the compartments that they connect.
        Allowed syntax is:
        - 'source_name:' - All links going out from source
        - ':dest_name' - All links going into destination
        - 'source_name:dest_name' - All links from Source to Dest
        - 'source_name:dest_name:par_name' - All links from Source to Dest belonging to a given Parameter
        - ':dest:par_name'
        - 'source::par_name' - As per above
        - '::par_name' - All links with specified par_name (less efficient than 'par_name:flow')

        :param name: Code name to search for
        :return: A list of Variables

        """

        name = name.replace('___', ':')  # Parameter functions will convert ':' to '___' for use in variable names

        if name in self.comp_lookup:
            return [self.comp_lookup[name]]
        elif name in self.charac_lookup:
            return [self.charac_lookup[name]]
        elif name in self.par_lookup:
            return [self.par_lookup[name]]
        elif name in self.link_lookup:
            return self.link_lookup[name]
        elif ':' in name:

            name_tokens = name.split(':')
            if len(name_tokens) == 2:
                name_tokens.append('')
            src, dest, par = name_tokens

            if src and dest:
                links = [l for l in self.get_comp(src).outlinks if l.dest.name == dest]
            elif src:
                links = self.get_comp(src).outlinks
            elif dest:
                links = self.get_comp(dest).inlinks
            else:
                links = self.links

            if par:
                links = [l for l in links if l.parameter.name == par]

            return links
        else:
            raise NotFoundError(f"Object '{name}' not found in population '{self.name}'")

    def get_comp(self, comp_name):
        """ Allow compartments to be retrieved by name rather than index. Returns a Compartment. """
        try:
            return self.comp_lookup[comp_name]
        except KeyError:
            raise NotFoundError(f'Compartment {comp_name} not found')

    def get_links(self, name) -> list:
        """ Retrieve Links. """
        # Links can be looked up by parameter name or by link name, unlike get_variable. This is because
        # get_links() is guaranteed to return a list of Link objects
        # As opposed to get_variable which would retrieve the Parameter for 'doth rate' and the Links for 'z'
        if name in self.par_lookup:
            return self.par_lookup[name].links
        elif name in self.link_lookup:
            return self.link_lookup[name]
        else:
            raise NotFoundError("Object '{0}' not found.".format(name))

    def get_charac(self, charac_name):
        """ Allow dependencies to be retrieved by name rather than index. Returns a Variable. """
        try:
            return self.charac_lookup[charac_name]
        except KeyError:
            raise NotFoundError(f'Characteristic {charac_name} not found')

    def get_par(self, par_name):
        """ Allow dependencies to be retrieved by name rather than index. Returns a Variable. """
        try:
            return self.par_lookup[par_name]
        except KeyError:
            raise NotFoundError(f'Parameter {par_name} not found')

    def gen_cascade(self, framework, progset):
        """
        Generate a compartmental cascade as defined in a settings object.
        Fill out the compartment, transition and dependency lists within the model population object.
        Maintaining order as defined in a cascade workbook is crucial due to cross-referencing.
        """

        comps = framework.comps
        characs = framework.characs
        pars = framework.pars

        # Instantiate compartments
        for comp_name in list(comps.index):
            if comps.at[comp_name,'population type'] == self.type:
                self.comps.append(Compartment(pop=self, name=comp_name))
                if comps.at[comp_name, "is source"] == 'y':
                    self.comps[-1].tag_birth = True
                if comps.at[comp_name, "is sink"] == 'y':
                    self.comps[-1].tag_dead = True
                if comps.at[comp_name, "is junction"] == 'y':
                    self.comps[-1].is_junction = True
        self.comp_lookup = {comp.name: comp for comp in self.comps}

        # Characteristics first pass, instantiate objects
        for charac_name in list(characs.index):
            if characs.at[charac_name,'population type'] == self.type:
                self.characs.append(Characteristic(pop=self, name=charac_name))
        self.charac_lookup = {charac.name: charac for charac in self.characs}

        # Characteristics second pass, add includes and denominator
        for charac in self.characs:
            includes = [x.strip() for x in characs.at[charac.name, 'components'].split(',')]
            for inc_name in includes:
                charac.add_include(self.get_variable(inc_name)[0])  # nb. We expect to only get one match for the name, so use index 0
            denominator = characs.at[charac.name, "denominator"]
            if denominator is not None:
                charac.add_denom(self.get_variable(denominator)[0])  # nb. framework import strips whitespace from the overall field

        # Parameters first pass, create parameter objects and links
        for par_name in list(pars.index):
            if pars.at[par_name,'population type'] == self.type:
                par = Parameter(pop=self, name=par_name)
                par.units = pars.at[par_name, "format"]
                par.timescale = pars.at[par_name, "timescale"]
                par.derivative = pars.at[par_name, "is derivative"] == 'y'
                self.pars.append(par)
                if framework.transitions[par_name]:
                    for pair in framework.transitions[par_name]:
                        src = self.get_comp(pair[0])
                        dst = self.get_comp(pair[1])
                        tag = par.name + ':flow'
                        new_link = Link(self, par, src, dst, tag)
                        if tag not in self.link_lookup:
                            self.link_lookup[tag] = [new_link]
                        else:
                            self.link_lookup[tag].append(new_link)
                        self.links.append(new_link)
        self.par_lookup = {par.name: par for par in self.pars}

        # Parameters second pass, process f_stacks, deps, and limits
        for par in self.pars:
            min_value = pars.at[par.name, 'minimum value']
            max_value = pars.at[par.name, 'maximum value']

            if (min_value is not None) or (max_value is not None):
                par.limits = [-np.inf, np.inf]
                if min_value is not None:
                    par.limits[0] = min_value
                if max_value is not None:
                    par.limits[1] = max_value

            fcn_str = pars.at[par.name, 'function']
            if fcn_str is not None:
                par.set_fcn(framework, fcn_str, progset)

    def preallocate(self, tvec, dt):
        """
        Pre-allocate variable arrays in compartments, links and dependent variables for faster processing.
        Array maintains initial value but pre-fills everything else with NaNs.
        Thus errors due to incorrect parset value saturation should be obvious from results.
        """
        for obj in self.comps + self.characs + self.links + self.pars:
            obj.preallocate(tvec, dt)

    def initialize_compartments(self, parset, framework, t_init):
        # Given a set of characteristics and their initial values, compute the initial
        # values for the compartments by solving the set of characteristics simultaneously

        # Build up the comps and characs containing the setup values in the databook - the `b` in `x=A*b`
        characs_to_use = framework.characs.index[(~framework.characs['databook page'].isnull() & framework.characs['setup weight'] & (framework.characs['population type'] == self.type))]
        comps_to_use = framework.comps.index[(~framework.comps['databook page'].isnull() & framework.comps['setup weight'] & (framework.comps['population type'] == self.type))]
        b_objs = [self.charac_lookup[x] for x in characs_to_use] + [self.comp_lookup[x] for x in comps_to_use]

        # Build up the comps corresponding to the `x` values in `x=A*b` i.e. the compartments being solved for
        comps = [c for c in self.comps if not (c.tag_birth or c.tag_dead)]
        charac_indices = {c.name: i for i, c in enumerate(b_objs)}  # Make lookup dict for characteristic indices
        comp_indices = {c.name: i for i, c in enumerate(comps)}  # Make lookup dict for compartment indices

        b = np.zeros((len(b_objs), 1))
        A = np.zeros((len(b_objs), len(comps)))

        # Construct the characteristic value vector (b) and the includes matrix (A)
        for i, obj in enumerate(b_objs):
            # Look up the characteristic value
            par = parset.pars[obj.name]
            b[i] = par.interpolate(tvec=np.array([t_init]), pop_name=self.name)[0] * par.y_factor[self.name] * par.meta_y_factor
            if isinstance(obj, Characteristic):
                if obj.denominator is not None:
                    denom_par = parset.pars[obj.denominator.name]
                    b[i] *= denom_par.interpolate(tvec=np.array([t_init]), pop_name=self.name)[0] * denom_par.y_factor[self.name] * denom_par.meta_y_factor
                for inc in obj.get_included_comps():
                    A[i, comp_indices[inc.name]] = 1.0
            else:
                A[i, comp_indices[obj.name]] = 1.0

        # Solve the linear system (nb. lstsq returns the minimum norm solution
        x = np.linalg.lstsq(A, b.ravel(), rcond=None)[0].reshape(-1, 1)
        proposed = np.matmul(A, x)
        residual = np.sum((proposed.ravel()-b.ravel())**2)

        # Accumulate any errors here. The errors could occur either at the system level or at the level
        # of individual comps/characs. To avoid
        error_msg = ''
        characteristic_tolerence_failed = False

        # Print warning for characteristics that are not well matched by the compartment size solution
        for i in range(0, len(b_objs)):
            if abs(proposed[i] - b[i]) > model_settings['tolerance']:
                characteristic_tolerence_failed = True
                error_msg += "Characteristic '{0}' '{1}' - Requested {2}, Calculated {3}\n".format(self.name, b_objs[i].name, b[i], proposed[i])

        # Print expanded diagnostic for negative compartments showing parent characteristics
        def report_characteristic(charac, n_indent=0):
            """
            Recursively diagnose characteristic

            If a compartment has been assigned a negative value, it is usually because
            that negative value is required to match a target characteristic value. This
            method takes the root characteristic, and prints out all of the compartments
            relating to it, as well as descending further into any included characteristics.
            This brings together all of the affected quantities to help diagnose where the
            negative compartment size originates.

            :param charac: A :class:`Characteristic` instance
            :param n_indent: Indent level used to prefix the log message
            :return: A string containing the debug output

            """

            msg = ''
            if charac.name in charac_indices:
                msg += n_indent * "\t" + "Characteristic '{0}': Target value = {1}\n".format(charac.name, b[charac_indices[charac.name]])
            else:
                msg += n_indent * "\t" + "Characteristic '{0}' not in databook: Target value = N/A (0.0)\n".format(charac.name)

            n_indent += 1
            if isinstance(charac, Characteristic):
                for inc in charac.includes:
                    if isinstance(inc, Characteristic):
                        msg += report_characteristic(inc, n_indent)
                    else:
                        msg += n_indent * '\t' + 'Compartment %s: Computed value = %f\n' % (inc.name, x[comp_indices[inc.name]])
            return msg

        for i in range(0, len(comps)):
            if x[i] < -model_settings['tolerance']:
                error_msg += 'Compartment %s %s - Calculated %f\n' % (self.name, comps[i].name, x[i])
                for charac in b_objs:
                    try:
                        if comps[i] in charac.get_included_comps():
                            error_msg += report_characteristic(charac)
                    except Exception:
                        if comps[i] == charac:
                            error_msg += report_characteristic(charac)

        if residual > model_settings["tolerance"]:
            # Halt for an unsatisfactory overall solution
            raise BadInitialization("Global residual was %g which is unacceptably large (should be < %g)\n%s" % (residual, model_settings['tolerance'],error_msg))
        elif np.any(np.less(x, -model_settings['tolerance'])):
            # Halt for any negative popsizes
            raise BadInitialization('Negative initial popsizes:\n%s' % (error_msg))
        elif characteristic_tolerence_failed:
            raise BadInitialization('Characteristics failed to meet tolerances\n%s' % (error_msg))
        elif error_msg:
            # Generic error message if any of the warning messages were encountered - not entirely sure when
            # this would happen so if this *does* occur, it should be written as an explicit branch above
            # (but it exists as a fallback to ensure that any inconsistencies result in the error being raised)
            raise BadInitialization('Initialization error\n%s' % (error_msg))

        # Otherwise, insert the values
        for i, c in enumerate(comps):
            c.vals[0] = max(0.0, x[i])

        for c in self.comps:
            if c.tag_birth or c.tag_dead:
                c.vals[0] = 0


class Model(object):
    """ A class to wrap up multiple populations within model and handle cross-population transitions. """

    def __init__(self, settings, framework, parset, progset=None, program_instructions=None):
        #
        # Note that if a progset is provided and program instructions are not, then programs will not be
        # turned on. However, the progset is still available so that the coverage can still be probed
        # (in particular, the coverage denominator from Result.get_coverage('denominator') is used
        # for reconciliation
        #
        # Record version info for the model run. These are generally NOT updated in migration. Thus, they serve
        # as a record of which specific version of the code was used to generate the results
        self.version = version
        self.gitinfo = sc.dcp(gitinfo)
        self.created = sc.now()

        self.pops = list()  # List of population groups that this model subdivides into.
        self.interactions = sc.odict()
        self.programs_active = None  # True or False depending on whether Programs will be used or not
        self.progset = sc.dcp(progset)
        self.program_instructions = sc.dcp(program_instructions)  # program instructions
        self.t = None
        self.dt = None

        self._t_index = 0  # Keeps track of array index for current timepoint data within all compartments.
        self._vars_by_pop = None  # Cache to look up lists of variables by name across populations
        self._pop_ids = sc.odict()  # Maps name of a population to its position index within populations list.
        self._program_cache = None
        self._par_list = None  # This is a list of all parameters code names in the model

        self.framework = sc.dcp(framework)  # Store a copy of the Framework used to generate this model
        self.framework.spreadsheet = None  # No need to keep the spreadsheet
        self.build(settings, parset)

    def unlink(self):
        # Break cycles when deepcopying or pickling by swapping them for IDs
        # Primary storage is in the comps, links, and outputs properties

        # If we are already unlinked, do nothing
        if self._vars_by_pop is None:
            return

        for pop in self.pops:
            pop.unlink()

        self._vars_by_pop = None
        self._program_cache = None  # This drops the cache when pickling, but its only going to have anything if pickled DURING process() i.e. only devs would encounter this

    def relink(self):
        # Need to enumerate objects at Model level because transitions link across pops

        # Do we need to link any pops?
        objs = {}
        if any([not x.is_linked for x in self.pops]):
            for pop in self.pops:
                objs[pop.name] = pop
                for obj in pop.comps + pop.characs + pop.pars + pop.links:
                    objs[obj.id] = obj

            for pop in self.pops:
                pop.relink(objs)

        if self._vars_by_pop is None:
            self.set_vars_by_pop()

    def update_program_cache(self):

        # Finally, prepare programs
        if self.progset and self.program_instructions:
            self.programs_active = True
            self._program_cache = dict()

            self._program_cache['comps'] = dict()
            for prog in self.progset.programs.values():
                self._program_cache['comps'][prog.name] = []
                for pop_name in prog.target_pops:
                    for comp_name in prog.target_comps:
                        self._program_cache['comps'][prog.name].append(self.get_pop(pop_name).get_comp(comp_name))

            self._program_cache['capacities'] = self.progset.get_capacities(tvec=self.t, dt=self.dt, instructions=self.program_instructions)

            # Cache the proportion coverage for coverage scenarios so that we don't call interpolate() every timestep
            self._program_cache['prop_coverage'] = dict()
            for prog_name, coverage_ts in self.program_instructions.coverage.items():
                self._program_cache['prop_coverage'][prog_name] = coverage_ts.interpolate(self.t)

        else:
            self.programs_active = False

    def set_vars_by_pop(self):
        self._vars_by_pop = defaultdict(list)
        par_names = []
        for pop in self.pops:
            for var in pop.comps + pop.characs + pop.pars + pop.links:
                self._vars_by_pop[var.name].append(var)
            for par in pop.pars:
                par_names.append(par.name)
        self._vars_by_pop = dict(self._vars_by_pop)  # Stop new entries from appearing in here by accident
        self._par_list = list(sc.odict.fromkeys(par_names))

    def __getstate__(self):
        self.unlink()
        d = sc.dcp(self.__dict__)  # Pickling to string results in a copy
        self.relink()  # Relink, otherwise the original object gets unlinked
        return d

    def __setstate__(self, d):
        self.__dict__ = d
        self.relink()

    def __deepcopy__(self, memodict={}):
        # Using dcp(self.__dict__) is faster than pickle getstate/setstate
        # when this is called via copy.deepcopy()
        self.unlink()
        d = sc.dcp(self.__dict__)
        self.relink()
        new = Model.__new__(Model)
        new.__dict__.update(d)
        new.relink()
        return new

    def get_pop(self, pop_name):
        """ Allow model populations to be retrieved by name rather than index. """
        pop_index = self._pop_ids[pop_name]
        return self.pops[pop_index]

    def build(self, settings, parset):
        """ Build the full model. """

        self.t = settings.tvec  # Note: Class @property method returns a new object each time.
        self.dt = settings.sim_dt

        # First construct all of the object instances nested within each population
        # This also performs population-specific initialization of dependencies
        # e.g. parameter functions, but NOT any that transcend populations i.e. pop aggregations
        for k, (pop_name, pop_label, pop_type) in enumerate(zip(parset.pop_names, parset.pop_labels, parset.pop_types)):
            self.pops.append(Population(framework=self.framework, name=pop_name, label=pop_label, progset=self.progset, pop_type=pop_type))
            # Memory is allocated, speeding up model. However, values are NaN to enforce proper parset value saturation.
            self.pops[-1].preallocate(self.t, self.dt)
            self._pop_ids[pop_name] = k
            self.pops[-1].initialize_compartments(parset, self.framework, self.t[0])

        # Expand interactions into matrix form
        self.interactions = dict()
        for name, weights in parset.interactions.items():
            from_pops = [x.name for x in self.pops if x.type == self.framework.interactions.at[name,'from population type']]
            to_pops = [x.name for x in self.pops if x.type == self.framework.interactions.at[name,'to population type']]
            self.interactions[name] = np.zeros((len(from_pops), len(to_pops), len(self.t)))
            for from_pop, par in weights.items():
                for to_pop in par.pops:
                    self.interactions[name][from_pops.index(from_pop), to_pops.index(to_pop), :] = par.interpolate(self.t, to_pop) * par.y_factor[to_pop] * par.meta_y_factor


        # Instantiate transfer parameters
        # Note transfer parameters can currently only be data parameters (i.e. they don't have any functions) so
        # no need to worry about setting functions and flagging dependencies for them
        for transfer_name in parset.transfers:
            if parset.transfers[transfer_name]:
                for pop_source in parset.transfers[transfer_name]:

                    # This contains the data for all of the destination pops.
                    transfer_parameter = parset.transfers[transfer_name][pop_source]

                    pop = self.get_pop(pop_source)

                    for pop_target in transfer_parameter.ts:

                        # Create the parameter object for this link (shared across all compartments)
                        par_name = "%s_%s_to_%s" % (transfer_name, pop_source , pop_target)  # e.g. 'aging_0-4_to_15-64'
                        par = Parameter(pop=pop, name=par_name)
                        par.preallocate(self.t, self.dt)
                        par.scale_factor = transfer_parameter.y_factor[pop_target] * transfer_parameter.meta_y_factor
                        par.vals = transfer_parameter.interpolate(tvec=self.t, pop_name=pop_target) * par.scale_factor
                        par.units = transfer_parameter.ts[pop_target].units.strip().split()[0].strip().lower()
                        pop.pars.append(par)
                        pop.par_lookup[par_name] = par

                        target_pop_obj = self.get_pop(pop_target)

                        for source in pop.comps:
                            if not (source.tag_birth or source.tag_dead or source.is_junction):
                                # Instantiate a link between corresponding compartments
                                dest = target_pop_obj.get_comp(source.name)  # Get the corresponding compartment
                                link = Link(pop, par, source, dest, par.name + ':flow')
                                link.preallocate(self.t, self.dt)
                                pop.links.append(link)
                                if link.name in pop.link_lookup:
                                    pop.link_lookup[link.name].append(link)
                                else:
                                    pop.link_lookup[link.name] = [link]

        # Now that all object have been created, update _vars_by_pop() accordingly
        self.set_vars_by_pop()

        # Flag dependencies for aggregated parameters prior to precomputing
        for par in self._par_list:
            pars = self._vars_by_pop[par]
            if pars[0].pop_aggregation:
                for var in self._vars_by_pop[pars[0].pop_aggregation[1]]:
                    var.set_dynamic(progset=self.progset)
                if len(pars[0].pop_aggregation) > 3:
                    for var in self._vars_by_pop[pars[0].pop_aggregation[3]]:
                        var.set_dynamic(progset=self.progset)

        # Insert parameter initial values and do any required precomputation
        for par_name in self.framework.pars.index: # Iterate only over framework pars (parset.pars also includes characteristics)
            cascade_par = parset.pars[par_name]
            if cascade_par.name in self._vars_by_pop: # The parameter could be missing if it is defined in a population type that is not present in the simulation
                pars = self._vars_by_pop[cascade_par.name]
                for par in pars:
                    par.scale_factor = cascade_par.meta_y_factor # Set meta scale factor regardless of whether a population-specific y-factor is also provided

                    if par.pop.name in cascade_par.y_factor:
                        par.scale_factor *= cascade_par.y_factor[par.pop.name] # Add in population-specific scale factor

                    if par.pop.name in cascade_par.skip_function:
                        par.skip_function = cascade_par.skip_function[par.pop.name] # Copy in any skipped evaluations
                        if par.skip_function:
                            assert cascade_par.has_values(par.pop.name), 'Parameter function was marked as being skipped for some of the simulation, but the ParameterSet has no values to use instead. If skipping, the ParameterSet must contain some values'

                    if cascade_par.has_values(par.pop.name): # If the databook contains values, then insert them now
                        par.vals = cascade_par.interpolate(tvec=self.t, pop_name=par.pop.name) * par.scale_factor

                    if par.fcn_str and par._precompute: # If the parameter is marked for precomputation, then insert it now
                        par.update()

                    par.constrain()  # Sampling might result in the parameter value going out of bounds (or user might have entered bad values in the databook) so ensure they are clipped here

    def process(self):
        """ Run the full model. """

        assert self._t_index == 0  # Only makes sense to process a simulation once, starting at ti=0 - this might be relaxed later on

        self.update_program_cache()

        # Initial flush of people in junctions
        if self._t_index == 0:
            # Make sure initially-filled junctions are processed and initial dependencies are calculated, and calculate initial flows
            self.update_pars()  # Update transition parameters in case junction outflows are function parameters
            self.update_junctions(initial_flush=True)  # Flush the current contents of the junction without considering any inflows
            self.update_pars()  # Update the transition parameters in case junction outflows are functions _and_ they depend on compartment sizes that just changed in the line above
            self.update_links()  # Update all of the links
            self.update_junctions()  # Junctions are now empty - perform a normal update by setting the outflows to be equal to the inflows so the usual condition outflow[t]=inflow[t] is satisfied

        # Main integration loop
        while self._t_index < (self.t.size - 1):
            self.update_comps()  # This writes values to comp.vals[ti+1] so this will be out of bounds if self._t_index == self.t.size-1
            self._t_index += 1  # Step the simulation forward
            self.update_pars()
            self.update_links()
            self.update_junctions()

        for pop in self.pops:

            for par in pop.pars:
                if par.fcn_str and not (par._is_dynamic or par._precompute):
                    par.update()
                    par.constrain()

            for charac in pop.characs:
                charac._vals = None  # Wipe out characteristic vals to save space

        self._program_cache = None  # Drop the program cache afterwards to save space

    def update_links(self):
        """
        Evolve model characteristics by one timestep (defaulting as 1 year).
        Each application of this method writes calculated values to the next position in popsize arrays.
        This is done regardless of dt.
        Thus the corresponding time vector associated with variable dt steps must be tracked externally.
        This function computes the link flow rates.
        """

        ti = self._t_index

        for pop in self.pops:

            # First, populate all of the link values without any outflow constraints
            for par in pop.pars:
                if par.links:

                    transition = par.vals[ti]
                    if transition < 0:
                        # This condition is likely to occur if the parameter has a function but it has been
                        # incorrectly/poorly defined so that it returns a negative value. If this is expected
                        # to happen under certain conditions, then the Framework should have a minimum value of 0
                        # entered for the parameter to make it explicit that the value is constrained to be positive.
                        # This could be important if the parameter is *also* used as a dependency in other parameters
                        # because clipping in the Framework is applied before downstream parameters are computed, whereas
                        # the check here only relates to the links, so an incorrect negative value could still propagate
                        # to other parameters (but we cannot be *certain* here that this isn't what the user intended)
                        logger.warning('Negative transition occurred')
                        transition = 0

                    if not transition:
                        for link in par.links:
                            link.vals[ti] = 0.0
                        continue
                    quantity_type = par.units

                    # Convert from duration to equivalent probability
                    if quantity_type == FS.QUANTITY_TYPE_DURATION:
                        converted_frac = min(1,self.dt / (transition * par.timescale))
                        for link in par.links:
                            link.vals[ti] = link.source.vals[ti] * converted_frac

                    # Convert probability by Poisson distribution formula to a value appropriate for timestep.
                    elif quantity_type == FS.QUANTITY_TYPE_PROBABILITY:
                        # Note that we convert the transition to the timestep before checking whether it is greater than 1 or not. That way,
                        # durations get preserved until we limit them based on the timestep size. The rationale is that the annual probability
                        # will come out at 1.0 if the *mean* duration is the same as the step size, but that doesn't mean that if the step size
                        # was smaller the timestep probability is also 1.0 - it's a consequence of the discretization. Essentially, a value
                        # greater than 1 simply implies that the mean duration is less than the timescale in question, and we need to retain that value
                        # to be able to correctly convert between timescales. The subsequent call to min() then ensures that the fraction moved never
                        # exceeds 1.0 once operating on the timestep level
                        converted_frac = min(1,transition * (self.dt / par.timescale))
                        for link in par.links:
                            link.vals[ti] = link.source.vals[ti] * converted_frac

                    # Linearly convert number down to that appropriate for one timestep.
                    elif quantity_type == FS.QUANTITY_TYPE_NUMBER:

                        # Disaggregate proportionally across all source compartment sizes related to all links.
                        converted_amt = transition * (self.dt / par.timescale) # Number flow in this timestep, so it includes a timescale factor
                        if len(par.links) > 1:
                            for link in par.links:
                                link.vals[ti] = converted_amt * link.source.vals[ti] / par.source_popsize(ti)
                        else:
                            par.links[0].vals[ti] = converted_amt

                    # Raise an error if the transition parameter has unrecognized units
                    elif quantity_type not in [FS.QUANTITY_TYPE_PROPORTION]:
                        try:
                            par_label = self.framework.get_label(par.name)
                        except:  # Name lookup will fail for transfer parameters
                            par_label = par.name
                        raise Exception("Encountered unknown units '%s' for Parameter '%s' (%s) in Population %s" % (quantity_type, par.name, par_label, pop.name))

            # Then, adjust outflows to prevent negative popsizes.
            for comp_source in pop.comps:
                if not (comp_source.is_junction or comp_source.tag_birth):
                    outflow = 0.0
                    for link in comp_source.outlinks:
                        outflow += link.vals[ti]

                    if outflow > comp_source.vals[ti]:
                        rescale = comp_source.vals[ti] / outflow
                        for link in comp_source.outlinks:
                            link.vals[ti] *= rescale

    def update_comps(self):
        """
        Set the compartment values at self._t_index+1 based on the current values at self._t_index
        and the link values at self._t_index. Values are updated by iterating over all outgoing links

        """

        ti = self._t_index

        # Pre-populate the current value - need to iterate over pops here because transfers
        # will cross population boundaries
        for pop in self.pops:
            for comp in pop.comps:
                comp.vals[ti + 1] = comp.vals[ti]

        # update_junctions will perform the compartment size update for all junctions but nothing else
        # Therefore, we need to resolve any links where neither endpoint is a junction
        # This is because a junction with inlinks still needs its sources to have the flow deducted, and
        # a junction with outlinks still needs its destination to have the flow applied
        for pop in self.pops:
            for comp in pop.comps:
                for link in comp.outlinks:
                    if not link.source.is_junction:
                        link.source.vals[ti + 1] -= link.vals[ti]
                    if not link.dest.is_junction:
                        link.dest.vals[ti + 1] += link.vals[ti]

        # Guard against populations becoming negative due to numerical artifacts
        for pop in self.pops:
            for comp in pop.comps:
                comp.vals[ti + 1] = max(0, comp.vals[ti + 1])

    def update_junctions(self, initial_flush=False):
        """
        For every compartment considered a junction, propagate the contents onwards.
        Do so until all junctions are empty.
        """

        # A junction can be called either at the very start of the simulation, when it might have
        # some people in it initially, or after `update_links` in which case it won't have any people
        # so it needs to fill itself from its incoming links

        ti = self._t_index  # The current simulation timestep, at time ti the inflow and outflow need to be balanced. `update_links()` sets the inflow but not the outflow, which is done here

        for pop in self.pops:

            # Initialize the junctions and their links
            junctions = [comp for comp in pop.comps if comp.is_junction]
            for junc in junctions:
                if not initial_flush:  # At most timesteps, initialize based on inflows
                    junc.vals[ti] = 0.
                    for link in junc.inlinks:
                        if not link.source.is_junction:  # inlinks that come from a junction won't have been initialized at this timestep yet
                            junc.vals[ti] += link.vals[ti]
                else:  # At the very first iteration, use the junction's current value (e.g., if a nonzero value arose from the databook)
                    if np.isnan(junc.vals[ti]):
                        junc.vals[ti] = 0.

                # Initialize the outflow links
                for link in junc.outlinks:
                    link.vals[ti] = 0.

            # Repeatedly flush the junctions until they have all resolved (this deals with cases where one
            # junction has a flow into another junction)
            for i in range(0, model_settings["iteration_limit"]):
                review_required = False

                for junc in junctions:
                    # If the compartment is numerically empty, make it empty
                    if junc.vals[ti] <= model_settings['tolerance']:  # Includes negative values.
                        junc.vals[ti] = 0.
                    else:
                        current_size = junc.vals[ti]
                        # This is the total fraction of people requested to leave.
                        # Outflows are scaled to the entire compartment size.
                        denom_val = sum(link.parameter.vals[ti] for link in junc.outlinks)
                        if denom_val == 0:
                            raise Exception("Total junction outflow for junction '%s' was zero - all junctions must have a nonzero outflow" % (self.framework.get_label(junc.name)))

                        for link in junc.outlinks:
                            flow = current_size * link.parameter.vals[ti] / denom_val
                            junc.vals[ti] -= flow
                            link.vals[ti] += flow
                            if link.dest.is_junction or initial_flush:
                                # In the initial flush, we need to update the downstream compartments
                                link.dest.vals[ti] += flow
                                review_required = True  # Need to review if a junction received an inflow at this step

                if not review_required:
                    break
            else:
                raise Exception("Processing junctions for timestep {0} is taking too long. Infinite loop suspected.".format(ti))

    def update_pars(self):
        """
        Run through all parameters and characteristics flagged as dependencies for custom-function parameters.
        Evaluate them for the current timestep.
        These dependencies must be calculated in the same order as defined in settings.
        This also means characteristics before parameters, otherwise references may break.
        Also, parameters in dependency list do not need calculation unless explicitly depending on another parameter.
        Parameters that have special rules are usually dependent on other population values, so are included here.
        """

        ti = self._t_index

        # First, compute dependent characteristics, as parameters might depend on them
        for pop in self.pops:
            for charac in pop.characs:
                if charac._is_dynamic:
                    charac.update(ti)

        do_program_overwrite = self.programs_active and self.program_instructions.start_year <= self.t[ti] <= self.program_instructions.stop_year

        if do_program_overwrite:
            prop_coverage = sc.odict.fromkeys(self._program_cache['comps'], 0.0)
            for k, comp_list in self._program_cache['comps'].items():
                if k in self._program_cache['prop_coverage']:  # If the coverage was precomputed in a coverage scenario
                    prop_coverage[k] = self._program_cache['prop_coverage'][k][[ti]]
                else:
                    n = 0.0
                    for comp in comp_list:
                        n += comp.vals[ti]
                    prop_coverage[k] = self.progset.programs[k].get_prop_covered(self.t[ti], self._program_cache['capacities'][k][ti], n)
            prog_vals = self.progset.get_outcomes(prop_coverage)

        for par_name in self._par_list:
            # All of the parameters with this name, across populations.
            # There should be one for each population (these are Parameters, not Links).
            pars = self._vars_by_pop[par_name]

            # First - update parameters that are dependencies, evaluating f_stack if required
            for par in pars:
                if par._is_dynamic:
                    par.update(ti)

            # Then overwrite with program values
            if do_program_overwrite:
                for par in pars:
                    if (par.name, par.pop.name) in prog_vals:
                        par.vals[ti] = prog_vals[(par.name, par.pop.name)]
                        if par.units == FS.QUANTITY_TYPE_NUMBER:
                            par.vals[ti] *= par.source_popsize(ti) / self.dt  # The outcome in the progbook is per person reached, which is a timestep specific value. Thus, need to annualize here

            # Handle parameters that aggregate over populations and use interactions in these functions.
            if pars[0].pop_aggregation:
                # NB. `par.pop_aggregation` is (agg_fcn,par_name,interaction_name,charac_name) where the last item is optional

                par_vals = [x.vals[ti] for x in self._vars_by_pop[pars[0].pop_aggregation[1]]]  # Value of variable being averaged
                par_vals = np.array(par_vals).reshape(-1, 1)

                # NOTE - When doing cross-population interactions, 'pars' is from the 'to' pop
                # and 'par_vals' is from the 'from pop
                if len(pars[0].pop_aggregation) < 3:
                    weights = np.ones((len(par_vals),len(pars)))
                else:
                    weights = self.interactions[pars[0].pop_aggregation[2]][:, :, ti].copy()

                if pars[0].pop_aggregation[0] in {'SRC_POP_AVG', 'SRC_POP_SUM'}:
                    weights = weights.T
                elif pars[0].pop_aggregation[0] in {'TGT_POP_AVG', 'TGT_POP_SUM'}:
                    pass
                else:
                    raise Exception("Unknown aggregation function '{0}'").format(pars[0].pop_aggregation[0])  # This should never happen, an error should be raised earlier

                # If we are weighting by a variable, multiply the weights matrix accordingly
                if len(pars[0].pop_aggregation) == 4:
                    vals = [par.vals[ti] for par in self._vars_by_pop[pars[0].pop_aggregation[3]]]  # Value of weighting variable
                    vals = np.array(vals).reshape(-1, 1)
                    weights *= vals.T

                if pars[0].pop_aggregation[0] in {'SRC_POP_AVG', 'TGT_POP_AVG'}:
                    weights /= np.sum(weights, axis=1, keepdims=1)  # Normalize the interaction
                par_vals = np.matmul(weights, par_vals)

                for par, val in zip(pars, par_vals):
                    par.vals[ti] = par.scale_factor * val

            # Restrict the parameter's value if a limiting range was defined
            for par in pars:
                if par.derivative and ti>0:
                    # If derivative parameter, then perform an Euler forward step
                    # Handling the derivative here means that it is possible to overwrite the derivative using programs
                    # The program outcome should be the derivative value
                    par.vals[ti] = par.vals[ti-1]+par.vals[ti]*self.dt
                par.constrain(ti)


def run_model(settings, framework, parset, progset=None, program_instructions=None, name=None):
    """
    Processes the TB epidemiological model.
    Parset-based overwrites are generally done externally, so the parset is only used for model-building.
    Progset-based overwrites take place internally and must be part of the processing step.
    The instructions dictionary is usually passed in with progset to specify when the overwrites take place.
    """

    m = Model(settings, framework, parset, progset, program_instructions)
    m.process()
    # NOTE - the `model` object contains model.framework, model.progset, and model.program_instructions
    return Result(model=m, parset=parset, name=name)
