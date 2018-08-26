from .plotting import plot_legend
import matplotlib.pyplot as plt
import numpy as np
import textwrap
import sciris as sc
import matplotlib
from .utils import NDict
from .results import Result
from six import string_types
from .system import logger, NotAllowedError, AtomicaException

default_figsize = (9,5)

class InvalidCascade(AtomicaException):
    # Throw this error if a cascade was not valid. This error should result in the
    # FE printing a persistent diagnosic message
    pass

def plot_cascade(results=None, cascade=None, pops=None, year=None, data=None, show_table=None):
    
    year    = sc.promotetolist(year)
    results = sc.promotetolist(results)
    if len(year)>1 or len(results)>1:
        output = plot_multi_cascade(results=results, cascade=cascade, pops=pops, year=year, data=data, show_table=show_table)
    else:
        fig = plot_single_cascade(result=results[0], cascade=cascade, pops=pops, year=year, data=data)
        table = None
        output = (fig,table)
    return output # Either fig or (fig,table)

def sanitize_cascade_inputs(result=None, cascade=None, pops=None, year=None):
    # INPUTS
    # - result : A single Result or a list of Results
    # - cascade : A specification of the cascade to plot. It can be
    #             - The name of a cascade as entered in the framework
    #             - The index of a cascade entered in the framework (0 for the first one)
    #             - A list of comps/characs to use in order e.g. ['all_people','all_dx','all_tx'] - the stage will be named using the variable's name
    #             - An odict of comps/charac combinations e.g. {'all_people':['sus','inf','rec'],'infected':['sus','inf'],'recovered':['rec']}
    #             - `None`, in which case either
    #               - The first user-defined cascade is used, OR
    #               - If there are no user defined cascades, a fallback cascade will be formed from all characteristics without denominators in framework order
    # - pops : A single code name or full name, or a list of code names or full names
    # - year : A single year, or array of years

    # Sanitize based on the first result provided, if it's a list
    if isinstance(result, list): result = result[0]  # Sanitize input -- if needed

    # Sanitize cascade input by turning non-names into output dicts
    cascade = sanitize_cascade(result.framework,cascade)

    # Convert input pops to code names, if they were provided as full names e.g. from the FE
    if pops is None or pops == 'all' or pops == 'All':
        pops = {'Entire population':result.pop_names} # Use all populations
    else:
        code_names = []

        if isinstance(pops,string_types):
            pops = [pops]

        for pop in pops:
            if pop not in result.pop_names:
                idx = result.pop_labels.index(pop)
                code_names.append(result.pop_names[idx])
            else:
                code_names.append(pop)

        if len(code_names) > 1:
            pops = {'Selected populations':code_names}
        else:
            idx = result.pop_names.index(code_names[0])
            pops = {result.pop_labels[idx]:code_names}

    # Sanitize year
    if year is None:
        year = result.t[0] # Draw cascade for first year
    else:
        year = sc.promotetoarray(year)
    
    return cascade, pops, year

def plot_single_cascade_series(result=None, cascade=None, pops=None, data=None):
    # Plot a stacked timeseries of the cascade. Unlike a normal stacked plot, the shaded areas show losses
    # so for example the overall height of the plot corresponds to the number of people in the first cascade stage
    from .plotting import PlotData, plot_series # Import here to avoid circular dependencies

    cascade, pops, _ = sanitize_cascade_inputs(result=result, cascade=cascade, pops=pops, year=None)

    if isinstance(result,list):
        figs = []
        for r in result:
            figs.append(plot_single_cascade(r,cascade,pops,data))
        return figs

    # Now, construct and plot the series
    assert isinstance(result,Result), 'Input must be a single Result object'
    if isinstance(cascade,string_types):
        outputs = get_cascade_outputs(result.framework,cascade)
    else:
        outputs = cascade

    d = PlotData(result, outputs=outputs, pops=pops)
    d.set_colors(outputs=d.outputs)
    assert len(d.pops) == 1, 'Only supports plotting one population at a time'

    figs = plot_series(d,axis='outputs') # 1 result, 1 pop, axis=outputs guarantees 1 plot
    ax = figs[0].axes[0]

    if data is not None:
        t = d.tvals()[0]
        cascade_data,_ = get_cascade_data(data,result.framework,cascade,pops,t)
        for stage,vals in cascade_data.items():
            color = d[d.results[0],d.pops[0],stage].color # Get the colour of this quantity
            flt = ~np.isnan(vals)
            if np.any(flt): # Need to only plot real values, because NaNs show up in mpld3 even though they don't appear in the normal figure
                ax.scatter(t[flt],vals[flt],marker='o', s=40, linewidths=1, facecolors=color,color='k',zorder=100)


