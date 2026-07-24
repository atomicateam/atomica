# Atomica

[![Build Status](https://dev.azure.com/AtomicaTeam/Atomica/_apis/build/status/atomicateam.atomica?branchName=master)](https://dev.azure.com/AtomicaTeam/Atomica/_build/latest?definitionId=1&branchName=master)

[![PyPi version](https://badgen.net/pypi/v/atomica/)](https://pypi.org/project/atomica)

Atomica is a simulation engine for compartmental models. It can be used to simulate disease epidemics, health care cascades, and many other things.

For detailed documentation, visit [https://atomica.tools/docs](https://atomica.tools/docs)

## Installation

Atomica requires Python 3.10 or later and is distributed via PyPI. To install, run

```
pip install atomica
```

## Git installation

If you want to install a different branch of Atomica, or plan to make changes to the Atomica source code, you will need to install Atomica via Git rather than via PyPI. This can be performed using

```
git clone https://github.com/atomicateam/atomica.git
cd atomica
pip install -e .
```

## Running tests

Atomica includes a suite of tests, some of which get automatically run and others that are used manually. The automated test suite can be executed with `pytest`, and can be run from within an isolated environment using `tox`. To use the tests, you will need to follow the steps above to perform a 'Git installation' because the tests are not included in the PyPI distribution. After installation, you can run individual test scripts from the `tests` directory with commands like:

```
python tests/testworkflow.py
```

Note that many of the tests open `matplotlib` figures as part of the test. If the test script is run on a machine without a display available, the error

```
_tkinter.TclError: couldn't connect to display "localhost:0.0"
```

will be raised. In that case, simply set the `matplotlib` backend to `agg` which allows the calls to succeed with a display present. For example, run

```
export MPLBACKEND=agg
python tests/testworkflow.py
```

To run the automated suite, install the test dependencies using

```
pip install -r requirements.txt
```

which will install the additional development dependencies. Then, to run the automated suite, from the root directory (the one containing `README.md`) run:

```
pytest
```

To run the tests in an isolated virtual environment, from the root directory, run

```
tox
```

If you don't have `tox`, install it using `pip install tox`. To test against a specific Python version, pass it as an argument, e.g.

```
tox -e py312
```

## Claude Code integration

Atomica ships an MCP server (`atomica.mcp`) that exposes tools for querying framework files and a set of built-in workflow skills (MCP prompts). The tools let Claude read compartments, parameters, transitions, and variable metadata directly from `.xlsx` framework files. The skills guide Claude through multi-step workflows such as producing a structured summary of a framework.

To register the server with Claude Code, run the following from within your project directory:

```
claude mcp add atomica -- uv run python -m atomica.mcp
```

Once added, the tools and skills are available automatically in any Claude Code session for that project. If you use Atomica across multiple projects and want the MCP server available in all of them without repeating the `claude mcp add` step, register it at the user level instead:

```
claude mcp add -s user atomica -- uv run python -m atomica.mcp
```

The Atomica MCP will then be used whenever you are working within a project that has `atomica` as a dependency.

### Adding custom skills

Skills are plain Markdown files in `atomica/mcp/skills/`. To add a new workflow, drop a `.md` file into that directory — it is registered as an MCP prompt automatically when the server starts, with no code changes required. The first `# Heading` line becomes the prompt description shown in the MCP client.

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
