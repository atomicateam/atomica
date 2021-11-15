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
from .programs import ProgramSet, ProgramInstructions
from .parameters import Parameter as ParsetParameter
from .parameters import ParameterSet as ParameterSet
import math

model_settings = dict()
model_settings["tolerance"] = 1e-6

__all__ = [
    "BadInitialization",
    "ModelError",
    "Variable",
    "Compartment",
    "JunctionCompartment",
    "ResidualJunctionCompartment",
    "SourceCompartment",
    "SinkCompartment",
    "TimedCompartment",
    "Characteristic",
    "Parameter",
    "Link",
    "TimedLink",
    "Population",
    "Model",
    "run_model",
]


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


class ModelError(Exception):
    """
    Exception type for general model errors

    This error gets raised for generic errors arising during integration

    """

    pass


class Variable:
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
        self.t = None  # : Array of time values. This should be a reference to the base array stored in a :class:`model` object
        self.dt = None  # : Time step size
        if "vals" not in dir(self):  # If a derived class implements a @property method for `vals`, then don't instantiate it as an attribute
            self.vals = None  # : The fundamental values stored by this object
        self.units = "unknown"  #: The units for the quantity, used for plotting and for validation. Note that the default ``'unknown'`` units are distinct to dimensionless units, which have value ``''``
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
        self.vals = np.empty(tvec.shape)
        self.vals.fill(np.nan)

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
        plt.xlabel("Year")
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

    def __getitem__(self, key):
        """
        Shortcut to access .vals attribute

        This simplifies syntax for the most common operations on Variable objects, but most importantly,
        enables derived classes that implement a ``@property`` method for ``vals`` to also overload the
        indexing.

        e.g. ``alive[ti]`` or ``b_rate[ti]``

        :param key: Indexer passed directly to the numpy array ``self.vals[key]``
        :return: A float or array of floats the same size as ``key``

        """
        return self.vals[key]

    def __setitem__(self, key, value) -> None:
        """
        Shortcut to set .vals attribute

        This method assigns values to the `.vals` attribute e.g., ``sus[ti] = 0`` instead of
        ``sus.vals[ti] = 0``. Importantly, this allows the derived class to overload ``__getitem__``
        if ``vals`` is a property method instead of an actual array.

        :param key: Indexer passed directly to the numpy array ``self.vals[item]``
        :param value: Value to assign to the result of the indexing operation

        """

        self.vals[key] = value


class Compartment(Variable):
    """A class to wrap up data for one compartment within a cascade network."""

    def __init__(self, pop, name):
        Variable.__init__(self, pop=pop, id=(pop.name, name))
        self.units = "Number of people"
        self.outlinks = []
        self.inlinks = []
        self._cached_outflow = None

    def unlink(self):
        Variable.unlink(self)
        self.outlinks = [x.id for x in self.outlinks]
        self.inlinks = [x.id for x in self.inlinks]

    def relink(self, objs):
        Variable.relink(self, objs)
        self.outlinks = [objs[x] for x in self.outlinks]
        self.inlinks = [objs[x] for x in self.inlinks]

    @property
    def outflow(self) -> np.array:
        """
        Return the outflow at all times

        :return: The sum of outgoing links at all time indices
        """
        # Return the outflow at each timestep - for a junction, this is equal to the number
        # of people that were in the junction
        x = np.zeros(self.t.shape)
        if self.outlinks:
            for link in self.outlinks:
                x += link.vals
        return x

    # Function below is a reference implementation but isn't used or needed anywhere yet
    # Keeping it here just in case it's useful later
    #
    # def inflow(self, ti:int=None):
    #     """
    #     Return the inflow at specified times
    #
    #     :param ti: Optionally specify a time index. Default is all times
    #     :return: If `ti` is None, an array the same size as `self.t`. Otherwise, returns a float
    #
    #     """
    #
    #     if ti is None:
    #         ti = np.arange(0, len(self.t))
    #         x = np.zeros(self.t.shape)
    #     else:
    #         x = 0
    #
    #     for link in self.inlinks:
    #         x += link[ti]
    #
    #     return x

    def expected_duration(self, ti=None):
        # Returns the expected number of years that an individual is expected to remain
        # in this compartment for, if the outgoing flow rates are maintained
        if ti is None:
            ti = np.arange(0, len(self.t))

        outflow_probability = 0  # Outflow probability at this timestep
        for link in self.outlinks:
            par = link.parameter
            transition = par[ti]

            if par.units == FS.QUANTITY_TYPE_DURATION:
                outflow_probability += min(1, self.dt / (transition * par.timescale))
            elif par.units in {FS.QUANTITY_TYPE_PROBABILITY, FS.QUANTITY_TYPE_RATE}:
                outflow_probability += min(1, transition * (self.dt / par.timescale))
            elif par.units == FS.QUANTITY_TYPE_NUMBER:
                outflow_probability += par[ti] * self.dt / self[ti]
            elif par.units == FS.QUANTITY_TYPE_PROPORTION:
                outflow_probability += par[ti]
            else:
                raise ModelError("Unknown parameter units")

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

        dur = (1 - (1.0 / np.log(remain_probability) ** 2) * (remain_probability - 1)) * self.dt
        return dur

    def expected_outflow(self, ti):
        # After 1 year, where are people expected to be? If people would leave in less than a year,
        # then the numbers correspond to when the compartment is empty
        popsize = self[ti]  # This is the number of people who are leaving

        outflow = {link.dest.name: popsize * link[ti] / self.dt for link in self.outlinks}
        rescale = popsize / sum([y for _, y in outflow.items()])
        for x in outflow.keys():
            outflow[x] *= rescale
        outflow[self.name] = popsize - sum([y for _, y in outflow.items()])

        return outflow

    def resolve_outflows(self, ti: int) -> None:
        """
        Resolve outgoing links and convert to number

        For the base class, rescale outgoing links so that the compartment won't go negative

        :param ti: Time index at which to update link outflows

        """

        outflow = 0.0
        for link in self.outlinks:
            outflow += link._cache

        if outflow > 1:
            rescale = 1 / outflow
        else:
            rescale = 1

        n = rescale * self.vals[ti]
        self._cached_outflow = 0
        for link in self.outlinks:
            link.vals[ti] = link._cache * n
            self._cached_outflow += link.vals[ti]

    def update(self, ti: int) -> None:
        """
        Update compartment value

        A compartment update passes in the time to assign (ti). We have

        x(ti) = x(ti-1) + inflow(ti-1) - outflow(ti-1)

        Thus, need to initialize the value and then resolve all inflows and outflows
        Junctions have already been flushed and thus do not need to be updated in this step

        :param ti:
        :return:

        """

        tr = ti - 1
        v = self.vals[tr]
        v -= self._cached_outflow
        for link in self.inlinks:
            v += link.vals[tr]

        # Guard against populations becoming negative due to numerical artifacts
        if v > 0:
            self.vals[ti] = v
        else:
            self.vals[ti] = 0.0

    def connect(self, dest, par) -> None:
        """
        Construct link out of this compartment

        :param dest: A ``Compartment`` instance
        :param par: The parameter that the Link will be associated with

        """
        Link.create(pop=self.pop, parameter=par, source=self, dest=dest)


class JunctionCompartment(Compartment):
    def __init__(self, pop, name: str, duration_group: str = None):
        """

        A TimedCompartment has a duration group by virtue of having a `.parameter` attribute and a flush link.
        A junction might belong to a duration group by having inflows and outflows exclusively from that group.
        However, it might not be directly attached to any timed compartments, if the connections are entirely
        via upstream and downstream junctions. Junctions also do not have flush links. Therefore, we record
        membership in the duration group by specifying the name of the parameter in the (indirect) upstream
        and downstream compartments.

        Note that having connections to timed compartments does not itself indicate membership in the duration
        group - the junction is only a member if all of the upstream and downstream compartments belong to the
        same duration group. The duration group is determined in framework validation and stored in the framework.

        :param pop:
        :param name:
        :param duration_group: Optionally specify a duration group

        """
        super().__init__(pop, name)
        self.duration_group = duration_group  #: Store the name of the duration group, if the junction belongs to one

    def connect(self, dest, par) -> None:
        """
        Construct link out of this compartment

        For junctions, outgoing links are normal links unless the junction belongs to a duration group.
        If the junction belongs to a duration group, then the output links should all be :class:`TimedLink` instances.

        :param dest: A ``Compartment`` instance
        :param par: The parameter that the Link will be associated with

        """

        if self.duration_group:
            if (isinstance(dest, TimedCompartment) and dest.duration_group != self.duration_group) or (isinstance(dest, JunctionCompartment) and dest.duration_group != self.duration_group):
                raise ModelError("Mismatched junction duration groups - the framework has not been validated correctly")
            TimedLink.create(pop=self.pop, parameter=par, source=self, dest=dest)
        else:
            Link.create(pop=self.pop, parameter=par, source=self, dest=dest)

    def resolve_outflows(self, ti: int) -> None:
        """
        Resolve outgoing links and convert to number

        For junctions, links are updated in a separate step because the logic is different - instead
        of the value of links coming from parameters, they come from the inflow into the junction.
        We cannot update the junctions in the same step as compartments because while the junction
        subgraphs must be acyclic, the entire system may contain cycles. Therefore it is not possible
        to determine a topological ordering for the entire system. The system is solvable because for
        normal compartments, only one transition per timestep is allowed. But regardless, this prevents
        using graph analysis to determine an execution order for the entire system that would allow
        junction computation in the same step.

        :param ti: Time index to resolve outflows

        """

        pass

    def update(self, ti: int) -> None:
        """
        Update the junction at given time index

        For compartments the ``update`` methods steps them forward in time. However, for junctions the
        value never needs to be stepped forward, because it's always zero. Thus, this function does nothing.

        :param ti: Time index to update

        """

        pass

    def preallocate(self, tvec: np.array, dt: float) -> None:
        """
        Preallocate junction values

        Junction preallocation pre-fills the values with zeros, since the junction must be empty
        at all times.

        :param tvec: An array of time values
        :param dt: Time step size

        """

        super().preallocate(tvec, dt)
        self.vals.fill(0.0)  #: Junction compartments are always empty (note the first entry may be given a nonzero value after compartment initialization and before the initial flush)

    def balance(self, ti: int) -> None:
        """
        Balance junction inflows and outflows

        This is the primary update for a junction - where outflows are adjusted so that they
        equal the inflows. It's analogous to `resolve_outflows` as a primary update method, but
        it takes place at a separate integration stage (once the outflows for normal compartments
        have been finalized, as these outputs serve as the junction inputs in that same timestep)
        After this method is called, all outflows should equal inflows

        The parameter workflow is simplified because all links flowing out of junctions must be
        in 'proportion' units, so they can be looked up and used directly.

        :param ti: Time index to update (scalar only, as this function is only called during integration)

        """

        # First, work out the total inflow that needs to pass through the junction
        net_inflow = 0
        if self.duration_group:
            for link in self.inlinks:
                net_inflow += link._vals[:, ti]  # If part of a duration group, get the flow from TimedLink._vals
        else:
            for link in self.inlinks:
                net_inflow += link.vals[ti]  # If not part of a duration group, get scalar flow from Link.vals

        # Next, get the total outflow. Note that the parameters are guaranteed to be in proportion units here
        outflow_fractions = [link.parameter.vals[ti] for link in self.outlinks]
        total_outflow = sum(outflow_fractions)

        # Finally, assign the inflow to the outflow proportionately accounting for the total outflow downscaling
        for frac, link in zip(outflow_fractions, self.outlinks):
            if self.duration_group:
                link._vals[:, ti] = net_inflow * frac / total_outflow
            else:
                link.vals[ti] = net_inflow * frac / total_outflow

    def initial_flush(self) -> None:
        """
        Perform an initial junction flush

        If the junction was initialized with a nonzero value, then the initial people need to be flushed.
        This is distinct from balancing, because the source of the people is the junction itself, rather
        than the incoming links.

        In this step, we need to actually update the value of the downstream compartments, rather than
        updating the link values - the links get rebalanced again based on the parameters after the
        initial flush has been completed

        """

        if self.vals[0] > 0:
            # Work out the outflow fractions
            outflow_fractions = np.array([link.parameter.vals[0] for link in self.outlinks])
            outflow_fractions /= np.sum(outflow_fractions)

            # Assign the inflow directly to the outflow compartments
            # This is done using the [] indexing on the downstream compartment so it is agnostic
            # to the downstream compartment type
            for frac, link in zip(outflow_fractions, self.outlinks):
                link.dest[0] += self.vals[0] * frac

            self.vals[0] = 0.0


