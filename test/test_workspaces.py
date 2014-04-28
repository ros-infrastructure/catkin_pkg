from __future__ import print_function

import os
import shutil
import tempfile
import unittest

try:
    from catkin_pkg.workspaces import ensure_workspace_marker, get_spaces, order_paths,\
        CATKIN_WORKSPACE_MARKER_FILE
except ImportError as e:
    raise ImportError('Please adjust your PYTHONPATH before running this test: %s' % str(e))


class WorkspacesTest(unittest.TestCase):

    def test_ensure_workspace_marker(self):
        try:
            root_dir = tempfile.mkdtemp()
            ensure_workspace_marker(root_dir)
            self.assertTrue(os.path.exists(os.path.join(root_dir, CATKIN_WORKSPACE_MARKER_FILE)))
            # assert no exception on revisit
            ensure_workspace_marker(root_dir)
        finally:
            shutil.rmtree(root_dir)

