# Software License Agreement (BSD License)
#
# Copyright (c) 2012, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
Library to find packages in the filesystem.
"""

import os
from .package import parse_package, PACKAGE_MANIFEST_FILENAME


def find_package_paths(basepath):
    """
    Crawls the filesystem to find package manifest files.

    When a subfolder contains a file ``CATKIN_IGNORE`` it is ignored.

    :param basepath: The path to search in, ``str``
    :returns: A list of relative paths containing package manifest files
    ``list``
    """
    paths = []
    for dirpath, dirnames, filenames in os.walk(basepath, followlinks=True):
        if 'CATKIN_IGNORE' in filenames:
            del dirnames[:]
            continue
        elif PACKAGE_MANIFEST_FILENAME in filenames:
            paths.append(os.path.relpath(dirpath, basepath))
            del dirnames[:]
            continue
        for dirname in dirnames:
            if dirname.startswith('.'):
                dirnames.remove(dirname)
    return paths


def find_packages(basepath):
    """
    Crawls the filesystem to find package manifest files and parses them.

    :param basepath: The path to search in, ``str``
    :returns: A dict mapping relative paths to ``Package`` objects
    ``dict``
    :raises: :exc:RuntimeError` If multiple packages have the same
    name
    """
    packages = {}
    duplicates = {}
    paths = find_package_paths(basepath)
    for path in paths:
        package = parse_package(os.path.join(basepath, path))
        paths_with_same_name = [path_ for path_, pkg in packages.items() if pkg.name == package.name]
        if paths_with_same_name:
            if package.name not in duplicates:
                duplicates[package.name] = paths_with_same_name
            duplicates[package.name].append(path)
        packages[path] = package
    if duplicates:
        duplicates = ['Multiple packages found with the same name "%s":%s' % (name, ''.join(['\n- %s' % path_ for path_ in paths])) for name, paths in duplicates.iteritems()]
        raise RuntimeError('\n'.join(duplicates))
    return packages


def verify_equal_package_versions(packages):
    """
    Verifies that all packages have the same version number.

    :param packages: The list of ``Package`` objects, ``list``
    :returns: The version number
    :raises: :exc:RuntimeError` If the version is not equal in all
    packages
    """
    version = None
    for package in packages:
        if version is None:
            version = package.version
        elif package.version != version:
            raise RuntimeError('Two packages have different version numbers (%s != %s):\n- %s\n- %s' % (package.version, version, package.filename, packages[0].filename))
    return version
