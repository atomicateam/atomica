#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

cwd = os.path.abspath(os.path.dirname(__file__))

# Read version
with open(os.path.join(cwd, "atomica", "version.py"), "r") as f:
    version = [x.split("=")[1].replace('"', "").strip() for x in f if x.startswith("version =")][0]

# Read README.md for description
with open(os.path.join(cwd, "README.md"), "r") as f:
    long_description = f.read()

CLASSIFIERS = [
    "Environment :: Console",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Development Status :: 5 - Production/Stable",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

setup(
    name="atomica",
    version=version,
    author="Atomica Team",
    author_email="info@atomica.tools",
    description="Toolbox for compartment-based dynamic systems with costing and optimization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://atomica.tools",
    keywords=["dynamic", "compartment", "optimization", "disease"],
    platforms=["OS Independent"],
    classifiers=CLASSIFIERS,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "matplotlib",
        "numpy>=1.10.1,<2",
        "scipy>=1.6",
        "pandas",
        "xlsxwriter",
        "openpyxl",
        "pyswarm",
        "hyperopt",
        "sciris",
        "tqdm",
    ],
)
