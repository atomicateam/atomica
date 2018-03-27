#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

from setuptools import setup, find_packages

with open("./optimacore/_version.py", "r") as f:
    version_file = {}
    exec(f.read(), version_file)
    version = version_file["__version__"]

#try:
#    from pypandoc import convert
#except ImportError:
#    import io
#    def convert(filename, fmt):
#        with io.open(filename, encoding='utf-8') as fd:
#            return fd.read()

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
    #long_description=convert('README.md', 'md'),
    url='http://github.com/optimamodel/atomica',
    keywords=['optima','disease'],
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'six>=1.11.0',
        'matplotlib>=1.4.2',
        'numpy>=1.10.1',
        'decorator>=4.1.2'
    ],
)