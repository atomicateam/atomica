# Atomica

[![PyPi version](https://badgen.net/pypi/v/atomica/)](https://pypi.org/project/atomica)
[![Tests](https://github.com/atomicateam/atomica/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/atomicateam/atomica/actions/workflows/tests.yml)

Atomica is a simulation engine for compartmental models. It can be used to simulate disease epidemics, health care cascades, and many other things.

For detailed documentation, visit [https://atomica.tools/docs](https://atomica.tools/docs)

## Installation

Atomica requires Python 3.11 or later and is distributed via PyPI. To install, run

```
pip install atomica
```

Atomica is mainly used as the modelling platform for downstream analyses. Therefore, the most common usage is to set up an analysis-specific repository, and simply include `atomica` as a dependency that will be installed automatically via PyPI. We recommend using [uv](https://docs.astral.sh/uv/) to manage Python environments, in which case `atomica` can be added as a dependency using

```
uv add atomica
```

## Claude Code integration

Atomica ships an MCP server (`atomica.mcp`) that exposes tools for querying framework and databook files and a set of built-in workflow skills (MCP prompts). The tools let Claude read compartments, parameters, transitions, and variable metadata directly from `.xlsx` framework files, as well as read and write data in `.xlsx` databook files. The skills guide Claude through multi-step workflows such as producing a structured summary of a framework.

To register the server with Claude Code, run the following from within your project directory:

```
claude mcp add atomica -- uv run python -m atomica.mcp
```

Once added, the tools and skills are available automatically in any Claude Code session for that project. If you use Atomica across multiple projects and want the MCP server available in all of them without repeating the `claude mcp add` step, register it at the user level instead:

```
claude mcp add -s user atomica -- uv run python -m atomica.mcp
```

The Atomica MCP will then be used whenever you are working within a project that has `atomica` as a dependency.

## Advanced usage

### Using a branch in a downstream project

To use an Atomica branch in a downstream project with `uv`, you can add the Git repository directly as a dependency

```
uv add git+https://github.com/atomicateam/atomica --branch <branch name>
```

For more information on this usage, see https://docs.astral.sh/uv/concepts/projects/dependencies/.

### Developer installation

If you want to install a different branch of Atomica, or plan to make changes to the Atomica source code, you will need to install Atomica via Git rather than via PyPI. 

```
git clone https://github.com/atomicateam/atomica.git
cd atomica
pip install -e .
```

If using `uv`, simply cloning the repository is sufficient, and scripts can be run with `uv run`. If you are developing Atomica in parallel with your own analysis repository, it would be recommended to clone `atomica` and then install it in your analysis repository as an editable package with `uv` 

```
uv add --editable ../<path to atomica>
```

In which case you can edit your local copy of Atomica and have it reflected in your analysis code. 

### Running tests

Atomica includes a suite of tests. The automated test suite can be executed with `pytest`. 

```
uv run --extra test pytest
```

Note the inclusion of the extra `test` dependencies that are not installed by default. Many of the tests open `matplotlib` figures as part of the test. If the test script is run on a machine without a display available, the error

```
_tkinter.TclError: couldn't connect to display "localhost:0.0"
```

will be raised. In that case, simply set the `matplotlib` backend to `agg` which allows the calls to succeed with a display present. For example, run

```
export MPLBACKEND=agg
uv run --extra test pytest
```

To also validate the example and tutorial notebooks, include the `nbval` options:

```
uv run --extra test pytest --nbval-lax --current-env --nbval-cell-timeout=600 --dist loadscope
```

This will reproduce the automated testing that is executed on GitHub as part of the CI workflow. 

### Adding custom skills

The MCP server publishes a set of skills, which are plain Markdown files in `atomica/mcp/skills/`. To add a new workflow, add a `.md` file into that directory — it is registered as an MCP prompt automatically when the server starts, with no code changes required. The first `# Heading` line becomes the prompt description shown in the MCP client.

## Troubleshooting

### Installation fails due to missing `numpy`

If running `pip install -e .` in a new environment, `numpy` must be installed prior to `scipy`. In some cases,
installing `numpy` may fail due to missing compiler options. In that case, you may wish to install `numpy` via Anaconda
(by installing Python through Anaconda, and using `conda install numpy scipy matplotlib`). In general, our experience
has been that it is easier to set up the C binaries for `numpy` and the QT dependencies for `matplotlib` via Anaconda
rather than doing this via the system, which involves different steps on every platform.

### Figure plotting hangs

On some systems, the default `matplotlib` backend may hang - this is not an issue with `atomica`. To resolve, try changing the backend by including 

```
import matplotlib
matplotlib.use("Qt5Agg")
```

at the very start of your script. A different backend may be required for your system. You can make the change persistant by setting the backend in your `matplotlibrc` file.
