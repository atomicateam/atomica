from atomica.system import OptimaException, logger
from sciris.core import uuid, odict, defaultrepr, objrepr
#import optima_tb.settings as project_settings

import numpy as np
from math import ceil, floor
from copy import deepcopy as dcp
from collections import defaultdict

# %% Resultset class that contains one set of results
class ResultSet(object):
    """
    Class to hold one set of Results
    Fields: 
            name               name of result
            parset_name        name (not index) of parset used to create this result set
            parset_id          uuid of relevant parset (in case of duplication or missing parset_name)
            sim_settings       settings for simulation
            pop_labels         population tags for which siumulation was run (e.g. [])
            char_label         characteristics tags for which simulation was run
            ind_observed_data  indices for t that correspond to times at which observed data was collected
                               so that the observed data points can be compared against simulated data
                               using data_observed - data_sim[indices_observed_data]
            t_observed_data    t values for indices_observed_data points
                               popdata_sim        simulated compartment data points (format: ?)
            t_step             t_steps in real time 
            dt                 dt used to create this resultset
            outputs            simulated characteristic data points (format: ?)
            model              simulated model object
            
        Optional: ------------------------------------------------------
            data_observed      datapoints supplied (format: dataset)
            calibration_fit    calibration fit score
            calibration_metric calibration metric used
    
        Example
            if dt = 0.25, and observed data was taken annually
            then 
                indices_observed_data = [0,4,8,..]. This can be determined directly from dt
                t_observed_data       = [2000.,2001.,2002., ...]
    """

    # TODO - remove self.outputs() because everything should be accessible via the model directly?

    def __init__(self, model, parset, settings, progset=None, budget_options=None, name=None):

        self.uuid = uuid()
        if name is None:
            self.name = parset.name
        else:
            self.name = name
        self.parset_name = parset.name
        self.parset_id = parset.uid

        self.dt = settings.tvec_dt
        self.t_step = model.sim_settings['tvec']
        self.indices_observed_data = np.where(self.t_step % 1.0 == 0)
        self.t_observed_data = self.t_step[self.indices_observed_data]

        self.outputs = model.calculateOutputs(settings=settings)

        # Set up for future use
        self.calibration_fit = None
        self.calibration_score = None

        """
        # remaining fields to be set:
        self.popdata_sim
        self.chardata_sim
        self.data_observed
        """

        # work-in-progress: in time, these sections should be removed and only the data
        # points we are interested should be listed
        self.model = dcp(model)

        self.pop_label_index = {}
        for i, pop in enumerate(self.model.pops):
            self.pop_label_index[pop.label] = i

        self.sim_settings = model.sim_settings
        self.pop_labels = [pop.label for pop in model.pops]
        self.comp_labels = settings.node_names
        self.comp_specs = settings.node_specs
        self.comp_label_names = self.__generateLabelNames(self.comp_specs.keys(), self.comp_labels)
        self.char_labels = self.outputs.keys() # definitely need a better way of determining these
        self.link_labels = []
        for pop in model.pops:
            for link in pop.links:
                if link.label not in self.link_labels:
                    self.link_labels.append(link.label)

        self.budgets = {} # placeholders
        self.coverages = {}
        if progset is not None and budget_options is not None:
            budget_options = dcp(budget_options)
#            print [p.label for p in progset.progs]
            # we have results for progsets and budget_options
            if budget_options.has_key('alloc_is_coverage') and budget_options['alloc_is_coverage']: # TODO update post-Belarus
                self.coverages = budget_options['init_alloc']
                self.budgets = progset.getBudgets(self.coverages)
            else:
                self.budgets = budget_options['init_alloc']
                self.coverages = progset.getCoverages(self.budgets)

        # /work-in-progress

    def __repr__(self):
        ''' Print out useful information when called'''
        output = '====================================================================================\n'
        output += objrepr(self)
        return output


