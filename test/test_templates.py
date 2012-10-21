import os
import unittest
import tempfile
import shutil

from mock import MagicMock, Mock

from catkin_pkg.package_templates import _safe_write_files, create_package_files, \
    create_cmakelists, create_package_xml, PackageTemplate
from catkin_pkg.package import parse_package_for_distutils, parse_package, \
    Dependency, Export, Url, PACKAGE_MANIFEST_FILENAME


class TemplateTest(unittest.TestCase):

    def get_maintainer(self):
        maint = Mock()
        maint.email = 'foo@bar.com'
        maint.name = 'John Foo'
        return maint

    def test_safe_write_files(self):
        file1 = os.path.join('foo', 'bar')
        file2 = os.path.join('foo', 'baz')
        newfiles = {file1: 'foobar', file2: 'barfoo'}
        try:
            rootdir = tempfile.mkdtemp()
            _safe_write_files(newfiles, rootdir)
            self.assertTrue(os.path.isfile(os.path.join(rootdir, file1)))
            self.assertTrue(os.path.isfile(os.path.join(rootdir, file2)))
            self.assertRaises(ValueError, _safe_write_files, newfiles, rootdir)
        finally:
            shutil.rmtree(rootdir)

    def test_create_cmakelists(self):
        mock_pack = MagicMock()
        mock_pack.name = 'foo'
        mock_pack.components = []
        result = create_cmakelists(mock_pack, 'groovy')
        self.assertTrue('project(foo)' in result, result)
        self.assertTrue('find_package(catkin REQUIRED)' in result, result)

        mock_pack.components = ['bar', 'baz']
        result = create_cmakelists(mock_pack, 'groovy')
        self.assertTrue('project(foo)' in result, result)
        self.assertTrue('find_package(catkin REQUIRED COMPONENTS bar baz)' in result, result)

    def test_create_package_xml(self):
        maint = self.get_maintainer()
        pack = PackageTemplate(name='foo',
                               description='foo',
                               version='0.0.0',
                               maintainers=[maint],
                               licenses=['BSD'])

        result = create_package_xml(pack, 'groovy')
        self.assertTrue('<name>foo</name>' in result, result)

    def test_create_package(self):
        maint = self.get_maintainer()
        pack = PackageTemplate(name='bar',
                               description='bar',
                               package_format='1',
                               version='0.0.0',
                               version_abi='pabi',
                               maintainers=[maint],
                               licenses=['BSD'])
        try:
            rootdir = tempfile.mkdtemp()
            file1 = os.path.join(rootdir, 'CMakeLists.txt')
            file2 = os.path.join(rootdir, PACKAGE_MANIFEST_FILENAME)
            create_package_files(rootdir, pack, 'groovy', {file1: ''})
            self.assertTrue(os.path.isfile(file1))
            self.assertTrue(os.path.isfile(file2))
        finally:
            shutil.rmtree(rootdir)

    def test_parse_generated(self):
        maint = self.get_maintainer()
        pack = PackageTemplate(name='bar',
                               package_format=1,
                               version='0.0.0',
                               version_abi='pabi',
                               urls=[Url('foo')],
                               description='pdesc',
                               maintainers=[maint],
                               licenses=['BSD'])
        try:
            rootdir = tempfile.mkdtemp()
            file1 = os.path.join(rootdir, 'CMakeLists.txt')
            file2 = os.path.join(rootdir, PACKAGE_MANIFEST_FILENAME)
            create_package_files(rootdir, pack, 'groovy')
            self.assertTrue(os.path.isfile(file1))
            self.assertTrue(os.path.isfile(file2))

            pack_result = parse_package(file2)
            self.assertEqual(pack.name, pack_result.name)
            self.assertEqual(pack.package_format, pack_result.package_format)
            self.assertEqual(pack.version, pack_result.version)
            self.assertEqual(pack.version_abi, pack_result.version_abi)
            self.assertEqual(pack.description, pack_result.description)
            self.assertEqual(pack.maintainers[0].name, pack_result.maintainers[0].name)
            self.assertEqual(pack.maintainers[0].email, pack_result.maintainers[0].email)
            self.assertEqual(pack.authors, pack_result.authors)
            self.assertEqual(pack.urls[0].url, pack_result.urls[0].url)
            self.assertEqual('website', pack_result.urls[0].type)
            self.assertEqual(pack.licenses, pack_result.licenses)
            self.assertEqual(pack.build_depends, pack_result.build_depends)
            self.assertEqual(pack.buildtool_depends, pack_result.buildtool_depends)
            self.assertEqual(pack.run_depends, pack_result.run_depends)
            self.assertEqual(pack.test_depends, pack_result.test_depends)
            self.assertEqual(pack.conflicts, pack_result.conflicts)
            self.assertEqual(pack.replaces, pack_result.replaces)
            self.assertEqual(pack.exports, pack_result.exports)

            rdict = parse_package_for_distutils(file2)
            self.assertEqual({'name': 'bar',
                              'maintainer': u'John Foo',
                              'maintainer_email': 'foo@bar.com',
                              'description': 'pdesc',
                              'license': 'BSD',
                              'version': '0.0.0',
                              'author': '',
                              'url': 'foo',
                              'keywords': ['ROS']}, rdict)
        finally:
            shutil.rmtree(rootdir)

    def test_parse_generated_multi(self):
        # test with multiple attributes filled
        maint = self.get_maintainer()
        pack = PackageTemplate(name='bar',
                               package_format=1,
                               version='0.0.0',
                               version_abi='pabi',
                               description='pdesc',
                               maintainers=[maint, maint],
                               authors=[maint, maint],
                               licenses=['BSD', 'MIT'],
                               urls=[Url('foo', 'bugtracker'), Url('bar')],
                               build_depends=[Dependency('dep1')],
                               buildtool_depends=[Dependency('dep2'),
                                                      Dependency('dep3')],
                               run_depends=[Dependency('dep4', version_lt='4')],
                               test_depends=[Dependency('dep5',
                                                               version_gt='4',
                                                               version_lt='4')],
                               conflicts=[Dependency('dep6')],
                               replaces=[Dependency('dep7'),
                                             Dependency('dep8')],
                               exports=[Export('architecture_independent'),
                                        Export('meta_package')])

        def assertEqualDependencies(deplist1, deplist2):
            if len(deplist1) != len(deplist1):
                return False
            for depx, depy in zip(deplist1, deplist2):
                for attr in ['name', 'version_lt', 'version_lte',
                             'version_eq', 'version_gte', 'version_gt']:
                    if getattr(depx, attr) != getattr(depy, attr):
                        return False
            return True

        try:
            rootdir = tempfile.mkdtemp()
            file1 = os.path.join(rootdir, 'CMakeLists.txt')
            file2 = os.path.join(rootdir, PACKAGE_MANIFEST_FILENAME)
            create_package_files(rootdir, pack, 'groovy')
            self.assertTrue(os.path.isfile(file1))
            self.assertTrue(os.path.isfile(file2))

            pack_result = parse_package(file2)
            self.assertEqual(pack.name, pack_result.name)
            self.assertEqual(pack.package_format, pack_result.package_format)
            self.assertEqual(pack.version, pack_result.version)
            self.assertEqual(pack.version_abi, pack_result.version_abi)
            self.assertEqual(pack.description, pack_result.description)
            self.assertEqual(len(pack.maintainers), len(pack_result.maintainers))
            self.assertEqual(len(pack.authors), len(pack_result.authors))
            self.assertEqual(len(pack.urls), len(pack_result.urls))
            self.assertEqual(pack.urls[0].url, pack_result.urls[0].url)
            self.assertEqual(pack.urls[0].type, pack_result.urls[0].type)
            self.assertEqual(pack.licenses, pack_result.licenses)
            self.assertTrue(assertEqualDependencies(pack.build_depends,
                                                    pack_result.build_depends))
            self.assertTrue(assertEqualDependencies(pack.build_depends,
                                                    pack_result.build_depends))
            self.assertTrue(assertEqualDependencies(pack.buildtool_depends,
                                                    pack_result.buildtool_depends))
            self.assertTrue(assertEqualDependencies(pack.run_depends,
                                                    pack_result.run_depends))
            self.assertTrue(assertEqualDependencies(pack.test_depends,
                                                    pack_result.test_depends))
            self.assertTrue(assertEqualDependencies(pack.conflicts,
                                                    pack_result.conflicts))
            self.assertTrue(assertEqualDependencies(pack.replaces,
                                                    pack_result.replaces))
            self.assertEqual(pack.exports[0].tagname, pack_result.exports[0].tagname)
            self.assertEqual(pack.exports[1].tagname, pack_result.exports[1].tagname)

            rdict = parse_package_for_distutils(file2)
            self.assertEqual({'name': 'bar',
                              'maintainer': u'John Foo <foo@bar.com>, John Foo <foo@bar.com>',
                              'description': 'pdesc',
                              'license': 'BSD, MIT',
                              'version': '0.0.0',
                              'author': u'John Foo <foo@bar.com>, John Foo <foo@bar.com>',
                              'url': 'bar',
                              'keywords': ['ROS']}, rdict)
        finally:
            shutil.rmtree(rootdir)
