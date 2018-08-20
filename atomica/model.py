# Imports

from .system import AtomicaException, NotFoundError, AtomicaInputError, NotAllowedError, logger
from .structure import FrameworkSettings as FS
from .results import Result
from .parser_function import parse_function
from collections import defaultdict
import sciris as sc
import numpy as np
import matplotlib.pyplot as plt
from six import string_types

model_settings = dict()
model_settings['tolerance'] = 1e-6
model_settings['iteration_limit'] = 100

class BadInitialization(AtomicaException):
    # Throw this error if the simulation exited due to a bad initialization, specifically
    # due to negative initial popsizes or an excessive residual.
    # This can then be dealt with appropriately - e.g. calibration will catch this
    # error and instruct ASD to reject the proposed parameters
    pass

class Variable(object):
    """
    Lightweight abstract class to store variable array of values (presumably corresponding to an external time vector).
    Includes an attribute to describe the format of these values.
    Examples include characteristics and dependent parameters.
    Note: All non-dependent parameters correspond to links.
    """

    def __init__(self, pop, id):
        self.id = id # ID is a tuple that uniquely identifies the Variable within a model. The last entry in the Tuple is the cascade name
        self.t = None
        self.dt = None
        if 'vals' not in dir(self):  # characteristics already have a vals method
            self.vals = None
        self.units = 'unknown'  # 'unknown' units are distinct to dimensionless units, that have value ''
        self.pop = pop  # Reference back to the Population containing this object

    @property
    def name(self):
        # Facilitate retrieving the cascade name e.g. for plotting
        return self.id[-1]

    def preallocate(self, tvec, dt):
        self.t = tvec
        self.dt = dt
        self.vals = np.ones(tvec.shape) * np.nan

    def plot(self):
        plt.figure()
        plt.plot(self.t, self.vals, label=self.name)
        plt.legend()
        plt.xlabel('Year')
        plt.ylabel("%s (%s)" % (self.name, self.units))

    def update(self, ti):
        # A Variable can have a function to update its value at a given time, which is
        # overloaded differently for Characteristics and Parameters
        return

    def set_dependent(self):
        # Make the variable a dependency. For Compartments and Links, this does nothing. For Characteristics and
        # Parameters, it will set the dependent flag, but in addition, any validation constraints e.g. a Parameter
        # that depends on Links cannot itself be a dependency, will be enforced
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
        Variable.__init__(self, pop=pop, id=(pop.name,name))
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

        outflow_probability = 0 # Outflow probability at this timestep
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
                raise AtomicaInputError('Unknown parameter units')

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
        Variable.__init__(self, pop=pop, id=(pop.name,name))
        self.units = 'Number of people'
        self.includes = []
        self.denominator = None
        # The following flag indicates if another variable depends on this one.
        # This indicates a value needs computation during integration.
        self.dependency = False
        self.internal_vals = None

    def preallocate(self, tvec, dt):
        # Note that we don't use Variable.preallocate() here because we cannot
        # preallocate self.vals because it is a property method
        self.t = tvec
        self.dt = dt
        self.internal_vals = np.ones(tvec.shape) * np.nan

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
        if self.internal_vals is None:
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
            return self.internal_vals

    def set_dependent(self):
        self.dependency = True

        for inc in self.includes:
            inc.set_dependent()

        if self.denominator is not None:
            self.denominator.set_dependent()

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
        self.internal_vals[ti] = 0
        for comp in self.includes:
            self.internal_vals[ti] += comp.vals[ti]
        if self.denominator is not None:
            denom = self.denominator.vals[ti]
            if denom > 0:
                self.internal_vals[ti] /= denom
            elif self.internal_vals[ti] < model_settings['tolerance']:
                self.internal_vals[ti] = 0  # Given a zero/zero case, make the answer zero.
            else:
                self.internal_vals[ti] = np.inf  # Given a non-zero/zero case, keep the answer infinite.