#     def extractSimulationData(self):
#         """
#
#         Currently, only extract the simulated data for characteristics, as we should only use
#         this in fitting for calibration.
#         """
#         pass

    def __generateLabelNames(self, labels, names):
        """
        
        Note: this could potentially go in utils or another location, as it's not really 
        specific to results.py. 
        """
        label_names = odict()
        for (i, label) in enumerate(labels):
            label_names[label] = names[i]
        return label_names

    def getValuesAt(self, label, year_init, year_end=None, pop_labels=None, integrated=False):
        """
        Derives transition flow rates, characteristic or compartment values for results, according to label provided.
       
        The range of values correspond to timepoints from year_init (inclusive) to year_end (exclusive).
        In the absence of a year_end, the value corresponding to only the year_init timepoint is returned.
        Values are summed across all population groups unless a subset is specified with pop_labels.
        Values can also be optionally integrated to return a scalar.
        
        Outputs values as array or integrated scalar, as well as the the corresponding timepoints.
        """

        dt = self.dt

        if pop_labels is None:
            pop_labels = self.pop_labels

        # Get time array ids for values between initial (inclusive) and end year (exclusive).
        tvals = np.array(self.sim_settings['tvec'])
        if year_end is None: year_end = year_init + dt
        idx = (tvals >= year_init - dt / 2) * (tvals <= year_end - dt / 2)

        # Initialise output as appropriate array of zeros.
        output = np.zeros(len(tvals[idx]))
        units = ""

        # Find values in results and add them to the output array per relevant population group.
        # TODO: Semantics need to be cleaned during design review phase.
        if label in self.link_labels:

            values = self.getFlow(label, pop_labels=pop_labels)[0]

            for pop in values.keys():
                popvalues = values[pop]
                output += popvalues[idx]

        elif label in self.char_labels:

            values = self.getCharacteristicDatapoints(char_label=label, pop_label=pop_labels, use_observed_times=False)[0]
            values = values[label]

            for pop in values.keys():
                popvalues = values[pop]
                output += popvalues[idx]

        elif label in self.comp_label_names.keys():

            values, _, _, units = self.getCompartmentSizes(comp_label=label, pop_labels=pop_labels, use_observed_times=False)
            for pop in values.keys():
                output += values[pop][label].vals[idx]

        else:
            logger.warn('Unable to find values for label="%s", with no corresponding characteristic, transition or compartment found.' % label)

        # Do a simple integration process if specified by user.
        if integrated:
            output = output.sum() * dt

        return output, tvals[idx], units

    def getCompartmentSizes(self, pop_labels=None, comp_label=None, use_observed_times=False):
        """
        #PopDatapoints
        
        Returns the data points for the simulation, for each compartment, 
        that should correspond to times of the observed data. This method is intended for
        use with calibration. 
        
        [Comment to DK: will we need compartments at all during calibration, scenarios or optimization?
        Possibly for post-hoc analysis, but perhaps it would be worthwhile to assume no, and only
        for some cases should a user - perhaps via a flag in settings - save all data.]
        
        [Intended]
        If pop_id or comp_id are specified, then the method returns the simulated data points for
        just those populations or compartments.
        Otherwise, the simulated data points for all populations and compartments are returned.

        @param pop_id: population id, either as single id or as list
        @param comp_id: compartment id, either as single id or as list
                
        """
        if pop_labels is not None:
            if isinstance(pop_labels, list):
                pops = pop_labels
            else:
                pops = [pop_labels]
        else:
            pops = self.pop_labels

        if comp_label is not None:
            if isinstance(comp_label, list):
                comps = comp_label
            elif isinstance(comp_label, odict):
                comps = comp_label.keys()
            else:
                comps = [comp_label]
        else:
            comps = self.comp_specs.keys()

        # this currently uses odict for the output ...
        datapoints = odict()
        comp_labels = []
        for pi in pops:

            datapoints[pi] = odict()
            p_index = self.pop_label_index[pi]

            for ci, c_label in enumerate(comps):

                comp = self.model.pops[p_index].getComp(c_label)
                if use_observed_times:
                    datapoints[pi][c_label] = comp[self.indices_observed_data]
                else:
                    datapoints[pi][c_label] = comp
                comp_labels.append(c_label)

        units = 'people'

        return datapoints, pops, comps, units


    def getCharacteristicDatapoints(self, pop_label=None, char_label=None, use_observed_times=False):
        """
        Returns the data points for the simulation, for each characteristics, 
        that should correspond to times of the observed data. This method is intended for
        use with calibration. 
        
        [Intended]
        If pop_id or char_id are specified, then the method returns the simulated data points for
        just those populations or compartments.
        Otherwise, the simulated data points for all popuations and compartments are returned.
        
        Param:
             pop_label                          population labels, either as single id or as list
             char_label                         characteristic id, either as single label or as list of labels
             use_observed_times                 boolean flag. If True, returns only datapoints for which there was a corresponding data observation; 
                                                else, returns all characteristic data points
        
        """
        if pop_label is not None:
            if isinstance(pop_label, list):
                pop_labels = pop_label
            else:
                pop_labels = [pop_label]
        else:
            pop_labels = self.pop_labels

        if char_label is not None:
            if isinstance(char_label, list):
                char_labels = char_label
            else:
                char_labels = [char_label]
        else:
            char_labels = self.char_labels

        datapoints = defaultdict(dict)

        for pop_label in pop_labels:
            for char_label in char_labels:
                if use_observed_times:
                    datapoints[char_label][pop_label] = self.outputs[char_label][pop_label][self.indices_observed_data]
                else:
                    datapoints[char_label][pop_label] = self.outputs[char_label][pop_label]

        units = ''

        return datapoints, char_label, pop_label, units


    def getFlow(self, link_tag, pop_labels=None,annualize=True,as_fraction=False):
        """
        Return the flow at each time point in the simulation for a single parameter

        INPUTS
        - par_label : A string specifying a single Parameter to retrieve flow rates for
        - pop_label : A list or list of strings of population labels. If None, use all populations
        - annualize : Boolean which specifies if the number of moved people should be annualized or not. If True, an annual average is computed; if False, the number of people per time step is computed
        - as_fraction : Boolean which specifies if the flow rate should be expressed as a fraction of the source compartment size.
            - If True, the fractional flow rate for each link will be computed by dividing the net flow by the sum of source compartment sizes
            - If None, it will be set to the same value as par.is_fraction for each parameter requested
        For each parameter label, the flow from all links deriving from the parameter will be summed within requested populations. Thus if there are multiple links
        with the same link_label (e.g. a 'doth' link for death by other causes, for which there may be one for every compartment)
        then these will be aggregated

        OUTPUT
        - datapoints : dictionary `datapoints[pop_label]` has an array of flow rate in requested units
        - units : the units of the returned data
        
        Note that the flow rate is linked to the time step by

        popsize[t+1] = popsize[t]+net_flow[t]

        That is, it is the number of people who will transition between t and t+dt (i.e. after the current time)
        """

        if pop_labels is not None:
            if isinstance(pop_labels, list):
                pop_labels = pop_labels
            else:
                pop_labels = [pop_labels]

        datapoints = defaultdict(float)
        source_size = defaultdict(float)

        for pop in self.model.pops:
            if pop_labels is None or pop.label in pop_labels:
                for link in pop.getVariable(link_tag):
                    datapoints[pop.label] += link.vals
                    source_size[pop.label] += (link.source.vals if not link.source.is_junction else link.source.vals_old)

        # If as_fraction is None, use the same units as the Parameter. All Parameters should have the same units
        # in all populations so can use whichever one is left after the loop above
        if as_fraction is None and (par.units == 'fraction' or par.units == 'proportion'):
            as_fraction = True

        if as_fraction:
            units = 'proportion'
            for pop_label in datapoints:
                datapoints[pop_label] /=  source_size[pop_label]
        else:
            units = 'people'

        # If we need to convert from dt units to annualized units
        # If as_fraction is true, then the quantity is a proportion and no further time units are required
        if annualize and not as_fraction:
            units += '/year'
            for pop_label in datapoints:
                datapoints[pop_label] = datapoints[pop_label] * (1.0 / self.dt)
        elif not as_fraction:
            units += '/timestep'

        return datapoints, units


    def export(self, filestem=None, sep=',', writetofile=True, use_alltimesteps=True):
        """
        Export method for characteristics results obtained from a simulation that should correspond 
        to times of the observed data (i.e. annually). This method is intended for use with runSim 
        currently and will be extended to include optimization and scenario results.
        """
        import os

        if filestem is None:  # Doesn't include extension, hence filestem
            filestem = self.name
        filestem = os.path.abspath(filestem)
        filename = filestem + '.csv'


        keys = self.char_labels


        if use_alltimesteps:
            output = sep.join(['Indicator', 'Population'] + ['%g' % t for t in self.t_step]) # Create header and years
            npts = len(self.t_step)
        else:
            output = sep.join(['Indicator', 'Population'] + ['%g' % t for t in self.t_observed_data]) # Create header and years
            npts = len(self.t_observed_data)
        for key in keys:
            output += '\n' # Add a line break between different indicators
            popkeys = self.pop_labels
            for pk, popkey in enumerate(popkeys):
                if popkey in self.outputs[key]:
                    output += '\n'
                    if use_alltimesteps:
                        data = self.outputs[key][popkey]
                    else:
                        data = self.outputs[key][popkey][self.indices_observed_data]

                    output += key + sep + popkey + sep
                    for t in range(npts):
                        output += ('%g' + sep) % data[t]

        if writetofile:
            with open(filename, 'w') as f: f.write(output)
            logger.info('Results exported to "%s"' % (filename))
            return None
        else:
            return output




