from catkin_pkg.packages import find_packages_allowing_duplicates

from .util import in_temporary_directory


@in_temporary_directory
def test_find_packages_allowing_duplicates_with_no_packages():
    res = find_packages_allowing_duplicates('.')
    assert isinstance(res, dict)
    assert not res
