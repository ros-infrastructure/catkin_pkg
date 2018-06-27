import os

from catkin_pkg.package import InvalidPackage
from catkin_pkg.packages import find_package_paths
from catkin_pkg.packages import find_packages
from catkin_pkg.packages import find_packages_allowing_duplicates

from .util import in_temporary_directory


def _create_pkg_in_dir(path, version='0.1.0'):
    path = os.path.abspath(path)
    os.makedirs(path)

    template = """\
<?xml version="1.0"?>
<package>
  <name>{0}</name>
  <version>{1}</version>
  <description>Package {0}</description>
  <license>BSD</license>

  <maintainer email="foo@bar.com">Foo Bar</maintainer>
</package>
""".format(path.split('/')[-1], version)

    with open(os.path.join(path, 'package.xml'), 'w+') as f:
        f.write(template)


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


@in_temporary_directory
def test_find_packages_invalid_version():
    version = ':{version}'
    path = 'src/foo'
    _create_pkg_in_dir(path, version)
    try:
        find_packages(path.split('/')[0])
        assert False, 'Must raise'
    except InvalidPackage as e:
        exception_message = str(e)
        assert version in exception_message
        assert path in exception_message
