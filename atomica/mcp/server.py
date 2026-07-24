from typing import Annotated
import pandas as pd
from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
import atomica as at
from atomica.function_parser import parse_function
from atomica.mcp.skills import register_skills

mcp = FastMCP(
    "atomica",
    instructions=(
        "Tools for querying Atomica framework .xlsx files. "
        "A framework defines compartmental model structure and all variable definitions "
        "(compartments, characteristics, parameters, interactions); "
        "population and calibration data lives in the databook, not the framework.\n\n"
        "Use list_variables as the first step whenever the user asks which parameter, "
        "compartment, or variable corresponds to a concept (e.g. 'which parameter is TB incidence?', "
        "'what does inci_per_100k mean?'). Do not search code or files for this until after you have tried "
        "these tools, as they are the authoritative source for framework variable lookups. "
        "Use detail_parameter for parameters (includes transition compartment info); "
        "use detail_variable for compartments, characteristics, and interactions.\n\n"
        "Databook data values (the population/calibration time series) are read with "
        "get_data_values (raw stored points) and evaluate_data_values (interpolated values at "
        "chosen years, for comparing across populations), and modified with set_data_values and "
        "clear_data_values. Use get_populations to list the databook's populations."
    ),
)


@mcp.tool()
def list_variables(
    framework_path: Annotated[str, Field(description="Absolute path to the .xlsx framework file")],
    search_terms: list[str] | None = None,
) -> dict:
    """
    Return {code_name: {"display name": ..., "type": ...}} for all variables.
    Types: "comp" (compartment), "charac" (characteristic), "par" (parameter), "interpop" (interaction).
    search_terms filters by case-insensitive substring against code name or display name; any term matches.
    Use this as the first step when the user asks which variable corresponds to a concept
    (e.g. "incidence", "mortality"). Pass the concept as a search term.
    """
    F = at.ProjectFramework(framework_path)
    result = {}
    for df, vtype in [
        (F.comps, "comp"),
        (F.characs, "charac"),
        (F.pars, "par"),
        (F.interactions, "interpop"),
    ]:
        display = df['display name']
        if search_terms:
            idx = display.index.to_series()
            mask = pd.Series(False, index=display.index)
            for term in search_terms:
                mask |= (
                    idx.str.contains(term, case=False, regex=False) |
                    display.str.contains(term, case=False, regex=False)
                )
            display = display[mask]
        for code_name, display_name in display.items():
            result[code_name] = {"display name": display_name, "type": vtype}
    return result


@mcp.tool()
def detail_variable(
    framework_path: Annotated[str, Field(description="Absolute path to the .xlsx framework file")],
    code_name: Annotated[str, Field(description="Code name or display name of the variable")],
) -> dict:
    """
    Return the full metadata row for a compartment, characteristic, or interaction.
    For parameters, use detail_parameter instead.
    """
    F = at.ProjectFramework(framework_path)
    series, var_type = F.get_variable(code_name)
    result = series.to_dict()
    result['type'] = var_type
    return result


@mcp.tool()
def detail_parameter(
    framework_path: Annotated[str, Field(description="Absolute path to the .xlsx framework file")],
    code_name: Annotated[str, Field(description="Code name or display name of the parameter")],
) -> dict:
    """
    Return the full metadata row for a parameter, including transition and dependency information.
    "transitions": [[from_comp, to_comp], ...] pairs governed by this parameter.
    "transition_compartments": full metadata for each compartment in those transitions.
    "function_dependencies": {code_name: display_name} for variables referenced in the parameter function.
    """
    F = at.ProjectFramework(framework_path)
    series, var_type = F.get_variable(code_name)
    result = series.to_dict()
    result['type'] = var_type

    pairs = F.transitions[series.name]
    result['transitions'] = [list(p) for p in pairs]
    comp_codes = {comp for pair in pairs for comp in pair}
    result['transition_compartments'] = {c: F.comps.loc[c].to_dict() for c in comp_codes}

    fcn = series.get('function')
    if fcn and not pd.isna(fcn):
        _, deps = parse_function(fcn)
        deps_out = {}
        for dep in deps:
            try:
                dep_series, _ = F.get_variable(dep)
                deps_out[dep] = dep_series['display name']
            except Exception:
                deps_out[dep] = None
        result['function_dependencies'] = deps_out
    else:
        result['function_dependencies'] = {}

    return result


