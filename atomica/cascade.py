"""
Utility functions for working with cascades

Cascades are defined in a :class:`ProjectFramework` object. This module
implements functions that are useful for working with the cascades, including

- Validation
- Plotting
- Value extraction

On the plotting side, the two key functions are

- :func:`plot_single_cascade` which makes a single cascade plot complete with
  shaded regions between bars, and conversion arrows
- :func:`plot_multi_cascade` which makes a scenario comparison type cascade
  plot with bars grouped by cascade stage (not possible with normal
  :func:`plotting.plot_bars`)

The plot takes in as arguments the cascade and populations. Users can specify
cascades as

- The name of a cascade in the Framework
- The index of a cascade in the Framework
- A list of comps/characs in stage order, with stage names matching the
  comps/characs
- A ordered dict with ``{stage:comps/characs}``, with a customized stage name.
  This is referred to in code as a **cascade dict**

The first two representations map to cascades defined in the framework, while
the last two representations relate to defining custom cascades on the fly.
They are therefore sanitized in two stages

- :func:`sanitize_cascade_inputs` turns cascade indices into names, and
  cascade lists into dicts. Returning string names for predefined cascades
  allows the name to be used in the title of plots
- :func:`get_cascade_outputs` turns cascade names into cascade dicts

The dictionary representation is always required when retrieving the values of
cascades. There are two types of value retrieval:

- :func:`get_cascade_vals` which returns values for each cascade stage from a
  model result
- :func:`get_cascade_data` which attempts to compute values for each cascade
  stage from a :class:`ProjectData` instance. This is used when plotting data
  points on the cascade plot. Compartments and characteristics are
  automatically summed as required. Data points will only be displayed if the
  data has values for all of the included quantities in the year being
  plotted.


"""


from .plotting import plot_legend
import matplotlib.pyplot as plt
import numpy as np
import textwrap
import sciris as sc
import matplotlib
from .utils import NDict
from .results import Result
from .system import logger
from .data import ProjectData

default_figsize = (10, 4)
default_ax_position = [0.15, 0.2, 0.35, 0.7]


class InvalidCascade(Exception):
    """
    Error if cascade is not valid

    This error gets thrown if a cascade failed validation - for example, because the
    requested stages were not correctly nested

    """

    pass


def plot_cascade(results=None, cascade=None, pops=None, year=None, data=None, show_table:bool =None):
    """
    Plot single or multiple cascade plot

    :func:`plot_single_cascade` generates a plot where multiple results each have their
    own figure. A common requirement (used on the FE) is to decide between calling
    :func:`plot_single_cascade` or calling :func:`plot_multi_cascade` based on whether
    there are multiple :class:`Result` instances or not.

    A multi-cascade plot will be displayed if there are multiple years or if there are multiple
    results. Thus this function is always guaranteed to return a single figure.

    :param results: A single :class:`Result` instance, or list of instances
    :param cascade: A cascade specification supported by :func:`sanitize_cascade`
    :param pops: A population specification supported by :func:`sanitize_pops` - must correspond to a single aggregation
    :param year: A single year, or multiple years (can be a scalar, list, or array)
    :param data: A :class:`ProjectData` instance
    :param show_table: If ``True`` and a multi-cascade plot is generated, then the loss table will also be shown
    :return: Figure object containing the plot that was produced

    """
    year = sc.promotetolist(year)
    results = sc.promotetolist(results)
    if len(year) > 1 or len(results) > 1:
        output = plot_multi_cascade(results=results, cascade=cascade, pops=pops, year=year, data=data, show_table=show_table)
    else:
        fig = plot_single_cascade(result=results[0], cascade=cascade, pops=pops, year=year, data=data)
        table = None
        output = (fig, table)
    return output  # Either fig or (fig,table)

