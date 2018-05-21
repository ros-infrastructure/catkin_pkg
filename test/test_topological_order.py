from __future__ import print_function

import unittest

from mock import Mock

try:
    from catkin_pkg.topological_order import topological_order_packages, _PackageDecorator, \
        _sort_decorated_packages
except ImportError as e:
    raise ImportError('Please adjust your PYTHONPATH before running this test: %s' % str(e))


def create_mock(name, build_depends, run_depends, path):
    m = Mock()
    m.name = name
    m.build_depends = build_depends
    m.buildtool_depends = []
    m.run_depends = run_depends
    m.test_depends = []
    m.group_depends = []
    m.exports = []
    m.path = path
    return m


class TopologicalOrderTest(unittest.TestCase):

    def test_topological_order_packages(self):
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

    def test_topological_order_packages_with_duplicates(self):
        pkg1 = create_mock('pkg', [], [], 'path/to/pkg1')
        pkg2_dep = create_mock('pkg_dep', [], [], 'path/to/pkg2_dep')
        pkg2 = create_mock('pkg', [pkg2_dep], [], 'path/to/pkg2')
        if hasattr(self, 'assertRaisesRegexp'):
            with self.assertRaisesRegexp(RuntimeError, 'Two packages with the same name "pkg" in the workspace'):
                topological_order_packages({
                    pkg1.path: pkg1,
                    pkg2_dep.path: pkg2_dep,
                    pkg2.path: pkg2,
                })

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
            m.group_depends = []
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
        mockproject.test_depends = []
        mockproject.group_depends = []
        mockproject.exports = []

        pd = _PackageDecorator(mockproject, 'foo/bar')
        # 2 and 3 as external dependencies
        packages = {mockproject1.name: mockproject1,
                    mockproject4.name: mockproject4,
                    mockproject5.name: mockproject5,
                    mockproject6.name: mockproject6}

        pd.calculate_depends_for_topological_order(packages)
        self.assertEqual(set([mockproject1.name, mockproject4.name, mockproject5.name, mockproject6.name]),
                         pd.depends_for_topological_order)

    def test_sort_decorated_packages(self):
        projects = {}
        sprojects = _sort_decorated_packages(projects)
        self.assertEqual([], sprojects)

        def create_mock(path):
            m = Mock()
            m.path = path
            m.depends_for_topological_order = set()
            m.message_generator = False
            return m

        mock1 = create_mock('mock1')
        mock2 = create_mock('mock2')
        mock3 = create_mock('mock3')
        mock3.message_generator = True

        projects = {'mock3': mock3, 'mock2': mock2, 'mock1': mock1}
        sprojects = _sort_decorated_packages(projects)

        # mock3 first since it is a message generator
        # mock1 before mock2 due to alphabetic order
        self.assertEqual(['mock3', 'mock1', 'mock2'], [path for path, _ in sprojects])

    def test_sort_decorated_packages_favoring_message_generators(self):
        def create_mock(path):
            m = Mock()
            m.path = path
            m.depends_for_topological_order = set()
            m.message_generator = False
            return m

        mock1 = create_mock('mock1')
        mock2 = create_mock('mock2')
        mock3 = create_mock('mock3')
        mock3.depends_for_topological_order = set(['mock2'])
        mock3.message_generator = True

        projects = {'mock3': mock3, 'mock2': mock2, 'mock1': mock1}
        sprojects = _sort_decorated_packages(projects)

        # mock2 first since it is the dependency of a message generator
        # mock3 since it is a message generator
        # mock1 last, although having no dependencies and being first in alphabetic order
        self.assertEqual(['mock2', 'mock3', 'mock1'], [path for path, _ in sprojects])

    def test_sort_decorated_packages_cycles(self):
        def create_mock(path, depend):
            m = Mock()
            m.path = path
            m.depends_for_topological_order = set([depend])
            m.message_generator = False
            return m

        # creating a cycle for cycle detection
        mock1 = create_mock('mock1', 'mock2')
        mock2 = create_mock('mock2', 'mock3')
        mock3 = create_mock('mock3', 'mock4')
        mock4 = create_mock('mock4', 'mock2')

        projects = {'mock3': mock3, 'mock2': mock2, 'mock1': mock1, 'mock4': mock4}
        sprojects = _sort_decorated_packages(projects)
        self.assertEqual([[None, 'mock2, mock3, mock4']], sprojects)

        # remove cycle
        mock4.depends_for_topological_order = set()
        sprojects = _sort_decorated_packages(projects)

        # mock4 first since it has no dependencies
        # than mock3 since it only had mock4 as a dependency
        # than mock2 since it only had mock3 as a dependency
        # than mock1 since it only had mock2 as a dependency
        self.assertEqual(['mock4', 'mock3', 'mock2', 'mock1'], [path for path, _ in sprojects])

    def test_topological_order_packages_with_underlay(self):
        def create_mock(name, build_depends, path):
            m = Mock()
            m.name = name
            m.build_depends = build_depends
            m.buildtool_depends = []
            m.run_depends = []
            m.test_depends = []
            m.group_depends = []
            m.exports = []
            m.path = path
            return m

        mc = create_mock('c', [], 'pc')
        mb = create_mock('b', [mc], 'pb')
        ma = create_mock('a', [mb], 'pa')

        packages = {ma.path: ma,
                    mc.path: mc}
        underlay_packages = {mb.path: mb}

        ordered_packages = topological_order_packages(packages, underlay_packages=underlay_packages)
        # c before a because of the indirect dependency via b which is part of an underlay
        self.assertEqual(['pc', 'pa'], [path for path, _ in ordered_packages])

    def test_topological_order_packages_cycles(self):
        def create_mock(name, build_depends, path):
            m = Mock()
            m.name = name
            m.build_depends = build_depends
            m.buildtool_depends = []
            m.test_depends = []
            m.run_depends = []
            m.group_depends = []
            m.exports = []
            m.path = path
            return m

        mc = create_mock('c', [], 'pc')
        mb = create_mock('b', [mc], 'pb')
        ma = create_mock('a', [mb], 'pa')
        mc.build_depends = [ma]

        packages = {ma.path: ma,
                    mb.math: mb,
                    mc.path: mc}

        ordered_packages = topological_order_packages(packages)
        self.assertEqual([(None, 'a, b, c')], ordered_packages)
