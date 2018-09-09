import numpy as np
import pandas as pd
import sciris as sc
from .utils import NamedItem
import matplotlib.pyplot as plt
import ast
from .excel import standard_formats
from .system import logger
from zipfile import ZipFile
import os

class Result(NamedItem):
    # A Result stores a single model run
    def __init__(self, model, parset=None, name=None):
        if name is None:
            if parset is None:
                name = None
            else:
                name = parset.name
        NamedItem.__init__(self,name)

        self.uid = sc.uuid()

        # The Result constructor is called in model.run_model and the Model is no longer returned.
        # The following should be the only reference to that instance so no need to dcp.
        self.model = model
        self.parset_name = parset.name if parset is not None else None
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

    @property
    def pop_labels(self):
        return [x.label for x in self.model.pops]

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
        output = sc.prepr(self)
        return output

    def get_variable(self, pops, name):
        # Retrieve a list of variables from a population
        return self.model.get_pop(pops).get_variable(name)

    def export(self,filename,plot_names=None,cascade_names=None, include_target_pars=True, include_programs=True):
        # This function writes an XLSX file with the data corresponding to any Cascades or Plots
        # that are present. Note that results are exported for every year by selecting integer years.
        # Flow rates are annualized instantaneously. So for example, the flow will have values from
        # 2014, 2015, 2016, but the 2015 flow rate is the actual flow at 2015.0 divided by dt, not the
        # time-aggregated flow rate. Time-aggregation isn't appropriate here because many of the quantities
        # plotted are probabilities. Selecting the annualized value at a particular year also means that the
        # data being exported will match up with whatever plots are generated from within Atomica
        #
        # Optionally can specify a list/set of names of the plots/cascades to include in the export
        # Set to an empty list to omit that category e.g.
        #
        #   plot_names = None # export all plots in framework
        #   plot_names = ['a','b'] # export only plots 'a' and 'b'
        #   plot_names = [] # don't export any plots e.g. to only export cascades
        #
        # First, make a dataframe for all the plot data, if plots are specified in the cascade
        # Imports here to avoid circular references

        from .plotting import PlotData
        from .cascade import get_cascade_vals

        pop_names = sc.odict()
        pop_names['all'] = 'Entire population'
        for pop_name,pop_label in zip(self.pop_names,self.pop_labels):
            pop_names[pop_name] = pop_label

        new_tvals = np.arange(np.ceil(self.t[0]), np.floor(self.t[-1]) + 1)

        if 'plots' not in self.framework.sheets:
            plot_df = None
        else:
            plots_required = self.framework.sheets['plots'][0]
            if plot_names is not None:
                plots_required = plots_required[plots_required['name'].isin(plot_names)]
            plot_df = []

            # Now for each plot, we have one output and several populations
            # We will have one dataframe for each output
            for _,spec in plots_required.iterrows():
                if 'type' in spec and spec['type'] == 'bar':
                    continue # For now, don't do bars - not implemented yet
                data = sc.odict()
                popdata = PlotData(self,outputs=evaluate_plot_string(spec['quantities']))
                assert len(popdata.outputs) == 1, 'Framework plot specification should evaluate to exactly one output series - there were %d' % (len(popdata.outputs))
                popdata.interpolate(new_tvals)
                for pop in popdata.pops:
                    data[pop_names[pop]] = popdata[self.name,pop,popdata.outputs[0]].vals
                df = pd.DataFrame(data, index=new_tvals)
                df = df.T
                df.name = spec['name']
                plot_df.append(df)

        cascade_df = list()

        for name in self.framework.cascades.keys():
            if cascade_names is None or name in cascade_names:
                for pop,label in pop_names.items():
                    data = sc.odict()
                    cascade_vals,_ = get_cascade_vals(self,name,pops=pop,year=new_tvals)
                    for stage,vals in cascade_vals.items():
                        data[stage] = vals
                    df = pd.DataFrame(data, index=new_tvals)
                    df = df.T
                    df.name = '%s - %s' % (name,label)
                    cascade_df.append(df)

        output_fname = filename + '.xlsx' if not filename.endswith('.xlsx') else filename
        writer = pd.ExcelWriter(output_fname,engine='xlsxwriter')
        formats = standard_formats(writer.book)

        # WRITE THE PLOTS
        def write_df_list(df_list,sheet_name):
            i = 0
            for n, df in enumerate(df_list):
                df.to_excel(writer, sheet_name, startcol=0, startrow=i)
                worksheet = writer.sheets[sheet_name]
                worksheet.write_string(i,0, df.name,formats['center_bold'])
                i += df.shape[0] + 2
            worksheet = writer.sheets[sheet_name]

            required_width = 0.0
            for df in df_list:
                required_width = max(required_width,len(df.name))
                if not isinstance(df.index,pd.MultiIndex):
                    required_width = max(required_width, max(df.index.str.len()))
            worksheet.set_column(0, 0, required_width * 1.1 + 1)

        if plot_df:
            write_df_list(plot_df,'Plot data')

        if cascade_df:
            write_df_list(cascade_df,'Cascades')

        if include_target_pars:
            targetable_code_names = list(self.framework.pars.index[self.framework.pars['targetable']=='y'])
            if targetable_code_names:
                par_df = []

                for par_name in targetable_code_names:
                    data = sc.odict()
                    popdata = PlotData(self, outputs=par_name)
                    popdata.interpolate(new_tvals)
                    for pop in popdata.pops:
                        data[pop_names[pop]] = popdata[self.name, pop, popdata.outputs[0]].vals
                    df = pd.DataFrame(data, index=new_tvals)
                    df = df.T
                    df.name = self.framework.pars.loc[par_name]['display name']
                    par_df.append(df)

                write_df_list(par_df, 'Target parameters')

        if include_programs:
            if self.model.progset is not None:
                prog_df = []
                for prog_name in self.model.progset.programs:
                    data = sc.odict()

                    spending = PlotData.programs(self, outputs=prog_name,quantity='spending').interpolate(new_tvals)
                    data['Spending ($/year)'] = spending.series[0].vals

                    spending = PlotData.programs(self, outputs=prog_name,quantity='coverage_number').interpolate(new_tvals)
                    data['People covered'] = spending.series[0].vals

                    spending = PlotData.programs(self, outputs=prog_name,quantity='coverage_denominator').interpolate(new_tvals)
                    data['People eligible'] = spending.series[0].vals

                    spending = PlotData.programs(self, outputs=prog_name,quantity='coverage_fraction').interpolate(new_tvals)
                    data['Proportion covered'] = spending.series[0].vals

                    df = pd.DataFrame(data, index=new_tvals)
                    df = df.T
                    df.name = self.framework.pars.loc[par_name]['display name']
                    prog_df.append(df)

                write_df_list(prog_df, 'Programs')

        writer.save()
        writer.close()

        return output_fname

    def export_raw(self, filename=None):
        """Convert raw outputs to a single DataFrame and optionally write it to a file"""

        # Assemble the outputs into a dict
        d = dict()

        for pop in self.model.pops:
            for comp in pop.comps:
                d[('Compartments', pop.name, comp.name)] = comp.vals
            for charac in pop.characs:
                d[('Characteristics', pop.name, charac.name)] = charac.vals
            for par in pop.pars:
                if par.vals is not None:
                    d[('Parameters', pop.name, par.name)] = par.vals
            for link in pop.links:
                # Sum over duplicate links and annualize flow rate
                key = ('Flow rates', pop.name, link.name)
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
        # Plot a single Result instance using the plots defined in the framework
        # INPUTS
        # - plot_name : The name of a single plot in the Framework
        # - plot_group : The name of a plot group
        # - pops : A population aggregation supposed by PlotData (e.g. 'all')
        # - project : A Project instance used to plot data and full names
        #
        # If plot_group is not None, then plot_name is ignored
        # If plot_name and plot_group are both None, then all plots will be displayed
        from .plotting import PlotData, plot_series

        df = self.framework.sheets['plots'][0]

        if plot_group is None and plot_name is None:
            for plot_name in df['name']:
                self.plot(plot_name,pops=pops,project=project)
            return
        elif plot_group is not None:
            for plot_name in df.loc[df['plot group']==plot_group,'name']:
                self.plot(plot_name=plot_name,pops=pops,project=project)
            return

        this_plot = df.loc[df['name'] == plot_name, :].iloc[0] # A Series with the row of the 'Plots' sheet corresponding to the plot we want to render

        quantities = evaluate_plot_string(this_plot['quantities'])

        d = PlotData(self, outputs=quantities, pops=pops,project=project)
        h = plot_series(d, axis='pops',data=(project.data if project is not None else None))
        plt.title(this_plot['name'])
        return h

