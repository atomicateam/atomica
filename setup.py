#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("./atomica/version.py", "r") as f:
    version = [x.split('=')[1].replace('"','').strip() for x in f if x.startswith('version =')][0]

CLASSIFIERS = [
    'Environment :: Console',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GPLv3',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Development Status :: 3 - Alpha',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
]

setup(
    name='atomica',
    version=version,
    author='Atomica Team',
    author_email='info@atomica.tools',
    description='Toolbox for compartment-based dynamic systems with costing and optimization',
    url='http://github.com/atomicateam/atomica',
    keywords=['dynamic','compartment','optimization', 'disease'],
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'matplotlib>=1.4.2',
        'numpy>=1.10.1',
        'scipy',
        'pandas',
        'six>=1.11.0',
        'xlsxwriter',
        'openpyxl>=2.5,<2.6',
        'pyswarm',
        'hyperopt',
        'sciris',
    ],
)