def sanitize_cascade(framework, cascade) -> tuple:
    """
    Normalize cascade inputs

    For convenience, users can specify cascades in one of several
    representations. To facilitate working with these representations on the
    backend, this function turns any valid representation into a dictionary
    mapping cascade stage names to a list of compartments/characs. It also
    returns the name of the cascade (if one is present) for use in plot
    titles.

    As an example of the cascade dictionary, suppose the spreadsheet had
    stages

    - Stage 1 - ``sus,vac,inf``
    - Stage 2 - ``vac,inf``

    Then example usage would be:

    >>> sanitize_cascade(framework,'main')[1]
    {'Stage 1':['sus','vac','inf'],'Stage 2':['vac','inf']

    This function also validates the cascade, so it is not necessary to call :func:`validate_cascade` separately.

    :param framework: A :class:`ProjectFramework` instance
    :param cascade: Supported cascade representation. Could be
        - A string cascade name
        - An integer specifying the index of the cascade
        - ``None``, which maps to the first cascade in the framework
        - A ``list`` of cascade stages
        - A ``dict`` defining the cascade The first three input formats will
          result in the cascade name also being returned (otherwise it will be
          assigned ``None``
    :return: A tuple with ``(cascade_name,cascade_dict)`` - the cascade name
        is ``None`` if the cascade was specified as a ``list`` or ``dict``

    """

    if cascade is None:
        cascade = 0  # Use the first cascade

    if isinstance(cascade, list):
        # Assemble cascade from comp/charac names using the display name as the stage name
        outputs = sc.odict()
        for name in cascade:
            spec = framework.get_variable(name)[0]
            outputs[spec['display name']] = [spec.name]
        cascade = outputs
    elif isinstance(cascade, int):
        # Retrieve the cascade name based on index
        cascade = framework.cascades.keys()[cascade]

    if sc.isstring(cascade):
        cascade_name = cascade
        df = framework.cascades[cascade_name]
        cascade_dict = sc.odict()
        for _, stage in df.iterrows():
            cascade_dict[stage[0]] = [x.strip() for x in stage[1].split(',')]  # Split the name of the stage and the constituents
    else:
        cascade_name = None
        cascade_dict = cascade

    validate_cascade(framework, cascade_dict)  # Check that the requested cascade dictionary is valid

    return cascade_name,cascade_dict

def sanitize_pops(pops,pop_source) -> dict:
    """
    Sanitize input populations

    The input populations could be specified as

    - A list or dict (with single key) containing either population code names
      or full names (e.g. from the FE)
    - A string like 'all'
    - None, which is shorthand for all populations

    For cascade purposes, the specified populations must evaluate to a single
    aggregation. That is, a cascade plot can only be made for a single group
    of people at a time.

    :param pops: The population representation to sanitize (list, dict,
        string)
    :param pop_source: Object to draw available populations from (a
        :class:`Result` or :class:`PlotData`)
    :return: A dict with a single key that can be used by :class:`PlotData` to
        specify populations

    """

    # Retrieve a list mapping result names to labels
    if isinstance(pop_source,Result):
        available = [(x.name,x.label) for x in pop_source.model.pops]
    elif isinstance(pop_source,ProjectData):
        available = [(x,y['label']) for x,y in pop_source.pops.items()]
    else:
        raise Exception("Unrecognized source for pop names - must be a Result or a ProjectData instance")

    def sanitize_name(name):
        name = name.strip()
        for x,y in available:
            if x == name or y == name:
                return x,y
        raise Exception('Name "%s" not found' % (name))

    if pops in [None, 'all', 'All', 'aggregate', 'total']:
        # If populations are an aggregation for all pops, then set the dict appropriately
        pops = {'Entire population': [x[0] for x in available]}

    elif isinstance(pops,list) or sc.isstring(pops):
        # If it's a list or string, convert it to a dict
        if sc.isstring(pops):
            pops = sc.promotetolist(pops)

        code_names = [sanitize_name(x)[0] for x in pops]

        if len(code_names) > 1:
            pops = {'Selected populations': code_names}
        else:
            pops = {sanitize_name(code_names[0])[1]:[code_names[0]]}

    assert isinstance(pops,dict) # At this point, it should be a dictionary
    assert len(pops) == 1, 'Aggregation must evaluate to only one output population'

    return sc.odict(pops) # Make sure an odict gets returned rather than a dict

