from __future__ import print_function

import contextlib
import os
import re

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import sys
import unittest

from catkin_pkg.metapackage import get_expected_cmakelists_txt
from catkin_pkg.metapackage import InvalidMetapackage
from catkin_pkg.metapackage import validate_metapackage
from catkin_pkg.packages import find_packages


test_data_dir = os.path.join(os.path.dirname(__file__), 'data', 'metapackages')

test_expectations = {
    # Test name: [ExceptionType or None, ExceptionRegex or None, WarningRegex or None]
    'invalid_cmake': [InvalidMetapackage, 'Invalid CMakeLists.txt', None],
    'invalid_depends': [InvalidMetapackage, 'Has build, buildtool, and/or test depends', None],
    'leftover_files': [None, None, None],
    'no_buildtool_depend_catkin': [InvalidMetapackage, 'No buildtool dependency on catkin', None],
    'no_cmake': [InvalidMetapackage, 'No CMakeLists.txt', None],
    'no_metapackage_tag': [InvalidMetapackage, 'No <metapackage/> tag in <export>', None],
    'NonConformingName': [None, None, None],
    'valid_metapackage': [None, None, None],
    'valid_metapackage_format2': [None, None, None],
}

test_expected_warnings = [
    'Metapackage "invalid_depends" should not have other dependencies besides '
    'a buildtool_depend on catkin and run_depends.',
    'Metapackage "no_buildtool_depend_catkin" must buildtool_depend on '
    'catkin.',
    'Package name "NonConformingName" does not follow the naming conventions. '
    'It should start with a lower case letter and only contain lower case '
    'letters, digits and underscores.']


@contextlib.contextmanager
def assert_warning(warnreg):
    orig_stdout = sys.stdout
    orig_stderr = sys.stderr
    try:
        out = StringIO()
        sys.stdout = out
        sys.stderr = sys.stdout
        yield
    finally:
        if warnreg is not None:
            out = out.getvalue()
            assert re.search(warnreg, out) is not None, "'%s' does not match warning '%s'" % (warnreg, out)
        else:
            print(out)
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr


def _validate_metapackage(path, package):
    try:
        validate_metapackage(path, package)
    except Exception:
        # print('on package ' + package.name, file=sys.stderr)
        raise


class TestMetapackageValidation(unittest.TestCase):
    """Tests the metapackage validator."""

    def test_validate_metapackage(self):
        pkgs_dict = find_packages(test_data_dir)
        for path, package in pkgs_dict.items():
            path = os.path.join(test_data_dir, path)
            assert package.name in test_expectations, 'Unknown test %s' % package.name
            exc, excreg, warnreg = test_expectations[package.name]
            with assert_warning(warnreg):
                if exc is not None:
                    if excreg is not None:
                        with self.assertRaisesRegexp(exc, excreg):
                            _validate_metapackage(path, package)
                    else:
                        with self.assertRaises(exc):
                            _validate_metapackage(path, package)
                else:
                    _validate_metapackage(path, package)

    def test_collect_warnings(self):
        """Tests warnings collection."""
        warnings = []
        find_packages(test_data_dir, warnings=warnings)

        self.assertEqual(warnings.sort(), test_expected_warnings.sort())


def test_get_expected_cmakelists_txt():
    expected = """\
cmake_minimum_required(VERSION 2.8.3)
project(example)
find_package(catkin REQUIRED)
catkin_metapackage()
"""
    assert expected == get_expected_cmakelists_txt('example')