@mcp.tool()
def map_transitions(
    framework_path: Annotated[str, Field(description="Absolute path to the .xlsx framework file")],
    code_name: Annotated[str, Field(description="Code name of a source compartment")],
) -> list:
    """
    Return all transitions out of a given source compartment
    :return: A list of tuples containing (destination compartment, parameter driving transition). A parameter '>'
             corresponds to the residual outflow from a junction.
    """
    F = at.ProjectFramework(framework_path)
    out = []
    for par, pairs in F.transitions.items():
        for src, dst in pairs:
            if code_name == src:
                out.append([dst, par])
    return out

@mcp.tool()
def get_populations(
    framework_path: Annotated[str, Field(description="Absolute path to the .xlsx framework file")],
    databook_path: Annotated[str, Field(description="Absolute path to the .xlsx databook file")],
) -> dict:
    """
    Return the populations defined in the databook.

    Returns ProjectData.pops: a dict keyed by population code name, each value a dict with at
    minimum 'label' (the population full name) and 'type' (the population type).
    """
    F, D = _load(framework_path, databook_path)
    return dict(D.pops)


# ---------------------------------------------------------------------------
# Helpers for reading/writing databook data values
# ---------------------------------------------------------------------------


def _load(framework_path: str, databook_path: str):
    """Load a framework and its databook. Returns ``(ProjectFramework, ProjectData)``."""
    F = at.ProjectFramework(framework_path)
    D = at.ProjectData.from_spreadsheet(databook_path, F)
    return F, D


def _num(x):
    """Coerce to a JSON-safe float (NaN -> None); pass ``None`` through."""
    if x is None:
        return None
    x = float(x)
    return None if x != x else x


def _fmt_year(t) -> str:
    """Format a (float) year as a compact dict key: ``'2018'`` or ``'2000.4972677595629'``."""
    t = float(t)
    return str(int(t)) if t.is_integer() else str(t)


def _row_to_str(row_key, key_type: str):
    """Return ``(string_key, extra_fields)`` for a container row key."""
    if key_type == "connection":
        return "%s->%s" % (row_key[0], row_key[1]), {"from": row_key[0], "to": row_key[1]}
    return row_key, {}


def _str_to_row(row_str: str, key_type: str):
    """Convert an external row key string back to the internal container key."""
    if key_type == "connection":
        parts = row_str.split("->")
        if len(parts) != 2:
            raise ValueError("Connection row key %r must be of the form 'from_pop->to_pop'" % row_str)
        return (parts[0], parts[1])
    return row_str


def _find_container(F, D, code_name: str):
    """
    Locate the data container for a variable/transfer/interaction.

    :return: ``(container, key_type, code_name, display_name, var_type)`` where ``container`` is a
             ``TimeDependentValuesEntry`` or ``TimeDependentConnections``, and ``key_type`` is
             ``'population'`` (compartment/characteristic/parameter) or ``'connection'``
             (transfer/interaction).
    """
    resolved = code_name
    display_name = None
    var_type = None
    try:
        series, var_type = F.get_variable(code_name)
        resolved = series.name
        display_name = series["display name"]
    except Exception:
        pass  # transfers are not defined in the framework - fall through to the databook

    if resolved in D.tdve:
        tdve = D.tdve[resolved]
        return tdve, "population", resolved, (display_name or tdve.name), (var_type or "par")

    for tdc in list(D.transfers) + list(D.interpops):
        if code_name in (tdc.code_name, tdc.full_name) or resolved == tdc.code_name:
            return tdc, "connection", tdc.code_name, tdc.full_name, tdc.type

    valid = list(D.tdve.keys()) + [t.code_name for t in list(D.transfers) + list(D.interpops)]
    raise KeyError("No variable, transfer, or interaction named %r in the databook. Valid code names: %s" % (code_name, sorted(valid)))