def validate_cascade(framework, cascade, cascade_name=None, fallback_used:bool =False) -> bool:
    """
    Check if a cascade is valid

    A cascade is invalid if any stage does not contain a compartment that appears in subsequent stages i.e.
    if the stages are not all nested.

    :param framework: A :class:`ProjectFramework` instance
    :param cascade: A cascade representation supported by :func:`sanitize_cascade`
    :param cascade_name: Name of cascade to be printed in error messages
    :param fallback_used: If ``True``, then in the event that the cascade is not valid, the error message will reflect the fact that it was not a user-defined cascade
    :return: ``True`` if the cascade is valid
    :raises: ``InvalidCascade`` if the cascade is not valid

    """

    if not isinstance(cascade,dict):
        sanitize_cascade(framework, cascade) # This will result in a call to validate_cascade()
        return True
    else:
        cascade_dict = cascade

    if len(cascade_dict) < 2:
        # A 'cascade' with 0 or 1 stages is by definition valid, although it would not be sensible!
        return True

    expanded = sc.odict()
    for stage, includes in cascade_dict.items():
        expanded[stage] = framework.get_charac_includes(includes)

    for i in range(0, len(expanded) - 1):
        if not (set(expanded[i + 1]) <= set(expanded[i])):
            message = ''
            if fallback_used:
                message += 'The fallback cascade is not properly nested\n\n'
            elif sc.isstring(cascade_name):
                message += 'The cascade "%s" is not properly nested\n\n' % (cascade_name)
            else:
                message += 'The requested cascade is not properly nested\n\n'

            message += 'Stage "%s" appears after stage "%s" so it must contain a subset of the compartments in "%s"\n\n' % (expanded.keys()[i + 1], expanded.keys()[i], expanded.keys()[i])
            message += 'After expansion of any characteristics, the compartments comprising these stages are:\n'
            message += '"%s" = %s\n' % (expanded.keys()[i], expanded[i])
            message += '"%s" = %s\n' % (expanded.keys()[i + 1], expanded[i + 1])
            message += '\nTo be valid, stage "%s" would need the following compartments added to it: %s' % (expanded.keys()[i], list(set(expanded[i + 1]) - set(expanded[i])))
            if fallback_used and not framework.cascades:
                message += '\n\nNote that the framework did not contain a cascade - in many cases, the characteristics do not form a valid cascade. You will likely need to explicitly define a cascade in the framework file'
            if fallback_used and framework.cascades:
                message += '\n\nAlthough the framework fallback cascade was not valid, user-specified cascades do exist. The fallback cascade should only be used if user cascades are not present.'
            elif sc.isstring(cascade):
                message += '\n\nTo fix this error, please modify the definition of the cascade in the framework file'

            raise InvalidCascade(message)

    return True