def plot_single_cascade(result=None, cascade=None, pops=None, year=None, data=None, title=False):
    # This is the fancy cascade plot, which only applies to a single result at a single time
    # INPUTS
    # result - A single result, or list of results. One figure will be generated for each result
    # cascade - A string naming a cascade, or an odict specifying cascade stages and constituents
    #           e.g. {'stage 1':['sus','vac'],'stage 2':['vac']}
    # pops - The name of a population, or a population aggregation that maps to a single population. For example
    #        '0-4', 'all', or {'HIV':['15-64 HIV','65+ HIV']}
    # year - A single year, could be a length 1 ndarray or a scalar
    # data - A ProjectData instance
    #
    # OUTPUTS
    # figs - a Figure handle

    barcolor  = (0.00, 0.15, 0.48) # Cascade color -- array([0,38,122])/255.
    diffcolor = (0.85, 0.89, 1.00) # (0.74, 0.82, 1.00) # Original: (0.93,0.93,0.93)
    losscolor = (0,0,0) # (0.8,0.2,0.2)

    cascade, pops, year = sanitize_cascade_inputs(result=result, cascade=cascade, pops=pops, year=year)

    if isinstance(result,list):
        figs = []
        for r in result:
            figs.append(plot_single_cascade(r,cascade,pops,year,data))
        return figs

#    fontsize=14
    assert len(year) == 1
    assert isinstance(result,Result), 'Input must be a single Result object'
    cascade_vals,t = get_cascade_vals(result,cascade,pops,year)
    if data is not None:
        cascade_data,_ = get_cascade_data(data,result.framework,cascade,pops,year)
        cascade_data_array = np.hstack(cascade_data.values())

    assert len(t) == 1, 'Plot cascade requires time aggregation'
    cascade_array = np.hstack(cascade_vals.values())

    fig = plt.figure(figsize=default_figsize)
    fig.set_figwidth(fig.get_figwidth()*1.5)
    ax = plt.gca()
    bar_x = np.arange(len(cascade_vals))
    h = plt.bar(bar_x,cascade_array, width=0.5, color=barcolor)
    if data is not None:
        non_nan = np.isfinite(cascade_data_array)
        if np.any(non_nan):
            plt.scatter(bar_x[non_nan], cascade_data_array[non_nan],s=40,c='#ff9900',marker='s',zorder=100)

    ax.set_xticks(np.arange(len(cascade_vals)))
    ax.set_xticklabels([ '\n'.join(textwrap.wrap(x, 15)) for x in cascade_vals.keys()])

    ylim = ax.get_ylim()
    yticks = ax.get_yticks()
    data_yrange = np.diff(ylim)
    ax.set_ylim(-data_yrange*0.2,data_yrange*1.1)
    ax.set_yticks(yticks)
    for i,val in enumerate(cascade_array):
        plt.text(i, val*1.01, '%s' % sc.sigfig(val, sigfigs=3, sep=True), verticalalignment='bottom', horizontalalignment='center', zorder=200)

    bars = h.get_children()
    conversion = cascade_array[1:]/cascade_array[0:-1] # Fraction not lost
    conversion_text_height = cascade_array[-1]/2

    for i in range(len(bars)-1):
        left_bar = bars[i]
        right_bar = bars[i+1]

        xy = np.array([
        (left_bar.get_x() + left_bar.get_width(), 0), # Bottom left corner
        (left_bar.get_x() + left_bar.get_width(), left_bar.get_y() + left_bar.get_height()), # Top left corner
        (right_bar.get_x(), right_bar.get_y() + right_bar.get_height()),  # Top right corner
        (right_bar.get_x(), 0),  # Bottom right corner
        ])

        p = matplotlib.patches.Polygon(xy, closed=True,facecolor=diffcolor)
        ax.add_patch(p)

        bbox_props = dict(boxstyle="rarrow", fc=(0.7, 0.7, 0.7),lw=1)

        t = ax.text(np.average(xy[1:3,0]), conversion_text_height, '%s%%' % sc.sigfig(conversion[i]*100, sigfigs=3, sep=True), ha="center", va="center", rotation=0, bbox=bbox_props)


    loss = np.diff(cascade_array)
    for i,val in enumerate(loss):

        plt.text(i, -data_yrange[0]*0.02, 'Loss: %s' % sc.sigfig(-val, sigfigs=3, sep=True), verticalalignment='top', horizontalalignment='center', color=losscolor)

    pop_label = list(pops.keys())[0]
    plt.ylabel('Number of people')
    if title:
        if isinstance(cascade,string_types):
            plt.title('%s cascade for %s in %d' % (cascade, pop_label, year))
        else:
            plt.title('Cascade for %s in %d' % (pop_label, year))
    plt.tight_layout()

    return fig
    
    
