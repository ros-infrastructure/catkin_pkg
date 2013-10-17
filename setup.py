#!/usr/bin/env python

from distutils.core import setup

import os
import sys
source = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, source)

from catkin_pkg import __version__

setup(
    name='catkin_pkg',
    version=__version__,
    packages=['catkin_pkg'],
    package_dir={'': 'src'},
    package_data={'catkin_pkg': ['templates/*.in']},
    scripts=[
        'bin/catkin_create_pkg',
        'bin/catkin_find_pkg',
        'bin/catkin_generate_changelog',
        'bin/catkin_tag_changelog',
        'bin/catkin_test_changelog'
    ],
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
