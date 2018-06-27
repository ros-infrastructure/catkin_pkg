import os
import shutil
import tempfile
import unittest

from catkin_pkg.package import Dependency, Export, PACKAGE_MANIFEST_FILENAME, parse_package, Url
from catkin_pkg.package_templates import _create_include_macro, _create_targetlib_args, _safe_write_files, \
    create_cmakelists, create_package_files, create_package_xml, PackageTemplate
from catkin_pkg.python_setup import generate_distutils_setup

from mock import MagicMock, Mock


def u(line):
    try:
        return unicode(line)
    except NameError:
        return line


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
        mock_pack.catkin_deps = []
        result = create_cmakelists(mock_pack, 'groovy')
        self.assertTrue('project(foo)' in result, result)
        self.assertTrue('find_package(catkin REQUIRED)' in result, result)

        mock_pack.catkin_deps = ['bar', 'baz']
        result = create_cmakelists(mock_pack, 'groovy')
        self.assertTrue('project(foo)' in result, result)
        expected = """find_package(catkin REQUIRED COMPONENTS
  bar
  baz
)"""

        self.assertTrue(expected in result, result)

    def test_create_package_xml(self):
        maint = self.get_maintainer()
        pack = PackageTemplate(name='foo',
                               description='foo',
                               version='0.0.0',
                               maintainers=[maint],
                               licenses=['BSD'])

        result = create_package_xml(pack, 'groovy')
        self.assertTrue('<name>foo</name>' in result, result)

    def test_create_targetlib_args(self):
        mock_pack = MagicMock()
        mock_pack.name = 'foo'
        mock_pack.catkin_deps = []
        mock_pack.boost_comps = []
        mock_pack.system_deps = []
        statement = _create_targetlib_args(mock_pack)
        self.assertEqual('#   ${catkin_LIBRARIES}\n', statement)
        mock_pack.catkin_deps = ['roscpp', 'rospy']
        mock_pack.boost_comps = []
        mock_pack.system_deps = []
        statement = _create_targetlib_args(mock_pack)
        self.assertEqual('#   ${catkin_LIBRARIES}\n', statement)
        mock_pack.catkin_deps = ['roscpp']
        mock_pack.boost_comps = ['thread', 'filesystem']
        mock_pack.system_deps = []
        statement = _create_targetlib_args(mock_pack)
        self.assertEqual('#   ${catkin_LIBRARIES}\n#   ${Boost_LIBRARIES}\n', statement)
        mock_pack.catkin_deps = ['roscpp']
        mock_pack.boost_comps = []
        mock_pack.system_deps = ['log4cxx', 'BZip2']
        statement = _create_targetlib_args(mock_pack)
        self.assertEqual('#   ${catkin_LIBRARIES}\n#   ${log4cxx_LIBRARIES}\n#   ${BZip2_LIBRARIES}\n', statement)
        mock_pack.catkin_deps = ['roscpp']
        mock_pack.boost_comps = ['thread', 'filesystem']
        mock_pack.system_deps = ['log4cxx', 'BZip2']
        statement = _create_targetlib_args(mock_pack)
        self.assertEqual('#   ${catkin_LIBRARIES}\n#   ${Boost_LIBRARIES}\n#   ${log4cxx_LIBRARIES}\n#   ${BZip2_LIBRARIES}\n', statement)

    def test_create_include_macro(self):
        mock_pack = MagicMock()
        mock_pack.name = 'foo'
        mock_pack.catkin_deps = []
        mock_pack.boost_comps = []
        mock_pack.system_deps = []
        statement = _create_include_macro(mock_pack)
        self.assertEqual('# include\n# ${catkin_INCLUDE_DIRS}', statement)
        mock_pack.catkin_deps = ['roscpp', 'rospy']
        mock_pack.boost_comps = []
        mock_pack.system_deps = []
        statement = _create_include_macro(mock_pack)
        self.assertEqual('# include\n  ${catkin_INCLUDE_DIRS}', statement)
        mock_pack.catkin_deps = ['roscpp']
        mock_pack.boost_comps = ['thread', 'filesystem']
        mock_pack.system_deps = []
        statement = _create_include_macro(mock_pack)
        self.assertEqual('# include\n  ${catkin_INCLUDE_DIRS}\n  ${Boost_INCLUDE_DIRS}', statement)
        mock_pack.catkin_deps = ['roscpp']
        mock_pack.boost_comps = []
        mock_pack.system_deps = ['log4cxx', 'BZip2']
        statement = _create_include_macro(mock_pack)
        self.assertEqual('# include\n  ${catkin_INCLUDE_DIRS}\n# TODO: Check names of system library include directories (log4cxx, BZip2)\n'
                         '  ${log4cxx_INCLUDE_DIRS}\n  ${BZip2_INCLUDE_DIRS}', statement)
        mock_pack.catkin_deps = ['roscpp']
        mock_pack.boost_comps = ['thread', 'filesystem']
        mock_pack.system_deps = ['log4cxx', 'BZip2']
        statement = _create_include_macro(mock_pack)
        self.assertEqual('# include\n  ${catkin_INCLUDE_DIRS}\n  ${Boost_INCLUDE_DIRS}\n# TODO: Check names of system library include directories (log4cxx, BZip2)\n'
                         '  ${log4cxx_INCLUDE_DIRS}\n  ${BZip2_INCLUDE_DIRS}', statement)

    def test_create_package(self):
        maint = self.get_maintainer()
        pack = PackageTemplate(name='bar',
                               description='bar',
                               package_format='1',
                               version='0.0.1',
                               version_compatibility='0.0.0',
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

    def test_create_package_template(self):
        template = PackageTemplate._create_package_template(
            package_name='bar2',
            catkin_deps=['dep1', 'dep2'])
        self.assertEqual('dep1', template.build_depends[0].name)
        self.assertEqual('dep2', template.build_depends[1].name)

    def test_parse_generated(self):
        maint = self.get_maintainer()
        pack = PackageTemplate(name='bar',
                               package_format=2,
                               version='0.0.1',
                               version_compatibility='0.0.0',
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
            self.assertEqual(pack.version_compatibility, pack_result.version_compatibility)
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

            rdict = generate_distutils_setup(package_xml_path=file2)
            self.assertEqual({'name': 'bar',
                              'maintainer': u('John Foo'),
                              'maintainer_email': 'foo@bar.com',
                              'description': 'pdesc',
                              'license': 'BSD',
                              'version': '0.0.1',
                              'author': '',
                              'url': 'foo'}, rdict)
        finally:
            shutil.rmtree(rootdir)

    def test_parse_generated_multi(self):
        # test with multiple attributes filled
        maint = self.get_maintainer()
        pack = PackageTemplate(name='bar',
                               package_format=2,
                               version='0.0.1',
                               version_compatibility='0.0.0',
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
            self.assertEqual(pack.version_compatibility, pack_result.version_compatibility)
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

            rdict = generate_distutils_setup(package_xml_path=file2)
            self.assertEqual({'name': 'bar',
                              'maintainer': u('John Foo <foo@bar.com>, John Foo <foo@bar.com>'),
                              'description': 'pdesc',
                              'license': 'BSD, MIT',
                              'version': '0.0.1',
                              'author': u('John Foo <foo@bar.com>, John Foo <foo@bar.com>'),
                              'url': 'bar'}, rdict)
        finally:
            shutil.rmtree(rootdir)
