import datetime
import os
import shutil
import tempfile
import unittest

from catkin_pkg.package_version import _replace_version
from catkin_pkg.package_version import bump_version
from catkin_pkg.package_version import update_changelog_sections
from catkin_pkg.package_version import update_versions

import mock

from .util import in_temporary_directory


class PackageVersionTest(unittest.TestCase):

    def test_bump_version(self):
        self.assertEqual('0.0.1', bump_version('0.0.0'))
        self.assertEqual('1.0.1', bump_version('1.0.0'))
        self.assertEqual('0.1.1', bump_version('0.1.0'))
        self.assertEqual('0.0.1', bump_version('0.0.0', 'patch'))
        self.assertEqual('1.0.1', bump_version('1.0.0', 'patch'))
        self.assertEqual('0.1.1', bump_version('0.1.0', 'patch'))
        self.assertEqual('1.0.0', bump_version('0.0.0', 'major'))
        self.assertEqual('1.0.0', bump_version('0.0.1', 'major'))
        self.assertEqual('1.0.0', bump_version('0.1.1', 'major'))
        self.assertEqual('0.1.0', bump_version('0.0.0', 'minor'))
        self.assertEqual('0.1.0', bump_version('0.0.1', 'minor'))
        self.assertEqual('1.1.0', bump_version('1.0.1', 'minor'))
        self.assertRaises(ValueError, bump_version, '0.0.asd')
        self.assertRaises(ValueError, bump_version, '0.0')
        self.assertRaises(ValueError, bump_version, '0')
        self.assertRaises(ValueError, bump_version, '0.0.-1')

    def test_replace_version(self):
        self.assertEqual('<package><version>0.1.1</version></package>',
                         _replace_version('<package><version>0.1.0</version></package>', '0.1.1'))
        self.assertEqual("<package><version abi='0.1.0'>0.1.1</version></package>",
                         _replace_version("<package><version abi='0.1.0'>0.1.0</version></package>", '0.1.1'))
        self.assertRaises(RuntimeError, _replace_version, '<package></package>', '0.1.1')
        self.assertRaises(RuntimeError, _replace_version, '<package><version>0.1.1</version><version>0.1.1</version></package>', '0.1.1')

    def test_update_versions(self):
        try:
            root_dir = tempfile.mkdtemp()
            sub_dir = os.path.join(root_dir, 'sub')
            with open(os.path.join(root_dir, 'package.xml'), 'w') as fhand:
                fhand.write('<package><version>2.3.4</version></package>')
            os.makedirs(os.path.join(sub_dir))
            with open(os.path.join(sub_dir, 'package.xml'), 'w') as fhand:
                fhand.write('<package><version>1.5.4</version></package>')

            update_versions([root_dir, sub_dir], '7.6.5')

            with open(os.path.join(root_dir, 'package.xml'), 'r') as fhand:
                contents = fhand.read()
                self.assertEqual('<package><version>7.6.5</version></package>', contents)
            with open(os.path.join(sub_dir, 'package.xml'), 'r') as fhand:
                contents = fhand.read()
                self.assertEqual('<package><version>7.6.5</version></package>', contents)
        finally:
            shutil.rmtree(root_dir)

    @in_temporary_directory
    def test_update_changelog_unicode(self, directory=None):
        """Test that updating the changelog does not throw an exception on unicode characters."""
        temp_file = os.path.join(directory, 'changelog')
        missing_changelogs_but_forthcoming = {}
        # Mock the Changelog object from catkin_pkg
        mock_changelog = mock.Mock()
        # Create a changelog entry with a unicode char.
        mock_changelog.rst = ('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n'
                              'Changelog for package fake_pkg\n'
                              '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n'
                              '\n'
                              'Forthcoming\n'
                              '-----------\n'
                              '* This is my changelog entry\n'
                              '* This is a line that has unicode' u'\xfc''\n'
                              '\n'
                              '0.0.9 (2017-01-30)\n'
                              '------------------\n'
                              '* This is old version.\n')

        # Create tuple with expected entires.
        missing_changelogs_but_forthcoming['fake_pkg'] = (temp_file, mock_changelog, 'Forthcoming')
        # Should not raise an exception
        update_changelog_sections(missing_changelogs_but_forthcoming, '1.0.0')

        # Generate dynamic lines, using present system date,
        # the length of the line of '-'s for the underline
        # and the utf-8 encoded data expected to be read back.
        ver_line = '1.0.0 (%s)' % datetime.date.today().isoformat()
        ver_line = ver_line.encode('utf-8')
        dash_line = '-' * len(ver_line)
        dash_line = dash_line.encode('utf-8')
        unicode_line = u'* This is a line that has unicode\xfc'.encode('utf-8')
        expected = [b'^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^',
                    b'Changelog for package fake_pkg',
                    b'^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^',
                    b'',
                    ver_line,
                    dash_line,
                    b'* This is my changelog entry',
                    unicode_line,
                    b'',
                    b'0.0.9 (2017-01-30)',
                    b'------------------',
                    b'* This is old version.']

        # Open the file written, and compare each line written to
        # the one read back.
        with open(temp_file, 'rb') as verify_file:
            content = verify_file.read().splitlines()
            for line_written, line_expected in zip(content, expected):
                self.assertEqual(line_written.strip(), line_expected)
