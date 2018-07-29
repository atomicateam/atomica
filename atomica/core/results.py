import numpy as np
import pandas as pd
import sciris.core as sc
from .utils import NamedItem
from .system import AtomicaException


# import optima_tb.settings as project_settings

class Result(NamedItem):
    # A Result stores a single model run
    def __init__(self, model, parset, name):
        if name is None:
            name = parset.name
        NamedItem.__init__(self,name)

        self.uid = sc.uuid()

        # The Result constructor is called in model.run_model and the Model is no longer returned.
        # The following should be the only reference to that instance so no need to dcp.
        self.model = model
        self.parset_name = parset.name
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


    def get_cascade_vals(self,cascade_name=None,pops=None):
        '''
        Gets values for populating a cascade plot
        See https://docs.google.com/presentation/d/1lEEyPFORH3UeFpmaxEAGTKyHAbJRnKTm5YIsfV1iJjc/edit?usp=sharing
        Returns an odict with 4 keys:
            vals: a flat odict where the keys are the (ordered) cascade stages and the values are the height of the bars by year
            loss: a flat odict where the keys are the (ordered) cascade stages and the values are tuples consisting of the absolute # and proportion lost by year
            conv: a flat odict where the keys are the (ordered) cascade stages and the values are tuples consisting of the absolute # and proportion converted by year
            t: list of the years
        '''
        if cascade_name is None:
            return
        if project is None:
            errormsg = 'You need to supply a project in order to plot the cascade.'
            raise AtomicaException(errormsg)
            
        cascade = sc.odict()
        cascade['vals'] = sc.odict()
        cascade['loss'] = sc.odict()
        cascade['conv'] = sc.odict()
        F = project.framework
        for sno,stage in enumerate(F.filter['stages']):
            cascade['vals'][stage] = sc.odict()
            cascade['conv'][stage] = sc.odict()
            cascade['loss'][stage] = sc.odict()
            for pno,pop in enumerate(project.pop_names):
                cascade['vals'][stage][pop] = self.get_variable(pop,stage)[0].vals
                cascade['t'] = self.get_variable(pop,stage)[0].t
                if sno > 0:
                    cascade['conv'][stage][pop] = (cascade['vals'][stage][pop], cascade['vals'][sno][pop]/cascade['vals'][sno-1][pop])
                    cascade['loss'][stage][pop] = (cascade['vals'][sno-1][pop]-cascade['vals'][sno][pop], 1.-cascade['conv'][stage][pop][1])
                
        return cascade


