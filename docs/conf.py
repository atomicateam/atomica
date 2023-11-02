# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

import matplotlib

matplotlib.use("agg")

import os
import sys

sys.path.insert(0, os.path.abspath("../"))  # Source code dir relative to this file

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# -- Project information -----------------------------------------------------

project = "Atomica"
copyright = "2023, Atomica Team"
author = "Atomica Team"

import atomica

# The short X.Y version
version = atomica.__version__
# The full version, including alpha/beta/rc tags
release = ""


# -- General configuration ---------------------------------------------------

os.environ["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"  # Suppress harmless warning in documentation build

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",  # Core Sphinx library for auto html doc generation from docstrings
    "sphinx.ext.autosummary",  # Create neat summary tables for modules/classes/methods etc
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",  # Add a link to the Python source code for classes, functions etc.
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    "sphinx_autodoc_typehints",  # Automatically document param types (less noise in class signature)
    "sphinx_markdown_tables",
    "recommonmark",
    "nbsphinx",
    "sphinx.ext.intersphinx",  # Link to other project's documentation (see mapping below)
    "IPython.sphinxext.ipython_console_highlighting",  # Temporary fix for https://github.com/spatialaudio/nbsphinx/issues/687
    "sphinxcontrib.jquery",  # Fix for https://github.com/readthedocs/sphinx_rtd_theme/issues/1452
]

# Configure intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sciris": ("https://sciris.readthedocs.io/en/latest/", None),  # This doesn't really work though, because things are accessed via sciris.Spreadsheet not sciris.sc_file.Spreadshee
}

# Configure autosummary
autosummary_generate = True  # Turn on sphinx.ext.autosummary
autoclass_content = "both"  # Add __init__ doc (ie. params) to class summaries
html_show_sourcelink = False  # Remove 'view source code' from top of page (for html, not python)
# autodoc_default_options = {
#     'members': False,
#     'private-members': False,
#     'undoc-members': False,
#     'ignore-module-all': False,
# }

# Configure nbsphinx
nbsphinx_kernel_name = "python"
nbsphinx_timeout = -1  # Disable timeout for slow cells
nbsphinx_execute_arguments = [
    "--InlineBackend.figure_formats={'svg', 'pdf'}",
    "--InlineBackend.rc=figure.dpi=96",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "**.ipynb_checkpoints",
    "general/programs/saturation.ipynb",  # This is not a documentation page - just for generating a figure
]


# -- Options for HTML output -------------------------------------------------

# Use RTD
import sphinx_rtd_theme

html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": -1,
}
