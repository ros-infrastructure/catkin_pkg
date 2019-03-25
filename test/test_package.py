import os.path
# Redirect stderr to stdout to suppress output in tests
import sys
import unittest

import xml.dom.minidom as dom

from catkin_pkg.package import (
    _check_known_attributes,
    _get_package_xml,
    Dependency,
    Export,
    InvalidPackage,
    License,
    Package,
    parse_package,
    parse_package_string,
    Person,
)

from mock import Mock

sys.stderr = sys.stdout

test_data_dir = os.path.join(os.path.dirname(__file__), 'data', 'package')


class PackageTest(unittest.TestCase):

    def get_maintainer(self):
        maint = Mock()
        maint.email = 'foo@bar.com'
        maint.name = 'John Foo'
        return maint

    def get_group_dependency(self, name):
        group = Mock()
        group.name = name
        return group

    def test_init(self):
        maint = self.get_maintainer()
        pack = Package(name='foo',
                       version='0.0.0',
                       maintainers=[maint],
                       licenses=['BSD'])
        self.assertEqual(None, pack.filename)
        self.assertEqual('0.0.0', pack.version)
        self.assertEqual(None, pack.version_compatibility)
        self.assertEqual([], pack.urls)
        self.assertEqual([], pack.authors)
        self.assertEqual([maint], pack.maintainers)
        self.assertEqual(['BSD'], pack.licenses)
        self.assertEqual([None], [l.file for l in pack.licenses])
        self.assertEqual([], pack.build_depends)
        self.assertEqual([], pack.buildtool_depends)
        self.assertEqual([], pack.run_depends)
        self.assertEqual([], pack.test_depends)
        self.assertEqual([], pack.conflicts)
        self.assertEqual([], pack.replaces)
        self.assertEqual([], pack.exports)
        self.assertEqual([], pack.group_depends)
        self.assertEqual([], pack.member_of_groups)
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
                         version_gt=5,
                         condition='$foo == 23 and $bar != 42')
        self.assertEqual('foo', dep.name)
        self.assertEqual(1, dep.version_lt)
        self.assertEqual(2, dep.version_lte)
        self.assertEqual(3, dep.version_eq)
        self.assertEqual(4, dep.version_gte)
        self.assertEqual(5, dep.version_gt)
        self.assertFalse(dep.evaluate_condition({'foo': 23, 'bar': 42}))
        self.assertFalse(dep.evaluated_condition)
        self.assertTrue(dep.evaluate_condition({'foo': 23, 'bar': 43}))
        self.assertTrue(dep.evaluated_condition)
        self.assertRaises(TypeError, Dependency, 'foo', unknownattribute=42)

        d = {}
        d[dep] = None
        dep2 = Dependency('foo',
                          version_lt=1,
                          version_lte=2,
                          version_eq=3,
                          version_gte=4,
                          version_gt=5,
                          condition='$foo == 23 and $bar != 42')
        dep2.evaluate_condition({'foo': 23, 'bar': 43})
        d[dep2] = None
        self.assertEqual(len(d), 1)
        dep3 = Dependency('foo',
                          version_lt=1,
                          version_lte=2,
                          version_eq=3,
                          version_gte=4,
                          version_gt=6)
        d[dep3] = None
        self.assertEqual(len(d), 2)

        dep = Dependency('foo', condition='foo > bar and bar < baz')
        self.assertTrue(dep.evaluate_condition({}))

        dep = Dependency('foo', condition='foo <= bar or bar >= baz')
        self.assertFalse(dep.evaluate_condition({}))

    def test_init_kwargs_string(self):
        pack = Package('foo',
                       name='bar',
                       package_format='1',
                       version='0.0.1',
                       version_compatibility='0.0.0',
                       description='pdesc',
                       licenses=['BSD'],
                       maintainers=[self.get_maintainer()])
        self.assertEqual('foo', pack.filename)
        self.assertEqual('bar', pack.name)
        self.assertEqual('1', pack.package_format)
        self.assertEqual('0.0.0', pack.version_compatibility)
        self.assertEqual('0.0.1', pack.version)
        self.assertEqual('pdesc', pack.description)

    def test_init_kwargs_object(self):
        mmain = [self.get_maintainer(), self.get_maintainer()]
        mlis = ['MIT', License('BSD', 'LICENSE')]
        mauth = [self.get_maintainer(), self.get_maintainer()]
        murl = [Mock(), Mock()]
        mbuilddep = [Mock(), Mock()]
        mbuildtooldep = [Mock(), Mock()]
        mrundep = [Mock(), Mock()]
        mtestdep = [Mock(), Mock()]
        mconf = [Mock(), Mock()]
        mrepl = [Mock(), Mock()]
        mexp = [Mock(), Mock()]
        mgroup = [
            self.get_group_dependency('group1'),
            self.get_group_dependency('group2')]
        mmember = ['member1', 'member2']
        pack = Package(package_format='3',
                       name='bar',
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
                       group_depends=mgroup,
                       member_of_groups=mmember,
                       exports=mexp)
        self.assertEqual(mmain, pack.maintainers)
        self.assertEqual(mlis, pack.licenses)
        self.assertEqual([None, 'LICENSE'], [l.file for l in pack.licenses])
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
        self.assertEqual(mgroup, pack.group_depends)
        self.assertEqual(mmember, pack.member_of_groups)

    def test_validate_package(self):
        maint = self.get_maintainer()
        pack = Package('foo',
                       name='bar_2go',
                       package_format='1',
                       version='0.0.1',
                       description='pdesc',
                       licenses=['BSD'],
                       maintainers=[maint])
        pack.validate()

        # names that should error
        pack.name = 'bar bza'
        self.assertRaises(InvalidPackage, Package.validate, pack)
        pack.name = 'foo%'
        self.assertRaises(InvalidPackage, Package.validate, pack)

        # names that should throw warnings
        pack.name = '2bar'
        warnings = []
        pack.validate(warnings=warnings)
        self.assertIn('naming conventions', warnings[0])

        pack.name = 'bar-bza'
        warnings = []
        pack.validate(warnings=warnings)
        self.assertEqual(warnings, [])

        pack.name = 'BAR'
        warnings = []
        pack.validate(warnings=warnings)
        self.assertIn('naming conventions', warnings[0])

        # dashes are permitted for a non-catkin package
        pack.exports.append(Export('build_type', 'other'))
        pack.name = 'bar-bza'
        warnings = []
        pack.validate(warnings=warnings)
        self.assertEqual(warnings, [])
        pack.exports.pop()

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

    def test_invalid_package_exception(self):
        try:
            raise InvalidPackage('foo')
        except InvalidPackage as e:
            self.assertEqual('foo', str(e))
            self.assertEqual(None, e.package_path)
        try:
            raise InvalidPackage('foo', package_path='./bar')
        except InvalidPackage as e:
            self.assertEqual("Error(s) in package './bar':\nfoo", str(e))
            self.assertEqual('./bar', e.package_path)

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

    def test_check_known_attributes(self):

        def create_node(tag, attrs):
            data = '<%s %s/>' % (tag, ' '.join(('%s="%s"' % p) for p in attrs.items()))
            return dom.parseString(data).firstChild

        try:
            create_node('tag', {'key': 'value'})
        except Exception as e:
            self.fail('create_node() raised %s "%s" unexpectedly!' % (type(e), str(e)))

        self.assertRaisesRegexp(Exception, 'unbound prefix: line 1, column 0', create_node, 'tag', {'ns:key': 'value'})

        try:
            create_node('tag', {'ns:key': 'value', 'xmlns:ns': 'urn:ns'})
        except Exception as e:
            self.fail('create_node() raised %s "%s" unexpectedly!' % (type(e), str(e)))

        def check(attrs, known, res=[]):
            self.assertEqual(res, _check_known_attributes(create_node('tag', attrs), known))

        expected_err = ['The "tag" tag must not have the following attributes: attr2']

        check({}, [])
        check({}, ['attr'])
        check({'attr': 'value'}, ['attr'])
        check({'attr2': 'value'}, ['attr'], expected_err)

        check({'xmlns': 'urn:ns'}, ['attr'])
        check({'xmlns:ns': 'urn:ns'}, ['attr'])
        check({'xmlns:ns': 'urn:ns', 'ns:attr': 'value'}, ['attr'])
        check({'xmlns:ns': 'urn:ns', 'ns:attr': 'value', 'attr2': 'value'}, ['attr'], expected_err)

    def test_parse_package_valid(self):
        filename = os.path.join(test_data_dir, 'valid_package.xml')
        package = parse_package(filename)
        assert package.filename == filename
        assert not package.is_metapackage()
        assert package.name == 'valid_package'
        assert package.description == 'valid_package description'
        assert package.version == '0.1.0'
        assert package.licenses == ['BSD']
        assert [x.name for x in package.run_depends] == ['foo', 'bar', 'baz']

    def test_parse_package_invalid(self):
        filename = os.path.join(test_data_dir, 'invalid_package.xml')
        self.assertRaises(InvalidPackage, parse_package, filename)

    def test_parse_package_string(self):
        filename = os.path.join(test_data_dir, 'valid_package.xml')
        xml = _get_package_xml(filename)[0]

        assert isinstance(xml, str)
        parse_package_string(xml)

        if sys.version_info[0] == 2:
            xml = xml.decode('utf-8')
            assert not isinstance(xml, str)
        else:
            xml = xml.encode('utf-8')
            assert isinstance(xml, bytes)
        parse_package_string(xml)
