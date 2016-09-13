#!/usr/bin/env python

from setuptools import setup

import os
import sys
source = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, source)

from catkin_pkg import __version__

setup(
    name='catkin_pkg',
    version=__version__,
    packages=['catkin_pkg', 'catkin_pkg.cli'],
    package_dir={'': 'src'},
    package_data={'catkin_pkg': ['templates/*.in']},
    entry_points={
        'console_scripts' : [
            'catkin_create_pkg = catkin_pkg.cli.create_pkg:main',
            'catkin_find_pkg = catkin_pkg.cli.find_pkg:main',
            'catkin_generate_changelog = catkin_pkg.cli.generate_changelog:main_catching_runtime_error',
            'catkin_tag_changelog = catkin_pkg.cli.tag_changelog:main',
            'catkin_test_changelog = catkin_pkg.cli.test_changelog:main',
        ]
    },
    author='Dirk Thomas',
    author_email='dthomas@osrfoundation.org',
    url='http://wiki.ros.org/catkin_pkg',
    download_url='http://download.ros.org/downloads/catkin_pkg/',
    keywords=['catkin', 'ROS'],
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License'
    ],
    description='catkin package library',
    long_description='Library for retrieving information about catkin packages.',
    license='BSD',
    install_requires=[
        'argparse',
        'docutils',
        'python-dateutil'
    ],
)
