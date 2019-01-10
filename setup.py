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
    'Development Status :: 1 - Planning',
    'Programming Language :: Python :: 2.7',
]

setup(
    name='atomica',
    version=version,
    author='David J. Kedziora, Robyn M. Stuart, Romesh Abeysuriya, Cliff C. Kerr',
    author_email='info@optimamodel.com',
    description='Software package for the optimization of complex Markov chain models',
    url='http://github.com/optimamodel/atomica',
    keywords=['optima', 'disease'],
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
        'pyswarm',
        'hyperopt',
        'sciris',
    ],
)