def plot_multi_cascade(results=None, cascade=None, pops=None, year=None, data=None, show_table=None):
    # This is a cascade plot that handles multiple results and times
    # Results are grouped by stage/output, which is not possible to do with plot_bars()
    #
    # INPUTS
    # results - A single result, or list of results. A single figure will be generated
    # cascade - A string naming a cascade, or an odict specifying cascade stages and constituents
    #           e.g. {'stage 1':['sus','vac'],'stage 2':['vac']}
    # pops - The name of a population, or a population aggregation that maps to a single population. For example
    #        '0-4', 'all', or {'HIV':['15-64 HIV','65+ HIV']}
    # year - A scalar, or array of time points. Bars will be plotted for every time point
    # data - A ProjectData instance
    #
    # OUTPUTS
    # fig - a figure handle

    if show_table is None: show_table = True

    # First, process the cascade into an odict of outputs for PlotData
    if isinstance(results, sc.odict):
        results = [result for _, result in results.items()]
    elif isinstance(results, Result):
        results = [results]
    elif isinstance(results, NDict):
        results = list(results)
        
    cascade, pops, year = sanitize_cascade_inputs(result=results[0], cascade=cascade, pops=pops, year=year)
    
    if (len(results)>1 and len(year)>1):
        label_fcn = lambda result,t: '%s (%s)' % (result.name,t)
    elif len(results) > 1:
        label_fcn = lambda result,t: '%s' % (result.name)
    else:
        label_fcn = lambda result,t: '%s' % (t)

    # Gather all of the cascade outputs and years
    cascade_vals = sc.odict()
    for result in results:
        for t in year:
            cascade_vals[label_fcn(result,t)] = get_cascade_vals(result,cascade,pops=pops,year=t)[0]

    # Determine the number of bars, per stage - based either on result or time point
    n_bars = len(cascade_vals)
    bar_width = 1. # This is the width of the bars
    bar_gap = 0.15 # This is the width of the bars
    block_gap = 1. # This is the gap between blocks
    block_size = n_bars*(bar_width+bar_gap)
    x = np.arange(0,len(cascade_vals[0].keys()))*(block_size+block_gap) # One block for each cascade stage
    colors = sc.gridcolors(n_bars)  # Default colors
    legend_entries = sc.odict()

    fig = plt.figure(figsize=default_figsize)
    fig.set_figwidth(fig.get_figwidth()*1.5)

    for offset,(bar_label,data) in enumerate(cascade_vals.items()):
        legend_entries[bar_label] = colors[offset]
        vals = np.hstack(data.values())
        plt.bar(x+offset*(bar_width+bar_gap),vals,color=colors[offset],width=bar_width)

    plot_legend(legend_entries,fig=fig)
    ax = fig.axes[0]
    ax.set_xticks(x+(block_size-bar_gap-bar_width)/2)
    ax.set_xticklabels(['\n'.join(textwrap.wrap(k, 15)) for k in cascade_vals[0].keys()])
    if show_table:
        ax.get_xaxis().set_ticks_position('top')

    # Make the loss table
    cell_text = []
    for data in cascade_vals.values():
        cascade_array = np.hstack(data.values())
        loss = np.diff(cascade_array)
        loss_str = ['%s' % sc.sigfig(-val, sigfigs=3, sep=True) for val in loss]
        loss_str.append('-') # No loss for final stage
        cell_text.append(loss_str)

    # Clean up formatting
    yticks = ax.get_yticks()
    ax.set_yticks(yticks[1:]) # Remove the first tick at 0 so it doesn't clash with table - TODO: improve table spacing so this isn't needed
    plt.ylabel('Number of people')
    if show_table:
        plt.subplots_adjust(top=0.8,right=0.75,left=0.2, bottom=0.25)
    else:
        plt.subplots_adjust(top=0.95, right=0.75, left=0.2, bottom=0.25)

    # Add a table at the bottom of the axes
    row_labels = list(cascade_vals.keys())
    if show_table:
        plt.table(cellText=cell_text,rowLabels=row_labels,rowColours=None,colLabels=None,loc='bottom',cellLoc='center')
        return fig
    else:
        col_labels = [k for k in cascade_vals[0].keys()]
        table = {'text':cell_text, 'rowlabels':row_labels, 'collabels':col_labels}
        return fig,table

