#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from glob import glob

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'packaging',
    'rasterio',
    'shapely',
    'numpy',
    'python-logstash',
    'asynchronousfilereader',
    'boto3',
    'urljoin',
    'botocore',
]

setup_requirements = []

test_requirements = ['nose2', 'coverage']

setup(
    author="Wil Selwood",
    author_email='wil.selwood@sa.catapult.org.uk',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.7',
    ],
    description="s1_ard_pypeline contains tools to run an ARD process on S1 images",
    install_requires=requirements,
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='s1_ard_pypeline',
    name='s1_ard_pypeline',
    packages=find_packages(include=['s1_ard_pypeline', 's1_ard_pypeline.*']),
    # everything in s1_ard_pypeline counts as a script. Non script files should be in sub folders.
    scripts=glob('s1_ard_pypeline/[!_][!_]*.py'),
    data_files=[(".", ["config.cfg"]), ("graphs", glob('graphs/*.xml'))],
    setup_requires=setup_requirements,
    test_suite='nose2.collector.collector',
    tests_require=test_requirements,
    url='https://bitbucket.satapps.org/projects/GIA/repos/s1_ard_pypeline',
    version='0.1.0',
    zip_safe=False,
)