class ResidualJunctionCompartment(JunctionCompartment):
    """
    Junction with a residual outflow

    A residual outflow junction has a single additional outflow link
    """

    def balance(self, ti: int) -> None:
        """
        Balance junction inflows and outflows

        For a ResidualJunctionCompartment, if the outflows sum to less than 1, rather than
        scaling them up proportionately, the residual is assigned to the residual link.

        :param ti: Time index to update (scalar only, as this function is only called during integration)

        """

        # First, work out the total inflow that needs to pass through the junction
        net_inflow = 0
        if self.duration_group:
            for link in self.inlinks:
                net_inflow += link._vals[:, ti]  # If part of a duration group, get the flow from TimedLink._vals
        else:
            for link in self.inlinks:
                net_inflow += link.vals[ti]  # If not part of a duration group, get scalar flow from Link.vals

        outflow_fractions = np.zeros(len(self.outlinks))
        for i, link in enumerate(self.outlinks):
            if link.parameter is not None:
                outflow_fractions[i] = link.parameter.vals[ti]
            else:
                outflow_fractions[i] = 0

        total_outflow = sum(outflow_fractions)

        if total_outflow < 1:
            has_residual = True
        else:
            outflow_fractions /= total_outflow
            has_residual = False

        # Finally, assign the inflow to the outflow proportionately accounting for the total outflow downscaling
        for frac, link in zip(outflow_fractions, self.outlinks):
            if link.parameter is None:
                if has_residual:
                    flow = net_inflow - sum(net_inflow * outflow_fractions)
                else:
                    flow = 0
            else:
                flow = net_inflow * frac

            if self.duration_group:
                link._vals[:, ti] = flow
            else:
                link.vals[ti] = flow

    def initial_flush(self) -> None:
        """
        Perform an initial junction flush

        """

        if self.vals[0] > 0:
            # Work out the outflow fractions
            outflow_fractions = np.zeros(len(self.outlinks))
            for i, link in enumerate(self.outlinks):
                if link.parameter is not None:
                    outflow_fractions[i] = link.parameter.vals[0]
                else:
                    outflow_fractions[i] = 0

            total_outflow = sum(outflow_fractions)

            if total_outflow < 1:
                has_residual = True
            else:
                outflow_fractions /= total_outflow
                has_residual = False

            # Assign the inflow directly to the outflow compartments
            # This is done using the [] indexing on the downstream compartment so it is agnostic
            # to the downstream compartment type

            # Finally, assign the inflow to the outflow proportionately accounting for the total outflow downscaling
            for frac, link in zip(outflow_fractions, self.outlinks):
                if link.parameter is None:
                    if has_residual:
                        link.dest[0] += self.vals[0] - sum(self.vals[0] * outflow_fractions)
                else:
                    link.dest[0] += self.vals[0] * frac

            self.vals[0] = 0.0


class SourceCompartment(Compartment):
    """
    Derived class for source compartments

    Source compartments are unlimited reservoirs, and are subject to limitations like

    - Unlimited size
    - No inflows
    - Only one outflow

    Therefore, the methods to update these compartments can take some shortcuts not available
    to normal compartments. These shortcuts are implemented in the overloaded methods here.

    """

    def __init__(self, pop, name):
        super().__init__(pop, name)

    def preallocate(self, tvec: np.array, dt: float) -> None:
        super().preallocate(tvec, dt)
        self.vals.fill(0.0)  #: Source compartments have an unlimited number of people in them. TODO: If this complicates validation, set to 0.0

    def resolve_outflows(self, ti: int) -> None:
        for link in self.outlinks:
            link.vals[ti] = link._cache

    def update(self, ti: int) -> None:
        pass


class SinkCompartment(Compartment):
    def __init__(self, pop, name):
        super().__init__(pop, name)

    def preallocate(self, tvec: np.array, dt: float) -> None:
        """
        Preallocate sink compartment

        A sink compartment is initialized with 0.0 value at the initial timestep

        :param tvec: Simulation time vector
        :param dt: Simulation time step

        """

        super().preallocate(tvec, dt)
        self.vals[0] = 0.0

    def resolve_outflows(self, ti: int) -> None:
        """
        Resolve sink outflows

        There should not be any outflows, so this function immediately returns

        """
        pass

    def connect(self, dest, par) -> None:
        """
        Construct link out of sink compartment

        This method raises an error because sinks cannot have outflows

        :param dest: A ``Compartment`` instance
        :param par: The parameter that the Link will be associated with

        """

        raise ModelError("Sink compartments cannot have outflows")

    def update(self, ti: int) -> None:
        """
        Update sink compartment value

        A sink compartment has inputs only

        :param ti: Time index to update

        """

        tr = ti - 1
        v = self.vals[tr]
        for link in self.inlinks:
            v += link.vals[tr]
        self.vals[ti] = v