def get_cascade_outputs(framework,cascade_name):
    # Given a cascade name, return an outputs dicts corresponding to the cascade stages
    # suitable for use in PlotData
    # INPUTS
    # - framework : a ProjectFramework
    # - cascade_name : one of framework.cascade.keys()
    #
    # OUTPUTS
    # - outputs : A odict suitable for PlotData(outputs=outputs)
    #
    # Example
    # a = get_cascade(framework,'main')
    # Suppose the spreadsheet had stages
    # Stage 1 - sus,vac,inf
    # Stage 2 - vac,inf
    #
    # Then the output of this function would be
    # output = {'Stage 1':['sus','vac','inf'],'Stage 2':['vac','inf']
    df = framework.cascades[cascade_name]
    outputs = sc.odict()
    for _, stage in df.iterrows():
        outputs[stage[0]] = [x.strip() for x in stage[1].split(',')]  # Split the name of the stage and the constituents
    return outputs

def get_cascade_vals(result,cascade,pops=None,year=None):
    '''
    Gets values for populating a cascade plot
    '''
    # INPUTS
    # - result is a single result object
    # - cascade can be a list of cascade entries, or the name of a cascade in a Framework
    # - pops should map to a single population output (a single pop name, or a single aggregation)
    # - year controls which time points appear in the output. Possible values are
    #   - None : all time points in the Result
    #   - scalar or np.array : one entry for each time specified e.g. `year=2020` or `year=[2020,2025,2030]`
    #
    # OUTPUTS
    # - cascade_output : odict with {stage_name:vals} where vals is an ndarray the same shape as the 't' output
    # - t : ndarray of time values

    from .plotting import PlotData # Import here to avoid circular dependencies

    if pops is None: pops = 'all'

    # Sanitize the cascade inputs
    cascade = sanitize_cascade(result.framework, cascade)

    if isinstance(cascade,string_types):
        outputs = get_cascade_outputs(result.framework,cascade)
    else:
        outputs = cascade

    validate_cascade(result.framework, outputs) # Check that the requested cascade is valid

    if year is None:
        d = PlotData(result, outputs=outputs, pops=pops)
    else:
        year = sc.promotetoarray(year)
        d = PlotData(result, outputs=outputs, pops=pops)
        d.interpolate(year)

    assert len(d.pops) == 1, 'get_cascade_vals() cannot get results for multiple populations or population aggregations, only a single pop or single aggregation'
    cascade_vals = sc.odict()
    for result in d.results:
        for pop in d.pops:
            for output in d.outputs:
                cascade_vals[output] = d[(result,pop,output)].vals # NB. Might want to return the Series here to retain formatting, units etc.
    t = d.tvals()[0] # nb. first entry in d.tvals() is time values, second entry is time labels

    return cascade_vals,t