def plot_single_cascade_series(result=None, cascade=None, pops=None, data=None) -> list:
    """
    Plot stacked timeseries

    Plot a stacked timeseries of the cascade. Unlike a normal stacked plot, the shaded areas show losses
    so for example the overall height of the plot corresponds to the number of people in the first cascade stage.
    Thus instead of the cascade progressing from left to right, the cascade progresses from top to bottom.
    This way, the left-right axis can be used to show the change in cascade flow over time.


    :param results: A single result, or list of results. One figure will be generated for each result
    :param cascade: A cascade specification supported by :func:`sanitize_cascade`
    :param pops: A population specification supported by :func:`sanitize_pops` - must correspond to a single aggregation
    :param data: A :class:`ProjectData` instance
    :return: List of Figure objects for all figures that were generated

    """

    from .plotting import PlotData, plot_series  # Import here to avoid circular dependencies

    if isinstance(result, list):
        figs = []
        for r in result:
            figs.append(plot_single_cascade(r, cascade, pops, data))
        return figs

    assert isinstance(result, Result), 'Input must be a single Result object'

    cascade_name, cascade_dict = sanitize_cascade(result.framework,cascade)
    pops = sanitize_pops(pops,result)
    d = PlotData(result, outputs=cascade_dict, pops=pops)
    d.set_colors(outputs=d.outputs)

    figs = plot_series(d, axis='outputs')  # 1 result, 1 pop, axis=outputs guarantees 1 plot
    ax = figs[0].axes[0]

    if data is not None:
        t = d.tvals()[0]
        cascade_data, _ = get_cascade_data(data, result.framework, cascade_dict, pops, t)
        for stage, vals in cascade_data.items():
            color = d[d.results[0], d.pops[0], stage].color  # Get the colour of this quantity
            flt = ~np.isnan(vals)
            if np.any(flt):  # Need to only plot real values, because NaNs show up in mpld3 even though they don't appear in the normal figure
                ax.scatter(t[flt], vals[flt], marker='o', s=40, linewidths=1, facecolors=color, color='k', zorder=100)

    return figs

def plot_single_cascade(result=None, cascade=None, pops=None, year=None, data=None, title=False):
    """
    Plot cascade for a single result

    This is the fancy cascade plot, which only applies to a single result at a single time

    :param results: A single result, or list of results. One figure will be generated for each result
    :param cascade: A cascade specification supported by :func:`sanitize_cascade`
    :param pops: A population specification supported by :func:`sanitize_pops` - must correspond to a single aggregation
    :param year: A single year, can be a scalar or an iterable of length 1
    :param data: A :class:`ProjectData` instance
    :param title: Optionally override the title of the plot
    :return: Figure object containing the plot, or list of figures if multiple figures were produced

    """

    barcolor = (0.00, 0.15, 0.48)  # Cascade color -- array([0,38,122])/255.
    diffcolor = (0.85, 0.89, 1.00)  # (0.74, 0.82, 1.00) # Original: (0.93,0.93,0.93)
    losscolor = (0, 0, 0)  # (0.8,0.2,0.2)

    cascade_name, cascade_dict = sanitize_cascade(result.framework,cascade)
    pops = sanitize_pops(pops,result)

    if not year:
        year = result.t[-1]  # Draw cascade for last year
    year = sc.promotetoarray(year)

    if isinstance(result, list):
        figs = []
        for r in result:
            figs.append(plot_single_cascade(r, cascade, pops, year, data))
        return figs

    assert len(year) == 1
    assert isinstance(result, Result), 'Input must be a single Result object'
    cascade_vals, t = get_cascade_vals(result, cascade, pops, year)
    if data is not None:
        cascade_data, _ = get_cascade_data(data, result.framework, cascade, pops, year)
        cascade_data_array = np.hstack(cascade_data.values())

    assert len(t) == 1, 'Plot cascade requires time aggregation'
    cascade_array = np.hstack(cascade_vals.values())

    fig = plt.figure(figsize=default_figsize)
