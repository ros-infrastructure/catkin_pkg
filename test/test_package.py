import sys
import os
import unittest

from catkin_pkg.package import Package

from mock import Mock

class PackageTest(unittest.TestCase):

    def test_init(self):
        pack = Package()
        self.assertEqual(None, pack.filename)
        self.assertEqual([], pack.urls)
        self.assertEqual([], pack.authors)
        self.assertEqual([], pack.maintainers)
        self.assertEqual([], pack.licenses)
        self.assertEqual([], pack.build_depends)
        self.assertEqual([], pack.buildtool_depends)
        self.assertEqual([], pack.run_depends)
        self.assertEqual([], pack.test_depends)
        self.assertEqual([], pack.conflicts)
        self.assertEqual([], pack.replaces)
        self.assertEqual([], pack.exports)
        pack = Package('foo')
        self.assertEqual('foo', pack.filename)

        self.assertRaises(TypeError, Package, unknownattribute=42)


    def test_init_kwargs_string(self):
        pack = Package('foo',
                       name='bar',
                       package_format='pformat',
                       version='pversion',
                       version_abi='pabi',
                       description='pdesc')
        self.assertEqual('foo', pack.filename)
        self.assertEqual('bar', pack.name)
        self.assertEqual('pformat', pack.package_format)
        self.assertEqual('pabi', pack.version_abi)
        self.assertEqual('pversion', pack.version)
        self.assertEqual('pdesc', pack.description)

    def test_init_kwargs_object(self):
        mmain = [Mock(), Mock()]
        mlis = [Mock(), Mock()]
        mauth = [Mock(), Mock()]
        murl = [Mock(), Mock()]
        mbuilddep = [Mock(), Mock()]
        mbuildtooldep = [Mock(), Mock()]
        mrundep = [Mock(), Mock()]
        mtestdep = [Mock(), Mock()]
        mconf = [Mock(), Mock()]
        mrepl = [Mock(), Mock()]
        mexp = [Mock(), Mock()]
        pack = Package(maintainers=mmain,
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
        self.assertEqual(mrundep, pack.run_depends)
        self.assertEqual(mtestdep, pack.test_depends)
        self.assertEqual(mconf, pack.conflicts)
        self.assertEqual(mrepl, pack.replaces)
        self.assertEqual(mexp, pack.exports)
        
