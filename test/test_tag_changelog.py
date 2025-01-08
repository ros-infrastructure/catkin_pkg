# coding=utf-8

from catkin_pkg.cli.tag_changelog import get_forthcoming_label
from catkin_pkg.cli.tag_changelog import rename_section

single_forthcoming_rst = """\
^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package foo
^^^^^^^^^^^^^^^^^^^^^^^^^

Forthcoming
-----------

* Initial release
* Initial bugs
* Contributors: Sömeöne with UTF-8 in their name
"""

single_version_rst = """\
^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package foo
^^^^^^^^^^^^^^^^^^^^^^^^^

0.0.1 (2012-01-31)
------------------

* Initial release
* Initial bugs
* Contributors: Sömeöne with UTF-8 in their name
"""


def test_get_forthcoming_label():
    assert get_forthcoming_label(single_version_rst) is None
    assert get_forthcoming_label(single_forthcoming_rst) == 'Forthcoming'


def test_rename_section():
    res = rename_section(
        single_forthcoming_rst,
        'Forthcoming',
        '0.0.1 (2012-01-31)')
    assert res == single_version_rst