@mcp.tool()
def get_data_values(
    framework_path: Annotated[str, Field(description="Absolute path to the .xlsx framework file")],
    databook_path: Annotated[str, Field(description="Absolute path to the .xlsx databook file")],
    code_name: Annotated[str, Field(description="Code name or display name of the variable, transfer, or interaction")],
    populations: Annotated[list[str] | None, Field(description="Optional filter: population code names, or 'from->to' keys for transfers/interactions. Omit to return every row.")] = None,
) -> dict:
    """
    Return all stored data values for a single variable (or transfer/interaction), one entry per row.

    Return shape::

        {
          "code_name": ..., "display_name": ..., "type": ..., "key_type": "population"|"connection",
          "container_tvec": [years that will be written to the spreadsheet],
          "rows": {
            "<pop or from->to>": {"units": ..., "assumption": <constant or null>, "sigma": ...,
                                  "data": {"<year>": <value>, ...}}
          },
          "all_row": true  # only present if the variable stores a single 'All' row for every population
        }

    'data' maps year->value for time-specific points ({} if the row holds only a constant);
    'assumption' is the time-independent constant, used only when 'data' is empty. Covers the common
    query patterns: a single point (read the year from a row's 'data'), all years for one population
    (pass 'populations'), or all populations/years (omit 'populations').
    """
    F, D = _load(framework_path, databook_path)
    container, key_type, code, display_name, var_type = _find_container(F, D, code_name)

    rows = {}
    for row_key, ts in container.ts.items():
        out_key, extra = _row_to_str(row_key, key_type)
        if populations is not None and out_key not in populations:
            continue
        row = {
            "units": ts.units,
            "assumption": _num(ts.assumption),
            "sigma": _num(ts.sigma),
            "data": {_fmt_year(t): _num(v) for t, v in zip(ts.t, ts.vals)},
        }
        row.update(extra)
        rows[out_key] = row

    result = {
        "code_name": code,
        "display_name": display_name,
        "type": var_type,
        "key_type": key_type,
        "container_tvec": [float(x) for x in container.tvec],
        "rows": rows,
    }
    if key_type == "population" and ({"all", "All"} & set(container.ts.keys())):
        result["all_row"] = True
    return result


@mcp.tool()
def evaluate_data_values(
    framework_path: Annotated[str, Field(description="Absolute path to the .xlsx framework file")],
    databook_path: Annotated[str, Field(description="Absolute path to the .xlsx databook file")],
    code_name: Annotated[str, Field(description="Code name or display name of the variable, transfer, or interaction")],
    years: Annotated[list[float], Field(description="Years at which to evaluate the (interpolated) value")],
    populations: Annotated[list[str] | None, Field(description="Optional row filter: population code names, or 'from->to' keys. Omit for every row.")] = None,
) -> dict:
    """
    Return interpolated values at the requested years for each row of a single variable.

    Mirrors what the simulation uses: linear interpolation between stored points with flat (constant)
    extrapolation beyond the ends; a row with only a constant returns that constant at every year; a
    row with no data returns null. Useful for comparing a variable across populations whose stored
    years differ.

    Return: ``{"<pop or from->to>": {"years": [...], "values": [...]}}`` (values may contain nulls).
    """
    F, D = _load(framework_path, databook_path)
    container, key_type, code, display_name, var_type = _find_container(F, D, code_name)

    years_f = [float(y) for y in years]
    out = {}
    for row_key, ts in container.ts.items():
        out_key, _ = _row_to_str(row_key, key_type)
        if populations is not None and out_key not in populations:
            continue
        if ts.has_data:
            values = [_num(v) for v in ts.interpolate(years_f)]
        else:
            values = [None] * len(years_f)
        out[out_key] = {"years": years_f, "values": values}
    return out


