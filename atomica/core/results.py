import numpy as np
import pandas as pd
import sciris.core as sc
from .utils import NamedItem
from .system import AtomicaException
import matplotlib.pyplot as plt
import ast
from six import string_types

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
    def framework(self):
        return self.model.framework

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

    def export(self, export_everything=False, filename=None):
        """Convert output to a single DataFrame and optionally write it to a file"""

        # Assemble the outputs into a dict
        d = dict()

        if not export_everything:
            exportable = set()
            for df in [self.framework.comps,self.framework.characs,self.framework.pars]:
                exports = df['Export']
                for var,flag in zip(exports.index,exports.values):
                    if flag == 'y':
                        exportable.add(var)
        else:
            exportable = None


        for pop in self.model.pops:
            for comp in pop.comps:
                if export_everything or comp.name in exportable:
                    d[('compartments', pop.name, comp.name)] = comp.vals
            for charac in pop.characs:
                if charac.vals is not None:
                    if export_everything or charac.name in exportable:
                        d[('characteristics', pop.name, charac.name)] = charac.vals
            for par in pop.pars:
                if par.vals is not None:
                    if export_everything or par.name in exportable:
                        d[('parameters', pop.name, par.name)] = par.vals
            for link in pop.links:
                # Sum over duplicate links and annualize flow rate
                key = ('flow rates', pop.name, link.name)
                if export_everything or link.parameter.name in exportable:
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

    def plot(self,plot_name=None,plot_group=None,pops=None,project=None):
        from .plotting import PlotData, plot_series

        df = self.framework.sheets['Plots']

        if plot_group is not None:
            for plot_name in df.loc[df['Plot Group']==plot_group,'Code Name']:
                self.plot(plot_name=plot_name)
            return

        this_plot = df.loc[df['Code Name'] == plot_name, :].iloc[0] # A Series with the row of the 'Plots' sheet corresponding to the plot we want to render

        if this_plot['Aggregate pops'] == 'y':
            pops = 'all'

        quantities = this_plot['Quantities']
        if '{' in quantities or '[' in quantities:
            # Evaluate the string to set lists and dicts - do at least a little validation
            assert '__' not in quantities, 'Cannot use double underscores in functions'
            assert len(quantities) < 1800  # Function string must be less than 1800 characters
            fcn_ast = ast.parse(quantities, mode='eval')
            for node in ast.walk(fcn_ast):
                if not (node is fcn_ast):
                    assert isinstance(node, ast.Dict) or isinstance(node, ast.Str) or isinstance(node, ast.List) or isinstance(node, ast.Load), 'Only allowed to initialize lists and dicts of strings here'
            compiled_code = compile(fcn_ast, filename="<ast>", mode="eval")
            quantities = eval(compiled_code)

        d = PlotData(self, outputs=quantities, pops=pops,project=project)
        h = plot_series(d, axis='pops',data=(project.data if project is not None else None))
        plt.title(this_plot['Display Name'])
        return h



    def get_cascade_vals(self,cascade,pops='all',t_bins=None):
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

        assert isinstance(pops,string_types), 'At this stage, get_cascade_vals only intended to retrieve one population at a time, or to aggregate over all pops'

        if isinstance(cascade,string_types):
            if isinstance(self.framework.sheets['Cascades'],list):
                available_cascades = []
                for df in self.framework.sheets['Cascades']:
                    if df.columns[0].strip() == cascade.strip(): # If this cascade name matches the requested cascade
                        break
                    else:
                        available_cascades.append(df.columns[0])
                else:
                    raise AtomicaException('Cascade name "%s" not found in framework - must be one of %s' % (cascade,available_cascades))
            else:
                df = self.framework.sheets['Cascades']
                assert df.columns[0].strip() == cascade.strip()

            cascade = sc.odict()
            for _,stage in df.iterrows():
                cascade[stage[0]] = stage[1] # Split the name of the stage and the constituents

        if t_bins is not None:
            t_bins = sc.promotetoarray(t_bins)
            if len(t_bins) == 1:
                t_bins = np.append(t_bins,t_bins[0]) # Default is to just select the one time point requested, if not aggregating over a range

        d = PlotData(self,outputs=cascade,pops=pops,t_bins=t_bins)

        cascade_output = sc.odict()
        for result in d.results:
            for pop in d.pops:
                for output in d.outputs:
                    cascade_output[output] = d[(result,pop,output)].vals # NB. Might want to return the Series here to retain formatting, units etc.
        t = d.tvals()[0] # nb. first entry in d.tvals() is time values, second entry is time labels

        return cascade_output,t