class TimedCompartment(Compartment):
    def __init__(self, pop, name: str, parameter: ParsetParameter):
        """
        Instantiate the TimedCompartment

        Preallocation takes place before the compartment values are initialized. Therefore, we need to
        calculate the duration here, hence there is a need to take in the parset here.

        :param pop: A ``Population`` instance (the instance that will store this compartment)
        :param name: The name of the compartment
        :param parameter: The parameter that will supply the duration (to be read after the parameter function is evaluated, if applicable)

        """

        Compartment.__init__(self, pop=pop, name=name)
        self._vals = None  #: Primary storage, a matrix of size (duration x timesteps). The first row is the one that people leave from, the last row is the one that people arrive in
        self.parameter = parameter  #: The parameter to read the duration from - this needs to be done after parameters are precomputed though, in case the duration is coming from a (constant) function
        self.flush_link = None  #: Reference to the timed outflow link that flushes the compartment. Note that this needs to be set externally because Links are instantiated after Compartments

    @property
    def duration_group(self):
        return self.parameter.name

    def unlink(self):
        Compartment.unlink(self)
        if self.flush_link:
            self.flush_link = self.flush_link.id

    def relink(self, objs):
        # Given a dictionary of objects, restore the internal references
        Compartment.relink(self, objs)
        if self.flush_link:
            self.flush_link = objs[self.flush_link]

    @property
    def vals(self) -> np.array:
        """
        Compartment size

        This returns the compartment size at all times, obtained by summing over the people in each time bin

        :return: A numpy array with the compartment size

        """

        return self._vals.sum(axis=0)

    def __getitem__(self, ti):
        """
        Retrieve compartment size at given time index

        By only adding the requested timesteps, this approach is faster than accessing ``vals`` first i.e.

        >>> self.vals[ti]
        >>> self[ti] # <-- Faster

        :param ti: Time index/indices
        :return: Total compartment size at given time index/indices

        """

        return self._vals[:, ti].sum(axis=0)

    def __setitem__(self, ti, value) -> None:
        """
        Assign to values assuming constant arrival rate

        This method takes in the total population size at time(s) ``ti``, and assigns them equally
        to all of the time bins in the compartment. Currently, this is only expected to be needed
        during initialization, so for maximum safety, this method will raise an error if any other
        times are used. This is because setting the value will destroy any information about the
        distribution of times. This constraint could be safely relaxed if it's needed for a specific
        purpose, but otherwise it's safer not to permit it.

        :param ti: Time indices to assign. Currently, only `0` is allowed
        :param value: The value to assign to times `ti`

        """
        ti = sc.promotetoarray(ti)
        value = sc.promotetoarray(value)

        if ti.size > 1 or ti[0] != 0:
            raise ModelError("For safety, explicitly setting the compartment size for a TimedCompartment can currently only be done for the initial conditions. This requirement can be likely be relaxed if needed for a particular use case")
        self._vals[:, ti] = value.reshape((1, -1)) / (self._vals.shape[0] * np.ones((self._vals.shape[0], 1)))

    def preallocate(self, tvec: np.array, dt: float) -> None:
        """
        Preallocate data storage

        :param tvec: An array of time values
        :param dt: Time step size

        """

        # Preallocating the keyring matrix rounds the duration down
        # That way, if the duration is less than the step size, the compartment will
        # be emptied every timestep
        # Note that the effective duration is _entirely_ driven by the number of rows in `self._vals`
        # because the logic is simply - flush the topmost row, shift the array by 1, inflow goes in the bottom row
        self.t = tvec
        self.dt = dt
        assert np.all(self.parameter.vals == self.parameter.vals[0]), "Duration parameter value cannot vary over time"
        duration = self.parameter.vals[0] * self.parameter.timescale * self.parameter.scale_factor
        self._vals = np.empty((max(1, math.ceil(duration / dt)), tvec.size), order="F")  # Fortran/column-major order should be faster for summing over lags to get `vals`
        self._vals.fill(np.nan)

    def resolve_outflows(self, ti: int) -> None:
        """
        Resolve outgoing links

        At this point, all links going out of the compartment would have had their ``._cache`` value set to the
        fraction to transfer. This method converts them to numbers, taking into account the fact that only
        certain subcompartments are eligible for timed links within the same duration group

        :param ti: Time index at which to update link outflows

        """

        # First, work out the scale factors as usual
        self.flush_link._cache = 0.0  # At this stage, no outflow goes via the flush link

        total_outflow = np.zeros(self._vals.shape[0])
        for link in self.outlinks:
            if isinstance(link, TimedLink):
                total_outflow[1:] += link._cache  # Timed link outflows do not act on the final subcompartment
            else:
                total_outflow[:] += link._cache  # Normal link outflows do act on the final subcompartment

        # Rescaling factors for each subcompartment
        rescale = np.divide(1, total_outflow, out=np.ones_like(total_outflow), where=total_outflow > 1)
        n = rescale * self._vals[:, ti]  # Rescaled number of people - to multiply by the cache value on each link

        self._cached_outflow = np.zeros(self._vals.shape[0])  # Cache the outflow, because for Links, we accumulate the subcompartment outflow but we need to record the subcompartment outflow separately
        for link in self.outlinks:
            if isinstance(link, TimedLink):
                link._vals[:, ti] = n * link._cache
                link._vals[0, ti] = 0.0  # No flow out of final subcompartment
                self._cached_outflow += link._vals[:, ti]
            else:
                link.vals[ti] = sum(n * link._cache)
                self._cached_outflow += n * link._cache

        self.flush_link.vals[ti] = max(0, self._vals[0, ti] - self._cached_outflow[0])
        self._cached_outflow[0] += self.flush_link.vals[ti]

    def update(self, ti: int) -> None:
        """
        Update compartment value

        This compartment update goes from ``ti-1`` to ``ti``. As part of this, the counts for each
        duration are rolled over.

        :param ti: Time index to step to

        """

        tr = ti - 1

        # First, apply all of the outflows (computed by `resolve_outflows()` at the last timestep)
        self._vals[:, ti] = self._vals[:, tr] - self._cached_outflow

        # Then, add in TimedLink inputs (prior to advancing the keyring)
        for link in self.inlinks:
            if isinstance(link, TimedLink):
                if self._vals.shape[0] == link._vals.shape[0]:
                    # The sizes match exactly, no need to index rows at all
                    self._vals[:, ti] += link._vals[:, tr]
                elif self._vals.shape[0] > link._vals.shape[0]:
                    # This compartment has a longer duration, so only insert the rows we've got
                    self._vals[: link._vals.shape[0], ti] += link._vals[:, tr]
                else:
                    # This compartment has a shorter duration, so first insert the values we've got
                    # then sum up and add the extra values to the initial subcompartment
                    self._vals[:, ti] += link._vals[: self._vals.shape[0], tr]
                    self._vals[-1, ti] += sum(link._vals[self._vals.shape[0] :, tr].tolist())

        # Advance the keyring
        # If this TimedCompartment has only one row, then anyone coming in via TimedLinks will be placed directly
        # in the final subcompartment (which is also the initial subcompartment). We are assuming that the cached
        # outflow correctly emptied everyone in the flush compartment so don't check that the final subcompartment
        # is empty because people could have been added to it in this timestep
        if self._vals.shape[0] > 1:
            self._vals[0:-1, ti] = self._vals[1:, ti]
            self._vals[-1, ti] = 0.0  # Zero out the inflow (otherwise, it just replicates previous value)

        # Now, resolve other inputs for which durations are not preserved
        # Regardless of whether they are TimedLinks or not, they should go into the initial subcompartment
        for link in self.inlinks:
            if not isinstance(link, TimedLink):
                self._vals[-1, ti] += link[tr]

        self._vals[self._vals[:, ti] < 0, ti] = 0

    def connect(self, dest, par) -> None:
        """
        Construct link out of this compartment

        For TimedCompartments, outgoing links are TimedLinks if the downstream compartment belongs to the same
        duration group. For this purpose, a junction can be part of a duration group if all of the downstream
        junction outputs are in this compartment's duration group.

        :param dest: A ``Compartment`` instance
        :param par: The parameter that the Link will be associated with

        """

        if (isinstance(dest, TimedCompartment) and dest.parameter.name == self.parameter.name) or (isinstance(dest, JunctionCompartment) and dest.duration_group == self.parameter.name):
            # Note that comparing the name rather than the instance ID will allow duration-preserving transfers where a difference instance of the same parameter is present in the dest population
            new_link = TimedLink.create(pop=self.pop, parameter=par, source=self, dest=dest)
        else:
            # Note that if the duration group doesn't match, then a Link rather than a TimedLink will be instantiated
            new_link = Link.create(pop=self.pop, parameter=par, source=self, dest=dest)

        if par is self.parameter:
            # If we are connecting up the timed parameter, also assign it to the flush link
            # We also need to break the connection between the parameter and the link
            # so that the parameter doesn't try to update the link during `update_pars()`
            assert not isinstance(new_link, TimedLink), "Cannot flush into the same duration group"
            self.flush_link = new_link
            new_link.parameter = None
            par.links = []


class Characteristic(Variable):
    """A characteristic represents a grouping of compartments."""

    def __init__(self, pop, name):
        # includes is a list of Compartments, whose values are summed
        # the denominator is another Characteristic that normalizes this one
        # All passed by reference so minimal performance impact
        Variable.__init__(self, pop=pop, id=(pop.name, name))
        self.units = "Number of people"
        self.includes = []
        self.denominator = None
        # The following flag indicates if another variable depends on this one.
        # This indicates a value needs computation during integration.
        self._is_dynamic = False
        self._vals = None

    def preallocate(self, tvec: np.array, dt: float) -> None:
        """
        Preallocate data storage

        :param tvec: An array of time values
        :param dt: Time step size

        """

        self.t = tvec
        self.dt = dt
        if self._is_dynamic:
            self._vals = np.empty(tvec.shape)
            self._vals.fill(np.nan)

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
                vals_zero = vals < model_settings["tolerance"]
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
        self.units = ""

    def update(self, ti):
        self._vals[ti] = 0
        for comp in self.includes:
            self._vals[ti] += comp[ti]
        if self.denominator is not None:
            denom = self.denominator[ti]
            if denom > 0:
                self._vals[ti] /= denom
            elif self._vals[ti] < model_settings["tolerance"]:
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
        self._source_popsize_cache_time = None  # : Internal cache for the time at which the source popsize was previously computed
        self._source_popsize_cache_val = None  # : Internal cache for the last previously computed source popsize
        self.fcn_str = None  #: String representation of parameter function
        self.deps = dict()  #: Dict of dependencies containing lists of integration objects
        self._fcn = None  #: Internal cache for parsed parameter function (this will be dropped when pickled)
        self._precompute = False  #: If True, the parameter function will be computed in a vector operation prior to integration
        self._is_dynamic = False  #: If True, this parameter has values that need to be updated or assigned during integration. Note that `precompute` and `dynamic` are mutually exclusive
        self.derivative = False  #: If True, the parameter function will be treated as a derivative and the value added on to the end
        self._dx = None  #: Internal cache for the value of the derivative at the current timestep
        self.skip_function = None  #: Can optionally be set to a (start,stop) tuple of times. Between these times, the parameter will not be updated so the parset value will be left unchanged

        #: For transition parameters, the ``vals`` stored by the parameter is effectively a rate. The ``timescale``
        #: attribute informs the time period corresponding to the units in which the rate has been provided.
        #: If the units are ``number`` or ``probability`` then the ``timescale`` corresponds to the denominator of the units
        #: e.g. probability/day (with ``timescale=1/365``).
        #: If the units are ``duration`` then the timescale stores the units in which the duration has been specified
        #: e.g. ``duration=1`` with ``timescale=1/52`` is the same as ``duration=7`` with ``timescale=1/365``
        #: The effective duration used in the simulation is ``duration*timescale`` with units of years (so it will behave correctly if
        #: one wanted to use 1/365.25 instead of 1/365)
        self.timescale = 1.0

    def set_fcn(self, fcn_str) -> None:
        """
        Add a function to this parameter

        This method adds a function to the parameter. The following steps are carried out

            - The function is parsed and stored in the ``._fcn`` attribute (until the Parameter is pickled)
            - The dependencies are extracted, and are stored as references to the actual integration objects
              to increase performance during integration
            - If this is a transition parameter, then dependencies will have their `dynamic` flag updated

        :param framework: A py:class:`ProjectFramework` instance, used to identify and retrieve interaction terms
        :param fcn_str: The string containing the function to add

        """

        assert sc.isstring(fcn_str), "Parameter function must be supplied as a string"
        self.fcn_str = fcn_str
        self._fcn, dep_list = parse_function(self.fcn_str)
        if fcn_str.startswith("SRC_POP_AVG") or fcn_str.startswith("TGT_POP_AVG") or fcn_str.startswith("SRC_POP_SUM") or fcn_str.startswith("TGT_POP_SUM"):
            # The function is like 'SRC_POP_AVG(par_name,interaction_name,charac_name)'
            # self.pop_aggregation will be ['SRC_POP_AVG',par_name,interaction_name,charac_object]
            special_function, temp_list = self.fcn_str.split("(")
            function_args = temp_list.rstrip(")").split(",")
            function_args = [x.strip() for x in function_args]
            self.pop_aggregation = [special_function] + function_args
            # Aggregation dependencies are set externally because they may cross populations - see `Model.build()`
            # Note that aggregations are computed externally rather than via `Parameter.update`
        else:
            for dep_name in dep_list:
                if not (dep_name in ["t", "dt"]):  # There are no integration variables associated with the interactions, as they are treated as a special matrix
                    self.deps[dep_name] = self.pop.get_variable(dep_name)  # nb. this lookup will fail if the user has a function that depends on a quantity outside this population

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

        if self.pop_aggregation or self.derivative:
            # Pop aggregations and derivatives are handled in `update_pars()` so we set the dynamic flag
            # because the values are modified during integration
            self._is_dynamic = True

        if self.deps:  # If there are no dependencies, then we know that this is precompute-only
            for deps in self.deps.values():  # deps is {'dep_name':[dep_objects]}
                for dep in deps:
                    if isinstance(dep, Link):
                        raise ModelError(f"Parameter '{self.name}' depends on transition flow '{dep.name}' thus it cannot be a dependency, it must be output only.")
                    elif isinstance(dep, Compartment) or isinstance(dep, Characteristic):
                        dep.set_dynamic()
                        self._is_dynamic = True
                    elif isinstance(dep, Parameter):
                        dep.set_dynamic()  # Run `set_dynamic()` on the parameter which will descend further to see if the Parameter depends on comps/characs or on overwritten parameters
                        if dep._is_dynamic or (progset and dep.name in progset.pars):
                            self._is_dynamic = True
                    else:
                        raise ModelError("Unexpected dependency type")

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
                self.vals = np.clip(self.vals, self.limits[0], self.limits[1])
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
                raise ModelError("Cannot perform a vector update of a derivative parameter (these parameters intrinsically require integration to be computed)")
            ti = np.arange(0, self.vals.size)  # This corresponds to every time point

        if self.skip_function:
            # If we don't want to overwrite the parameter in certain years, those years need to be excluded
            if hasattr(ti, "__len__"):
                # Filter out years outside the excluded range
                ti = ti[np.where((self.t[ti] < self.skip_function[0]) | (self.t[ti] > self.skip_function[1]))]
                if ti.size == 0:  # If all times were removed
                    return
            else:
                # Dealing with a scalar ti
                if (self.t[ti] >= self.skip_function[0]) and (self.t[ti] <= self.skip_function[1]):
                    return

        dep_vals = dict.fromkeys(self.deps, 0.0)
        for dep_name, deps in self.deps.items():
            for dep in deps:
                if isinstance(dep, Parameter) or isinstance(dep, Characteristic):
                    dep_vals[dep_name] += dep.vals[ti]
                elif isinstance(dep, Compartment):
                    dep_vals[dep_name] += dep[ti]
                elif isinstance(dep, Link):
                    dep_vals[dep_name] += dep[ti] / dep.dt
                else:
                    raise ModelError("Unhandled case")

        dep_vals["t"] = self.t[ti]
        dep_vals["dt"] = self.dt
        v = self.scale_factor * self._fcn(**dep_vals)

        if self.derivative:
            self._dx = v
        else:
            self[ti] = v

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
                    n += link.source[ti]  # Use the direct indexing because we don't know what type of compartment we are operating on
            else:
                raise ModelError("Cannot retrieve source popsize for a non-transition parameter")
            self._source_popsize_cache_time = ti
            self._source_popsize_cache_val = n
            return n


