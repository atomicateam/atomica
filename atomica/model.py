# %% Imports

from optima_tb.utils import OptimaException # CK: warning, should remove
from optima_tb.validation import checkTransitionFraction
import optima_tb.settings as project_settings
from optima_tb.results import ResultSet
from optima_tb.parsing import FunctionParser
from optima_tb.ModelPrograms import ModelProgramSet, ModelProgram
from collections import defaultdict # CK: warning, should probably remove
from sciris.utils import odict

import logging
logger = logging.getLogger(__name__)
parser = FunctionParser(debug=False)  # Decomposes and evaluates functions written as strings, in accordance with a grammar defined within the parser object.

import numpy as np
from copy import deepcopy as dcp
import uuid

import matplotlib.pyplot as plt

# np.seterr(all='raise')
# %% Abstract classes used in model

class ModelCompartment(object):
    pass


class Node(object):
    ''' Lightweight abstract class to represent one object within a network. '''
    def __init__(self, label='default'):
        self.uid = uuid.uuid4()
        self.label = label          # Reference name for this object.
        # self.index = index          # Index to denote storage position in Model object. Format is left unspecified.
        #                             # For a ModelPopulation, this is intended as an integer.
        #                             # For a Compartment, this is intended as a tuple with first element denoting index of ModelPopulation.

class Variable(object):
    '''
    Lightweight abstract class to store a variable array of values (presumably corresponding to an external time vector).
    Includes an attribute to describe the format of these values.
    Examples include characteristics and dependent parameters (NB. all non-dependents parameter correspond to links)
    '''
    def __init__(self, label='default'):
        self.uid = uuid.uuid4()
        self.label = label
        self.t = None
        self.dt = None
        self.vals = None
        self.vals_old = None                # An optional array that stores old values in the case of overwriting.
        self.units = 'unknown'              # 'unknown' units are distinct to dimensionless units, that have value ''

    def preallocate(self,tvec,dt):
        self.t = tvec
        self.dt = dt
        self.vals = np.ones(tvec.shape) * np.nan
        self.vals_old = np.ones(tvec.shape) * np.nan

    def plot(self):
        plt.figure()
        d = self.__dict__
        for label,val in d.items():
            if isinstance(val,np.ndarray) and val is not self.t and val.size == self.t.size:
                plt.plot(self.t,val,label=label)
        plt.legend()
        plt.xlabel('Year')
        plt.ylabel("%s (%s)" % (self.label,self.units))

    def update(self,ti=None):
        # A Variable can have a function to update its value at a given time, which is
        # overloaded differently for Characteristics and Parameters
        return

    def unlink(self):
        # A Variable has an unlink function that replaces all of its internal references 
        # with the corresponding object UUID
        for prop in self.__dict__.keys():
            if isinstance(self.__dict__[prop],list):
                for i,obj in enumerate(self.__dict__[prop]):
                    if hasattr(obj,'uid'):
                        self.__dict__[prop][i] = obj.uid
            else:
                obj = self.__dict__[prop]
                if hasattr(obj,'uid'):
                    self.__dict__[prop] = obj.uid

    def relink(self,objs):
        # Given a dictionary of objects, restore the internal references
        # based on the UUID
        for prop in self.__dict__.keys():
            if prop == 'uid':
                continue
            elif isinstance(self.__dict__[prop],list):
                for i,obj in enumerate(self.__dict__[prop]):
                    if isinstance(obj,uuid.UUID):
                        self.__dict__[prop][i] = objs[obj]
            else:
                obj = self.__dict__[prop]
                if isinstance(obj,uuid.UUID):
                    self.__dict__[prop] = objs[obj]

    def set_dependent(self):
        # Make the variable a dependency. For Compartments and Links, this does nothing. For Characteristics and
        # Parameters, it will set the dependent flag, but in addition, any validation constraints e.g. a Parameter
        # that depends on Links cannot itself be a dependency, will be enforced
        return

    def __repr__(self):
        return '%s "%s" (%s)' % (self.__class__.__name__,self.label,self.uid)

class Compartment(Variable):
    ''' A class to wrap up data for one compartment within a cascade network. '''

    def __init__(self, label='default'):
        Variable.__init__(self, label=label)
        self.units = 'people'
        self.tag_birth = False                      # Tag for whether this compartment contains unborn people.
        self.tag_dead = False                       # Tag for whether this compartment contains dead people.
        self.is_junction = False

        self.outlinks = []
        self.inlinks = []

    def __repr__(self, *args, **kwargs):
        return "Compartment %s: %g" % (self.label, self.vals[0])

    def getValue(self, ti):
        """ Get value of population at timestep ti """
        return self.vals[ti]

