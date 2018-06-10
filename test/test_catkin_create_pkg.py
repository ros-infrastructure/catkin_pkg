import os
import shutil
import tempfile
import unittest

try:
    from catkin_pkg.package_templates import PackageTemplate
except ImportError as impe:
    raise ImportError(
        'Please adjust your pythonpath before running this test: %s' % str(impe))


from catkin_pkg.cli.create_pkg import main


class CreatePkgTest(unittest.TestCase):

    def test_create_package_template(self):
        template = PackageTemplate._create_package_template('foopackage')
        self.assertEqual('foopackage', template.name)
        self.assertEqual('0.0.0', template.version)
        self.assertEqual('The foopackage package', template.description)
        self.assertEqual([], template.catkin_deps)
        self.assertEqual([], template.authors)
        self.assertEqual(1, len(template.maintainers))
        self.assertIsNotNone(template.maintainers[0].email)
        self.assertEqual([], template.urls)
        # with args
        template = PackageTemplate._create_package_template(
            'foopackage',
            description='foo_desc',
            licenses=['a', 'b'],
            maintainer_names=['John Doe', 'Jim Daniels'],
            author_names=['Harry Smith'],
            version='1.2.3',
            catkin_deps=['foobar', 'baz'])
        self.assertEqual('foopackage', template.name)
        self.assertEqual('1.2.3', template.version)
        self.assertEqual('foo_desc', template.description)
        self.assertEqual(['baz', 'foobar'], template.catkin_deps)
        self.assertEqual(1, len(template.authors))
        self.assertEqual('Jim Daniels', template.maintainers[0].name)
        self.assertEqual('John Doe', template.maintainers[1].name)
        self.assertEqual('Harry Smith', template.authors[0].name)
        self.assertEqual(2, len(template.maintainers))
        self.assertEqual([], template.urls)

    def test_main(self):
        try:
            root_dir = tempfile.mkdtemp()
            main(['--rosdistro', 'groovy', 'foo'], root_dir)
            self.assertTrue(os.path.isdir(os.path.join(root_dir, 'foo')))
            self.assertTrue(os.path.isfile(os.path.join(root_dir, 'foo', 'CMakeLists.txt')))
            self.assertTrue(os.path.isfile(os.path.join(root_dir, 'foo', 'package.xml')))
        finally:
            shutil.rmtree(root_dir)
