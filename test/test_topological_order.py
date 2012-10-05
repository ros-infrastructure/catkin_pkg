from __future__ import print_function
import os
import unittest
import sys

try:
    from catkin_pkg.topological_order import topological_order
except ImportError as e:
    raise ImportError('Please adjust your PYTHONPATH before running this test: %s' % str(e))


class TopologicalOrderTest(unittest.TestCase):

    def test_recursive_run_depends(self):
        test_dir = os.path.join(os.path.dirname(__file__), 'topological_order')

        packages = topological_order(test_dir, blacklisted=['c'])
        # d before b because of the run dependency from a to d
        # a before d only because of alphabetic order, a run depend on d should not influence the order
        self.assertEqual(['a', 'd', 'b'], [name for name, _ in packages])

        packages = topological_order(test_dir, whitelisted=['a', 'b', 'c'])
        # c before a because of the run dependency from a to c
        self.assertEqual(['c', 'a', 'b'], [name for name, _ in packages])