#    fig.set_figwidth(fig.get_figwidth()*1.5)
    ax = plt.gca()
    bar_x = np.arange(len(cascade_vals))
    h = plt.bar(bar_x, cascade_array, width=0.5, color=barcolor)
    if data is not None:
        non_nan = np.isfinite(cascade_data_array)
        if np.any(non_nan):
            plt.scatter(bar_x[non_nan], cascade_data_array[non_nan], s=40, c='#ff9900', marker='s', zorder=100)

    ax.set_xticks(np.arange(len(cascade_vals)))
    ax.set_xticklabels(['\n'.join(textwrap.wrap(x, 15)) for x in cascade_vals.keys()])

    ylim = ax.get_ylim()
    yticks = ax.get_yticks()
    data_yrange = np.diff(ylim)
    ax.set_ylim(-data_yrange * 0.2, data_yrange * 1.1)
    ax.set_yticks(yticks)
    for i, val in enumerate(cascade_array):
        plt.text(i, val * 1.01, '%s' % sc.sigfig(val, sigfigs=3, sep=True, keepints=True), verticalalignment='bottom', horizontalalignment='center', zorder=200)

    bars = h.get_children()
    conversion = cascade_array[1:] / cascade_array[0:-1]  # Fraction not lost
    conversion_text_height = cascade_array[-1] / 2

    for i in range(len(bars) - 1):
        left_bar = bars[i]
        right_bar = bars[i + 1]

        xy = np.array([
            (left_bar.get_x() + left_bar.get_width(), 0),  # Bottom left corner
            (left_bar.get_x() + left_bar.get_width(), left_bar.get_y() + left_bar.get_height()),  # Top left corner
            (right_bar.get_x(), right_bar.get_y() + right_bar.get_height()),  # Top right corner
            (right_bar.get_x(), 0),  # Bottom right corner
        ])

        p = matplotlib.patches.Polygon(xy, closed=True, facecolor=diffcolor)
        ax.add_patch(p)

        bbox_props = dict(boxstyle="rarrow", fc=(0.7, 0.7, 0.7), lw=1)

        t = ax.text(np.average(xy[1:3, 0]), conversion_text_height, '%s%%' % sc.sigfig(conversion[i] * 100, sigfigs=3, sep=True), ha="center", va="center", rotation=0, bbox=bbox_props)

    loss = np.diff(cascade_array)
    for i, val in enumerate(loss):

        plt.text(i, -data_yrange[0] * 0.02, 'Loss: %s' % sc.sigfig(-val, sigfigs=3, sep=True), verticalalignment='top', horizontalalignment='center', color=losscolor)

    pop_label = list(pops.keys())[0]
    plt.ylabel('Number of people')
    if title:
        if sc.isstring(cascade) and not cascade.lower() == 'cascade':
            plt.title('%s cascade for %s in %d' % (cascade, pop_label, year))
        else:
            plt.title('Cascade for %s in %d' % (pop_label, year))
    plt.tight_layout()

    return fig

def plot_multi_cascade(results=None, cascade=None, pops=None, year=None, data=None, show_table=None):
    """"
    Plot cascade for multiple results

    This is a cascade plot that handles multiple results and times
    Results are grouped by stage/output, which is not possible to do with plot_bars()

    :param results: A single result, or list of results. A single figure will be generated
    :param cascade: A cascade specification supported by :func:`sanitize_cascade`
    :param pops: A population specification supported by :func:`sanitize_pops` - must correspond to a single aggregation
    :param year: A scalar, or array of time points. Bars will be plotted for every time point
    :param data: A :class:`ProjectData` instance (currently not used)
    :param show_table: If ``True`` then a table with loss values will be rendered in the figure
    :return: Figure object containing the plot

    """

    if show_table is None:
        show_table = True

    # First, process the cascade into an odict of outputs for PlotData
    if isinstance(results, sc.odict):
        results = [result for _, result in results.items()]
    elif isinstance(results, Result):
        results = [results]
    elif isinstance(results, NDict):
        results = list(results)

    cascade_name, cascade_dict = sanitize_cascade(results[0].framework,cascade)
    pops = sanitize_pops(pops,results[0])

    if not year:
        year = results[0].t[-1]  # Draw cascade for last year
    year = sc.promotetoarray(year)

    if (len(results) > 1 and len(year) > 1):
        def label_fcn(result, t): return '%s (%s)' % (result.name, t)
    elif len(results) > 1:
        def label_fcn(result, t): return '%s' % (result.name)
    else:
        def label_fcn(result, t): return '%s' % (t)

    # Gather all of the cascade outputs and years
    cascade_vals = sc.odict()
    for result in results:
        for t in year:
            cascade_vals[label_fcn(result, t)] = get_cascade_vals(result, cascade, pops=pops, year=t)[0]

    # Determine the number of bars, per stage - based either on result or time point
    n_bars = len(cascade_vals)
    bar_width = 1.  # This is the width of the bars
    bar_gap = 0.15  # This is the width of the bars
    block_gap = 1.  # This is the gap between blocks
    block_size = n_bars * (bar_width + bar_gap)
    x = np.arange(0, len(cascade_vals[0].keys())) * (block_size + block_gap)  # One block for each cascade stage
    colors = sc.gridcolors(n_bars)  # Default colors
    legend_entries = sc.odict()

    fig = plt.figure(figsize=default_figsize)
