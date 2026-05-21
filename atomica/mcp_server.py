import io
from mcp.server.fastmcp import FastMCP
from atomica import ProjectFramework, generate_framework_doc as _generate_framework_doc

mcp = FastMCP(
    "atomica",
    instructions=(
        "Use the generate_framework_doc tool whenever the user asks questions about "
        "model structure, compartments, characteristics, parameters, or any quantity "
        "defined in a framework file. Call it with the path to the framework .xlsx file "
        "before answering, so your response is grounded in the actual framework contents."
    ),
)


@mcp.tool()
def generate_framework_doc(framework_path: str, databook_only: bool = False) -> str:
    """
    Return a plain-text Markdown description of an Atomica framework file.

    Use this whenever the user asks questions about model structure, compartments,
    parameters, characteristics, or any quantity defined in the framework.

    :param framework_path: Path to the framework .xlsx file
    :param databook_only: If True, only include quantities that appear in the databook
    :return: Markdown string describing the framework
    """
    framework = ProjectFramework(framework_path)
    buf = io.StringIO()
    _generate_framework_doc(framework, buf, databook_only=databook_only)
    return buf.getvalue()


if __name__ == "__main__":
    mcp.run()
