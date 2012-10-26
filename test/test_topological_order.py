from __future__ import print_function
import unittest
from mock import Mock
try:
    from catkin_pkg.topological_order import topological_order_packages, _PackageDecorator, \
        _sort_decorated_packages
except ImportError as e:
    raise ImportError('Please adjust your PYTHONPATH before running this test: %s' % str(e))


class TopologicalOrderTest(unittest.TestCase):

    def test_topological_order_packages(self):
        def create_mock(name, build_depends, run_depends, path):
            m = Mock()
            m.name = name
            m.build_depends = build_depends
            m.buildtool_depends = []
            m.run_depends = run_depends
            m.exports = []
            m.path = path
            return m

        mc = create_mock('c', [], [], 'pc')
        md = create_mock('d', [], [], 'pd')
        ma = create_mock('a', [mc], [md], 'pa')
        mb = create_mock('b', [ma], [], 'pb')

        packages = {ma.path: ma,
                    mb.path: mb,
                    mc.path: mc,
                    md.path: md}

        ordered_packages = topological_order_packages(packages, blacklisted=['c'])
        # d before b because of the run dependency from a to d
        # a before d only because of alphabetic order, a run depend on d should not influence the order
        self.assertEqual(['pa', 'pd', 'pb'], [path for path, _ in ordered_packages])

        ordered_packages = topological_order_packages(packages, whitelisted=['a', 'b', 'c'])
        # c before a because of the run dependency from a to c
        self.assertEqual(['pc', 'pa', 'pb'], [path for path, _ in ordered_packages])

    def test_package_decorator_init(self):

        mockproject = Mock()

        mockexport = Mock()
        mockexport.tagname = 'message_generator'
        mockexport.content = 'foolang'
        mockproject.exports = [mockexport]

        pd = _PackageDecorator(mockproject, 'foo/bar')
        self.assertEqual(mockproject.name, pd.name)
        self.assertEqual('foo/bar', pd.path)
        self.assertFalse(pd.is_metapackage)
        self.assertEqual(mockexport.content, pd.message_generator)
        self.assertIsNotNone(str(pd))

    def test_calculate_depends_for_topological_order(self):
        def create_mock(name, run_depends):
            m = Mock()
            m.name = name
            m.build_depends = []
            m.buildtool_depends = []
            m.run_depends = run_depends
            m.exports = []
            return m

        mockproject1 = _PackageDecorator(create_mock('n1', []), 'p1')
        mockproject2 = _PackageDecorator(create_mock('n2', []), 'p2')
        mockproject3 = _PackageDecorator(create_mock('n3', []), 'p3')
        mockproject4 = _PackageDecorator(create_mock('n4', []), 'p4')
        mockproject5 = _PackageDecorator(create_mock('n5', [mockproject4]), 'p5')
        mockproject6 = _PackageDecorator(create_mock('n6', [mockproject5]), 'p6')
        mockproject7 = _PackageDecorator(create_mock('n7', []), 'p7')

        mockproject = Mock()
        mockproject.build_depends = [mockproject1, mockproject2]
        mockproject.buildtool_depends = [mockproject3, mockproject6]
        mockproject.run_depends = [mockproject7]
        mockproject.exports = []

        pd = _PackageDecorator(mockproject, 'foo/bar')
        # 2 and 3 as external dependencies
        packages = {mockproject1.name: mockproject1,
                    mockproject4.name: mockproject4,
                    mockproject5.name: mockproject5,
                    mockproject6.name: mockproject6}

        pd.calculate_depends_for_topological_order(packages)
        self.assertEqual(set([mockproject1.name, mockproject4.name, mockproject5.name, mockproject6.name]), pd.depends_for_topological_order)

    def test_sort_decorated_packages(self):
        projects = {}
        sprojects = _sort_decorated_packages(projects)
        self.assertEqual([], sprojects)

        mock1 = Mock()
        mock1.depends_for_topological_order = set()

        mock1.message_generator = True

        mock2 = Mock()
        mock2.depends_for_topological_order = set()
        mock2.message_generator = False

        mock3 = Mock()
        mock3.depends_for_topological_order = set()
        mock3.message_generator = False

        projects = {'baz': mock3, 'bar': mock2, 'foo': mock1}
        sprojects = _sort_decorated_packages(projects)
        # mock1 has message generator, come first
        # mock2 before mock3 because of alphabetical ordering
        self.assertEqual([[mock1.path, mock1.package],
                          [mock2.path, mock2.package],
                          [mock3.path, mock3.package]], sprojects)
