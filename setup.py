#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("./atomica/_version.py", "r") as f:
    version_file = {}
    exec(f.read(), version_file)
    version = version_file["__version__"]

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
    author='David J. Kedziora, Robyn M. Stuart',
    author_email='info@optimamodel.com',
    description='Software package for the optimization of complex Markov chain models',
    url='http://github.com/optimamodel/atomica',
    keywords=['optima', 'disease'],
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'six>=1.11.0',
        'matplotlib>=1.4.2',
        'numpy>=1.10.1',
        'decorator>=4.1.2',
        'dill>=0.2.7.1',
        'xlsxwriter',
        'xlrd'
    ],
)
