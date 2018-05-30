# coding=utf-8

import unittest

from catkin_pkg.changelog import BulletList
from catkin_pkg.changelog import Changelog
from catkin_pkg.changelog import example_rst
from catkin_pkg.changelog import InvalidSectionTitle
from catkin_pkg.changelog import MixedText
from catkin_pkg.changelog import populate_changelog_from_rst
from catkin_pkg.changelog import Transition
from catkin_pkg.changelog import version_and_date_from_title


class TestSectionTitleParsing(unittest.TestCase):
    """Tests the section title parsing."""

    def test_version_and_date_from_title(self):
        title = '0.1.26 (2012-12-26)'
        assert '0.1.26' == version_and_date_from_title(title)[0]
        title = '0.1'
        self.assertRaises(InvalidSectionTitle, version_and_date_from_title, title)
        title = '0.1.27 (forthcoming)'
        self.assertRaises(InvalidSectionTitle, version_and_date_from_title, title)
        title = ' 0.1.26 (2012-12-26)'
        self.assertRaises(InvalidSectionTitle, version_and_date_from_title, title)
        title = '0.1.26 (2012-12-26) '
        self.assertRaises(InvalidSectionTitle, version_and_date_from_title, title)
        # TODO: Add some more sofisticated Date entries


def check_0_1_26(content):
    assert len(content) == 1
    assert type(content[0]) == BulletList
    assert len(content[0].bullets) == 3


def check_0_1_25(content):
    assert len(content) == 3
    assert type(content[0]) == BulletList
    assert len(content[0].bullets) == 5
    mtext = content[0].bullets[3]
    assert type(mtext) == MixedText
    assert len(mtext.texts) == 2
    assert type(content[1]) == Transition
    assert type(content[2]) == MixedText


def check_0_1_0(content):
    assert len(content) == 1
    assert type(content[0]) == MixedText
    assert len(content[0].texts) == 4


def check_0_0_1(content):
    assert len(content) == 1
    assert type(content[0]) == BulletList
    assert content[0].bullet_type == 'enumerated'


def test_Changelog():
    # Example is from REP-0132
    changelog = Changelog('foo')
    populate_changelog_from_rst(changelog, example_rst)
    expected_versions = ['0.1.26', '0.1.25', '0.1.0', '0.0.1']
    versions = []
    content_checks = {
        '0.1.26': check_0_1_26,
        '0.1.25': check_0_1_25,
        '0.1.0': check_0_1_0,
        '0.0.1': check_0_0_1
    }
    for version, date, content in changelog.foreach_version():
        versions.append(version)
        if version in content_checks:
            content_checks[version](content)
    assert sorted(expected_versions) == sorted(versions)


single_version_rst = """\
0.0.1 (2012-01-31)
------------------

* Initial release
* Initial bugs
* Contributors: Sömeöne with UTF-8 in their name
"""


def test_single_version_Changelog():
    changelog = Changelog('foo')
    populate_changelog_from_rst(changelog, single_version_rst)
    expected_versions = ['0.0.1']
    versions = []
    for version, date, content in changelog.foreach_version():
        versions.append(version)
    assert sorted(expected_versions) == sorted(versions)
    str(changelog)


single_version_with_header_rst = """\
^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package foo
^^^^^^^^^^^^^^^^^^^^^^^^^

0.0.1 (2012-01-31)
------------------

* Initial release
* Initial bugs
"""


def test_single_version_with_header_Changelog():
    changelog = Changelog('foo')
    populate_changelog_from_rst(changelog, single_version_with_header_rst)
    expected_versions = ['0.0.1']
    versions = []
    for version, date, content in changelog.foreach_version():
        versions.append(version)
    assert sorted(expected_versions) == sorted(versions)