#    fig.set_figwidth(fig.get_figwidth()*1.5)

    for offset, (bar_label, data) in enumerate(cascade_vals.items()):
        legend_entries[bar_label] = colors[offset]
        vals = np.hstack(data.values())
        plt.bar(x + offset * (bar_width + bar_gap), vals, color=colors[offset], width=bar_width)

    plot_legend(legend_entries, fig=fig)
    ax = fig.axes[0]
    ax.set_xticks(x + (block_size - bar_gap - bar_width) / 2)
    ax.set_xticklabels(['\n'.join(textwrap.wrap(k, 15)) for k in cascade_vals[0].keys()])
    if show_table:
        ax.get_xaxis().set_ticks_position('top')

    # Make the loss table
    cell_text = []
    for data in cascade_vals.values():
        cascade_array = np.hstack(data.values())
        loss = np.diff(cascade_array)
        loss_str = ['%s' % sc.sigfig(-val, sigfigs=3, sep=True) for val in loss]
        loss_str.append('-')  # No loss for final stage
        cell_text.append(loss_str)

    # Clean up formatting
    yticks = ax.get_yticks()
    ax.set_yticks(yticks[1:])  # Remove the first tick at 0 so it doesn't clash with table - TODO: improve table spacing so this isn't needed
    plt.ylabel('Number of people')
    if show_table:
        plt.subplots_adjust(top=0.8, right=0.75, left=0.2, bottom=0.25)
    else:
        plt.subplots_adjust(top=0.95, right=0.75, left=0.2, bottom=0.25)

    # Reset axes
    plt.tight_layout()

    # Add a table at the bottom of the axes
    row_labels = list(cascade_vals.keys())
    if show_table:
        plt.table(cellText=cell_text, rowLabels=row_labels, rowColours=None, colLabels=None, loc='bottom', cellLoc='center')
        return fig
    else:
        col_labels = [k for k in cascade_vals[0].keys()]
        table = {'text': cell_text, 'rowlabels': row_labels, 'collabels': col_labels}
        return fig, table

def get_cascade_vals(result, cascade, pops=None, year=None) -> tuple:
    """
    Get values for a cascade

    :param result: A single :class:`Result` instance
    :param cascade: A cascade representation supported by
        :func:`sanitize_cascade`
    :param pops: A string (like ``'all'``), a list of pops to aggregate, or a
        dict with a single key specifying an aggregation and the name of the
        resulting aggregation
    :param year: Optionally specify a subset of years to retrieve values for.
        Can be a scalar, list, or array. If ``None``, all time points in the
        result will be used
    :return: A tuple with ``(cascade_vals,t)`` where ``cascade_vals`` is the
        form ``{stage_name:np.array}`` and ``t`` is a ``np.array`` with the
        year values

    """

    from .plotting import PlotData  # Import here to avoid circular dependencies

    if pops in [None, 'all', 'All']:
        pops = 'total'

    # Sanitize the cascade inputs
    _, cascade_dict = sanitize_cascade(result.framework, cascade)

    if year is None:
        d = PlotData(result, outputs=cascade_dict, pops=pops)
    else:
        year = sc.promotetoarray(year)
        d = PlotData(result, outputs=cascade_dict, pops=pops)
        d.interpolate(year)

    assert len(d.pops) == 1, 'get_cascade_vals() cannot get results for multiple populations or population aggregations, only a single pop or single aggregation'
    cascade_vals = sc.odict()
    for result in d.results:
        for pop in d.pops:
            for output in d.outputs:
                cascade_vals[output] = d[(result, pop, output)].vals  # NB. Might want to return the Series here to retain formatting, units etc.
    t = d.tvals()[0]  # nb. first entry in d.tvals() is time values, second entry is time labels

    return cascade_vals, t

