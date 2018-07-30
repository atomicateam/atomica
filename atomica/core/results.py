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

    def export(self, framework=None, filename=None):
        """Convert output to a single DataFrame and optionally write it to a file"""

        # Assemble the outputs into a dict
        d = dict()

        if framework:
            exportable = set()
            for df in [framework.comps,framework.characs,framework.pars]:
                exports = df['Export']
                for var,flag in zip(exports.index,exports.values):
                    if flag == 'y':
                        exportable.add(var)
        else:
            exportable = None


        for pop in self.model.pops:
            for comp in pop.comps:
                if exportable is None or comp.name in exportable:
                    d[('compartments', pop.name, comp.name)] = comp.vals
            for charac in pop.characs:
                if charac.vals is not None:
                    if exportable is None or charac.name in exportable:
                        d[('characteristics', pop.name, charac.name)] = charac.vals
            for par in pop.pars:
                if par.vals is not None:
                    if exportable is None or par.name in exportable:
                        d[('parameters', pop.name, par.name)] = par.vals
            for link in pop.links:
                # Sum over duplicate links and annualize flow rate
                key = ('flow rates', pop.name, link.name)
                if exportable is None or link.parameter.name in exportable:
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


    def get_cascade_vals(self,cascade,framework=None,pops='all',t_bins=None):
        '''
        Gets values for populating a cascade plot
        See https://docs.google.com/presentation/d/1lEEyPFORH3UeFpmaxEAGTKyHAbJRnKTm5YIsfV1iJjc/edit?usp=sharing
        Returns an odict with 4 keys:
            vals: a flat odict where the keys are the (ordered) cascade stages and the values are the height of the bars by year
            loss: a flat odict where the keys are the (ordered) cascade stages and the values are tuples consisting of the absolute # and proportion lost by year
            conv: a flat odict where the keys are the (ordered) cascade stages and the values are tuples consisting of the absolute # and proportion converted by year
            t: list of the years
        '''
        # INPUTS
        # - cascade can be a list of cascade entries, or the name of a cascade in a Framework
        # - framework should be a ProjectFramework and is only required if cascade is a string rather than a list
        from .plotting import PlotData # Import here to avoid circular dependencies

        assert isinstance(pops,str), 'At this stage, get_cascade_vals only intended to retrieve one population at a time, or to aggregate over all pops'

        if isinstance(cascade,str):
            if isinstance(framework.sheets['Cascades'],list):
                available_cascades = []
                for df in framework.sheets['Cascades']:
                    if df.columns[0].strip() == cascade.strip(): # If this cascade name matches the requested cascade
                        break
                    else:
                        available_cascades.append(df.columns[0])
                else:
                    raise AtomicaException('Cascade name "%s" not found in framework - must be one of %s' % (cascade,available_cascades))
            else:
                df = framework.sheets['Cascades']
                assert df.columns[0].strip() == cascade.strip()

            cascade = sc.odict()
            for _,stage in df.iterrows():
                cascade[stage[0]] = stage[1] # Split the name of the stage and the constituents

        if t_bins is not None:
            t_bins = sc.promotetoarray(t_bins)
            if len(t_bins) == 1:
                t_bins.append(t_bins[0]+self.dt) # Default is to aggregate over an entire year by summing over timesteps

        d = PlotData(self,outputs=cascade,pops=pops,t_bins=t_bins)

        cascade_output = sc.odict()
        for result in d.results:
            for pop in d.pops:
                for output in d.outputs:
                    cascade_output[output] = d[(result,pop,output)].vals # NB. Might want to return the Series here to retain formatting, units etc.
        t = d.tvals()[0] # nb. first entry in d.tvals() is time values, second entry is time labels

        return cascade_output,t