def get_cascade_data(data,framework,cascade,pops=None,year=None):
    # This function is the counterpart to get_cascade_vals but it returns data
    # instead. Note that the inputs and outputs are slightly different
    # - If year is specified, the output is guaranteed to be the same size as the input year array, the same as get_cascade_vals
    #   However, the get_cascade_vals defaults to all time points in the simulation output, whereas get_cascade_data defaults to
    #   all data years. To make a plot superimposing data and model output, the year should be specified to ensure that the years
    #   match up
    # pops - can be 'all', or a pop name, or a list of pop names
    #
    # NB - In general, data probably will NOT exist
    # Set the logging level to 'DEBUG' to have messages regarding this printed out

    if pops is None: pops = 'all'

    if isinstance(cascade,string_types):
        outputs = get_cascade_outputs(framework,cascade)
    else:
        outputs = cascade

    validate_cascade(framework, outputs) # Check that the requested cascade is valid

    if pops == 'all':
        pops = list(data.pops.keys())
    elif isinstance(pops,string_types):
        pops = [pops]
    elif isinstance(pops,dict):
        assert len(pops) == 1, 'Aggregation should have only one output population'
        pops = list(pops.values())[0]

    if year is not None:
        t = sc.promotetoarray(year) # Output times are guaranteed to be
    else:
        t = data.tvec # Defaults to data's time vector

    # Now, get the outputs in the given years
    data_values = dict()
    for stage_constituents in outputs.values():
        if isinstance(stage_constituents,string_types):
            stage_constituents = [stage_constituents] # Make it a list - this is going to be a common source of errors otherwise
        for code_name in stage_constituents:
            if code_name not in data_values:
                data_values[code_name] = np.zeros(t.shape)* np.nan # data values start out as NaN - this is a fallback in case for some reason pops is empty (the data will be all NaNs then)

                for pop_idx,pop in enumerate(pops):
                    ts = data.get_ts(code_name,pop) # The TimeSeries data for the required variable and population
                    vals = np.ones(t.shape) * np.nan # preallocate output values coming from this TimeSeries object

                    # Now populate this array
                    if ts is not None:
                        for i,tval in enumerate(ts.t):
                            match = np.where(t==tval)[0]
                            if len(match): # If a time point in the TimeSeries matches the requested time - then match[0] is the index in t
                                vals[match[0]] = ts.vals[i]
                        if np.any(np.isnan(vals)):
                            logger.debug('Data for %s (%s) did not contain values for some of the requested years' % (code_name, pop))
                    else:
                        logger.debug('Data not present for %s (%s)' % (code_name,pop))


                    if pop_idx == 0:
                        data_values[code_name] = vals  # If at least one TimeSeries was found, use the first one as the data values (it could still be NaN if no times match)
                    else:
                        data_values[code_name] += vals

    # Now, data values contains all of the required quantities in all of the required years. Last step is to aggregate them
    cascade_data = sc.odict()
    for stage_name,stage_constituents in outputs.items():
        for code_name in stage_constituents:
            if stage_name not in cascade_data:
                cascade_data[stage_name] = data_values[code_name]
            else:
                cascade_data[stage_name] += data_values[code_name]

    return cascade_data,t

