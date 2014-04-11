import unittest

# Redirect stderr to stdout to suppress output in tests
import sys
sys.stderr = sys.stdout

from catkin_pkg.package import Dependency, InvalidPackage, Package, Person

from mock import Mock


class PackageTest(unittest.TestCase):

    def get_maintainer(self):
        maint = Mock()
        maint.email = 'foo@bar.com'
        maint.name = 'John Foo'
        return maint

    def test_init(self):
        maint = self.get_maintainer()
        pack = Package(name='foo',
                       version='0.0.0',
                       maintainers=[maint],
                       licenses=['BSD'])
        self.assertEqual(None, pack.filename)
        self.assertEqual([], pack.urls)
        self.assertEqual([], pack.authors)
        self.assertEqual([maint], pack.maintainers)
        self.assertEqual(['BSD'], pack.licenses)
        self.assertEqual([], pack.build_depends)
        self.assertEqual([], pack.buildtool_depends)
        self.assertEqual([], pack.run_depends)
        self.assertEqual([], pack.test_depends)
        self.assertEqual([], pack.conflicts)
        self.assertEqual([], pack.replaces)
        self.assertEqual([], pack.exports)
        pack = Package('foo',
                       name='bar',
                       version='0.0.0',
                       licenses=['BSD'],
                       maintainers=[self.get_maintainer()])
        self.assertEqual('foo', pack.filename)

        self.assertRaises(TypeError, Package, unknownattribute=42)

    def test_init_dependency(self):
        dep = Dependency('foo',
                         version_lt=1,
                         version_lte=2,
                         version_eq=3,
                         version_gte=4,
                         version_gt=5)
        self.assertEquals('foo', dep.name)
        self.assertEquals(1, dep.version_lt)
        self.assertEquals(2, dep.version_lte)
        self.assertEquals(3, dep.version_eq)
        self.assertEquals(4, dep.version_gte)
        self.assertEquals(5, dep.version_gt)
        self.assertRaises(TypeError, Dependency, 'foo', unknownattribute=42)

    def test_init_kwargs_string(self):
        pack = Package('foo',
                       name='bar',
                       package_format='1',
                       version='0.0.0',
                       version_abi='pabi',
                       description='pdesc',
                       licenses=['BSD'],
                       maintainers=[self.get_maintainer()])
        self.assertEqual('foo', pack.filename)
        self.assertEqual('bar', pack.name)
        self.assertEqual('1', pack.package_format)
        self.assertEqual('pabi', pack.version_abi)
        self.assertEqual('0.0.0', pack.version)
        self.assertEqual('pdesc', pack.description)

    def test_init_kwargs_object(self):
        mmain = [self.get_maintainer(), self.get_maintainer()]
        mlis = ['MIT', 'BSD']
        mauth = [self.get_maintainer(), self.get_maintainer()]
        murl = [Mock(), Mock()]
        mbuilddep = [Mock(), Mock()]
        mbuildtooldep = [Mock(), Mock()]
        mrundep = [Mock(), Mock()]
        mtestdep = [Mock(), Mock()]
        mconf = [Mock(), Mock()]
        mrepl = [Mock(), Mock()]
        mexp = [Mock(), Mock()]
        pack = Package(name='bar',
                       version='0.0.0',
                       maintainers=mmain,
                       licenses=mlis,
                       urls=murl,
                       authors=mauth,
                       build_depends=mbuilddep,
                       buildtool_depends=mbuildtooldep,
                       run_depends=mrundep,
                       test_depends=mtestdep,
                       conflicts=mconf,
                       replaces=mrepl,
                       exports=mexp)
        self.assertEqual(mmain, pack.maintainers)
        self.assertEqual(mlis, pack.licenses)
        self.assertEqual(murl, pack.urls)
        self.assertEqual(mauth, pack.authors)
        self.assertEqual(mbuilddep, pack.build_depends)
        self.assertEqual(mbuildtooldep, pack.buildtool_depends)
        # since run_depends are getting stores as build_export_depends as well as exec_depends
        # and the dependency objects are being cloned only the double count can be checked for
        self.assertEqual(2 * len(mrundep), len(pack.run_depends))
        self.assertEqual(mtestdep, pack.test_depends)
        self.assertEqual(mconf, pack.conflicts)
        self.assertEqual(mrepl, pack.replaces)
        self.assertEqual(mexp, pack.exports)

    def test_validate_package(self):
        maint = self.get_maintainer()
        pack = Package('foo',
                       name='bar_2go',
                       package_format='1',
                       version='0.0.0',
                       version_abi='pabi',
                       description='pdesc',
                       licenses=['BSD'],
                       maintainers=[maint])
        pack.validate()
        # check invalid names
        pack.name = '2bar'
        pack.validate()
        pack.name = 'bar bza'
        self.assertRaises(InvalidPackage, Package.validate, pack)
        pack.name = 'bar-bza'
        # valid for now because for backward compatibility only
        #self.assertRaises(InvalidPackage, Package.validate, pack)
        pack.name = 'BAR'
        pack.validate()
        # check authors emails
        pack.name = 'bar'
        auth1 = Mock()
        auth2 = Mock()
        auth2.validate.side_effect = InvalidPackage('foo')
        pack.authors = [auth1, auth2]
        self.assertRaises(InvalidPackage, Package.validate, pack)
        pack.authors = []
        pack.validate()
        # check maintainer required with email
        pack.maintainers = []
        self.assertRaises(InvalidPackage, Package.validate, pack)
        pack.maintainers = [maint]
        maint.email = None
        self.assertRaises(InvalidPackage, Package.validate, pack)
        maint.email = 'foo@bar.com'

        for dep_type in [pack.build_depends, pack.buildtool_depends, pack.build_export_depends, pack.buildtool_export_depends, pack.exec_depends, pack.test_depends, pack.doc_depends]:
            pack.validate()
            depend = Dependency(pack.name)
            dep_type.append(depend)
            self.assertRaises(InvalidPackage, Package.validate, pack)
            dep_type.remove(depend)

    def test_validate_person(self):
        auth1 = Person('foo')
        auth1.email = 'foo@bar.com'
        auth1.validate()
        auth1.email = 'foo-bar@bar.com'
        auth1.validate()
        auth1.email = 'foo+bar@bar.com'
        auth1.validate()

        auth1.email = 'foo[at]bar.com'
        self.assertRaises(InvalidPackage, Person.validate, auth1)
        auth1.email = 'foo bar.com'
        self.assertRaises(InvalidPackage, Person.validate, auth1)
        auth1.email = 'foo<bar.com'
        self.assertRaises(InvalidPackage, Person.validate, auth1)
