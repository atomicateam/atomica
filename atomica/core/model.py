# Imports

from .system import AtomicaException, logger, NotFoundError, AtomicaInputError, NotAllowedError
from .structure_settings import FrameworkSettings as FS
from .excel import ExcelSettings as ES
from .results import Result
from .parser_function import parse_function
from collections import defaultdict
import sciris.core as sc

import pickle
import numpy as np
from copy import deepcopy as dcp
import matplotlib.pyplot as plt

# TODO: Consider renaming and decide what to do with project settings as an object.
#       Maybe have Project methods for changing sim time ranges act on these model settings.
model_settings = dict()
model_settings['tolerance'] = 1e-6
model_settings['iteration_limit'] = 100


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
        self.units = 'people'
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

    def expected_duration(self, ti=None):
        # Returns the expected number of years that an individual is expected to remain
        # in this compartment for, if the outgoing flow rates are maintained
        if ti is None:
            ti = np.arange(0, len(self.t))

        outflow_probability = 0
        for link in self.outlinks:
            if link.parameter.units == 'fraction':
                outflow_probability += 1 - (1 - link.parameter.vals[ti]) ** self.dt  # A formula for converting from yearly fraction values to the dt equivalent.
            elif link.parameter.units == 'number':
                outflow_probability += link.parameter.vals[ti] * self.dt / self.vals[ti]
            else:
                raise AtomicaInputError('Unknown parameter units')

        # remain_probability = 1 - outflow_probability

        dur = np.zeros(outflow_probability.shape)
        # From OSL/HMM-MAR:
        # Given a transition probability, what is the expected lifetime in units of steps?
        # This can be determined using a symbolic integration, below
        # syms k_step p;
        # assume(p>0);
        # f =(k_step)*p^k_step*(1-p); # (probability that state lasts k *more* steps, multiplied by lifetime which is k)
        # fa = 1+int(f,k_step,0,inf); # Add 1 to the lifetime because all states last at least 1 sample
        # f = @(x) double(subs(fa,p,x));
        #
        # However, the result of the symbolic integration contains a limit which is
        # zero unless p=1, but p=1 is not needed because we know it means the compartment immediately empties.
        # So instead of the function above, can instead drop the limit term and write the rest of the
        # expression out which gives identical results from p=0.00001 to p=0.99 (note that if dirichletdiag>=1)
        # then the upper bound on the transition probability is p=0.5 anyway for K=2
        dur[dur < 1] = (1 - (1. / np.log(remain_probability[dur < 1]) ** 2) *
                        (remain_probability[dur < 1] - 1)) * self.dt
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
        self.units = 'people'
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

    def set_fcn(self, framework, spec):
        # fcn_input could be
        # - string, which gets converted to a functor via parse_function()
        # - functor, which gets stored in self._fcn directly
        #
        # Supported functions will be given as input a dict where the keys are
        # the dependencies in dep_list, and the values are scalars computed from the
        # current state of the model during integration

        fcn_input = spec[FS.TERM_FUNCTION]
        dep_list = spec['dependencies']

        assert isinstance(fcn_input,str), "Parameter function must be supplied as a string"
        self.fcn_str = fcn_input
        self._fcn = parse_function(self.fcn_str)[0]
        if fcn_input.startswith("SRC_POP_AVG") or fcn_input.startswith("TGT_POP_AVG"):
            # The function is like 'SRC_POP_AVG(par_name,interaction_name,charac_name)'
            # self.pop_aggregation will be ['SRC_POP_AVG',parname,interaction_name,charac_object]
            special_function, temp_list = self.fcn_str.split("(")
            function_args = temp_list.rstrip(")").split(ES.LIST_SEPARATOR)
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
        for dep_name in dep_list:
            if not (self.pop_aggregation and dep_name in framework.specs[FS.KEY_INTERACTION]):
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
        self.units = 'people'

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