class Parameter(Variable):
    # A parameter is a Variable that can have a value computed via an fcn_str and a list of
    # dependent Variables. This class may need to be relabeld to avoid confusion with
    # the class in Parameter.py which provides a means of computing the Parameter that is used by the model.
    # This is a Parameter in the cascade.xlsx sense - there is one Parameter object for every item in the 
    # Parameters sheet. A parameter that maps to multiple transitions (e.g. doth_rate) will have one parameter
    # and multiple Link instances that depend on the same Parameter instance
    #
    #  *** Parameter values are always annualized ***
    def __init__(self, pop, name):
        Variable.__init__(self, pop=pop, id=(pop.name,name))
        self.vals = None
        self.limits = None  # Can be a two element vector [min,max]
        self.dependency = False
        self.pop_aggregation = None    # If True, value update in Model.update_pars(), not self.update().
        self.scale_factor = 1.0
        self.links = []  # References to links that derive from this parameter
        self.source_popsize_cache_time = None
        self.source_popsize_cache_val = None

        self.fcn_str = None # String representation of parameter function
        self.deps = None # Dict of dependencies containing lists of integration objects
        self._fcn = None # Internal cache for parsed parameter function (this will be dropped when pickled)

    def set_fcn(self, framework, fcn_str):
        # fcn_input could be
        # - string, which gets converted to a functor via parse_function()
        # - functor, which gets stored in self._fcn directly
        #
        # Supported functions will be given as input a dict where the keys are
        # the dependencies in dep_list, and the values are scalars computed from the
        # current state of the model during integration

        assert isinstance(fcn_str,string_types), "Parameter function must be supplied as a string"
        self.fcn_str = fcn_str
        self._fcn, dep_list = parse_function(self.fcn_str)
        if fcn_str.startswith("SRC_POP_AVG") or fcn_str.startswith("TGT_POP_AVG"):
            # The function is like 'SRC_POP_AVG(par_name,interaction_name,charac_name)'
            # self.pop_aggregation will be ['SRC_POP_AVG',parname,interaction_name,charac_object]
            special_function, temp_list = self.fcn_str.split("(")
            function_args = temp_list.rstrip(")").split(',')
            function_args = [x.strip() for x in function_args]

            if len(function_args) == 2: # If weighting variable not provided
                function_args.append(None)

            # Convert average variable to object reference
            v1 = self.pop.get_variable(function_args[0])[0]
            if isinstance(v1, Link):
                raise NotAllowedError('Links cannot be aggregated across populations')
            function_args[0] = v1

            # Convert weighting variable to object reference
            if len(function_args) == 3:
                v2 = self.pop.get_variable(function_args[2])[0]
                if isinstance(v2,Link):
                    raise NotAllowedError('Links cannot be used to weight interactions')
                function_args[-1] = v2

            self.pop_aggregation = [special_function] + function_args

        deps = {}
        interactions = set(framework.interactions.index)
        for dep_name in dep_list:
            if not dep_name in interactions: # There are no integration variables associated with the interactions, as they are treated as a special matrix
                deps[dep_name] = self.pop.get_variable(dep_name)
        self.deps = deps

        # If this Parameter has links, it must be marked as dependent for evaluation during integration
        if self.links or self.pop_aggregation:
            self.set_dependent()

    def set_dependent(self):
        self.dependency = True
        if self.deps is not None:  # Make all dependencies dependent, this will propagate through dependent parameters.
            for deps in self.deps.values():
                for dep in deps:
                    if isinstance(dep, Link):
                        raise NotAllowedError("A Parameter that depends on transition flow rates cannot be a dependency, it must be output only.")
                    dep.set_dependent()

    def unlink(self):
        Variable.unlink(self)
        self.links = [x.id for x in self.links]
        if self.deps is not None:
            for dep_name in self.deps:
                self.deps[dep_name] = [x.id for x in self.deps[dep_name]]
        if self._fcn is not None:
            self._fcn = None
        if self.pop_aggregation and len(self.pop_aggregation) == 4:
            self.pop_aggregation[3] = self.pop_aggregation[3].id

    def relink(self, objs):
        # Given a dictionary of objects, restore the internal references
        Variable.relink(self, objs)
        self.links = [objs[x] for x in self.links]
        if self.deps is not None:
            for dep_name in self.deps:
                self.deps[dep_name] = [objs[x] for x in self.deps[dep_name]]
        if self.fcn_str:
            self._fcn = parse_function(self.fcn_str)[0]
        if self.pop_aggregation and len(self.pop_aggregation) == 4:
            self.pop_aggregation[3] = objs[self.pop_aggregation[3]]

    def constrain(self, ti):
        # NB. Must be an array, so ti must must not be supplied
        if self.limits is not None:
            self.vals[ti] = max(self.limits[0], self.vals[ti])
            self.vals[ti] = min(self.limits[1], self.vals[ti])

    def update(self, ti=None):
        # Update the value of this Parameter at time index ti
        # by evaluating its f_stack function using the 
        # current values of all dependent variables at time index ti

        if not self._fcn or self.pop_aggregation:
            return

        if ti is None:
            ti = np.arange(0, self.vals.size)  # This corresponds to every time point
        else:
            ti = np.array(ti)

        dep_vals = dict.fromkeys(self.deps,0.0)
        for dep_name, deps in self.deps.items():
            for dep in deps:
                if isinstance(dep, Link):
                    dep_vals[dep_name] += dep.vals[[ti]] / dep.dt
                else:
                    dep_vals[dep_name] += dep.vals[[ti]]

        self.vals[ti] = self.scale_factor*self._fcn(**dep_vals)

    def source_popsize(self, ti):
        # Get the total number of people covered by this program
        # i.e. the sum of the source compartments of all links that
        # derive from this program
        # If impact_names is specified, it must be a list of link names
        # Then only links whose name is in that list will be included
        if ti == self.source_popsize_cache_time:
            return self.source_popsize_cache_val
        else:
            n = 0
            for link in self.links:
                n += link.source.vals[ti]
            self.source_popsize_cache_time = ti
            self.source_popsize_cache_val = n
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
    def __init__(self, pop, parameter, source, dest, tag):
        # Note that the Link's name is the transition tag
        Variable.__init__(self, pop=pop, id=(pop.name,source.name,dest.name,tag)) # A Link is only uniquely identified by (Pop,Source,Dest,Par)
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

    def __init__(self, framework, name, label):

        self.name = name # This is the code name
        self.label = label # This is the full name

        self.comps = list()  # List of cascade compartments that this model population subdivides into.
        # List of characteristics and output parameters.
        # Dependencies computed during integration, pure outputs added after.
        self.characs = list()
        self.links = list()  # List of intra-population cascade transitions within this model population.
        self.pars = list()

        self.comp_lookup = dict()  # Maps name of a compartment to a compartment
        self.charac_lookup = dict()
        self.par_lookup = dict()
        self.link_lookup = dict()  # Map name of Link to a list of Links with that name

        self.gen_cascade(framework=framework)  # Convert compartmental cascade into lists of compartment and link objects.

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

    def get_variable(self, name):
        # Returns a list of variables whose name matches the requested name
        # At the moment, names are unique across object types and within object
        # types except for links, but if that logic changes, simple modifications can
        # be made here

        name = name.replace('___',':') # Parameter functions will convert ':' to '___' for use in variable names

        if name in self.comp_lookup:
            return [self.comp_lookup[name]]
        elif name in self.charac_lookup:
            return [self.charac_lookup[name]]
        elif name in self.par_lookup:
            return [self.par_lookup[name]]
        elif name in self.link_lookup:
            return self.link_lookup[name]
        elif ':' in name:
            # Link names in Atomica end in 'par_name:flow' so they are handled above
            # This branch of the if statement is exclusively for compartment lookup
            # Allowed syntax is
            # 'source_name:' - All links going out from source
            # ':dest_name' - All links going into destination
            # 'source_name:dest_name' - All links from Source to Dest
            # 'source_name:dest_name:par_name' - All links from Source to Dest belonging to a given Parameter
            # ':dest:par_name'
            # 'source::par_name' - As per above
            # '::par_name' - All links with specified par_name (less efficient than 'par_name:flow')
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
            raise NotFoundError("Object '{0}' not found.".format(name))

    def get_comp(self, comp_name):
        """ Allow compartments to be retrieved by name rather than index. Returns a Compartment. """
        return self.comp_lookup[comp_name]

    def get_links(self, name):
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
        return self.charac_lookup[charac_name]

    def get_par(self, par_name):
        """ Allow dependencies to be retrieved by name rather than index. Returns a Variable. """
        return self.par_lookup[par_name]

    def gen_cascade(self, framework):
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
            self.comps.append(Compartment(pop=self, name=comp_name))
            if comps.at[comp_name,"is source"] == 'y':
                self.comps[-1].tag_birth = True
            if comps.at[comp_name,"is sink"] == 'y':
                self.comps[-1].tag_dead = True
            if comps.at[comp_name,"is junction"] == 'y':
                self.comps[-1].is_junction = True
        self.comp_lookup = {comp.name: comp for comp in self.comps}

        # Characteristics first pass, instantiate objects
        for charac_name in list(characs.index):
            self.characs.append(Characteristic(pop=self, name=charac_name))
        self.charac_lookup = {charac.name: charac for charac in self.characs}

        # Characteristics second pass, add includes and denominator
        for charac_name,charac in zip(list(characs.index),self.characs):
            includes = [x.strip() for x in characs.at[charac_name,'components'].split(',')]
            for inc_name in includes:
                charac.add_include(self.get_variable(inc_name)[0])  # nb. We expect to only get one match for the name, so use index 0
            denominator = characs.at[charac_name,"denominator"]
            if denominator is not None:
                charac.add_denom(self.get_variable(denominator)[0]) # nb. framework import strips whitespace from the overall field

        # Parameters first pass, create parameter objects and links
        for par_name in list(pars.index):
            par = Parameter(pop=self, name=par_name)
            self.pars.append(par)
            if framework.transitions[par_name]: # If there are any links associated with this parameter
                par.units = pars.at[par_name,"format"] # First copy in the units from the Framework - mainly for transition parameters that are functions. Others will get overwritten from databook later
                for pair in framework.transitions[par_name]:
                    src = self.get_comp(pair[0])
                    dst = self.get_comp(pair[1])
                    tag = par.name + ':flow'  # Temporary tag solution.
                    new_link = Link(self, par, src, dst, tag)
                    if tag not in self.link_lookup:
                        self.link_lookup[tag] = [new_link]
                    else:
                        self.link_lookup[tag].append(new_link)
                    self.links.append(new_link)
        self.par_lookup = {par.name: par for par in self.pars}

        # Parameters second pass, process f_stacks, deps, and limits
        for par_name,par in zip(list(pars.index),self.pars):
            min_value = pars.at[par_name,'minimum value']
            max_value = pars.at[par_name,'maximum value']

            if (min_value is not None) or (max_value is not None):
                par.limits = [-np.inf, np.inf]
                if min_value is not None:
                    par.limits[0] = min_value
                if max_value is not None:
                    par.limits[1] = max_value

            fcn_str = pars.at[par_name,'function']
            if fcn_str is not None:
                par.set_fcn(framework,fcn_str)

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

        characs = [c for c in self.characs if framework.get_charac(c.name)['databook page'] is not None and framework.get_charac(c.name)['setup weight']]
        characs += [c for c in self.comps if framework.get_comp(c.name)['databook page'] is not None and framework.get_comp(c.name)['setup weight']]

        comps = [c for c in self.comps if not (c.tag_birth or c.tag_dead)]
        charac_indices = {c.name: i for i, c in enumerate(characs)}  # Make lookup dict for characteristic indices
        comp_indices = {c.name: i for i, c in enumerate(comps)}  # Make lookup dict for compartment indices

        b = np.zeros((len(characs), 1))
        A = np.zeros((len(characs), len(comps)))

        # Construct the characteristic value vector (b) and the includes matrix (A)
        for i, c in enumerate(characs):
            # Look up the characteristic value
            par = parset.get_par(c.name)
            b[i] = par.interpolate(tvec=np.array([t_init]), pop_name=self.name)[0]*par.y_factor[self.name]
            # Run exception clauses for compartment logic.
            try:
                if c.denominator is not None:
                    denom_par = parset.pars['characs'][parset.par_ids['characs'][c.denominator.name]]
                    b[i] *= denom_par.interpolate(tvec=np.array([t_init]), pop_name=self.name)[0]*denom_par.y_factor[self.name]
            except Exception:
                pass
            try:
                for inc in c.get_included_comps():
                    A[i, comp_indices[inc.name]] = 1.0
            except Exception:
                A[i, comp_indices[c.name]] = 1.0

        # Solve the linear system
        x, residual, rank, _ = np.linalg.lstsq(A, b, rcond=-1)

        # Halt if the solution is not unique (could relax this check later)
        if rank < A.shape[1]:
            raise AtomicaException('Characteristics are not full rank, cannot determine a unique initialization')

        # Print warning for characteristics that are not well matched by the compartment size solution
        proposed = np.matmul(A, x)
        for i in range(0, len(characs)):
            if abs(proposed[i] - b[i]) > model_settings['tolerance']:  # project_settings.model_settings['tolerance']:
                logger.warning("Characteristic '{0}' '{1}' - Requested {2}, "
                               "Calculated {3}".format(self.name, characs[i].name, b[i], proposed[i]))

        # Print diagnostic output for compartments that were assigned a negative value
        def report_characteristic(charac, n_indent=0):
            if charac.name in charac_indices:
                logger.warning(n_indent * "\t" + "Characteristic '{0}': Target value = "
                                                 "{1}".format(charac.name, b[charac_indices[charac.name]]))
            else:
                logger.warning(n_indent * "\t" + "Characteristic '{0}' not in databook: "
                                                 "Target value = N/A (0.0)".format(charac.name))

            n_indent += 1
            for inc in charac.includes:
                if isinstance(inc, Characteristic):
                    report_characteristic(inc, n_indent)
                else:
                    logger.warning(
                        n_indent * '\t' + 'Compartment %s: Computed value = %f' % (inc.name, x[comp_indices[inc.name]]))

        for i in range(0, len(comps)):
            if x[i] < -model_settings['tolerance']:
                logger.warning('Compartment %s %s - Calculated %f' % (self.name, comps[i].name, x[i]))
                for charac in characs:
                    try:
                        if comps[i] in charac.get_included_comps():
                            report_characteristic(charac)
                    except Exception:
                        if comps[i] == charac:
                            report_characteristic(charac)

        # Halt for an unsatisfactory overall solution (could relax this check later)
        if residual > model_settings["tolerance"]:
            print(x)
            raise BadInitialization("Residual was {0} which is unacceptably large (should be < {1}). "
                                   "This points to a probable inconsistency in the initial "
                                   "values.".format(residual, model_settings["tolerance"]))

        # Halt for any negative popsizes
        if np.any(np.less(x, -model_settings['tolerance'])):
            raise BadInitialization('Negative initial popsizes')

        # Otherwise, insert the values
        for i, c in enumerate(comps):
            c.vals[0] = max(0.0, x[i])

        for c in self.comps:
            if c.tag_birth or c.tag_dead:
                c.vals[0] = 0

