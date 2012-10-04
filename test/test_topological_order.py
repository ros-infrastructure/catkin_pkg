import os
import unittest

try:
    from catkin_pkg.topological_order import topological_order
except ImportError as e:
    raise ImportError('Please adjust your PYTHONPATH before running this test: %s' % str(e))


class TopologicalOrderTest(unittest.TestCase):

    def test_recursive_run_depends(self):
        test_dir = os.path.join(os.path.dirname(__file__), 'topological_order')
        packages = topological_order(test_dir)
        # c must be before b because of the run dependency from a to c
        self.assertEqual(['a', 'c', 'b'], [name for name, _ in packages])
