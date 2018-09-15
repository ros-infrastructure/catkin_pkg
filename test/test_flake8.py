# Copyright 2018 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import os
import sys

from flake8.api.legacy import get_style_guide


def test_flake8():
    # Configure flake8 using the .flake8 file in the root of this repository.
    style_guide = get_style_guide()

    style_guide.options.exclude += ['*/doc/_build']

    stdout = sys.stdout
    sys.stdout = sys.stderr
    # implicitly calls report_errors()
    report = style_guide.check_files([
        os.path.dirname(os.path.dirname(__file__)),
    ])
    sys.stdout = stdout

    if report.total_errors:
        # output summary with per-category counts
        print()
        report._application.formatter.show_statistics(report._stats)
        print(
            'flake8 reported %d errors' % report.total_errors,
            file=sys.stderr)

    assert not report.total_errors, \
        'flake8 reported %d errors' % report.total_errors