class Characteristic(Variable):
    ''' A characteristic represents a grouping of compartments 
    '''
    def __init__(self, label='default'):
        # includes is a list of Compartments, whose values are summed
        # the denominator is another Characteristic that normalizes this one
        # All passed by reference so minimal performance impact
        Variable.__init__(self, label=label)
        self.units = 'people'
        self.includes = []
        self.denominator = None
        self.dependency = False # This flag indicates whether another variable depends on this one, indicating the value needs to be computed during integration

    def set_dependent(self):
        self.dependency = True

    def add_include(self,x):
        assert isinstance(x,Compartment) or isinstance(x,Characteristic)
        self.includes.append(x)
        x.set_dependent()

    def add_denom(self,x):
        assert isinstance(x,Compartment) or isinstance(x,Characteristic)
        self.denominator = x
        x.set_dependent()
        self.units = ''

    def update(self,ti=None):
        # Read popsizes at time ti from includes, and update the value of this characteristic
        # If ti is none, then use all vals
        if ti is None:
            ti = np.arange(0,self.vals.size) # This corresponds to every time point
        else:
            ti = np.array(ti).ravel()

        self.vals[ti] = 0

        for comp in self.includes:
            self.vals[ti] += comp.vals[ti]

        if self.denominator is not None:
            denom  = self.denominator.vals[[ti]]

            ## Todo - do this better!
            for i in xrange(0,ti.size):
                if denom[i] > 0:
                    self.vals[ti[i]] /= denom[i]
                elif self.vals[ti[i]] < project_settings.TOLERANCE:
                    self.vals[ti[i]] = 0  # Given a zero/zero case, make the answer zero.
                else:
                    self.vals[ti[i]] = np.inf  # Given a non-zero/zero case, keep the answer infinite.
    
class Parameter(Variable):
    # A parameter is a Variable that can have a value computed via an f_stack and a list of 
    # dependent Variables. This class may need to be renamed to avoid confusion with
    # the class in Parameter.py which provides a means of computing the Parameter that is used by the model.
    # This is a Parameter in the cascade.xlsx sense - there is one Parameter object for every item in the 
    # Parameters sheet. A parameter that maps to multiple transitions (e.g. doth_rate) will have one parameter
    # and multiple Link instances that depend on the same Parameter instance
    #
    #  *** Parameter values are always annualized ***
    def __init__(self, label='default'):
        Variable.__init__(self, label=label)
        self.deps = None
        self.f_stack = None
        self.limits = None # Can be a two element vector [min,max]
        self.dependency = False 
        self.scale_factor = 1.0
        self.links = [] # References to links that derive from this parameter
        self.source_popsize_cache_time = None
        self.source_popsize_cache_val = None

    def set_f_stack(self,f_stack,deps):
        self.f_stack = f_stack
        self.deps = deps
        if self.links: # We only need to set dependencies if this is a Transition parameter and thus dependencies must be evaluated during integration
            for dep in deps:
                if isinstance(dep,Link):
                    raise OptimaException('A transition parameter cannot itself depend on a transition tag')
                dep.set_dependent()

    def set_dependent(self):
        self.dependency = True
        if self.deps is not None:
            for dep in self.deps:
                if isinstance(dep,Link):
                    raise OptimaException('A Parameter that depends on transition flow rates cannot be a dependency, it must be output only')

    def constrain(self,ti):
        # NB. Must be an array, so ti must must not be supplied
        if self.limits is not None:
            self.vals[ti] = max(self.limits[0],self.vals[ti])
            self.vals[ti] = min(self.limits[1],self.vals[ti])

    def update(self,ti=None):
        # Update the value of this Parameter at time index ti
        # by evaluating its f_stack function using the 
        # current values of all dependent variables at time index ti
        if ti is None:
            ti = np.arange(0,self.vals.size) # This corresponds to every time point
        else:
            ti = np.array(ti)

        if self.f_stack is None:
            return

        dep_vals = defaultdict(np.float64)
        for dep in self.deps:
            if isinstance(dep,Link):
                dep_vals[dep.label] += dep.vals[[ti]]/dep.dt
            else:
                dep_vals[dep.label] += dep.vals[[ti]]
        self.vals[ti] = parser.evaluateStack(stack=self.f_stack[0:], deps=dep_vals)   # self.f_stack[0:] makes a copy

    def source_popsize(self,ti):
        # Get the total number of people covered by this program
        # i.e. the sum of the source compartments of all links that
        # derive from this program
        # If impact_labels is specified, it must be a list of link labels
        # Then only links whose label is in that list will be included
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
    '''
    A Link is a Variable that maps to a transition between compartments. As
    such, it contains an inflow and outflow compartment.  A Link's value is
    drawn from a Parameter, and there may be multiple links that draw values
    from the same parameter. The values stored in this extended version of
    Variable refer to flow rates. If used in ModelPop, the Link references two
    cascade compartments within a single population.
    '''
    #
    # *** Link values are always dt-based ***
    def __init__(self, parameter, object_from, object_to,tag,is_transfer=False):
        # Note that the Link's label is the transition tag
        Variable.__init__(self, label=tag)
        self.tag = tag
        self.units = 'people'

        self.parameter = parameter # Source parameter where the unscaled link value is drawn from (a single parameter may have multiple links)
        self.parameter.dependency = True # A transition parameter must be updated during integration

        self.source = object_from # Compartment to remove people from
        self.dest = object_to # Compartment to add people to

        # Wire up references to this object
        self.parameter.links.append(self)
        self.source.outlinks.append(self)
        self.dest.inlinks.append(self)

        self.is_transfer = is_transfer # A transfer connections compartments across populations
        
        # Link vals stores the number of people actually transferred
        # The target flow also stores for each time point, the number of people proposed to move
        # The original parameter value is available from the Link's bound parameter
        self.target_flow = None # For each time point, store the number of people that were proposed to move (in units of number of people)
        
    def __repr__(self, *args, **kwargs):
        return "Link %s (parameter %s) - %s to %s" % (self.label, self.parameter.label, self.source.label, self.dest.label)

    def preallocate(self,tvec,dt):
        Variable.preallocate(self, tvec,dt)
        self.target_flow = np.ones(tvec.shape) * np.nan

    def plot(self):
        Variable.plot(self)
        plt.title('Link %s to %s' % (self.source.label,self.dest.label))