class Link(Variable):
    """
    A Link is a Variable that maps to a transition between compartments. As
    such, it contains an inflow and outflow compartment.  A Link's value is
    generally derived from a Parameter, and there may be multiple links that draw values
    from the same parameter. The value corresponds to the number transferred
    from the source compartment to the destination compartment in the subsequent timestep.

    Some links do not have an associated Parameter object because their values are calculated
    by means other than parameters. For example

    - Flush links have their values calculated from the source timed compartment
    - Junction residual links have their values calculated by junction balancing

    """

    @classmethod
    def create(cls, pop, parameter, source, dest):
        """
        Create and wire up a new link

        This method instantiates a Link (including of derived types) and also wires it up to
        the population, parameter, source, and destination compartments. This allows the ``Link``
        constructor to be used without needing the entire population infrastructure

        :param pop: A ``Population`` instance that will contain the new ``Link``
        :param parameter: A ``Parameter`` instance that will supply values for the new ``Link``
        :param source: A ``Compartment`` instance to transfer from
        :param dest: A ``Compartment`` instance to transfer to
        :return: The newly created ``Link`` instance

        """

        # Instantiate the link
        new_link = cls(pop, parameter, source, dest)

        # Wire it up
        if parameter is not None:
            new_link.parameter.links.append(new_link)
        new_link.source.outlinks.append(new_link)
        new_link.dest.inlinks.append(new_link)
        pop.links.append(new_link)

        # Add the link to the population's lookup
        if new_link.name in pop.link_lookup:
            pop.link_lookup[new_link.name].append(new_link)
        else:
            pop.link_lookup[new_link.name] = [new_link]

        return new_link

    def __init__(self, pop, parameter, source, dest):
        if parameter is None:
            # If the parameter is None then assign a random name
            link_name = sc.uuid(tostring=True, length=8)
        else:
            # Otherwise, name the link after the parameter governing it
            link_name = parameter.name + ":flow"

        Variable.__init__(self, pop=pop, id=(pop.name, source.name, dest.name, link_name))  # A Link is only uniquely identified by (Pop,Source,Dest,Par)
        self.units = "Number of people"

        # Source parameter where unscaled link value is drawn from (a single parameter may have multiple links).
        self.parameter = parameter
        self.source = source  # Compartment to remove people from
        self.dest = dest  # Compartment to add people to

        self._cache = None  #: Temporarily cache either the fraction converted (normal links) or number of people (source outflows)

    def __setitem__(self, key, value) -> None:
        """
        Shortcut to set .vals attribute

        This method assigns values to the `.vals` attribute e.g., ``sus[ti] = 0`` instead of
        ``sus.vals[ti] = 0``. Importantly, this allows the derived class to overload ``__getitem__``
        if ``vals`` is a property method instead of an actual array.

        :param key: Indexer passed directly to the numpy array ``self.vals[item]``
        :param value: Value to assign to the result of the indexing operation

        """

        self.vals[key] = value

    def unlink(self):
        Variable.unlink(self)
        if self.parameter is not None:
            # Flush links have their values computed from a compartment rather than a parameter
            # So it is possible to have a transition/Link without an associated parameter
            self.parameter = self.parameter.id
        self.source = self.source.id
        self.dest = self.dest.id

    def relink(self, objs):
        # Given a dictionary of objects, restore the internal references
        Variable.relink(self, objs)
        if self.parameter is not None:
            self.parameter = objs[self.parameter]
        self.source = objs[self.source]
        self.dest = objs[self.dest]

    def __repr__(self, *args, **kwargs):
        if self.parameter:
            return "%s %s (parameter %s) - %s to %s" % (type(self).__name__, self.name, self.parameter.name, self.source.name, self.dest.name)
        elif isinstance(self.source, TimedCompartment) and self.source.flush_link is self:
            return "%s %s - %s to %s (flush)" % (type(self).__name__, self.name, self.source.name, self.dest.name)
        else:
            return "%s %s - %s to %s" % (type(self).__name__, self.name, self.source.name, self.dest.name)

    def plot(self):
        Variable.plot(self)
        plt.title("Link %s to %s" % (self.source.name, self.dest.name))

    def update(self, ti: int, converted_frac: float) -> None:
        """
        Update the value of the link

        This method takes in the fraction of the source compartment to move, and
        updates the value of the link accordingly. In `update_links`, parameters are
        first all converted into timestep-based fractions. These fractions are then
        used to update the links. However, depending on whether the link stores
        compartment duration information, this update may or may not require the use
        of TimedCompartment properties. Therefore, updating the link is delegated
        to this Link method that can be overloaded in derived classes.

        :param ti: The time index to update
        :param converted_frac: The fraction of the source compartment to move (the parent parameter value, converted to timestep fraction)

        """

        self.vals[ti] = self.source.vals[ti] * converted_frac


class TimedLink(Link):
    """
    A TimedLink connects two TimedCompartments

    A TimedLink should be used between two TimedCompartments if it is important to preserve the 'time until forced removal'
    when making the transition. For example, a vaccinated individual with 3 years of protection remaining may need to move
    to a vaccinated+latent state, for instance. In that case, they would still have 3 years remaining in vaccinated+latent.

    The value for the TimedLink corresponds to the number of people in each time bin from the *source* compartment.
    If there is a mismatch in durations across the TimedLink endpoints, it is up to the destination compartment to
    resolve them.

    A TimedLink should _not_ be used for the timed outflow of a TimedCompartment as people flowing out of a timed outflow
    all originate at the same time.

    """

    def __init__(self, pop, parameter, source, dest):
        Link.__init__(self, pop, parameter, source, dest)
        self._vals = None  #: Primary storage, a matrix with size matching the source compartment

    @property
    def vals(self) -> np.array:
        """
        Link total flow

        This returns link outflow obtained by summing over the people in each time bin at each point in time

        :return: A numpy array with the link flow rate

        """

        return self._vals.sum(axis=0)

    def preallocate(self, tvec: np.array, dt: float) -> None:
        """
        Preallocate data storage

        Note that TimedLinks preallocate their internal storage based on the preallocated size
        of the source TimedCompartment. Therefore, it must be preallocated after the compartments
        have been preallocated.

        :param tvec: An array of time values
        :param dt: Time step size

        """

        # Preallocate to the same size as the source compartment
        self.t = tvec
        self.dt = dt
        if isinstance(self.source, TimedCompartment):
            # Preallocate based on the timed compartment size
            self._vals = np.empty(self.source._vals.shape, order="F")  # Fortran/column-major order should be faster for summing over lags to get `vals`
        else:
            # Preallocate based on the upstream junction's duration group
            # Note that the keyring size calculation is duplicated from TimedCompartment, this could be separated into a function if it is needed any more often than this
            parameter = self.pop.par_lookup[self.source.duration_group]
            assert np.all(parameter.vals == parameter.vals[0]), "Duration parameter value cannot vary over time"
            duration = parameter.vals[0] * parameter.timescale * parameter.scale_factor
            self._vals = np.empty((math.ceil(duration / dt), tvec.size), order="F")  # Fortran/column-major order should be faster for summing over lags to get `vals`
        self._vals.fill(np.nan)

    def update(self, ti: int, converted_frac: float) -> None:
        """
        Updated link flow rate

        For TimedLink instances, we update at all of the time indices

        :param ti: Time index to update
        :param converted_frac: The fraction of the source compartment to move (the parent parameter value, converted to timestep fraction)

        """

        self._vals[:, ti] = self.source._vals[:, ti] * converted_frac

    def __getitem__(self, ti):
        """
        Retrieve total flow at given time index

        By only adding the requested timesteps, this approach is faster than accessing ``vals`` first i.e.

        >>> self.vals[ti]
        >>> self[ti] # <-- Faster

        :param ti: Time index/indices
        :return: Total compartment size at given time index/indices

        """

        return self._vals[:, ti].sum(axis=0)