# Cascade compartment and population classes
class Population(object):
    """
    A class to wrap up data for one population within model.
    Each model population must contain a set of compartments with equivalent names.
    """

    def __init__(self, framework, name='default'):

        self.name = name
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

        self.gen_cascade(
            framework=framework)  # Convert compartmental cascade into lists of compartment and link objects.

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

        # Instantiate Compartments
        for name in framework.specs[FS.KEY_COMPARTMENT]:
            spec = framework.get_spec(name)
            self.comps.append(Compartment(pop=self, name=name))
            if spec["is_source"]:
                self.comps[-1].tag_birth = True
            if spec["is_sink"]:
                self.comps[-1].tag_dead = True
            if spec["is_junction"]:
                self.comps[-1].is_junction = True
        self.comp_lookup = {comp.name: comp for comp in self.comps}

        # Characteristics first pass, instantiate objects
        for name in framework.specs[FS.KEY_CHARACTERISTIC]:
            self.characs.append(Characteristic(pop=self, name=name))
        self.charac_lookup = {charac.name: charac for charac in self.characs}

        # Characteristics second pass, add includes and denominator
        for name in framework.specs[FS.KEY_CHARACTERISTIC]:
            spec = framework.get_spec(name)
            charac = self.get_charac(name)
            for inc_name in spec["includes"]:
                charac.add_include(
                    self.get_variable(inc_name)[0])  # nb. We expect to only get one match for the name, so use index 0
            if "denominator" in spec and not spec["denominator"] is None:
                charac.add_denom(self.get_variable(spec["denominator"])[0])

        # Parameters first pass, create parameter objects and links
        for name in framework.specs[FS.KEY_PARAMETER]:
            spec = framework.get_spec(name)
            par = Parameter(pop=self, name=name)
            self.pars.append(par)
            if "links" in spec:
                for pair in spec["links"]:
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
        for name in framework.specs[FS.KEY_PARAMETER]:
            spec = framework.get_spec(name)
            par = self.get_par(name)

            if ("min" in spec and spec["min"] is not None) or ("max" in spec and spec["max"] is not None):
                par.limits = [-np.inf, np.inf]
                if "min" in spec and spec["min"] is not None:
                    par.limits[0] = spec["min"]
                if "max" in spec and spec["max"] is not None:
                    par.limits[1] = spec["max"]

            if not spec[FS.TERM_FUNCTION] is None:
                par.set_fcn(framework, spec)

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

        characs = [c for c in self.characs if framework.get_spec_value(c.name, "datapage_order") != -1]
        characs += [c for c in self.comps if framework.get_spec_value(c.name, "datapage_order") != -1]
        #        print(characs)
        comps = [c for c in self.comps if not (c.tag_birth or c.tag_dead)]
        charac_indices = {c.name: i for i, c in enumerate(characs)}  # Make lookup dict for characteristic indices
        comp_indices = {c.name: i for i, c in enumerate(comps)}  # Make lookup dict for compartment indices

        b = np.zeros((len(characs), 1))
        A = np.zeros((len(characs), len(comps)))

        #        print([(c,framework.get_spec_value(c.name,"datapage_order")) for c in self.characs])
        # Construct the characteristic value vector (b) and the includes matrix (A)
        for i, c in enumerate(characs):
            # Look up the characteristic value
            par = parset.get_par(c.name)
            b[i] = par.interpolate(tvec=np.array([t_init]), pop_name=self.name)[0]
            # Run exception clauses for compartment logic.
            try:
                if c.denominator is not None:
                    denom_par = parset.pars['characs'][parset.par_ids['characs'][c.denominator.name]]
                    b[i] *= denom_par.interpolate(tvec=np.array([t_init]), pop_name=self.name)[0]
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
            raise AtomicaException("Residual was {0} which is unacceptably large (should be < {1}). "
                                   "This points to a probable inconsistency in the initial "
                                   "values.".format(residual, model_settings["tolerance"]))

        # Halt for any negative popsizes
        if np.any(np.less(x, -model_settings['tolerance'])):
            raise AtomicaException('Negative initial popsizes')

        # Otherwise, insert the values
        for i, c in enumerate(comps):
            c.vals[0] = max(0.0, x[i])

        for c in self.comps:
            if c.tag_birth or c.tag_dead:
                c.vals[0] = 0

# Model class

