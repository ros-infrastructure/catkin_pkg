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
    package_data={'catkin_pkg': ['templates/*/*.in']},
    scripts=['bin/catkin_create_pkg'],
    author='Dirk Thomas',
    author_email='dthomas@willowgarage.com',
    url='http://www.ros.org/wiki/catkin_pkg',
    download_url='http://pr.willowgarage.com/downloads/catkin_pkg/',
    keywords=['catkin', 'ROS'],
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License'
    ],
    description='catkin package library',
    long_description='Library for retrieving information about catkin packages.',
    license='BSD'
)
