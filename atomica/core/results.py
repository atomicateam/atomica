import numpy as np
import pandas as pd
import sciris.core as sc
from atomica.utils import NamedItem


# import optima_tb.settings as project_settings

class Result(NamedItem):
    # A Result stores a single model run
    def __init__(self, model, parset, name):
        if name is None:
            name = parset.name
        NamedItem.__init__(self,name)


        # The Result constructor is called in model.run_model and the Model is no longer returned.
        # The following should be the only reference to that instance so no need to dcp.
        self.model = model
        self.parset_name = parset.name
        self.parset_id = parset.uid
        self.pop_names = [x.name for x in self.model.pops]  # This gets frequently used, so save it as an actual output

    # Property methods trade off storage space against computation time. The property methods below
    # are cheap to compute or used less frequently, are read-only, and can always be changed to actual
    # later without needing changes in other code that uses Result objects
    @property
    def t(self):
        return self.model.t

    @property
    def dt(self):
        return self.model.dt

    @property
    def indices_observed_data(self):
        return np.where(self.t % 1.0 == 0)

    @property
    def t_observed_data(self):
        return self.t[self.indices_observed_data]

    # Methods to list available comps, characs, pars, and links
    # pop_name is required because different populations could have
    # different contents
    def comp_names(self, pop_name):
        # Return compartment names for a given population
        return sorted(self.model.get_pop(pop_name).comp_lookup.keys())

    def charac_names(self, pop_name):
        # Return characteristic names for a given population
        return sorted(self.model.get_pop(pop_name).charac_lookup.keys())

    def par_names(self, pop_name):
        # Return parteristic names for a given population
        return sorted(self.model.get_pop(pop_name).par_lookup.keys())

    def link_names(self, pop_name):
        # Return link names for a given population
        names = set()
        pop = self.model.get_pop(pop_name)
        for link in pop.links:
            names.add(link.name)
        return sorted(names)

    def __repr__(self):
        """ Print out useful information when called"""
        output = sc.desc(self)
        return output

    def get_variable(self, pops, name):
        # Retrieve a list of variables from a population
        return self.model.get_pop(pops).get_variable(name)

    def export(self, filename=None, ):
        """Convert output to a single DataFrame and optionally write it to a file"""

        # Assemble the outputs into a dict
        d = dict()
        for pop in self.model.pops:
            for comp in pop.comps:
                d[('compartments', pop.name, comp.name)] = comp.vals
            for charac in pop.characs:
                if charac.vals is not None:
                    d[('characteristics', pop.name, charac.name)] = charac.vals
            for par in pop.pars:
                if par.vals is not None:
                    d[('parameters', pop.name, par.name)] = par.vals
            for link in pop.links:
                # Sum over duplicate links and annualize flow rate
                key = ('flow rates', pop.name, link.name)
                if key not in d:
                    d[key] = np.zeros(self.t.shape)
                d[key] += link.vals / self.dt

        # Create DataFrame from dict
        df = pd.DataFrame(d, index=self.t)
        df.index.name = 'Time'

        # Optionally save it
        if filename is not None:
            df.T.to_excel(filename + '.xlsx' if not filename.endswith('.xlsx') else filename)

        return df

# """
# Defines the classes for storing results.
# Version: 2018mar23
# """
#
# from atomica.system import AtomicaException

# class Result(object):
#    ''' Class to hold individual results '''
#    def __init__(self, label=None):
#        self.label = label # label of this parameter
#    
#    def __repr__(self):
#        ''' Print out useful information when called '''
#        output = desc(self)
#        return output
#
#
# class Resultset(object):
#    ''' Structure to hold results '''
#    def __init__(self, raw=None, label=None, pars=None, simpars=None, project=None, settings=None, data=None,
# parsetlabel=None, progsetlabel=None, budget=None, coverage=None, budgetyears=None, domake=True, quantiles=None,
# keepraw=False, verbose=2, doround=True):
#        # Basic info
#        self.created = today()
#        self.label = label if label else 'default' # May be blank if automatically generated, but can be overwritten
#        self.main = odict() # For storing main results
#        self.other = odict() # For storing other results -- not available in the interface
#
#
# class Multiresultset(Resultset):
#    ''' Structure for holding multiple kinds of results, e.g. from an optimization, or scenarios '''
#    def __init__(self, resultsetlist=None, label=None):
#        # Basic info
#        self.label = label if label else 'default'
#        self.created = today()
#        self.nresultsets = len(resultsetlist)
#        self.resultsetlabels = [result.label for result in resultsetlist]
#  Pull the labels of the constituent resultsets
#        self.keys = []
#        self.budgets = odict()
#        self.coverages = odict()
#        self.budgetyears = odict() 
#        self.setup = odict() # For storing the setup attributes (e.g. tvec)
#        if type(resultsetlist)==list: pass # It's already a list, carry on
#        elif type(resultsetlist) in [odict, dict]: resultsetlist = resultsetlist.values() # Convert from odict to list
#        elif resultsetlist is None: raise AtomicaException('To generate multi-results,
# you must feed in a list of result sets: none provided')
#        else: raise AtomicaException('Resultsetlist type "%s" not understood' % str(type(resultsetlist)))
#
#
#
# def getresults(project=None, pointer=None, die=True):
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
#            resultlabels = [res.label for res in project.results.values()]
#            resultuids = [str(res.uid) for res in project.results.values()]
#        else: 
#            if die: raise AtomicaException('To get results using a key or index,
# getresults() must be given the project')
#            else: return None
#        try: # Try using pointer as key -- works if label
#            results = project.results[pointer]
#            return results
#        except: # If that doesn't match, keep going
#            if pointer in resultlabels: # Try again to extract it based on the label
#                results = project.results[resultlabels.index(pointer)]
#                return results
#            elif str(pointer) in resultuids: # Next, try extracting via the UID
#                results = project.results[resultuids.index(str(pointer))]
#                return results
#            else: # Give up
#                validchoices = ['#%i: label="%s", uid=%s' % (i, resultlabels[i], resultuids[i])
# for i in range(len(resultlabels))]
#                errormsg = 'Could not get result "%s": choices are:\n%s' % (pointer, '\n'.join(validchoices))
#                if die: raise AtomicaException(errormsg)
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
#            if die: raise AtomicaException('Results pointer "%s" seems to be callable, but call failed' % str(pointer))
#            else: return None
#    
#    # Could not figure out what to do with it
#    else: 
#        if die: raise AtomicaException('Could not retrieve results \n"%s"\n from project \n"%s"' % (pointer, project))
#        else: return None
#