class Population:
    """
    A class to wrap up data for one population within model.
    Each model population must contain a set of compartments with equivalent names.
    """

    def __init__(self, framework, name: str, label: str, progset: ProgramSet, pop_type: str):
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
        self.type = pop_type  #: The population's type

        self.comps = list()  #: List of Compartment objects
        self.characs = list()  #: List of Characteristic objects
        self.links = list()  #: List of Link objects
        self.pars = list()  #: List of Parameter objects

        self.comp_lookup = dict()  #: Maps name of a compartment to a Compartment
        self.charac_lookup = dict()  #: Maps name of a compartment to a Characteristic
        self.par_lookup = dict()  #: Maps name of a parameter to a Parameter
        self.link_lookup = dict()  #: Maps name of link to a list of Links with that name

        self.build(framework=framework, progset=progset)  # Convert compartmental cascade into lists of compartment and link objects.

        self.popsize_cache_time = None
        self.popsize_cache_val = None

        self.is_linked = True  # Flag to manage double unlinking/relinking

    def __repr__(self):
        return '%s "%s"' % (self.__class__.__name__, self.name)

    def __contains__(self, item: str) -> bool:
        """
        Check whether variables can be resolved

        This function returns True if ``Population.get_variable(item)`` would result
        in some variables being returned. This facilitates checking whether a population
        contains particular variables - for example, transfer links may only exist in
        a subset of the model populations, or if population types are being used, not all
        variables will be defined in any one population.

        :param item: The name of a parameter or a link specification (supported by ``get_variable``)
        :return: True if ``Population.get_variable`` would return at least one variable, otherwise False
        """
        try:
            self.get_variable(item)
            return True
        except NotFoundError:
            return False

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

    def popsize(self, ti: int = None):
        """
        Return population size

        A population's size is the sum of all of the people in its compartments, excluding
        birth and death compartments

        :param ti: Optionally specify a scalar time index to retrieve popsize for. ```None`` corresponds to all times
        :return: If ``ti`` is specified, returns a scalar population size. If ``ti`` is ``None``, return a numpy array the same size as the simulation time vector

        """

        if ti is None:
            return np.sum([comp.vals for comp in self.comps if (not isinstance(comp, SourceCompartment) and not isinstance(comp, SinkCompartment))], axis=0)

        if ti == self.popsize_cache_time:
            return self.popsize_cache_val
        else:
            n = 0
            for comp in self.comps:
                if not isinstance(comp, SourceCompartment) and not isinstance(comp, SinkCompartment):
                    n += comp[ti]
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

        name = name.replace("___", ":")  # Parameter functions will convert ':' to '___' for use in variable names

        if name in self.comp_lookup:
            return [self.comp_lookup[name]]
        elif name in self.charac_lookup:
            return [self.charac_lookup[name]]
        elif name in self.par_lookup:
            return [self.par_lookup[name]]
        elif name in self.link_lookup:
            return self.link_lookup[name]
        elif ":" in name and not name.endswith(":flow"):
            name_tokens = name.split(":")
            if len(name_tokens) == 2:
                name_tokens.append("")
            src, dest, par = name_tokens

            if src and dest:
                links = [link for link in self.get_comp(src).outlinks if link.dest.name == dest]
            elif src:
                links = self.get_comp(src).outlinks
            elif dest:
                links = self.get_comp(dest).inlinks
            else:
                links = self.links

            if par:
                links = [link for link in links if (link.parameter and link.parameter.name == par)]

            return links
        else:
            raise NotFoundError(f"Object '{name}' not found in population '{self.name}'")

    def get_comp(self, comp_name):
        """Allow compartments to be retrieved by name rather than index. Returns a Compartment."""
        try:
            return self.comp_lookup[comp_name]
        except KeyError:
            raise NotFoundError(f"Compartment {comp_name} not found")

    def get_links(self, name) -> list:
        """Retrieve Links."""
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
        """Allow dependencies to be retrieved by name rather than index. Returns a Variable."""
        try:
            return self.charac_lookup[charac_name]
        except KeyError:
            raise NotFoundError(f"Characteristic {charac_name} not found")

    def get_par(self, par_name):
        """Allow dependencies to be retrieved by name rather than index. Returns a Variable."""
        try:
            return self.par_lookup[par_name]
        except KeyError:
            raise NotFoundError(f"Parameter {par_name} not found")

    def build(self, framework, progset):
        """
        Generate a compartmental cascade as defined in a settings object.
        Fill out the compartment, transition and dependency lists within the model population object.
        Maintaining order as defined in a cascade workbook is crucial due to cross-referencing.

        The progset is required so that Parameter instances with functions can correctly identify dynamic quantities
        if they are only dynamic due to program overwrites.
        """

        comps = framework.comps
        characs = framework.characs
        pars = framework.pars

        # Parameters first pass
        # Instantiate all parameters first. That way, we know which compartments need to be TimedCompartments
        # We make a `timed_compartments` dict mapping {timed_compartment_name:parameter} so that we can identify
        # the timed compartments and quickly retrieve their parameters. This is done here partly because we need
        # to instantiate the parameters first, and also because `framework.transitions` is keyed by parameter
        # rather than compartment so it's straightforward to include here
        for par_name in list(pars.index):
            if pars.at[par_name, "population type"] == self.type:
                par = Parameter(pop=self, name=par_name)
                par.units = pars.at[par_name, "format"]
                par.timescale = pars.at[par_name, "timescale"]
                par.derivative = pars.at[par_name, "is derivative"] == "y"
                self.pars.append(par)
        self.par_lookup = {par.name: par for par in self.pars}

        # Instantiate compartments
        residual_junctions = {x[0] for x in framework.transitions.get(">", [])}
        for comp_name in list(comps.index):
            if comps.at[comp_name, "population type"] == self.type:
                if comp_name in residual_junctions:
                    self.comps.append(ResidualJunctionCompartment(pop=self, name=comp_name, duration_group=comps.at[comp_name, "duration group"]))
                elif comps.at[comp_name, "is junction"] == "y":
                    self.comps.append(JunctionCompartment(pop=self, name=comp_name, duration_group=comps.at[comp_name, "duration group"]))
                elif comps.at[comp_name, "duration group"]:
                    self.comps.append(TimedCompartment(pop=self, name=comp_name, parameter=self.par_lookup[comps.at[comp_name, "duration group"]]))
                elif comps.at[comp_name, "is source"] == "y":
                    self.comps.append(SourceCompartment(pop=self, name=comp_name))
                elif comps.at[comp_name, "is sink"] == "y":
                    self.comps.append(SinkCompartment(pop=self, name=comp_name))
                else:
                    self.comps.append(Compartment(pop=self, name=comp_name))

        self.comp_lookup = {comp.name: comp for comp in self.comps}

        # Characteristics first pass, instantiate objects
        for charac_name in list(characs.index):
            if characs.at[charac_name, "population type"] == self.type:
                self.characs.append(Characteristic(pop=self, name=charac_name))
        self.charac_lookup = {charac.name: charac for charac in self.characs}

        # Characteristics second pass, add includes and denominator
        # This is a separate pass because characteristics can depend on each other
        for charac in self.characs:
            includes = [x.strip() for x in characs.at[charac.name, "components"].split(",")]
            for inc_name in includes:
                charac.add_include(self.get_variable(inc_name)[0])  # nb. We expect to only get one match for the name, so use index 0
            denominator = characs.at[charac.name, "denominator"]
            if denominator is not None:
                charac.add_denom(self.get_variable(denominator)[0])  # nb. framework import strips whitespace from the overall field

        # Parameters second pass, create parameter objects and links
        # This is a separate pass because we can't create the links before the compartments are instantiated
        for par in self.pars:
            if framework.transitions[par.name]:
                for pair in framework.transitions[par.name]:
                    src = self.get_comp(pair[0])
                    dst = self.get_comp(pair[1])
                    src.connect(dst, par)  # If the parameter is a timed parameter, the TimedCompartment will also assign the FlushLink in this step

        if ">" in framework.transitions:
            for pair in framework.transitions[">"]:
                try:
                    src = self.get_comp(pair[0])
                    dst = self.get_comp(pair[1])
                    src.connect(dst, None)
                except NotFoundError:
                    continue

        # Parameters third pass, process f_stacks, deps, and limits
        # This is a separate pass because output parameters can depend on Links
        for par in self.pars:
            min_value = pars.at[par.name, "minimum value"]
            max_value = pars.at[par.name, "maximum value"]

            if np.isfinite(min_value) or np.isfinite(max_value):
                par.limits = [max(-np.inf, min_value), min(np.inf, max_value)]

            fcn_str = pars.at[par.name, "function"]
            if fcn_str is not None:
                par.set_fcn(fcn_str)

        # If this Parameter has links and a function, it must be updated before it is needed during integration.
        # If the function depends on any compartment sizes, it must be updated element-wise during integration.
        # Similarly, if it is a derivative parameter, it needs to be updated element-wise.
        # Otherwise, it can be pre-computed in a fast vector operation
        # A timed parameter doesn't _directly_ have links associated with it (because it does not supply values
        # for the links) but it does need to be precomputed
        for par in self.pars:
            if par.fcn_str and (par.links or par.derivative or framework.pars.at[par.name, "timed"] == "y" or (progset is not None and (par.name, self.name) in progset.covouts)):
                par.set_dynamic(progset)

    def initialize_compartments(self, parset: ParameterSet, framework, t_init: float) -> None:
        """
        Set compartment sizes

        This method takes the databook values for compartments and characteristics, and uses them to
        compute the initial compartment sizes at ``ti=0``. The computation is carried out by solving
        the linear matrix equation mapping characteristics to compartments. For this purpose,
        both compartments and characteristics in the databook are treated in the same way i.e. a databook
        compartment is treated like a characteristic containing only that compartment.

        :param parset: A py:class:`ParameterSet` instance with initial values for compartments/characteristics
        :param framework: A py:class:`ProjectFramework` instance, used to identify and retrieve interaction terms
        :param t_init: The year to use for initialization. This should generally be set to the sim start year

        """

        # Given a set of characteristics and their initial values, compute the initial
        # values for the compartments by solving the set of characteristics simultaneously

        # Build up the comps and characs containing the setup values in the databook - the `b` in `x=A*b`
        characs_to_use = framework.characs.index[(~framework.characs["databook page"].isnull() & framework.characs["setup weight"] & (framework.characs["population type"] == self.type))]
        comps_to_use = framework.comps.index[(~framework.comps["databook page"].isnull() & framework.comps["setup weight"] & (framework.comps["population type"] == self.type))]
        b_objs = [self.charac_lookup[x] for x in characs_to_use] + [self.comp_lookup[x] for x in comps_to_use]

        # Build up the comps corresponding to the `x` values in `x=A*b` i.e. the compartments being solved for
        comps = [c for c in self.comps if not (isinstance(c, SourceCompartment) or isinstance(c, SinkCompartment))]
        charac_indices = {c.name: i for i, c in enumerate(b_objs)}  # Make lookup dict for characteristic indices
        comp_indices = {c.name: i for i, c in enumerate(comps)}  # Make lookup dict for compartment indices

        b = np.zeros((len(b_objs), 1))
        A = np.zeros((len(b_objs), len(comps)))

        # Construct the characteristic value vector (b) and the includes matrix (A)
        for i, obj in enumerate(b_objs):
            # Look up the characteristic value
            par = parset.pars[obj.name]
            b[i] = par.interpolate(t_init, pop_name=self.name)[0] * par.y_factor[self.name] * par.meta_y_factor
            if isinstance(obj, Characteristic):
                if obj.denominator is not None:
                    denom_par = parset.pars[obj.denominator.name]
                    b[i] *= denom_par.interpolate(t_init, pop_name=self.name)[0] * denom_par.y_factor[self.name] * denom_par.meta_y_factor
                for inc in obj.get_included_comps():
                    A[i, comp_indices[inc.name]] = 1.0
            else:
                A[i, comp_indices[obj.name]] = 1.0

        # Solve the linear system (nb. lstsq returns the minimum norm solution
        x = np.linalg.lstsq(A, b.ravel(), rcond=None)[0].reshape(-1, 1)
        proposed = np.matmul(A, x)
        residual = np.sum((proposed.ravel() - b.ravel()) ** 2)

        # Accumulate any errors here. The errors could occur either at the system level or at the level
        # of individual comps/characs. To avoid
        error_msg = ""
        characteristic_tolerence_failed = False

        # Print warning for characteristics that are not well matched by the compartment size solution
        for i in range(0, len(b_objs)):
            if abs(proposed[i] - b[i]) > model_settings["tolerance"]:
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

            msg = ""
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
                        msg += n_indent * "\t" + "Compartment %s: Computed value = %f\n" % (inc.name, x[comp_indices[inc.name]])
            return msg

        for i in range(0, len(comps)):
            if x[i] < -model_settings["tolerance"]:
                error_msg += "Compartment %s %s - Calculated %f\n" % (self.name, comps[i].name, x[i])
                for charac in b_objs:
                    try:
                        if comps[i] in charac.get_included_comps():
                            error_msg += report_characteristic(charac)
                    except Exception:
                        if comps[i] == charac:
                            error_msg += report_characteristic(charac)

        if residual > model_settings["tolerance"]:
            # Halt for an unsatisfactory overall solution
            raise BadInitialization("Global residual was %g which is unacceptably large (should be < %g)\n%s" % (residual, model_settings["tolerance"], error_msg))
        elif np.any(np.less(x, -model_settings["tolerance"])):
            # Halt for any negative popsizes
            raise BadInitialization(f"Negative initial popsizes:\n{error_msg}")
        elif characteristic_tolerence_failed:
            raise BadInitialization(f"Characteristics failed to meet tolerances\n{error_msg}")
        elif error_msg:
            # Generic error message if any of the warning messages were encountered - not entirely sure when
            # this would happen so if this *does* occur, it should be written as an explicit branch above
            # (but it exists as a fallback to ensure that any inconsistencies result in the error being raised)
            raise BadInitialization(f"Initialization error\n{error_msg}")

        # Otherwise, insert the values
        for i, c in enumerate(comps):
            c[0] = max(0.0, x[i])