class Model(object):
    """ A class to wrap up multiple populations within model and handle cross-population transitions. """

    def __init__(self, settings, framework, parset, progset=None, instructions=None):

        self.pops = list()  # List of population groups that this model subdivides into.
        self.pop_ids = dict()  # Maps name of a population to its position index within populations list.
        self.interactions = dict()
        self.t_index = 0  # Keeps track of array index for current timepoint data within all compartments.

        self.programs_active = None  # True or False depending on whether Programs will be used or not
        self.progset = dcp(progset)
        self.program_instructions = instructions # program instructions
        self.program_cache_comps = None # Dict with {prog_name:[comps reached]}
        self.program_cache_pars = None # Dict with program_pars_reached[par_name][pop]=par to overwrite parameter values
        self.program_cache_coverage = None # Cache coverage numerator

        self.t = None
        self.dt = None
        self.vars_by_pop = None  # Cache to look up lists of variables by name across populations

        self.build(settings, framework, parset)

    def unlink(self):
        # Break cycles when deepcopying or pickling by swapping them for IDs
        # Primary storage is in the comps, links, and outputs properties

        # If we are already unlinked, do nothing
        if self.vars_by_pop is None:
            return

        for pop in self.pops:
            pop.unlink()

        self.vars_by_pop = None
        self.program_cache_comps = None
        self.program_cache_pars = None

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

        if self.vars_by_pop is None:
            self.set_vars_by_pop()

        if self.progset and self.program_instructions:
            self.set_program_cache()

    def set_program_cache(self):
        self.program_cache_comps = {}
        self.program_cache_pars = {}

        for prog in self.progset.programs.values():
            self.program_cache_comps[prog.short] = []

            for pop_name in prog.target_pops:
                for comp_name in prog.target_comps:
                    self.program_cache_comps[prog.short].append(self.get_pop(pop_name).get_comp(comp_name))

        for target_par in prog.target_pars:
            if target_par['param'] not in self.program_cache_pars:
                self.program_cache_pars[target_par['param']] = {}

            self.program_cache_pars[target_par['param']][target_par['pop']] = self.get_pop(target_par['pop']).get_par(target_par['param'])

    def set_vars_by_pop(self):
        self.vars_by_pop = defaultdict(list)
        for pop in self.pops:
            for var in pop.comps + pop.characs + pop.pars + pop.links:
                self.vars_by_pop[var.name].append(var)

    def __getstate__(self):
        self.unlink()
        d = pickle.dumps(self.__dict__, protocol=-1)  # Pickling to string results in a copy
        self.relink()  # Relink, otherwise the original object gets unlinked
        return d

    def __setstate__(self, d):
        self.__dict__ = pickle.loads(d)
        self.relink()

    def get_pop(self, pop_name):
        """ Allow model populations to be retrieved by name rather than index. """
        pop_index = self.pop_ids[pop_name]
        return self.pops[pop_index]


    def build(self, settings, framework, parset):
        """ Build the full model. """

        self.t = settings.tvec  # Note: Class @property method returns a new object each time.
        self.dt = settings.sim_dt

        for k, pop_name in enumerate(parset.pop_names):
            self.pops.append(Population(framework=framework, name=pop_name))
            # TODO: Update preallocate case.
            # Memory is allocated, speeding up model. However, values are NaN to enforce proper parset value saturation.
            self.pops[-1].preallocate(self.t, self.dt)
            self.pop_ids[pop_name] = k
            self.pops[-1].initialize_compartments(parset, framework, self.t[0])

        # Expand interactions into matrix form
        self.interactions = dict()
        for name, weights in parset.interactions.items():
            self.interactions[name] = np.zeros((len(self.pops), len(self.pops), len(self.t)))
            for from_pop, par in weights.items():
                for to_pop in par.pops:
                    self.interactions[name][parset.pop_names.index(from_pop), parset.pop_names.index(to_pop), :] = par.interpolate(self.t, to_pop)

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
                        par.vals = val
                        par.scale_factor = transfer_parameter.y_factor[pop_target]
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

        # Now that all object have been created, update vars_by_pop() accordingly
        self.set_vars_by_pop()

        # Finally, prepare programs
        if self.progset and self.program_instructions:
            self.programs_active = True

            self.set_program_cache() # Cache the parameters and characteristics used for overwriting

            # TODO: Any extra processing of the alloc
            alloc = self.progset.get_alloc(self.program_instructions,self.t)

            # TODO: Any overwrites needed in progset.progs depending on progset_instructions

            self.program_cache_coverage = self.progset.get_num_covered(year=self.t,alloc=alloc)

        else:
            self.programs_active = False

    def process(self, framework):
        """ Run the full model. """

        assert self.t_index == 0  # Only makes sense to process a simulation once, starting at ti=0

        # Make sure initially-filled junctions are processed and initial dependencies are calculated, and calculate
        # initial flow rates
        self.update_pars(framework=framework)
        self.update_junctions()
        self.update_pars(framework=framework)
        self.update_links()

        for t in self.t[1:]:
            self.update_comps()
            self.t_index += 1  # Step the simulation forward
            self.update_junctions()
            self.update_pars(framework=framework)
            self.update_links()

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

    def update_links(self):
        """
        Evolve model characteristics by one timestep (defaulting as 1 year).
        Each application of this method writes calculated values to the next position in popsize arrays.
        This is done regardless of dt.
        Thus the corresponding time vector associated with variable dt steps must be tracked externally.
        This function computes the link flow rates.
        """

        ti = self.t_index

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
                        raise AtomicaException("Encountered unknown quantity type '{0}' during model "
                                               "run.".format(quantity_type))

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
        Set the compartment values at self.t_index+1 based on the current values at self.t_index
        and the link values at self.t_index. Values are updated by iterating over all outgoing links

        """

        ti = self.t_index

        # Pre-populate the current value - need to iterate over pops here because transfers
        # will cross population boundaries
        for pop in self.pops:
            for comp in pop.comps:
                comp.vals[ti + 1] = comp.vals[ti]

        for pop in self.pops:
            for comp in pop.comps:
                if not comp.is_junction:
                    for link in comp.outlinks:
                        link.source.vals[ti + 1] -= link.vals[ti]
                        link.dest.vals[ti + 1] += link.vals[ti]

        # Guard against populations becoming negative due to numerical artifacts
        for pop in self.pops:
            for comp in pop.comps:
                comp.vals[ti + 1] = max(0, comp.vals[ti + 1])

    def update_junctions(self):
        """
        For every compartment considered a junction, propagate the contents onwards.
        Do so until all junctions are empty.
        """

        ti = self.t_index
        ti_link = ti - 1
        if ti_link < 0:
            ti_link = ti  # For the case where junctions are processed immediately after model initialisation.

        review_required = True
        review_count = 0
        while review_required:
            review_count += 1
            review_required = False  # Don't re-run unless a junction has refilled

            if review_count > model_settings["iteration_limit"]:
                raise AtomicaException("Processing junctions (i.e. propagating contents onwards) for timestep {0} "
                                       "is taking far too long. Infinite loop suspected.".format(ti_link))

            for pop in self.pops:
                junctions = [comp for comp in pop.comps if comp.is_junction]

                for junc in junctions:

                    if review_count == 1:
                        for link in junc.outlinks:
                            link.vals[ti_link] = 0

                    # If the compartment is numerically empty, make it empty
                    if junc.vals[ti] <= model_settings['tolerance']:  # Includes negative values.
                        junc.vals[ti] = 0
                    else:
                        current_size = junc.vals[ti]
                        # This is the total fraction of people requested to leave.
                        # Outflows are scaled to the entire compartment size.
                        denom_val = sum(link.parameter.vals[ti_link] for link in junc.outlinks)
                        if denom_val == 0:
                            raise AtomicaException("ERROR: Proportions for junction '{0}' outflows sum to zero, "
                                                   "resulting in a nonsensical ratio. There may even be (invalidly) "
                                                   "no outgoing transitions for this junction.".format(junc.name))
                        for link in junc.outlinks:
                            flow = current_size * link.parameter.vals[ti_link] / denom_val
                            link.source.vals[ti] -= flow
                            link.dest.vals[ti] += flow
                            link.vals[ti_link] += flow
                            if link.dest.is_junction:
                                review_required = True  # Need to review if a junction received an inflow at this step

    def update_pars(self, framework):
        """
        Run through all parameters and characteristics flagged as dependencies for custom-function parameters.
        Evaluate them for the current timestep.
        These dependencies must be calculated in the same order as defined in settings.
        This also means characteristics before parameters, otherwise references may break.
        Also, parameters in dependency list do not need calculation unless explicitly depending on another parameter.
        Parameters that have special rules are usually dependent on other population values, so are included here.
        """

        ti = self.t_index

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
            prop_covered = dict.fromkeys(self.program_cache_comps, 0.0)
            for k,comp_list in self.program_cache_comps.items():
                n = 0.0
                for comp in comp_list:
                    n += comp.vals[ti]
                prop_covered[k] = np.minimum(self.program_cache_coverage[k][ti]/n,1.)

            # Compute the updated program values
            prog_vals = self.progset.get_outcomes(prop_covered)

        # TODO: Remember to involve program impact parameters that are not already marked as functions here.
        for par_name in framework.specs[FS.KEY_PARAMETER].keys(): # FS.PARAMETER
            # All of the parameters with this name, across populations.
            # There should be one for each population (these are Parameters, not Links).
            pars = self.vars_by_pop[par_name]

            # First - update parameters that are dependencies, evaluating f_stack if required
            for par in pars:
                if par.dependency:
                    par.update(ti)

            # Then overwrite with program values
            if do_program_overwrite:
                for par in pars:
                    if par.name in prog_vals and par.pop.name in prog_vals[par.name]:
                        par.vals[ti] = prog_vals[par.name][par.pop.name]
                    else:
                        break

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
                    par.vals[ti] = val

            # Restrict the parameter's value if a limiting range was defined
            for par in pars:
                par.constrain(ti)


def run_model(settings, framework, parset, progset=None, progset_instructions=None, name=None):
    """
    Processes the TB epidemiological model.
    Parset-based overwrites are generally done externally, so the parset is only used for model-building.
    Progset-based overwrites take place internally and must be part of the processing step.
    The instructions dictionary is usually passed in with progset to specify when the overwrites take place.
    """

    m = Model(settings, framework, parset, progset, progset_instructions)
    m.process(framework)
    # TODO: Pass progset and instructions into results just like parset.
    return Result(model=m, parset=parset, name=name)