def evaluate_plot_string(plot_string):
    # The plots in the framework are specified as strings - for example,
    #
    # plot_string = "{'New active DS-TB':['pd_div:flow','nd_div:flow']}"
    #
    # This needs to be (safely) evaluated so that the actual dict can be
    # used. This function evaluates a string like this and returns a
    # variable accordingly. For example
    #
    # x = evaluate_plot_string("{'New active DS-TB':['pd_div:flow','nd_div:flow']}")
    #
    # is the same as
    #
    # x = {'New active DS-TB':['pd_div:flow','nd_div:flow']}
    #
    # This will only happen if tokens associated with dicts and lists are present -
    # otherwise the original string will just be returned directly

    if '{' in plot_string or '[' in plot_string:
        # Evaluate the string to set lists and dicts - do at least a little validation
        assert '__' not in plot_string, 'Cannot use double underscores in functions'
        assert len(plot_string) < 1800  # Function string must be less than 1800 characters
        fcn_ast = ast.parse(plot_string, mode='eval')
        for node in ast.walk(fcn_ast):
            if not (node is fcn_ast):
                assert isinstance(node, ast.Dict) or isinstance(node, ast.Str) or isinstance(node, ast.List) or isinstance(node, ast.Load), 'Only allowed to initialize lists and dicts of strings here'
        compiled_code = compile(fcn_ast, filename="<ast>", mode="eval")
        return eval(compiled_code)
    else:
        return plot_string


def export_results(results,fname):
    # fname is the output file to write, including path
    # e.g. concatenate downloads_dir.dir_path with 'output.zip'
    results = sc.promotetolist(results)
    result_names = [x.name for x in results]
    if len(result_names) != len(set(result_names)):
        logger.warning('Result names were not all unique, so not all results will be exported')

    # TODO - is this OK on the server side in regard to simultaneous
    # writing? Can two different sets of results be written to disk at the
    # same time with the same filenames?
    result_files = [x.export('temp_export_%s.xlsx' % (x.name)) for x in results]

    with ZipFile(fname,'w') as zipfile:  # Create the zip file, putting all of the .prj files in a projects directory.
        for result_file in result_files:
            zipfile.write(result_file,result_file.replace('temp_export_',''))
            os.remove(result_file)
    return fname  # Return the server file name.
