import os

from catkin_pkg.packages import find_package_paths
from catkin_pkg.packages import find_packages_allowing_duplicates

from .util import in_temporary_directory


def _create_pkg_in_dir(path):
    os.mkdir(path)
    open(os.path.join(path, 'package.xml'), 'a').close()


@in_temporary_directory
def test_package_paths_with_hidden_directories():
    _create_pkg_in_dir('.test1')
    _create_pkg_in_dir('.test2')
    _create_pkg_in_dir('test3')  # not hidden
    _create_pkg_in_dir('.test4')

    res = find_package_paths('.')
    assert res == ['test3']


@in_temporary_directory
def test_find_packages_allowing_duplicates_with_no_packages():
    res = find_packages_allowing_duplicates('.')
    assert isinstance(res, dict)
    assert not res
