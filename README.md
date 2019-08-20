# Atomica

[![Build Status](https://dev.azure.com/AtomicaTeam/Atomica/_apis/build/status/atomicateam.atomica?branchName=master)](https://dev.azure.com/AtomicaTeam/Atomica/_build/latest?definitionId=1&branchName=master)

Atomica is a simulation engine for compartmental models. It can be used to simulate disease epidemics, health care cascades, and many other things.

For detailed documentation, visit [https://atomica.tools/docs](https://atomica.tools/docs)

## Installation

Atomica is available for Python 3 only. Because we develop using Python 3.7, it is possible that dictionary order is relevant (although we endeavour to use ordered dictionaries via `Sciris` in places where order matters). Therefore, we only _officially_ support Python 3.7, as this is the first Python release that guarantees ordering of all dictionaries.

Atomica is distributed via PyPI, and the PyPI version corresponds to `master` branch of this repository. To install via PyPI, it is only necessary to run

```
pip install atomica
```

Installation of `numpy`, `scipy` and `matplotlib` will automatically take place via `pip` because they are dependencies of Atomica. However, in practice these packages may require system-level setup so it is usually easiest to install them separately beforehand. We recommend using Anaconda, which facilitates getting the binaries and dependencies like QT installed in a platform-agnostic manner. We also recommend working within an Anaconda environment.

You may also wish to install `mkl` first, before installing `numpy` etc. to improve performance. So for example:

```
conda install mkl
conda install numpy scipy matplotlib
```

## Git installation

If you want to install a different branch of Atomica, or plan to make changes to the Atomica source code, you will need to install Atomica via Git rather than via PyPI. This can be performed using

```
git clone https://github.com/atomicateam/atomica.git
cd atomica
python setup.py develop
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

If you don't have `tox`, install it using `pip install tox`. The default configuration expects Python 3.6 and Python 3.7 to be on your system - to test only against a specific version, pass the python version as an argument to `tox` e.g.

```
tox -e py37
```

to test Python 3.7 only. 

## Troubleshooting

### Installation fails due to missing `numpy`

If running `python setup.py develop` in a new environment, `numpy` must be installed prior to `scipy`. In some cases,
installing `numpy` may fail due to missing compiler options. In that case, you may wish to install `numpy` via Anaconda
(by installing Python through Anaconda, and using `conda install numpy scipy matplotlib`). In general, our experience
has been that it is easier to set up the C binaries for `numpy` and the QT dependencies for `matplotlib` via Anaconda
rather than doing this via the system, which involves different steps on every platform.