@mcp.tool(
    annotations=ToolAnnotations(
        title="Set databook values",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
    )
)
def set_data_values(
    framework_path: Annotated[str, Field(description="Absolute path to the .xlsx framework file")],
    databook_path: Annotated[str, Field(description="Absolute path to the .xlsx databook file to read")],
    output_path: Annotated[str, Field(description="Absolute path to write the modified databook. Pass the same value as databook_path to overwrite it in place.")],
    code_name: Annotated[str, Field(description="Code name or display name of the variable, transfer, or interaction")],
    rows: Annotated[dict, Field(description="Values to set, keyed by population code name (or 'from->to' for transfers/interactions). Each value is a dict that may contain 'data' ({year: value}), 'assumption' (the time-independent constant, or null to clear it), 'sigma', and 'units'.")],
    mode: Annotated[str, Field(description="'merge' (default): set only the given years/assumption and keep other points. 'replace': clear each listed row first, then set the given values.")] = "merge",
) -> dict:
    """
    Set data values for a single variable (or transfer/interaction) and save the databook.

    'rows' uses the same shape as get_data_values' output, e.g. ``{"adults": {"data": {"2026": 100}}}``.

    - mode='merge' overwrites/adds only the given points; mode='replace' clears the row first (its
      time points and constant), preserving units and (unless overridden) uncertainty.
    - The time-independent constant is set via a row's 'assumption' key; note it is ignored by the
      simulation whenever the row also has time-specific 'data'.
    - To make a value apply "from year Y onwards", first call clear_data_values(..., start_year=Y),
      then set the value at Y (flat extrapolation then carries it forward).
    - Unknown row keys are rejected; new populations/connections are not created by this tool.

    Returns a summary: ``{"output_path", "code_name", "mode", "changes": [...], "warnings": [...]}``.
    """
    if mode not in ("merge", "replace"):
        raise ValueError("mode must be 'merge' or 'replace', got %r" % mode)

    F, D = _load(framework_path, databook_path)
    container, key_type, code, display_name, var_type = _find_container(F, D, code_name)

    valid = {_row_to_str(k, key_type)[0] for k in container.ts.keys()}
    changes = []
    warnings = []

    for row_str, spec in rows.items():
        if row_str not in valid:
            raise KeyError("Unknown row %r for %r. Valid rows: %s. New populations/connections are not created by this tool." % (row_str, code, sorted(valid)))
        ts = container.ts[_str_to_row(row_str, key_type)]

        old_assumption = ts.assumption
        old_data = {float(t): v for t, v in zip(ts.t, ts.vals)}

        if mode == "replace":
            kept_units, kept_sigma = ts.units, ts.sigma
            ts.clear()
            ts.units = kept_units
            if "sigma" not in spec:
                ts.sigma = kept_sigma

        if "units" in spec:
            ts.units = spec["units"]
        if "sigma" in spec:
            ts.sigma = None if spec["sigma"] is None else float(spec["sigma"])

        if "assumption" in spec:
            a = spec["assumption"]
            if a is None:
                ts.assumption = None
            else:
                ts.insert(None, a)
            changes.append({"row": row_str, "assumption": True, "old": _num(old_assumption), "new": _num(ts.assumption)})

        data = spec.get("data") or {}
        for year_key, value in data.items():
            year = float(year_key)
            ts.insert(year, value)
            changes.append({"row": row_str, "year": year, "old": _num(old_data.get(year)), "new": _num(value)})

        if mode == "replace":
            dropped = sorted(set(old_data) - {float(y) for y in data})
            if dropped:
                changes.append({"row": row_str, "cleared_years": dropped})

        if ts.assumption is not None and len(ts.t) > 0:
            warnings.append("Row %r has both a constant/assumption and time data; the constant is ignored while time data is present." % row_str)

    D.save(output_path)
    return {"output_path": str(output_path), "code_name": code, "mode": mode, "changes": changes, "warnings": warnings}


@mcp.tool(
    annotations=ToolAnnotations(
        title="Clear databook values",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
    )
)
def clear_data_values(
    framework_path: Annotated[str, Field(description="Absolute path to the .xlsx framework file")],
    databook_path: Annotated[str, Field(description="Absolute path to the .xlsx databook file to read")],
    output_path: Annotated[str, Field(description="Absolute path to write the modified databook. Pass the same value as databook_path to overwrite it in place.")],
    code_name: Annotated[str, Field(description="Code name or display name of the variable, transfer, or interaction")],
    populations: Annotated[list[str] | None, Field(description="Rows to clear (population code names, or 'from->to'). Omit to clear every row of this variable.")] = None,
    start_year: Annotated[float | None, Field(description="Remove time points at or after this year (inclusive). Omit for no lower bound.")] = None,
    end_year: Annotated[float | None, Field(description="Remove time points at or before this year (inclusive). Omit for no upper bound.")] = None,
    clear_assumption: Annotated[bool, Field(description="Also clear the time-independent constant/assumption for the affected rows.")] = False,
) -> dict:
    """
    Remove data values from a single variable (or transfer/interaction) and save the databook.

    - Removes time points within the inclusive [start_year, end_year] range (either bound may be
      omitted). If both bounds are omitted, every time point of each affected row is removed.
    - Set clear_assumption=True to also remove the time-independent constant.
    - Common pattern, "use value V from year Y onwards": clear_data_values(..., start_year=Y) then
      set_data_values(..., rows={row: {"data": {Y: V}}}).

    Returns a summary: ``{"output_path", "code_name", "changes": [...]}``.
    """
    F, D = _load(framework_path, databook_path)
    container, key_type, code, display_name, var_type = _find_container(F, D, code_name)

    valid = {_row_to_str(k, key_type)[0] for k in container.ts.keys()}
    targets = populations if populations is not None else sorted(valid)
    changes = []

    for row_str in targets:
        if row_str not in valid:
            raise KeyError("Unknown row %r for %r. Valid rows: %s." % (row_str, code, sorted(valid)))
        ts = container.ts[_str_to_row(row_str, key_type)]

        removed = []
        for t in list(ts.t):
            if (start_year is None or t >= start_year) and (end_year is None or t <= end_year):
                ts.remove(t)
                removed.append(float(t))

        entry = {"row": row_str, "removed_years": removed}
        if clear_assumption and ts.assumption is not None:
            entry["cleared_assumption"] = _num(ts.assumption)
            ts.assumption = None
        changes.append(entry)

    D.save(output_path)
    return {"output_path": str(output_path), "code_name": code, "changes": changes}


register_skills(mcp)