# %% Cascade compartment and population classes
class ModelPopulation(Node):
    '''
    A class to wrap up data for one population within model.
    Each model population must contain a set of compartments with equivalent labels.
    '''

    def __init__(self, settings, label='default'):
        Node.__init__(self, label=label)
        self.comps = list()         # List of cascade compartments that this model population subdivides into.
        self.characs = list()       # List of output characteristics and parameters (dependencies computed during integration, pure outputs added after)
        self.links = list()         # List of intra-population cascade transitions within this model population.
        self.pars = list()
        
        self.comp_lookup = dict()      # Maps label of a compartment to a compartment
        self.charac_lookup = dict()
        self.par_lookup= dict()
        self.link_lookup = dict() # Map label of Link to a list of Links with that label

        self.genCascade(settings=settings)    # Convert compartmental cascade into lists of compartment and link objects.

    def __repr__(self):
        return '%s "%s" (%s)' % (self.__class__.__name__,self.label,self.uid)

    def unlink(self):
        for obj in self.comps + self.characs + self.pars + self.links:
            obj.unlink()
        self.comp_lookup = None
        self.charac_lookup = None
        self.par_lookup = None
        self.link_lookup = None

    def relink(self,objs):
        for obj in self.comps + self.characs + self.pars + self.links:
            obj.relink(objs)
        self.comp_lookup = {comp.label:comp for comp in self.comps}
        self.charac_lookup = {charac.label:charac for charac in self.characs}
        self.par_lookup = {par.label:par for par in self.pars}
        link_labels = set([link.label for link in self.links])
        self.link_lookup = {label:[link for link in self.links if link.label == label] for label in link_labels}

    def popsize(self,ti=None):
        # A population's popsize is the sum of all of the people in its compartments, excluding
        # birth and death compartments
        n = 0
        for comp in self.comps:
            if not comp.tag_birth and not comp.tag_dead:
                n += comp.vals[ti]
        return n.ravel()

    def getVariable(self,label):
        # Returns a list of variables whose label matches the requested label
        # At the moment, labels are unique across object types and within object
        # types except for links, but if that logic changes, simple modifications can
        # be made here
        if label in self.comp_lookup:
            return [self.comp_lookup[label]]
        elif label in self.charac_lookup:
            return [self.charac_lookup[label]]
        elif label in self.par_lookup:
            return [self.par_lookup[label]]
        elif label in self.link_lookup:
            return self.link_lookup[label]
        else:
            raise OptimaException('Object %s not found' % (label))

    def getComp(self, comp_label):
        ''' Allow compartments to be retrieved by label rather than index. Returns a Compartment. '''
        return self.comp_lookup[comp_label]

    def getLinks(self, par_label):
        ''' Retrieve Links associated with a Parameter label e.g. 'doth_rate' would return all of the associated Links '''
        # As opposed to getVariable which would retrieve the Parameter for 'doth rate' and the Links for 'z'
        par = self.getPar(par_label)
        return par.links

    def getCharac(self, charac_label):
        ''' Allow dependencies to be retrieved by label rather than index. Returns a Variable. '''
        return self.charac_lookup[charac_label]

    def getPar(self, par_label):
        ''' Allow dependencies to be retrieved by label rather than index. Returns a Variable. '''
        return self.par_lookup[par_label]

    def genCascade(self, settings):
        '''
        Generate a compartmental cascade as defined in a settings object.
        Fill out the compartment, transition and dependency lists within the model population object.
        Maintaining order as defined in a cascade workbook is crucial due to cross-referencing.
        '''

        # Instantiate Compartments
        for label,spec in settings.node_specs.items():
            self.comps.append(Compartment(label=label))
            if 'tag_birth' in spec:
                self.comps[-1].tag_birth = True
            if 'tag_dead' in spec:
                self.comps[-1].tag_dead = True
            if 'junction' in spec:
                self.comps[-1].is_junction = True
        self.comp_lookup = {comp.label:comp for comp in self.comps}

        # Characteristics first pass, instantiate objects
        for label in settings.charac_specs:
            self.characs.append(Characteristic(label=label))
        self.charac_lookup = {charac.label:charac for charac in self.characs}

        # Characteristics second pass, add includes and denominator
        for label,spec in settings.charac_specs.items():
            charac = self.getCharac(label)
            for inc_label in spec['includes']:
                charac.add_include(self.getVariable(inc_label)[0]) # nb. We expect to only get one match for the label, so use index 0
            if 'denom' in spec:
                charac.add_denom(self.getVariable(spec['denom'])[0])

        # Parameters first pass, create parameter objects and links
        for label,spec in settings.linkpar_specs.items():
            par = Parameter(label=label)
            self.pars.append(par)
            if 'tag' in settings.linkpar_specs[label]:
                tag = settings.linkpar_specs[label]['tag']
                for pair in settings.links[tag]:
                    src = self.getComp(pair[0])
                    dst = self.getComp(pair[1])
                    new_link = Link(par,src,dst,tag) # The link needs to be labelled with the Parameter it derives from so that Results can find it later
                    if tag not in self.link_lookup:
                        self.link_lookup[tag] = [new_link]
                    else:
                        self.link_lookup[tag].append(new_link)
                    self.links.append(new_link)
        self.par_lookup = {par.label:par for par in self.pars}

        # Parameters second pass, process f_stacks, deps, and limits
        for label,spec in settings.linkpar_specs.items():
            par = self.getPar(label)

            if ('min' in spec) or ('max' in spec):
                par.limits = [-np.inf, np.inf]
                if 'min' in spec:
                    par.limits[0] = spec['min']
                if 'max' in spec:
                    par.limits[1] = spec['max']

            if 'f_stack' in spec:
                f_stack = dcp(spec['f_stack'])
                deps = []
                for dep_label in spec['deps']:
                    deps += self.getVariable(dep_label)
                par.set_f_stack(f_stack,deps)

    def preAllocate(self, sim_settings):
        '''
        Pre-allocate variable arrays in compartments, links and dependent variables for faster processing.
        Array maintains initial value but pre-fills everything else with NaNs.
        Thus errors due to incorrect parset value saturation should be obvious from results.
        '''
        for obj in self.comps + self.characs + self.links + self.pars:
            obj.preallocate(tvec=sim_settings['tvec'],dt=sim_settings['tvec_dt'])

    def initialize_compartments(self,parset,settings,t_init):
        # Given a set of characteristics and their initial values, compute the initial
        # values for the compartments by solving the set of characteristics simultaneously

        characs = [c for c in self.characs if settings.charac_specs[c.label]['databook_order']!=-1]
        comps = [c for c in self.comps if not (c.tag_birth or c.tag_dead)]
        charac_indices = {c.label:i for i,c in enumerate(characs)} # Make lookup dict for characteristic indices
        comp_indices = {c.label:i for i,c in enumerate(comps)} # Make lookup dict for compartment indices

        b = np.zeros((len(characs),1))
        A = np.zeros((len(characs),len(comps)))

        def extract_includes(charac):
            includes = []
            for inc in charac.includes:
                if isinstance(inc,Characteristic):
                    includes += extract_includes(inc)
                else:
                    includes.append(inc)
            return includes

        # Construct the characteristic value vector (b) and the includes matrix (A)
        for i,c in enumerate(characs):
            # Look up the characteristic value
            par = parset.pars['characs'][parset.par_ids['characs'][c.label]]
            b[i] = par.interpolate(tvec=np.array([t_init]), pop_label=self.label)[0]
            if c.denominator is not None:
                denom_par = parset.pars['characs'][parset.par_ids['characs'][c.denominator.label]]
                b[i] *= denom_par.interpolate(tvec=np.array([t_init]), pop_label=self.label)[0]
            for inc in extract_includes(c):
                A[i,comp_indices[inc.label]] = 1.0

        # Solve the linear system
        x, residual, rank, _ = np.linalg.lstsq(A,b,rcond=-1)

        # Halt if the solution is not unique (could relax this check later)
        if rank < A.shape[1]:
            raise OptimaException('Characteristics are not full rank, cannot determine a unique initialization')

        # Print warning for characteristics that are not well matched by the compartment size solution
        proposed = np.matmul(A,x)
        for i in xrange(0,len(characs)):
            if abs(proposed[i]-b[i]) > project_settings.TOLERANCE:
                logger.warn('Characteristic %s %s - Requested %f, Calculated %f' % (self.label,characs[i].label,b[i],proposed[i]))
        
        # Print diagnostic output for compartments that were assigned a negative value
        def report_characteristic(charac,n_indent=0):
            if charac.label in charac_indices:
                logger.warn(n_indent * '\t' + 'Characteristic %s: Target value = %f' % (charac.label,b[charac_indices[charac.label]]))
            else:
                logger.warn(n_indent * '\t' + 'Characteristic %s not in databook: Target value = N/A (0.0)' % (charac.label))

            n_indent += 1
            for inc in charac.includes:
                if isinstance(inc,Characteristic):
                    report_characteristic(inc,n_indent)
                else:
                    logger.warn(n_indent * '\t' + 'Compartment %s: Computed value = %f' % (inc.label,x[comp_indices[inc.label]]))

        for i in xrange(0, len(comps)):
            if x[i] < -project_settings.TOLERANCE:
                logger.warn('Compartment %s %s - Calculated %f' % (self.label, comps[i].label, x[i]))
                for charac in characs:
                    if comps[i] in extract_includes(charac):
                        report_characteristic(charac)


        # Halt for an unsatisfactory overall solution (could relax this check later)
        if residual > project_settings.TOLERANCE:
            raise OptimaException('Residual was %f which is unacceptably large (should be < %f) - this points to a probable inconsistency in the initial values' % (residual,project_settings.TOLERANCE))

        # Halt for any negative popsizes
        if np.any(x < -project_settings.TOLERANCE):
            raise OptimaException('Negative initial popsizes')

        # Otherwise, insert the values
        for i,c in enumerate(comps):
            c.vals[0] = max(0.0,x[i])

