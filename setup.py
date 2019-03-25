#!/usr/bin/env python

import os
import sys

from setuptools import setup

install_requires = [
    'docutils',
    'python-dateutil',
    'pyparsing',
]

# argparse is part of the standard library since Python 2.7
if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    install_requires.append('argparse')

kwargs = {
    'name': 'catkin_pkg',
    # same version as in:
    # - src/catkin_pkg/__init__.py
    # - stdeb.cfg
    'version': '0.4.11',
    'packages': ['catkin_pkg', 'catkin_pkg.cli'],
    'package_dir': {'': 'src'},
    'package_data': {'catkin_pkg': ['templates/*.in']},
    'entry_points': {
        'console_scripts': [
            'catkin_create_pkg = catkin_pkg.cli.create_pkg:main',
            'catkin_find_pkg = catkin_pkg.cli.find_pkg:main',
            'catkin_generate_changelog = catkin_pkg.cli.generate_changelog:main_catching_runtime_error',
            'catkin_package_version = catkin_pkg.cli.package_version:main',
            'catkin_prepare_release = catkin_pkg.cli.prepare_release:main',
            'catkin_tag_changelog = catkin_pkg.cli.tag_changelog:main',
            'catkin_test_changelog = catkin_pkg.cli.test_changelog:main',
        ]},
    'author': 'Dirk Thomas',
    'author_email': 'dthomas@osrfoundation.org',
    'url': 'http://wiki.ros.org/catkin_pkg',
    'keywords': ['catkin', 'ROS'],
    'classifiers': [
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License'
    ],
    'description': 'catkin package library',
    'long_description': 'Library for retrieving information about catkin packages.',
    'license': 'BSD',
    'install_requires': install_requires,
}
if 'SKIP_PYTHON_MODULES' in os.environ:
    kwargs['packages'] = []
    kwargs['package_dir'] = {}
    kwargs['package_data'] = {}
if 'SKIP_PYTHON_SCRIPTS' in os.environ:
    kwargs['name'] += '_modules'
    kwargs['entry_points'] = {}

setup(**kwargs)
