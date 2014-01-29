import unittest

from catkin_pkg.package_version import bump_version


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