# %% Model class
class Model(object):
    ''' A class to wrap up multiple populations within model and handle cross-population transitions. '''

    def __init__(self):

        self.pops = list()              # List of population groups that this model subdivides into.
        self.pop_ids = dict()           # Maps label of a population to its position index within populations list.
        self.contacts = dict()          # Maps interactions 'from' (i.e. a->b for [a][b]) and 'into' (i.e. a<-b for [a][b]) ModelPopulations, marking them with a weight.
        self.sim_settings = odict()
        self.t_index = 0                # Keeps track of array index for current timepoint data within all compartments.
        self.programs_active = None     # True or False depending on whether Programs will be used or not
        self.pset = None                # Instance of ModelProgramSet

    def unlink(self):
        # Break cycles when deepcopying or pickling by swapping them for UIDs
        # Primary storage is in the comps, links, and outputs properties
        for pop in self.pops:
            pop.unlink()
        if self.pset is not None:
            self.pset.unlink()
        self.pars_by_pop = None

    def relink(self):
        # Need to enumerate objects at Model level because transitions link across pops
        objs = {}
        for pop in self.pops:
            for obj in pop.comps + pop.characs + pop.pars + pop.links:
                objs[obj.uid] = obj

        for pop in self.pops:
            pop.relink(objs)

        self.pars_by_pop = dict()
        for pop in self.pops:
            for par in pop.pars:
                if par.label in self.pars_by_pop:
                    self.pars_by_pop[par.label].append(par)
                else:
                    self.pars_by_pop[par.label] = [par]

        if self.pset is not None:
            self.pset.relink(objs)

    def __getstate__(self):
        self.unlink()
        d = dcp(self.__dict__) # Deepcopy so that relinking doesn't modify the originals
        self.relink() # Relink, otherwise the original object gets unlinked
        return d

    def __setstate__(self, d):
        self.__dict__ = d
        self.relink()

    def getPop(self, pop_label):
        ''' Allow model populations to be retrieved by label rather than index. '''
        pop_index = self.pop_ids[pop_label]
        return self.pops[pop_index]

    def build(self, settings, parset, progset=None, options=None):
        ''' Build the full model. '''

        if options is None: options = dict()

        self.sim_settings['tvec'] = settings.tvec # NB. returning a mutable variable in a class @property method returns a new object each time
        self.sim_settings['tvec_dt'] = settings.tvec_dt

        self.sim_settings['impact_pars_not_func'] = []      # Program impact parameters that are not functions of other parameters and thus already marked for dynamic updating.
                                                            # This is only non-empty if a progset is being used in the model.
        parser.debug = settings.parser_debug

        for k, pop_label in enumerate(parset.pop_labels):
            self.pops.append(ModelPopulation(settings=settings, label=pop_label))
            self.pops[-1].preAllocate(self.sim_settings)     # Memory is allocated, speeding up model. However, values are NaN so as to enforce proper parset value saturation.
            self.pop_ids[pop_label] = k
            self.pops[-1].initialize_compartments(parset,settings,self.sim_settings['tvec'][0])

        self.contacts = dcp(parset.contacts)    # Simple propagation of interaction details from parset to model.

        # Propagating cascade parameter parset values into ModelPops. Handle both 'tagged' links and 'untagged' dependencies.
        for cascade_par in parset.pars['cascade']:
            for pop_label in parset.pop_labels:
                pop = self.getPop(pop_label)
                par = pop.getPar(cascade_par.label) # Find the parameter with the requested label
                par.vals = cascade_par.interpolate(tvec=self.sim_settings['tvec'], pop_label=pop_label)
                par.scale_factor = cascade_par.y_factor[pop_label]
                if par.links:
                    par.units = cascade_par.y_format[pop_label]

        # Propagating transfer parameter parset values into Model object.
        # For each population pair, instantiate a Parameter with the values from the databook
        # For each compartment, instantiate a set of Links that all derive from that Parameter
        # NB. If a Program somehow targets the transfer parameter, those values will automatically
        for trans_type in parset.transfers:
            if parset.transfers[trans_type]:
                for pop_source in parset.transfers[trans_type]:

                    transfer_parameter = parset.transfers[trans_type][pop_source] # This contains the data for all of the destrination pops

                    pop = self.getPop(pop_source)


                    for pop_target in transfer_parameter.y:

                        # Create the parameter object for this link (shared across all compartments)
                        par_label = trans_type + '_' + pop_source + '_to_' + pop_target # e.g. 'aging_0-4_to_15-64'
                        par = Parameter(label=par_label)
                        par.preallocate(self.sim_settings['tvec'],self.sim_settings['tvec_dt'])
                        val = transfer_parameter.interpolate(tvec=self.sim_settings['tvec'], pop_label=pop_target)
                        par.vals = val
                        par.scale_factor = transfer_parameter.y_factor[pop_target]
                        par.units = transfer_parameter.y_format[pop_target]
                        pop.pars.append(par)
                        pop.par_lookup[par_label] = par

                        target_pop_obj = self.getPop(pop_target)

                        for source in pop.comps:
                            if not (source.tag_birth or source.tag_dead or source.is_junction):
                                # Instantiate a link between corresponding compartments
                                dest = target_pop_obj.getComp(source.label) # Get the corresponding compartment
                                link_tag = par_label + '_' + source.label # e.g. 'aging_0-4_to_15-64_sus'
                                link = Link(par, source, dest, link_tag, is_transfer=True)
                                link.preallocate(self.sim_settings['tvec'],self.sim_settings['tvec_dt'])
                                pop.links.append(link)
                                if link.label in pop.link_lookup:
                                    pop.link_lookup[link.label].append(link)
                                else:
                                    pop.link_lookup[link.label] = [link]

        # # Make a lookup dict for programs
        self.pars_by_pop = {}
        for pop in self.pops:
            for par in pop.pars:
                if par.label in self.pars_by_pop:
                    self.pars_by_pop[par.label].append(par)
                else:
                    self.pars_by_pop[par.label] = [par]

        # Finally, prepare ModelProgramSet helper if programs are going to be used
        if 'progs_start' in options:
            if progset is not None:
                self.programs_active = True
                self.sim_settings['progs_start'] = options['progs_start']

                if 'progs_end' in options:
                    self.sim_settings['progs_end'] = options['progs_end']
                else:
                    self.sim_settings['progs_end'] = np.inf # Neverending programs
                if 'init_alloc' in options:
                    self.sim_settings['init_alloc'] = options['init_alloc']
                else: self.sim_settings['init_alloc'] = {}
                if 'constraints' in options:
                    self.sim_settings['constraints'] = options['constraints']
                else:
                    self.sim_settings['constraints'] = None
                if 'alloc_is_coverage' in options:
                    self.sim_settings['alloc_is_coverage'] = options['alloc_is_coverage']
                else: self.sim_settings['alloc_is_coverage'] = False
                if 'saturate_with_default_budgets' in options:
                    self.sim_settings['saturate_with_default_budgets'] = options['saturate_with_default_budgets']
                for impact_label in progset.impacts:
                    if impact_label not in settings.par_funcs:
                        self.sim_settings['impact_pars_not_func'].append(impact_label)

                self.pset = ModelProgramSet(progset,self.pops) # Make a ModelProgramSet wrapper
                self.pset.load_constraints(self.sim_settings['constraints'])
                alloc = self.pset.get_alloc(self.sim_settings)[0]
                self.pset.update_cache(alloc,self.sim_settings['tvec'],self.sim_settings['tvec_dt']) # Perform precomputations

            else:
                raise OptimaException('ERROR: A model run was initiated with instructions to activate programs, but no program set was passed to the model.')
        else:
            self.programs_active = False

        # Make sure initially-filled junctions are processed and initial dependencies are calculated.
        self.updateValues(settings=settings, do_special=False)     # Done first just in case junctions are dependent on characteristics.
                                                                                                # No special rules are applied at this stage, otherwise calculations would be iterated twice before the first step forward.
                                                                                                # NOTE: If junction outflows were to be tagged by special rules, initial calculations may be off. Return to this later and consider logic rigorously.
        self.processJunctions(settings=settings)
        self.updateValues(settings=settings)


        # set up sim_settings for later use wrt population tags
        self.sim_settings['tag_birth'] = []
        self.sim_settings['tag_death'] = []
        self.sim_settings['tag_no_plot'] = []
        for node_label in settings.node_specs:
            for tag in ['tag_birth', 'tag_death', 'tag_no_plot']:
                if tag in settings.node_specs[node_label]:
                    self.sim_settings[tag] = node_label

    def process(self, settings, progset=None):
        ''' 
        Run the full model.
        '''

        for t in self.sim_settings['tvec'][1:]:
            self.stepForward(settings=settings, dt=settings.tvec_dt)
            self.processJunctions(settings=settings)
            self.updateValues(settings=settings)

        for pop in self.pops:
            [par.update() for par in pop.pars if not par.dependency]
            [charac.update() for charac in pop.characs if not charac.dependency]

        return self.pops, self.sim_settings

    def stepForward(self, settings, dt=1.0):
        '''
        Evolve model characteristics by one timestep (defaulting as 1 year).
        Each application of this method writes calculated values to the next position in popsize arrays, regardless of dt.
        Thus the corresponding time vector associated with variable dt steps must be tracked externally.
        '''

        ti = self.t_index

        for pop in self.pops:
            for comp in pop.comps:
                comp.vals[ti+1] = comp.vals[ti]

        for pop in self.pops:

            for comp_source in pop.comps:

                if not comp_source.is_junction:  # Junctions collect inflows during this step. They do not process outflows here.

                    outlinks = comp_source.outlinks  # List of outgoing links
                    outflow = np.zeros(len(comp_source.outlinks))  # Outflow for each link # TODO - store in the link objects?

                    for i, link in enumerate(outlinks):

                        # Compute the number of people that are going out of each link
                        transition = link.parameter.vals[ti]

                        if transition == 0.0:
                            # Note that commands below are all multiplicative and thus can't map an initial value of 0.0 to anything
                            # other than a flow rate of 0, so we can abort early here
                            outflow[i] = 0.0
                            link.target_flow[ti] = 0.0
                            continue

                        if link.parameter.scale_factor is not None and link.parameter.scale_factor != project_settings.DO_NOT_SCALE:  # scale factor should be available to be used
                            transition *= link.parameter.scale_factor

                        if link.parameter.units == 'fraction':
                            # check if there are any violations, and if so, deal with them
                            if transition > 1.:
                                transition = checkTransitionFraction(transition, settings.validation)
                            converted_frac = 1 - (1 - transition) ** dt  # A formula for converting from yearly fraction values to the dt equivalent.
                            if link.source.tag_birth:
                                n_alive = 0
                                for p in self.pops:
                                    n_alive += p.getCharac(settings.charac_pop_count).vals[ti]
                                converted_amt = n_alive * converted_frac
                            else:
                                converted_amt = comp_source.vals[ti] * converted_frac
                        elif link.parameter.units == 'number':
                            converted_amt = transition * dt
                            if link.is_transfer:
                                transfer_rescale = comp_source.vals[ti] / pop.getCharac(settings.charac_pop_count).vals[ti]
                                converted_amt *= transfer_rescale
                        else:
                            raise OptimaException('Unknown parameter units! NB. "proportion" links can only appear in junctions')

                        outflow[i] = converted_amt
                        link.target_flow[ti] = converted_amt

                    # Prevent negative population by proportionately downscaling the outflow
                    # if there are insufficient people _currently_ in the compartment
                    # Rescaling is performed if the validation setting is 'avert', otherwise
                    # either a warning will be displayed or an error will be printed
                    if not comp_source.tag_birth and np.sum(outflow) > comp_source.vals[ti]:
                        validation_level = settings.validation['negative_population']

                        if validation_level == project_settings.VALIDATION_AVERT or validation_level == project_settings.VALIDATION_WARN:
                            outflow = outflow / np.sum(outflow) * comp_source.vals[ti]
                        else:
                            warning = "Negative value encountered for: (%s - %s) at ti=%g : popsize = %g, outflow = %g" % (pop.label,comp_source.label,ti,comp_source.vals[ti],sum(outflow))
                            if validation_level == project_settings.VALIDATION_ERROR:
                                raise OptimaException(warning)
                            elif validation_level == project_settings.VALIDATION_WARN:
                                logger.warn(warning)

                    # Apply the flows to the compartments
                    for i, link in enumerate(outlinks):
                        link.dest.vals[ti+1] += outflow[i]
                        link.vals[ti] = outflow[i]

                    comp_source.vals[ti+1] -= np.sum(outflow)


        # Guard against populations becoming negative due to numerical artifacts
        for pop in self.pops:
            for comp in pop.comps:
                comp.vals[ti+1] = max(0,comp.vals[ti+1])

        # Update timestep index.
        self.t_index += 1

    def processJunctions(self, settings):
        '''
        For every compartment considered a junction, propagate the contents onwards until all junctions are empty.
        '''

        ti = self.t_index
        ti_link = ti - 1
        if ti_link < 0: 
            ti_link = ti    # For the case where junctions are processed immediately after model initialisation.

        review_required = True
        review_count = 0
        while review_required:
            review_count += 1
            review_required = False # Don't re-run unless a junction has refilled

            if review_count > settings.recursion_limit:
                raise OptimaException('ERROR: Processing junctions (i.e. propagating contents onwards) for timestep %i is taking far too long. Infinite loop suspected.' % ti_link)

            for pop in self.pops:
                junctions = [comp for comp in pop.comps if comp.is_junction]

                for junc in junctions:

                    # Stores junction popsize values before emptying - so vals_old stores the total number of people that transitioned out of this junction while vals = 0
                    if review_count == 1:
                        junc.vals_old[ti] = junc.vals[ti] # Back up the old value (should have been preallocated)
                    else:
                        # If a junction is being reviewed again, it means that it received inflow before emptying.
                        # Add this inflow to the stored popsize.
                        junc.vals_old[ti] += junc.vals[ti]

                    # If the compartment is numerically empty, make it empty
                    if junc.vals[ti] <= project_settings.TOLERANCE:   # Includes negative values.
                        junc.vals[ti] = 0
                    else:
                        current_size = junc.vals[ti]
                        denom_val = sum(link.parameter.vals[ti_link] for link in junc.outlinks) # This is the total number of people in the outflow compartments, at the previous timestep, used for splitting the outputs
                        if denom_val == 0:
                            raise OptimaException('ERROR: Proportions for junction "%s" outflows sum to zero, resulting in a nonsensical ratio. There may even be (invalidly) no outgoing transitions for this junction.' % junction_label)
                        for link in junc.outlinks:
                            if review_count == 1:
                                link.vals[ti] = 0
                                link.target_flow[ti] = 0
                            flow = current_size * link.parameter.vals[ti_link] / denom_val
                            link.source.vals[ti] -= flow
                            link.dest.vals[ti]   += flow
                            link.vals[ti] += flow
                            link.target_flow[ti] += flow
                            if link.dest.is_junction:
                                review_required = True # Need to review if a junction received an inflow at this step

    def updateValues(self, settings, do_special=True):
        '''
        Run through all parameters and characteristics flagged as dependencies for custom-function parameters and evaluate them for the current timestep.
        These dependencies must be calculated in the same order as defined in settings, characteristics before parameters, otherwise references may break.
        Also, parameters in the dependency list do not need to be calculated unless explicitly depending on another parameter.
        Parameters that have special rules are usually dependent on other population values, so are included here.
        '''

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
        # Looping through populations must be internal so that all values are calculated before special inter-population rules are applied.
        # We resolve one parameter at a time, in dependency order
        do_program_overwrite = self.programs_active and self.sim_settings['tvec'][ti] >= self.sim_settings['progs_start'] and self.sim_settings['tvec'][ti] <= self.sim_settings['progs_end']
        if do_program_overwrite:
            prog_vals = self.pset.compute_pars(ti)[0]

        for par_label in (settings.par_funcs.keys() + self.sim_settings['impact_pars_not_func']):
            pars = self.pars_by_pop[par_label] # All of the parameters with this label, across populations. There should be one for each population (these are Parameters, not Links)

            # First - update parameters that are dependencies, evaluating f_stack if required
            for par in pars:
                if par.dependency:
                    par.update(ti)

            # Then overwrite with program values
            if do_program_overwrite:
                for par in pars:
                    if par.uid in prog_vals:
                        par.vals[ti] = prog_vals[par.uid]

            # Handle parameters tagged with special rules. Overwrite vals if necessary.
            if do_special and 'rules' in settings.linkpar_specs[par_label]:
                pars = self.pars_by_pop[par_label]  # All of the parameters with this label, across populations. There should be one for each population (these are Parameters, not Links)

                for par in pars:
                    par.vals_old[ti] = par.vals[ti]

                rule = settings.linkpar_specs[par_label]['rules']
                for pop in self.pops:
                    if rule == 'avg_contacts_in':
                        from_list = self.contacts['into'][pop.label].keys()

                        # If interactions with a pop are initiated by the same pop, no need to proceed with special calculations. Else, carry on.
                        if not ((len(from_list) == 1 and from_list[0] == pop.label)):
                            old_vals = np.ones(len(from_list)) * np.nan
                            weights = np.ones(len(from_list)) * np.nan
                            pop_counts = np.ones(len(from_list)) * np.nan
                            if len(from_list) == 0:
                                new_val = 0.0
                            else:
                                k = 0
                                for from_pop in from_list:
                                    # All transition links with the same par_label are identically valued. For calculations, only one is needed for reference.
                                    par = self.getPop(from_pop).getPar(par_label)
                                    old_vals[k] = par.vals_old[ti]
                                    weights[k] = self.contacts['into'][pop.label][from_pop]
                                    pop_counts[k] = self.getPop(from_pop).getCharac(settings.charac_pop_count).vals[ti]
                                    k += 1
                                wpc = np.multiply(weights, pop_counts)          # Population counts weighted by contact rate.
                                wpc_sum = sum(wpc)                              # Normalisation factor for weighted population counts.
                                if abs(wpc_sum) > project_settings.TOLERANCE:
                                    new_val = np.dot(old_vals, wpc / wpc_sum)         # Do a weighted average of the parameter values pertaining to contact-initiating pop groups.
                                else:
                                    new_val = 0.0   # Only valid because if the weighted sum is zero, all pop_counts must be zero, meaning that the numerator is zero.

                            # Update the parameter's value in this population - will propagate to links in next stage
                            pop.getPar(par_label).vals[ti] = new_val

            # Restrict the parameter's value if a limiting range was defined
            for par in pars:
                par.constrain(ti)

    def calculateOutputs(self, settings):
        '''
        Calculate outputs (called cascade characteristics in settings).
        These outputs must be calculated in the same order as defined in settings, otherwise references may break.
        Include any parameters marked as an output in the cascade sheet.
        Return a dictionary with all of the outputs
        As outputs are all Variables or Characteristics they use the vals property for their value
        '''

        outputs = odict()

        for pop in self.pops:
            for output in pop.pars + pop.characs:
                if output.label not in outputs:
                    outputs[output.label] = odict()
                if pop.label in outputs[output.label]:
                    assert isinstance(output,Link), 'There is a duplicate output label that is NOT a link - this is not supposed to happen'
                    outputs[output.label][pop.label] += output.vals
                else:
                    outputs[output.label][pop.label] = output.vals
        return outputs



def runModel(settings, parset, progset=None, options=None):
    '''
    Processes the TB epidemiological model.
    Parset-based overwrites are generally done externally, so the parset is only used for model-building.
    Progset-based overwrites take place internally and must be part of the processing step.
    The options dictionary is usually passed in with progset to specify when the overwrites take place.
    '''

    m = Model()
    m.build(settings=settings, parset=parset, progset=progset, options=options)
    m.process(settings=settings, progset=progset)

    results = ResultSet(m, parset, settings, progset, options)    # NOTE: Progset may need to be passed to results. Depends on what results object stores.

    return results