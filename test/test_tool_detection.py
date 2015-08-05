import os

from catkin_pkg.tool_detection import get_previous_tool_used_on_the_space
from catkin_pkg.tool_detection import mark_space_as_built_by

from .util import in_temporary_directory


@in_temporary_directory
def test_get_previous_tool_used_on_the_space():
    res = get_previous_tool_used_on_the_space('folder_that_does_not_exist')
    assert res is None, res
    os.makedirs('build')
    res = get_previous_tool_used_on_the_space('build')
    assert res is None, res
    mark_space_as_built_by('build', 'foo')
    res = get_previous_tool_used_on_the_space('build')
    assert res == 'foo', res