def get_cascade_data(data, framework, cascade, pops=None, year=None):
    """
    Get data values for a cascade

    This function is the counterpart to :func:`get_cascade_vals` but it
    returns values from data rather than values from a :class:`Result`. Note
    that the inputs and outputs are slightly different - this function still
    needs the framework so that it can sanitize the requested cascade. If
    ``year`` is specified, the output is guaranteed to be the same size as the
    input year array, the same as :func:`get_cascade_vals`. However, the
    :func:`get_cascade_vals` defaults to all time points in the simulation
    output, whereas this function defaults to all data years. Thus, if the
    year is omitted, the returned time points may be different between the two
    functions. To make a plot superimposing data and model output, the year
    should be specified explicitly to ensure that the years match up.


    NB - In general, data probably will NOT exist
    Set the logging level to 'DEBUG' to have messages regarding this printed out

    :param data: A :class:`ProjectData` instance
    :param framework: A :class:`ProjectFramework` instance
    :param cascade: A cascade representation supported by
        :func:`sanitize_cascade`
    :param pops: Supported population representation. Can be 'all', or a pop
        name, or a list of pop names, or a dict with one key
    :param year: Optionally specify a subset of years to retrieve values for.
        Can be a scalar, list, or array. If ``None``, all time points in the
        :class:`ProjectData` instance will be used
    :return: A tuple with ``(cascade_vals,t)`` where ``cascade_vals`` is the
        form ``{stage_name:np.array}`` and ``t`` is a ``np.array`` with the
        year values

    """


    if pops is None:
        pops = 'all'

    _, cascade_dict = sanitize_cascade(framework, cascade)
    pops = sanitize_pops(pops,data)[0] # Get list representation since we don't care about the name of the aggregated pop

    if year is not None:
        t = sc.promotetoarray(year)  # Output times are guaranteed to be
    else:
        t = data.tvec  # Defaults to data's time vector

    # Now, get the outputs in the given years
    data_values = dict()
    for stage_constituents in cascade_dict.values():
        if sc.isstring(stage_constituents):
            stage_constituents = [stage_constituents]  # Make it a list - this is going to be a common source of errors otherwise
        for code_name in stage_constituents:
            if code_name not in data_values:
                data_values[code_name] = np.zeros(t.shape) * np.nan  # data values start out as NaN - this is a fallback in case for some reason pops is empty (the data will be all NaNs then)

                for pop_idx, pop in enumerate(pops):
                    ts = data.get_ts(code_name, pop)  # The TimeSeries data for the required variable and population
                    vals = np.ones(t.shape) * np.nan  # preallocate output values coming from this TimeSeries object

                    # Now populate this array
                    if ts is not None:
                        for i, tval in enumerate(ts.t):
                            match = np.where(t == tval)[0]
                            if len(match):  # If a time point in the TimeSeries matches the requested time - then match[0] is the index in t
                                vals[match[0]] = ts.vals[i]
                        if np.any(np.isnan(vals)):
                            logger.debug('Data for %s (%s) did not contain values for some of the requested years' % (code_name, pop))
                    else:
                        logger.debug('Data not present for %s (%s)' % (code_name, pop))

                    if pop_idx == 0:
                        data_values[code_name] = vals  # If at least one TimeSeries was found, use the first one as the data values (it could still be NaN if no times match)
                    else:
                        data_values[code_name] += vals

    # Now, data values contains all of the required quantities in all of the required years. Last step is to aggregate them
    cascade_data = sc.odict()
    for stage_name, stage_constituents in cascade_dict.items():
        for code_name in stage_constituents:
            if stage_name not in cascade_data:
                cascade_data[stage_name] = data_values[code_name]
            else:
                cascade_data[stage_name] += data_values[code_name]

    return cascade_data, t

