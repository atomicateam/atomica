import io
from typing import Annotated
import pandas as pd
from pydantic import Field
from mcp.server.fastmcp import FastMCP
from atomica import ProjectFramework, generate_framework_doc as _generate_framework_doc
from atomica.function_parser import parse_function

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
        "use detail_variable for compartments, characteristics, and interactions."
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
    fw = ProjectFramework(framework_path)
    result = {}
    for df, vtype in [
        (fw.comps, "comp"),
        (fw.characs, "charac"),
        (fw.pars, "par"),
        (fw.interactions, "interpop"),
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
    fw = ProjectFramework(framework_path)
    series, var_type = fw.get_variable(code_name)
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
    fw = ProjectFramework(framework_path)
    series, var_type = fw.get_variable(code_name)
    result = series.to_dict()
    result['type'] = var_type

    pairs = fw.transitions[series.name]
    result['transitions'] = [list(p) for p in pairs]
    comp_codes = {comp for pair in pairs for comp in pair}
    result['transition_compartments'] = {c: fw.comps.loc[c].to_dict() for c in comp_codes}

    fcn = series.get('function')
    if fcn and not pd.isna(fcn):
        _, deps = parse_function(fcn)
        deps_out = {}
        for dep in deps:
            try:
                dep_series, _ = fw.get_variable(dep)
                deps_out[dep] = dep_series['display name']
            except Exception:
                deps_out[dep] = None
        result['function_dependencies'] = deps_out
    else:
        result['function_dependencies'] = {}

    return result


if __name__ == "__main__":
    mcp.run()