class Model:
    """A class to wrap up multiple populations within model and handle cross-population transitions."""

    def __init__(self, settings, framework, parset, progset=None, program_instructions=None):

        # Note that if a progset is provided and program instructions are not, then programs will not be
        # turned on. However, the progset is still available so that the coverage can still be probed
        # (in particular, the coverage denominator from Result.get_coverage('denominator') is used
        # for reconciliation

        # Record version info for the model run. These are generally NOT updated in migration. Thus, they serve
        # as a record of which specific version of the code was used to generate the results
        self.version = version
        self.gitinfo = sc.dcp(gitinfo)
        self.created = sc.now(utc=True)

        self.pops = list()  # List of population groups that this model subdivides into.
        self.interactions = sc.odict()
        self.programs_active = None  # True or False depending on whether Programs will be used or not
        self.progset = sc.dcp(progset)
        self.program_instructions = sc.dcp(program_instructions)  # program instructions
        self.t = settings.tvec  #: Simulation time vector (this is a brand new instance from the `settings.tvec` property method)
        self.dt = settings.sim_dt  #: Simulation time step

        self._t_index = 0  # Keeps track of array index for current timepoint data within all compartments.
        self._vars_by_pop = None  # Cache to look up lists of variables by name across populations
        self._pop_ids = sc.odict()  # Maps name of a population to its position index within populations list.
        self._program_cache = None  #: Cache program capacities and coverage for coverage scenarios
        self._exec_order = None  #: Cache the dependency order of various quantities

        self.framework = sc.dcp(framework)  # Store a copy of the Framework used to generate this model
        self.framework.spreadsheet = None  # No need to keep the spreadsheet

        self.build(parset)

    def unlink(self) -> None:
        """
        Replace references with IDs

        This method replaces all references with IDs so that there are no circular references
        that prevent pickling. This operation is reversed using ``Model.relink()``. These get
        called automatically when pickling and unpickling.

        Note that primary storage of the variables is in the population objects, so that is the
        one place where the variables remain in-scope.

        """

        # If we are already unlinked, do nothing
        if self._vars_by_pop is None:
            return

        for pop in self.pops:
            pop.unlink()

        # Drop this, it gets set by self._set_vars_by_pop()
        self._vars_by_pop = None

        # Drop caches - these get set again inside `model.process()`
        self._program_cache = None
        self._exec_order = None

    def relink(self) -> None:
        """
        Replace IDs with references

        This is the reverse operation of ``Model.unlink()`` where IDs are replaced with
        object references.

        """

        # If we are already linked, do nothing
        if self._vars_by_pop is not None:
            return

        # Need to enumerate objects at Model level because transitions link across pops
        objs = {}
        for pop in self.pops:
            objs[pop.name] = pop
            for obj in pop.comps + pop.characs + pop.pars + pop.links:
                objs[obj.id] = obj

        # Relink populations
        for pop in self.pops:
            pop.relink(objs)

        # Set vars by pop
        self._set_vars_by_pop()

    def _update_program_cache(self):

        # Finally, prepare programs
        if self.progset and self.program_instructions:
            self.programs_active = True
            self._program_cache = dict()

            self._program_cache["comps"] = dict()
            for prog in self.progset.programs.values():
                self._program_cache["comps"][prog.name] = []
                for pop_name in prog.target_pops:
                    for comp_name in prog.target_comps:
                        self._program_cache["comps"][prog.name].append(self.get_pop(pop_name).get_comp(comp_name))

            self._program_cache["capacities"] = self.progset.get_capacities(tvec=self.t, dt=self.dt, instructions=self.program_instructions)

            # Cache the proportion coverage for coverage scenarios so that we don't call interpolate() every timestep
            coverage = self.progset.get_prop_coverage(tvec=self.t, dt=self.dt, capacities=self._program_cache["capacities"], num_eligible={k: np.nan for k in self.progset.programs}, instructions=self.program_instructions)
            self._program_cache["prop_coverage"] = {k: coverage[k] for k in self.program_instructions.coverage}

            # Check that any programs with no coverage denominator have been given coverage overwrites
            # Otherwise, the coverage denominator will be treated as 0 and will result in 100% coverage
            # but that would just be a side effect of not targeting anyone (division by 0 is treated as 100%)
            for prog in self.progset.programs.values():
                if not self._program_cache["comps"][prog.name] and prog.name not in self._program_cache["prop_coverage"]:
                    raise ModelError(f'Program "{prog.name}" does not target any compartments, but the program instructions did not specify coverage for this program. Programs without target compartments require their coverage to be explicitly specified in the instructions')

        else:
            self.programs_active = False

    def _set_vars_by_pop(self) -> None:
        """
        Update cache dicts and lists

        During integration, the model needs to iterate over parameters with the same name across populations.
        Therefore, we build a cache dict where we map code names to a list of references to the required
        Parameter objects. We also construct a cache list of the parameter names from the framework so we
        can quickly iterate over it.

        """

        self._vars_by_pop = defaultdict(list)
        for pop in self.pops:
            for var in pop.comps + pop.characs + pop.pars + pop.links:
                self._vars_by_pop[var.name].append(var)
        self._vars_by_pop = dict(self._vars_by_pop)  # Stop new entries from appearing in here by accident

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
        """Allow model populations to be retrieved by name rather than index."""
        pop_index = self._pop_ids[pop_name]
        return self.pops[pop_index]

    def build(self, parset):
        """Build the full model."""

        # First construct populations
        for k, (pop_name, pop_label, pop_type) in enumerate(zip(parset.pop_names, parset.pop_labels, parset.pop_types)):
            self.pops.append(Population(framework=self.framework, name=pop_name, label=pop_label, progset=self.progset, pop_type=pop_type))
            self._pop_ids[pop_name] = k

        # Expand interactions into matrix form
        self.interactions = dict()
        for name, weights in parset.interactions.items():
            from_pops = [x.name for x in self.pops if x.type == self.framework.interactions.at[name, "from population type"]]
            to_pops = [x.name for x in self.pops if x.type == self.framework.interactions.at[name, "to population type"]]
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
                        par_name = "%s_%s_to_%s" % (transfer_name, pop_source, pop_target)  # e.g. 'aging_0-4_to_15-64'
                        par = Parameter(pop=pop, name=par_name)
                        par.preallocate(self.t, self.dt)  # Preallocate now, because these parameters are not present in the framework so they won't get preallocated later
                        par.scale_factor = transfer_parameter.y_factor[pop_target] * transfer_parameter.meta_y_factor
                        par.vals = transfer_parameter.interpolate(tvec=self.t, pop_name=pop_target) * par.scale_factor
                        par.units = transfer_parameter.ts[pop_target].units.strip().split()[0].strip().lower()

                        # Sampling might result in the parameter value going out of bounds, so make sure the transfer parameter values are constrained
                        if par.units == FS.QUANTITY_TYPE_RATE or par.units == FS.QUANTITY_TYPE_PROBABILITY:
                            par.limits = [0, 1]
                        elif par.units == FS.QUANTITY_TYPE_NUMBER:
                            par.limits = [0, np.inf]
                        else:
                            raise Exception("Unknown transfer parameter units")
                        par.constrain()

                        pop.pars.append(par)
                        pop.par_lookup[par_name] = par

                        target_pop_obj = self.get_pop(pop_target)

                        for src in pop.comps:
                            if not (isinstance(src, SourceCompartment) or isinstance(src, SinkCompartment) or isinstance(src, JunctionCompartment)):
                                # Instantiate a link between corresponding compartments
                                dest = target_pop_obj.get_comp(src.name)  # Get the corresponding compartment
                                src.connect(dest, par)

        # Now that all object have been created, update _vars_by_pop() accordingly
        self._set_vars_by_pop()

        # Flag dependencies for aggregated parameters prior to precomputing
        # Note that all parameters have been instantiated and we can set_dynamic
        # in any order, as long as we examine all parameters
        for par_name in self.framework.pars.index:

            if par_name not in self._vars_by_pop:
                continue

            pars = self._vars_by_pop[par_name]

            if pars[0].pop_aggregation:
                # Make the parameter dynamic, because it needs to be computed during integration
                for par in pars:
                    par.set_dynamic()

                # Also make the variable being aggregated dynamic
                for var in self._vars_by_pop[pars[0].pop_aggregation[1]]:
                    var.set_dynamic(progset=self.progset)

                # If there is a weighting variable,
                if len(pars[0].pop_aggregation) > 3:
                    for var in self._vars_by_pop[pars[0].pop_aggregation[3]]:
                        var.set_dynamic(progset=self.progset)

        # Set execution order - needs to be done _after_ pop aggregations have been flagged as dynamic
        self._set_exec_order()

        # Insert parameter initial values and do any required precomputation
        for par_name in self._exec_order["all_pars"]:
            if par_name not in parset.pars:
                # This happens for transfer parameters that don't appear in parset.pars, but they have been updated already above
                continue

            cascade_par = parset.pars[par_name]
            pars = self._vars_by_pop[cascade_par.name]
            for par in pars:

                par.preallocate(self.t, self.dt)
                par.scale_factor = cascade_par.meta_y_factor  # Set meta scale factor regardless of whether a population-specific y-factor is also provided

                if par.pop.name in cascade_par.y_factor:
                    par.scale_factor *= cascade_par.y_factor[par.pop.name]  # Add in population-specific scale factor

                if par.pop.name in cascade_par.skip_function:
                    par.skip_function = cascade_par.skip_function[par.pop.name]  # Copy in any skipped evaluations
                    if par.skip_function:
                        assert cascade_par.has_values(par.pop.name), "Parameter function was marked as being skipped for some of the simulation, but the ParameterSet has no values to use instead. If skipping, the ParameterSet must contain some values"

                if par.fcn_str and par._precompute:
                    # If the parameter is marked for precomputation, then insert it now
                    par.update()
                elif cascade_par.has_values(par.pop.name):
                    # If the databook contains values, then insert them now
                    par.vals = cascade_par.interpolate(tvec=self.t, pop_name=par.pop.name) * par.scale_factor

                par.constrain()  # Sampling might result in the parameter value going out of bounds (or user might have entered bad values in the databook) so ensure they are clipped here

        # Finally, preallocate remaining quantities and initialize the compartments
        # Note that TimedLink preallocation depends on TimedCompartment preallocation
        # which is setting the duration based on the evaluated parameters above.
        # Therefore, in the loop below, compartments must be preallocated before links
        for pop in self.pops:
            for obj in pop.comps + pop.characs + pop.links:
                obj.preallocate(self.t, self.dt)
            pop.initialize_compartments(parset, self.framework, self.t[0])

    def _set_exec_order(self) -> None:
        """
        Get the execution order

        Some quantities, like parameters, characteristics, and junctions, have dependencies that
        require them to be updated in a specific order. This method constructs directed
        graphs of the dependencies and returns the topological ordering, which specifies the order
        in which to update each quantity.

        For parameters, we need to update them in dependency order in three places - when precomputing or
        postcomputing, in which case we need all parameters, and during integration, in which case we only
        work with the dynamic parameters.
        which case we need to work with all parameters, and during integration, in which case we need to
        work.

        We also need to iterate over transition parameters when updating links, but actually this can be
        done in any order. However, we cache the transition parameters into a flat list here so that
        they can be efficiently iterated over.

        Note that the parameter update order is calculated from the framework, which may be relevant if
        the model structure is changed after building the model but before processing.

        :return: Dict containing execution orders for ``'all_pars'``,``dynamic_pars``,``characs``,``junctions``

        """

        import networkx as nx

        exec_order = dict()

        # Set the parameter update order - this is a list of parameters names, in dependency order
        # The parameters may or may not exist in each population, but they are updated across populations
        # Since parameters are implemented one name at a time, here we set the parameter order by
        # making a graph using the names rather than actual parameter objects. Note that par_update_order
        # contains all parameters, which are used during initialization as well as in update_pars. However, we
        # could have update_pars only operate on the subset of the graph contributing to transitions, or to
        # dynamic programs or to program overwrites.
        par_derivative = self.framework.pars["is derivative"].to_dict()  # Store all parameter names in framework, as well as whether they are a derivative or not
        G = nx.DiGraph()
        G.add_nodes_from(par_derivative, keep=False)
        for pop in self.pops:
            for par in pop.pars:
                for dep, dep_var in par.deps.items():
                    if dep in par_derivative and par_derivative[dep] != "y":
                        # Derivative parameters are allowed to refer to themselves directly,
                        # and derivative parameters are not considered dependencies - so we do
                        # not need to add a dependency edge to the graph
                        G.add_edge(dep, par.name)
                if par.pop_aggregation and par.pop_aggregation[1] in par_derivative and par_derivative[par.pop_aggregation[1]] != "y":
                    G.add_edge(par.pop_aggregation[1], par.name)

                if par._is_dynamic or (self.progset and par.name in self.progset.pars):
                    # If the parameter is dynamic or appears in the progset, then we need to
                    # include it in the list of parameters to iterate over in `update_pars`
                    G.nodes[par.name]["keep"] = True

        if not nx.dag.is_directed_acyclic_graph(G):
            message = "Circular dependencies in parameters:"
            for cycle in nx.simple_cycles(G):
                message += "\n - " + " -> ".join(cycle)
            raise Exception(message)

        exec_order["all_pars"] = [x for x in nx.dag.topological_sort(G) if x in self._vars_by_pop]  # Not all parameters may exist depending on populations, so filter out only the ones that are actually instantiated in this Model
        exec_order["dynamic_pars"] = [x for x in exec_order["all_pars"] if G.nodes[x]["keep"]]

        # Set the parameter execution order - this is a list of only transition parameters, used when updating links
        # This is a flat list of parameters, but the order actually should not matter since all parameters should be
        # resolved at this point
        exec_order["transition_pars"] = []
        for pop in self.pops:
            for par in pop.pars:
                if par.links and par.units != FS.QUANTITY_TYPE_PROPORTION:
                    exec_order["transition_pars"].append(par)

        # Set characteristic execution order - in cases where characteristics depend on each other
        G = nx.DiGraph()
        for pop in self.pops:
            for charac in pop.characs:
                G.add_node(charac)
                for include in charac.includes:
                    if isinstance(include, Characteristic):
                        G.add_edge(include, charac)  # Note directionality - the included characteristic needs to be added first
                if isinstance(charac.denominator, Characteristic):
                    G.add_edge(charac.denominator, charac)  # Note directionality - the included characteristic needs to be added first
        assert nx.dag.is_directed_acyclic_graph(G), "There is a circular dependency in characteristics, which is not permitted"
        exec_order["characs"] = [c for c in nx.dag.topological_sort(G) if c._is_dynamic]  # Topological sorting of the junction graph, which is a valid execution order

        # TODO - Move normal compartments into here as well
        # Set the junction execution order
        G = nx.DiGraph()
        for pop in self.pops:
            for comp in pop.comps:
                if isinstance(comp, JunctionCompartment):
                    G.add_node(comp)
                    for link in comp.outlinks:
                        if isinstance(link.dest, JunctionCompartment):
                            G.add_edge(link.source, link.dest)

        assert nx.dag.is_directed_acyclic_graph(G), "There is a cycle present where one junction has flows into another, which results in an infinite loop and is not permitted"
        exec_order["junctions"] = list(nx.dag.topological_sort(G))  # Topological sorting of the junction graph, which is a valid execution order

        self._exec_order = exec_order

    def process(self) -> None:
        """Run the full model."""

        assert self._t_index == 0  # Only makes sense to process a simulation once, starting at ti=0 - this might be relaxed later on
        self._set_exec_order()  # Set the execution order again in case the user has updated the parameters etc. It is critically important that this is correct during integration
        self._update_program_cache()

        # Initial flush of people in junctions
        if self._t_index == 0:
            self.update_pars()  # Update transition parameters in case junction outflows are function parameters
            self.flush_junctions()  # Flush the current contents of the junction without including any inflows
            self.update_pars()  # Update the transition parameters in case junction outflows are functions _and_ they depend on compartment sizes that just changed in the line above
            self.update_links()  # Update all of the links

        # Main integration loop
        while self._t_index < (self.t.size - 1):
            self._t_index += 1  # Step the simulation forward
            self.update_comps()
            self.update_pars()
            self.update_links()

        # Update postcompute parameters - note that it needs to be done in execution order
        for par_name in self._exec_order["all_pars"]:
            for par in self._vars_by_pop[par_name]:
                if par.fcn_str and not (par._is_dynamic or par._precompute):
                    par.update()
                    par.constrain()

        # Clear characteristic internal storage and switch to dynamic computation to save space
        for pop in self.pops:
            for charac in pop.characs:
                charac._vals = None

        self._program_cache = None  # Drop the program cache afterwards to save space

    def update_links(self) -> None:
        """
        Update link values

        This method takes the current parameter values in the model, and uses them to populate
        associated links. This requires conversion between parameter units and actual flow rates.

        Methods that populate links by means other than parameter e.g. `Compartment.resolve_outflows`
        or `Junction.balance` also get called here.
        """

        ti = self._t_index

        # First, populate all of the link values without any outflow constraints
        for par in self._exec_order["transition_pars"]:

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
                logger.warning("Negative transition occurred")
                transition = 0

            if not transition:
                for link in par.links:
                    link._cache = 0.0
                continue

            # Convert probability by Poisson distribution formula to a value appropriate for timestep.
            if par.units == FS.QUANTITY_TYPE_RATE or par.units == FS.QUANTITY_TYPE_PROBABILITY:
                # Note that we convert the transition to the timestep before checking whether it is greater than 1 or not. That way,
                # durations get preserved until we limit them based on the timestep size. The rationale is that the annual probability
                # will come out at 1.0 if the *mean* duration is the same as the step size, but that doesn't mean that if the step size
                # was smaller the timestep probability is also 1.0 - it's a consequence of the discretization. Essentially, a value
                # greater than 1 simply implies that the mean duration is less than the timescale in question, and we need to retain that value
                # to be able to correctly convert between timescales. The subsequent call to min() then ensures that the fraction moved never
                # exceeds 1.0 once operating on the timestep level
                converted_frac = transition * (self.dt / par.timescale)
                for link in par.links:
                    link._cache = converted_frac

            # Linearly convert number down to that appropriate for one timestep.
            elif par.units == FS.QUANTITY_TYPE_NUMBER:
                # Disaggregate proportionally across all source compartment sizes related to all links.
                converted_amt = transition * (self.dt / par.timescale)  # Number flow in this timestep, so it includes a timescale factor

                if isinstance(par.links[0].source, SourceCompartment):
                    # For a source compartment, the link value should be explicitly set directly
                    # Also, there is guaranteed to only be one link per parameter for outflows from source compartments
                    par.links[0]._cache = converted_amt
                    continue

                source_popsize = par.source_popsize(ti)
                if source_popsize:
                    converted_frac = converted_amt / source_popsize
                else:
                    converted_frac = 0.0

                for link in par.links:
                    link._cache = converted_frac

            # Convert from duration to equivalent probability
            elif par.units == FS.QUANTITY_TYPE_DURATION:
                converted_frac = self.dt / (transition * par.timescale)
                for link in par.links:
                    link._cache = converted_frac

            # NOTE - proportion format parameters should not be present in the exec list, so any other units are an error
            else:
                try:
                    par_label = self.framework.get_label(par.name)
                except NotFoundError:  # Name lookup will fail for transfer parameters
                    par_label = par.name
                raise ModelError("Encountered unknown units '%s' for Parameter '%s' (%s) in Population %s" % (par.units, par.name, par_label, par.pop.name))

        # Adjust cached fraction outflows and convert them to number units
        # `Compartment.resolve_outflows()` also populates flush links
        for pop in self.pops:
            for comp in pop.comps:
                comp.resolve_outflows(ti)

        # Balance junctions. Note that the order of execution is critical here for junctions that flow into other junctions,
        # so `self._exec_order` must have already been populated
        for j in self._exec_order["junctions"]:
            j.balance(ti)

    def update_comps(self) -> None:
        """
        Set the compartment values at self._t_index+1 based on the current values at self._t_index
        and the link values at self._t_index. Values are updated by iterating over all outgoing links

        """

        ti = self._t_index

        # Pre-populate the current value - need to iterate over pops here because transfers
        # will cross population boundaries
        for pop in self.pops:
            for comp in pop.comps:
                comp.update(ti)

    def flush_junctions(self) -> None:
        """
        Flush initialization values from junctions

        If junctions have been initialized with nonzero values as a mcv1 for initializing the
        downstream compartments, then the junctions need to be flushed into the downstream
        compartments at the start of the simulation. This is done using the ``.flush()`` method
        of the ``JunctionCompartment``. The order of the loop is important if junctions flow into
        other junctions - this needs to be computed from the graph prior to calling this method
        (so that ``Model.junctions`` is in the correct order)

        """

        for j in self._exec_order["junctions"]:
            j.initial_flush()

    def update_pars(self) -> None:
        """
        Update parameter values

        Run through all parameters and characteristics, updating as required. This takes place in stages

        1. Characteristics that are dependencies of parameters are updated
        2. Parameters are updated in dependency order
            a. The parameter function is evaluated
            b. The parameter is overwritten by programs
            c. The parameter is updated with the population aggregation calculation
            d. The parameter value is constrained

        The parameters are updated parameter-at-a-time (across populations) so that the population aggregation
        can be carried out.

        Only parameters that are required for transitions or that are overwritten by programs are
        modified here - otherwise, parameter values are computed in vector calculations either before
        integration (if the value is purely from the databook) or after integration (if the parameter depends
        on any flow rates or compartment sizes).

        """

        ti = self._t_index

        # First, compute dependent characteristics, as parameters might depend on them
        for charac in self._exec_order["characs"]:
            charac.update(ti)

        do_program_overwrite = self.programs_active and self.program_instructions.start_year <= self.t[ti] <= self.program_instructions.stop_year

        if do_program_overwrite:
            prop_coverage = sc.odict.fromkeys(self._program_cache["comps"], 0.0)
            for k, comp_list in self._program_cache["comps"].items():
                if k in self._program_cache["prop_coverage"]:  # If the coverage was precomputed in a coverage scenario
                    prop_coverage[k] = self._program_cache["prop_coverage"][k][[ti]]
                else:
                    n = 0.0
                    for comp in comp_list:
                        n += comp[ti]
                    prop_coverage[k] = self.progset.programs[k].get_prop_covered(self.t[ti], self._program_cache["capacities"][k][ti], n)
            prog_vals = self.progset.get_outcomes(prop_coverage)

        for par_name in self._exec_order["dynamic_pars"]:
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
                        if par.derivative:
                            par._dx = prog_vals[(par.name, par.pop.name)]  # For derivative parameters, overwrite the derivative rather than the value
                        else:
                            par[ti] = prog_vals[(par.name, par.pop.name)]

                        if par.units == FS.QUANTITY_TYPE_NUMBER:
                            par[ti] *= par.source_popsize(ti) / self.dt  # The outcome in the progbook is per person reached, which is a timestep specific value. Thus, need to annualize here
                        elif par.units == FS.QUANTITY_TYPE_RATE or par.units == FS.QUANTITY_TYPE_PROBABILITY:
                            # Continuous programs generally should not target number or probability parameters
                            # We apply a factor of dt here regardless of the parameter's timescale. This is because the dt factor here
                            # matches the factor of dt used to divide the annual spending into timestep spending
                            par[ti] /= self.dt

            # Handle parameters that aggregate over populations and use interactions in these functions.
            if pars[0].pop_aggregation:
                # NB. `par.pop_aggregation` is (agg_fcn,par_name,interaction_name,charac_name) where the last item is optional

                par_vals = [x[ti] for x in self._vars_by_pop[pars[0].pop_aggregation[1]]]  # Value of variable being averaged
                par_vals = np.array(par_vals).reshape(-1, 1)

                # NOTE - When doing cross-population interactions, 'pars' is from the 'to' pop
                # and 'par_vals' is from the 'from pop
                if len(pars[0].pop_aggregation) < 3:
                    weights = np.ones((len(par_vals), len(pars)))
                else:
                    weights = self.interactions[pars[0].pop_aggregation[2]][:, :, ti].copy()

                if pars[0].pop_aggregation[0] in {"SRC_POP_AVG", "SRC_POP_SUM"}:
                    weights = weights.T
                elif pars[0].pop_aggregation[0] in {"TGT_POP_AVG", "TGT_POP_SUM"}:
                    pass
                else:
                    raise ModelError("Unknown aggregation function '{0}'").format(pars[0].pop_aggregation[0])  # This should never happen, an error should be raised earlier

                # If we are weighting by a variable, multiply the weights matrix accordingly
                if len(pars[0].pop_aggregation) == 4:
                    vals = [par[ti] for par in self._vars_by_pop[pars[0].pop_aggregation[3]]]  # Value of weighting variable
                    vals = np.array(vals).reshape(-1, 1)
                    weights *= vals.T

                if pars[0].pop_aggregation[0] in {"SRC_POP_AVG", "TGT_POP_AVG"}:
                    norm = np.sum(weights, axis=1, keepdims=1)
                    norm[norm == 0] = 1
                    weights /= norm
                par_vals = np.matmul(weights, par_vals)

                for par, val in zip(pars, par_vals):
                    if par.skip_function is None or (self.t[ti] < par.skip_function[0]) or (self.t[ti] > par.skip_function[1]):  # Careful - note how the < here matches >= in Parameter.update()
                        par[ti] = par.scale_factor * val

            # Restrict the parameter's value if a limiting range was defined
            for par in pars:
                if par.derivative and ti < len(self.t) - 1:
                    # If derivative parameter, then perform an Euler forward step before constraining
                    par[ti + 1] = par[ti] + par._dx * self.dt
                    par.constrain(ti + 1)
                else:
                    par.constrain(ti)