class Model(object):
    """ A class to wrap up multiple populations within model and handle cross-population transitions. """

    def __init__(self, settings, framework, parset, progset=None, program_instructions=None):

        self.pops = list()  # List of population groups that this model subdivides into.
        self.interactions = sc.odict()
        self.programs_active = None  # True or False depending on whether Programs will be used or not
        self.progset = sc.dcp(progset)
        self.program_instructions = sc.dcp(program_instructions) # program instructions
        self.t = None
        self.dt = None

        self._t_index = 0  # Keeps track of array index for current timepoint data within all compartments.
        self._vars_by_pop = None  # Cache to look up lists of variables by name across populations
        self._pop_ids = sc.odict()  # Maps name of a population to its position index within populations list.
        self._program_cache = None
        self._par_list = list(framework.pars.index) # This is a list of all parameters code names in the model

        self.framework = sc.dcp(framework) # Store a copy of the Framework used to generate this model
        self.framework.spreadsheet = None # No need to keep the spreadsheet
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
        self._program_cache = None # This drops the cache when pickling, but its only going to have anything if pickled DURING process() i.e. only devs would encounter this

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

            self._program_cache['comps'] = {}
            self._program_cache['pars'] = {}
            for prog in self.progset.programs.values():
                self._program_cache['comps'][prog.name] = []

                for pop_name in prog.target_pops:
                    for comp_name in prog.target_comps:
                        self._program_cache['comps'][prog.name].append(self.get_pop(pop_name).get_comp(comp_name))

            for target_par in prog.target_pars:
                if target_par['param'] not in self._program_cache['pars']:
                    self._program_cache['pars'][target_par['param']] = {}

                self._program_cache['pars'][target_par['param']][target_par['pop']] = self.get_pop(target_par['pop']).get_par(target_par['param'])

            self._program_cache['alloc'] = self.progset.get_alloc(self.program_instructions, self.t)
            self._program_cache['coverage'] = self.progset.get_num_covered(year=self.t, alloc=self._program_cache['alloc'])

            self.progset.prepare_cache()
        else:
            self.programs_active = False



    def set_vars_by_pop(self):
        self._vars_by_pop = defaultdict(list)
        for pop in self.pops:
            for var in pop.comps + pop.characs + pop.pars + pop.links:
                self._vars_by_pop[var.name].append(var)
        self._vars_by_pop = dict(self._vars_by_pop) # Stop new entries from appearing in here by accident

    def __getstate__(self):
        # The combination of
        self.unlink()
        d = sc.dcp(self.__dict__)  # Pickling to string results in a copy
        self.relink()  # Relink, otherwise the original object gets unlinked
        return d

    def __setstate__(self, d):
        self.__dict__ = d
        self.relink()

    def __deepcopy__(self,memodict={}):
        # Using dcp(self.__dict__) is faster than pickle getstate/setstate
        # when this is called via copy.deepcopy()
        self.unlink()
        d = sc.dcp(self.__dict__)
        self.relink()
        new = Model.__new__(Model)
        new.__dict__.update(d)
        return new

    def get_pop(self, pop_name):
        """ Allow model populations to be retrieved by name rather than index. """
        pop_index = self._pop_ids[pop_name]
        return self.pops[pop_index]


    def build(self, settings, parset):
        """ Build the full model. """

        self.t = settings.tvec  # Note: Class @property method returns a new object each time.
        self.dt = settings.sim_dt

        for k, (pop_name,pop_label) in enumerate(zip(parset.pop_names,parset.pop_labels)):
            self.pops.append(Population(framework=self.framework, name=pop_name, label=pop_label))
            # Memory is allocated, speeding up model. However, values are NaN to enforce proper parset value saturation.
            self.pops[-1].preallocate(self.t, self.dt)
            self._pop_ids[pop_name] = k
            self.pops[-1].initialize_compartments(parset, self.framework, self.t[0])

        # Expand interactions into matrix form
        self.interactions = dict()
        for name, weights in parset.interactions.items():
            self.interactions[name] = np.zeros((len(self.pops), len(self.pops), len(self.t)))
            for from_pop, par in weights.items():
                for to_pop in par.pops:
                    self.interactions[name][parset.pop_names.index(from_pop), parset.pop_names.index(to_pop), :] = par.interpolate(self.t, to_pop)*par.y_factor[to_pop]

        # Insert values from parset into model objects
        for cascade_par in parset.pars['cascade']:
            for pop_name in parset.pop_names:
                pop = self.get_pop(pop_name)
                par = pop.get_par(cascade_par.name)  # Find the parameter with the requested name
                # If parameter has an f-stack then vals will be calculated during/after integration.
                # This is opposed to values being supplied from databook.
                par.scale_factor = cascade_par.y_factor[pop_name]
                if not par.fcn_str:
                    par.vals = cascade_par.interpolate(tvec=self.t, pop_name=pop_name)
                    par.vals *= par.scale_factor  # Interpolation no longer rescales, so do it here
                if par.links:
                    par.units = cascade_par.y_format[pop_name]

        # Propagating transfer parameter parset values into Model object.
        # For each population pair, instantiate a Parameter with the values from the databook
        # For each compartment, instantiate a set of Links that all derive from that Parameter
        # NB. If a Program somehow targets the transfer parameter, those values will automatically... what?
        for trans_type in parset.transfers:
            if parset.transfers[trans_type]:
                for pop_source in parset.transfers[trans_type]:

                    # This contains the data for all of the destination pops.
                    transfer_parameter = parset.transfers[trans_type][pop_source]

                    pop = self.get_pop(pop_source)

                    for pop_target in transfer_parameter.y:

                        # Create the parameter object for this link (shared across all compartments)
                        par_name = trans_type + '_' + pop_source + '_to_' + pop_target  # e.g. 'aging_0-4_to_15-64'
                        par = Parameter(pop=pop, name=par_name)
                        par.preallocate(self.t, self.dt)
                        val = transfer_parameter.interpolate(tvec=self.t, pop_name=pop_target)
                        par.scale_factor = transfer_parameter.y_factor[pop_target]
                        par.vals = val*par.scale_factor
                        par.units = transfer_parameter.y_format[pop_target]
                        pop.pars.append(par)
                        # TODO: Reconsider manual lookup hack if Transfers are implemented differently.
                        pop.par_lookup[par_name] = par

                        target_pop_obj = self.get_pop(pop_target)

                        for source in pop.comps:
                            if not (source.tag_birth or source.tag_dead or source.is_junction):
                                # Instantiate a link between corresponding compartments
                                dest = target_pop_obj.get_comp(source.name)  # Get the corresponding compartment
                                link_tag = par_name + '_' + source.name + ':flow'  # e.g. 'aging_0-4_to_15-64_sus:flow'
                                link = Link(pop, par, source, dest, link_tag)
                                link.preallocate(self.t, self.dt)
                                pop.links.append(link)
                                if link.name in pop.link_lookup:
                                    pop.link_lookup[link.name].append(link)
                                else:
                                    pop.link_lookup[link.name] = [link]

        # Now that all object have been created, update _vars_by_pop() accordingly
        self.set_vars_by_pop()

    def process(self):
        """ Run the full model. """

        assert self._t_index == 0  # Only makes sense to process a simulation once, starting at ti=0 - this might be relaxed later on

        self.update_program_cache()

        # Initial flush of people in junctions
        if self._t_index == 0:
            # Make sure initially-filled junctions are processed and initial dependencies are calculated, and calculate initial flows
            self.update_pars() # Update transition parameters in case junction outflows are function parameters
            self.update_junctions(initial_flush=True) # Flush the current contents of the junction without considering any inflows
            self.update_pars() # Update the transition parameters in case junction outflows are functions _and_ they depend on compartment sizes that just changed in the line above
            self.update_links() # Update all of the links
            self.update_junctions() # Junctions are now empty - perform a normal update by setting the outflows to be equal to the inflows so the usual condition outflow[t]=inflow[t] is satisfied

        # Main integration loop
        while self._t_index < (self.t.size - 1):
            self.update_comps() # This writes values to comp.vals[ti+1] so this will be out of bounds if self._t_index == self.t.size-1
            self._t_index += 1  # Step the simulation forward
            self.update_pars()
            self.update_links()
            self.update_junctions()

        for pop in self.pops:
            [par.update() for par in pop.pars if not par.dependency]  # Update any remaining parameters
            for charac in pop.characs:
                charac.internal_vals = None  # Wipe out characteristic vals to save space

                # TODO: Consider whether it is worth reimplementing space-saving measures.
                # if not full_output:
                #     for par in pop.pars:
                #         if (not par.name in framework.linkpar_specs) \
                #                 or (not 'output' in settings.linkpar_specs[par.name]) \
                #                 or (settings.linkpar_specs[par.name] != 'y'):
                #             par.vals = None
                #             for link in par.links:
                #                 link.vals = None

        self._program_cache = None # Drop the program cache afterwards to save space

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

                    if not transition:
                        for link in par.links:
                            link.vals[ti] = 0.0
                        continue
                    quantity_type = par.units

                    # An annual duration can be converted into an annual probability; do it.
                    if quantity_type == FS.QUANTITY_TYPE_DURATION:
                        transition = 1.0 - np.exp(-1.0 / transition)
                        quantity_type = FS.QUANTITY_TYPE_PROBABILITY

                    # Convert probability by Poisson distribution formula to a value appropriate for timestep.
                    if quantity_type == FS.QUANTITY_TYPE_PROBABILITY:
                        if transition > 1.0:
                            transition = 1.0
                        converted_frac = 1 - (1 - transition) ** self.dt
                        for link in par.links:
                            link.vals[ti] = link.source.vals[ti] * converted_frac
                    # Linearly convert number down to that appropriate for one timestep.
                    # Disaggregate proportionally across all source compartment sizes related to all links.
                    elif quantity_type == FS.QUANTITY_TYPE_NUMBER:
                        converted_amt = transition * self.dt
                        if len(par.links) > 1:
                            for link in par.links:
                                link.vals[ti] = converted_amt * link.source.vals[ti] / par.source_popsize(ti)
                        else:
                            par.links[0].vals[ti] = converted_amt
                    elif quantity_type not in [FS.QUANTITY_TYPE_PROPORTION]:
                        raise AtomicaException("Encountered unknown quantity type %s for Parameter %s (%s)" % (quantity_type,par.name,pop.name))

            # Then, adjust outflows to prevent negative popsizes.
            for comp_source in pop.comps:
                if not (comp_source.is_junction or comp_source.tag_birth):
                    outflow = 0.0
                    for link in comp_source.outlinks:
                        outflow += link.vals[ti]

                    if outflow > comp_source.vals[ti]:
                        rescale = comp_source.vals[ti]/outflow
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

    def update_junctions(self,initial_flush=False):
        """
        For every compartment considered a junction, propagate the contents onwards.
        Do so until all junctions are empty.
        """

        # A junction can be called either at the very start of the simulation, when it might have
        # some people in it initially, or after `update_links` in which case it won't have any people
        # so it needs to fill itself from its incoming links

        ti = self._t_index # The current simulation timestep, at time ti the inflow and outflow need to be balanced. `update_links()` sets the inflow but not the outflow, which is done here

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
            for i in range(0,model_settings["iteration_limit"]):
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
                            raise AtomicaException("Total junction outflow for junction %s was zero - all junctions must have a nonzero outflow" % (junc.name))

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
                raise AtomicaException("Processing junctions for timestep {0} is taking too long. Infinite loop suspected.".format(ti))

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

        # The output list maintains the order in which characteristics and parameters appear in the
        # settings, and also puts characteristics before parameters. So iterating through that list
        # will automatically compute them in the correct order

        # First, compute dependent characteristics, as parameters might depend on them
        for pop in self.pops:
            for charac in pop.characs:
                if charac.dependency:
                    charac.update(ti)

        # 1st:  Update parameters if they have an f_stack variable
        # 2nd:  Any parameter that is overwritten by a program-based cost-coverage-impact transformation.
        # 3rd:  Any parameter that is overwritten by a special rule, e.g. averaging across populations.
        # 4th:  Any parameter that is restricted within a range of values, i.e. by min/max values.
        # Looping through populations must be internal.
        # This allows all values to be calculated before special inter-population rules are applied.
        # We resolve one parameter at a time, in dependency order
        do_program_overwrite = self.programs_active and self.program_instructions.start_year <= self.t[ti] <= self.program_instructions.stop_year

        if do_program_overwrite:
            # Compute the fraction covered
            prop_covered = dict.fromkeys(self._program_cache['comps'], 0.0)
            for k,comp_list in self._program_cache['comps'].items():
                n = 0.0
                for comp in comp_list:
                    n += comp.vals[ti]
                prop_covered[k] = np.minimum(self._program_cache['coverage'][k][ti] / n, 1.)

            # Compute the updated program values
            prog_vals = self.progset.get_outcomes(prop_covered)

        for par_name in self._par_list:
            # All of the parameters with this name, across populations.
            # There should be one for each population (these are Parameters, not Links).
            pars = self._vars_by_pop[par_name]

            # First - update parameters that are dependencies, evaluating f_stack if required
            for par in pars:
                if par.dependency:
                    par.update(ti)

            # Then overwrite with program values
            if do_program_overwrite:
                for par in pars:
                    if (par.name,par.pop.name) in prog_vals:
                        par.vals[ti] = prog_vals[(par.name,par.pop.name)]

            # Handle parameters that aggregate over populations and use interactions in these functions.
            if pars[0].pop_aggregation:
                # NB. `par.pop_aggregation` is (agg_fcn,par_name,interaction_name,charac_name) where the last item is optional

                par_vals = [par.pop_aggregation[1].vals[ti] for par in pars] # Value of variable being averaged
                par_vals = np.array(par_vals).reshape(-1, 1)

                weights = self.interactions[pars[0].pop_aggregation[2]][:,:,ti].copy()

                if pars[0].pop_aggregation[0] == 'SRC_POP_AVG':
                    weights = weights.T
                elif pars[0].pop_aggregation[0] == 'TGT_POP_AVG':
                    pass
                else:
                    raise AtomicaException("Unknown aggregation function '{0}'").format(pars[0].pop_aggregation[0])  # This should never happen, an error should be raised earlier

                # If we are weighting by a variable, multiply the weights matrix accordingly
                if len(pars[0].pop_aggregation) == 4:
                    charac_vals = [par.pop_aggregation[3].vals[ti] for par in pars] # Value of weighting variable
                    charac_vals = np.array(charac_vals).reshape(-1, 1)
                    weights *= charac_vals.T

                weights /= np.sum(weights, axis=1, keepdims=1) # Normalize the interaction
                par_vals = np.matmul(weights, par_vals)

                for par, val in zip(pars, par_vals):
                    par.vals[ti] = par.scale_factor*val

            # Restrict the parameter's value if a limiting range was defined
            for par in pars:
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