#"""
#Defines the classes for storing results.
#Version: 2018mar23
#"""
#
#from atomica.system import OptimaException
#from sciris.core import uuid, odict, today, defaultrepr # Printing/file utilities
#from numbers import Number

#class Result(object):
#    ''' Class to hold individual results '''
#    def __init__(self, name=None):
#        self.name = name # Name of this parameter
#    
#    def __repr__(self):
#        ''' Print out useful information when called '''
#        output = defaultrepr(self)
#        return output
#
#
#class Resultset(object):
#    ''' Structure to hold results '''
#    def __init__(self, raw=None, name=None, pars=None, simpars=None, project=None, settings=None, data=None, parsetname=None, progsetname=None, budget=None, coverage=None, budgetyears=None, domake=True, quantiles=None, keepraw=False, verbose=2, doround=True):
#        # Basic info
#        self.created = today()
#        self.name = name if name else 'default' # May be blank if automatically generated, but can be overwritten
#        self.main = odict() # For storing main results
#        self.other = odict() # For storing other results -- not available in the interface
#
#
#class Multiresultset(Resultset):
#    ''' Structure for holding multiple kinds of results, e.g. from an optimization, or scenarios '''
#    def __init__(self, resultsetlist=None, name=None):
#        # Basic info
#        self.name = name if name else 'default'
#        self.created = today()
#        self.nresultsets = len(resultsetlist)
#        self.resultsetnames = [result.name for result in resultsetlist] # Pull the names of the constituent resultsets
#        self.keys = []
#        self.budgets = odict()
#        self.coverages = odict()
#        self.budgetyears = odict() 
#        self.setup = odict() # For storing the setup attributes (e.g. tvec)
#        if type(resultsetlist)==list: pass # It's already a list, carry on
#        elif type(resultsetlist) in [odict, dict]: resultsetlist = resultsetlist.values() # Convert from odict to list
#        elif resultsetlist is None: raise OptimaException('To generate multi-results, you must feed in a list of result sets: none provided')
#        else: raise OptimaException('Resultsetlist type "%s" not understood' % str(type(resultsetlist)))
#
#
#
#def getresults(project=None, pointer=None, die=True):
#    '''
#    Function for returning the results associated with something. 'pointer' can eiher be a UID,
#    a string representation of the UID, the actual pointer to the results, or a function to return the
#    results.
#    
#    Example:
#        results = P.parsets[0].getresults()
#        calls
#        getresults(P, P.parsets[0].resultsref)
#        which returns
#        P.results[P.parsets[0].resultsref]
#    
#    The "die" keyword lets you choose whether a failure to retrieve results returns None or raises an exception.    
#    
#    Version: 1.2 (2016feb06)
#    '''
#    # Nothing supplied, don't try to guess
#    if pointer is None: 
#        return None 
#    
#    # Normal usage, e.g. getresults(P, 3) will retrieve the 3rd set of results
#    elif isinstance(pointer, (str, unicode, Number, type(uuid()))): # CK: warning, should replace with sciris.utils.checktype()
#        if project is not None:
#            resultnames = [res.name for res in project.results.values()]
#            resultuids = [str(res.uid) for res in project.results.values()]
#        else: 
#            if die: raise OptimaException('To get results using a key or index, getresults() must be given the project')
#            else: return None
#        try: # Try using pointer as key -- works if name
#            results = project.results[pointer]
#            return results
#        except: # If that doesn't match, keep going
#            if pointer in resultnames: # Try again to extract it based on the name
#                results = project.results[resultnames.index(pointer)]
#                return results
#            elif str(pointer) in resultuids: # Next, try extracting via the UID
#                results = project.results[resultuids.index(str(pointer))]
#                return results
#            else: # Give up
#                validchoices = ['#%i: name="%s", uid=%s' % (i, resultnames[i], resultuids[i]) for i in range(len(resultnames))]
#                errormsg = 'Could not get result "%s": choices are:\n%s' % (pointer, '\n'.join(validchoices))
#                if die: raise OptimaException(errormsg)
#                else: return None
#    
#    # The pointer is the results object
#    elif isinstance(pointer, (Resultset, Multiresultset)):
#        return pointer # Return pointer directly if it's already a results set
#    
#    # It seems to be some kind of function, so try calling it -- might be useful for the database or something
#    elif callable(pointer): 
#        try: 
#            return pointer()
#        except:
#            if die: raise OptimaException('Results pointer "%s" seems to be callable, but call failed' % str(pointer))
#            else: return None
#    
#    # Could not figure out what to do with it
#    else: 
#        if die: raise OptimaException('Could not retrieve results \n"%s"\n from project \n"%s"' % (pointer, project))
#        else: return None
#        
 