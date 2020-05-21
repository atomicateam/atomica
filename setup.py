#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

cwd = os.path.abspath(os.path.dirname(__file__))

# Read version
with open(os.path.join(cwd, 'atomica', 'version.py'), 'r') as f:
    version = [x.split('=')[1].replace('"', '').strip() for x in f if x.startswith('version =')][0]

# Read README.md for description
with open(os.path.join(cwd, 'README.md'), 'r') as f:
    long_description = f.read()

CLASSIFIERS = [
    'Environment :: Console',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Development Status :: 3 - Alpha',
    'Programming Language :: Python :: 3.7',
]

setup(
    name='atomica',
    version=version,
    author='Atomica Team',
    author_email='info@atomica.tools',
    description='Toolbox for compartment-based dynamic systems with costing and optimization',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://atomica.tools',
    keywords=['dynamic', 'compartment', 'optimization', 'disease'],
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'matplotlib>=3.0',
        'numpy>=1.10.1',
        'scipy>=1.2.1',
        'pandas',
        'six>=1.11.0',
        'xlsxwriter',
        'openpyxl>=2.5,<2.6',
        'pyswarm',
        'hyperopt',
        'sciris',
        'tqdm'
    ],
)
