#!/usr/bin/env python3

import os

from setuptools import setup


kwargs = {
    'name': 'catkin_pkg',
    # same version as in:
    # - src/catkin_pkg/__init__.py
    # - stdeb.cfg
    'version': '1.0.0',
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
    'maintainer': 'ROS Infrastructure Team',
    'project_urls': {
        'Source code':
        'https://github.com/ros-infrastructure/catkin_pkg',
        'Issue tracker':
        'https://github.com/ros-infrastructure/catkin_pkg/issues',
    },
    'url': 'http://wiki.ros.org/catkin_pkg',
    'keywords': ['catkin', 'ROS'],
    'classifiers': [
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License'
    ],
    'python_requires': '>=3.6',
    'description': 'catkin package library',
    'long_description': 'Library for retrieving information about catkin packages.',
    'license': 'BSD',
    'install_requires': [
        'docutils',
        'python-dateutil',
        'pyparsing',
        'setuptools',
    ],
    'extras_require': {
        'test': [
            'flake8',
            'flake8-blind-except',
            'flake8-builtins',
            'flake8-class-newline',
            'flake8-comprehensions',
            'flake8-deprecated',
            'flake8-docstrings',
            'flake8-import-order',
            'flake8-quotes',
            'pytest',
        ]},
}
if 'SKIP_PYTHON_MODULES' in os.environ:
    kwargs['packages'] = []
    kwargs['package_dir'] = {}
    kwargs['package_data'] = {}
if 'SKIP_PYTHON_SCRIPTS' in os.environ:
    kwargs['name'] += '_modules'
    kwargs['entry_points'] = {}

setup(**kwargs)
