#!/usr/bin/env python

from setuptools import setup
from setuptools import find_packages

import os
import sys
source = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, source)

#from catkin_pkg import __version__

setup(
    name='catkin_pkg',
    #version=__version__,
    version='0.2.10',
    packages=find_packages(exclude=['test']),
    #package_dir={'': 'src'},
    package_data={
        'catkin_pkg': [
            'templates/*.in',
            'bin/catkin_create_pkg',
            'bin/catkin_find_pkg',
            'bin/catkin_generate_changelog',
            'bin/catkin_tag_changelog',
            'bin/catkin_test_changelog',
        ],
    },
    #scripts=[
    #    'bin/catkin_create_pkg',
    #    'bin/catkin_find_pkg',
    #    'bin/catkin_generate_changelog',
    #    'bin/catkin_tag_changelog',
    #    'bin/catkin_test_changelog'
    #],
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