def sanitize_cascade(framework,cascade):
    # Construct a fallback cascade from all non-normalized characteristics
    if cascade is None:
        if framework.cascades:
            cascade = 0 # Use the first cascade
        else:
            # Assemble cascade from characteristics without denominators
            cascade = sc.odict()
            for _, spec in framework.characs.iterrows():
                if not spec['denominator']:
                    cascade[spec['display name']] = [spec.name]

    if isinstance(cascade, list):
        # Assemble cascade from comp/charac names using the display name as the stage name
        outputs = sc.odict()
        for name in cascade:
            spec = framework.get_variable(name)[0]
            outputs[spec['display name']] = [spec.name]
        cascade = outputs
    elif isinstance(cascade, int):
        # Retrieve the cascade name based on index
        available_cascades = list(framework.cascades)
        cascade = available_cascades[cascade]
    return cascade

def validate_cascade(framework,cascade):
    # Check if a cascade is valid
    # INPUTS
    # - framework
    # - cascade : specification of a cascade (None for default, int, name, list of comps, output dict)
    #

    # Turn whatever form the cascade was provided as into a dict of outputs
    fallback_used = cascade is None # Record whether or not the fallback cascade was used, to help customize error message

    cascade = sanitize_cascade(framework,cascade)
    if isinstance(cascade,string_types):
        outputs = get_cascade_outputs(framework,cascade)
    else:
        outputs = cascade

    if len(outputs) < 2:
        # A 'cascade' with 0 or 1 stages is by definition valid, although it would not be sensible!
        return True

    # Now, for each cascade stage we need to expand any characteristics into compartments
    def expand_includes(includes):
        # Take a list of included comps/characs and replace any characs with their included comps
        expanded = []
        for include in includes:
            if include in framework.characs.index:
                components = [x.strip() for x in framework.characs.at[include, 'components'].split(',')]
                expanded += expand_includes(components)
            else:
                expanded.append(str(include)) # Use 'str()' to get `'sus'` in the error message instead of  `u'sus'`
        return expanded

    expanded = sc.odict()
    for stage,includes in outputs.items():
        expanded[stage] = expand_includes(includes)

    for i in range(0,len(expanded)-1):
        if not (set(expanded[i+1]) <= set(expanded[i])):
            message = ''
            if fallback_used:
                message += 'The fallback cascade is not properly nested\n\n'
            elif isinstance(cascade,string_types):
                message += 'The cascade "%s" is not properly nested\n\n' % (cascade)
            else:
                message += 'The requested cascade is not properly nested\n\n' % (cascade)

            message += 'Stage "%s" appears after stage "%s" so it must contain a subset of the compartments in "%s"\n\n' % (expanded.keys()[i+1],expanded.keys()[i],expanded.keys()[i])
            message += 'After expansion of any characteristics, the compartments comprising these stages are:\n'
            message += '"%s" = %s\n' % (expanded.keys()[i],expanded[i])
            message += '"%s" = %s\n' % (expanded.keys()[i+1],expanded[i+1])
            message += '\nTo be valid, stage "%s" would need the following compartments added to it: %s' % (expanded.keys()[i],list(set(expanded[i+1])-set(expanded[i])))
            if fallback_used and not framework.cascades:
                message += '\n\nNote that the framework did not contain a cascade - in many cases, the characteristics do not form a valid cascade. You will likely need to explicitly define a cascade in the framework file'
            if fallback_used and framework.cascades:
                message += '\n\nAlthough the framework fallback cascade was not valid, user-specified cascades do exist. The fallback cascade should only be used if user cascades are not present.'
            elif isinstance(cascade,string_types):
                message += '\n\nTo fix this error, please modify the definition of the cascade in the framework file'

            raise InvalidCascade(message)

    return True