def run_model(settings, framework, parset: ParameterSet, progset: ProgramSet = None, program_instructions: ProgramInstructions = None, name: str = None):
    """
    Build and process model

    Running simulations is accomplished via the :class:`Model` object in two steps

    1. The :class:`Model` object is build, and all variables are initialized
    2. The integration is carried out

    ``run_model`` serves as a wrapper for both of these steps, which are commonly performed
    together. However, in some cases it may be desired to split the operations. For example

    - In optimization, the same ``Model`` is used at each iteration, but with different instructions.
      To save time, the model is built just once, and deep-copied after building but before processing
    - Sometimes it may be required to make changes to the model's structure e.g. to implement exotic
      cross-population interactions that cannot be expressed via the Excel inputs. In that case, it may
      again be necessary

    :param settings: Project settings defining simulation time span and time step
    :param framework: A :class:`ProjectFramework` instance
    :param parset: A :class:`ParameterSet` instance
    :param progset: Optionally provide a :class:`ProgramSet` instance to use programs
    :param program_instructions: Optional :class:`ProgramInstructions` instance. If ``progset`` is specified, then instructions must be provided
    :param name: Optionally specify the name to assign to the output result
    :return: A :class:`Result` object containing the processed model

    """

    m = Model(settings, framework, parset, progset, program_instructions)
    m.process()
    return Result(model=m, parset=parset, name=name)
