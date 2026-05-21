import io
from mcp.server.fastmcp import FastMCP
from atomica import ProjectFramework, generate_framework_doc as _generate_framework_doc

mcp = FastMCP(
    "atomica",
    instructions=(
        "These tools work with Atomica framework .xlsx files. "
        "Use list_parameters to discover what parameters exist in a framework — "
        "it returns a mapping of code names to human-readable display names. "
        "Use detail_parameters to get the full metadata for a single parameter "
        "(format, default value, min/max, function, databook page, etc.) — "
        "it requires the parameter's code name, so call list_parameters first if "
        "the code name is unknown."
    ),
)

@mcp.tool()
def list_parameters(framework_path: str) -> dict:
    """
    Return all parameters in a framework as a mapping of code name to display name.

    Use this to discover what parameters exist, or to resolve a human-readable
    name to the code name required by detail_parameters.

    :param framework_path: Path to the framework .xlsx file
    :return: Dict mapping parameter code names to their display names
    """
    return ProjectFramework(framework_path).pars['display name'].to_dict()

@mcp.tool()
def detail_parameters(framework_path: str, par_name: str) -> dict:
    """
    Return the full metadata row for a single parameter.

    Use this when the user asks for specifics about a parameter: its format,
    default value, min/max bounds, function definition, databook page,
    whether it is targetable, timescale, etc. Requires the parameter's code
    name — call list_parameters first if only a display name is known.

    :param framework_path: Path to the framework .xlsx file
    :param par_name: Code name of the parameter (from list_parameters)
    :return: Dict of column name to value for the parameter's row
    """
    return ProjectFramework(framework_path).pars.loc[par_name].to_dict()


if __name__ == "__main__":
    mcp.run()
