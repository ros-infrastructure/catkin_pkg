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
    style_guide = get_style_guide(
        ignore=[
            'C403',  # Unnecessary list comprehension - rewrite as a set comprehension -- invalid syntax in Python 2
            'C404',  # Unnecessary list comprehension - rewrite as a dict comprehension -- invalid syntax in Python 2
            'C405',  # Unnecessary list literal - rewrite as a set literal.  -- invalid syntax in Python 2
            'D100',  # Missing docstring in public module
            'D101',  # Missing docstring in public class
            'D102',  # Missing docstring in public method
            'D103',  # Missing docstring in public function
            'D104',  # Missing docstring in public package
            'D105',  # Missing docstring in magic method
            'D106',  # Missing docstring in public nested class
            'D107',  # Missing docstring in __init__
            'D203',  # 1 blank line required before class docstring
            'D212',  # Multi-line docstring summary should start at the first line
            'D404',  # First word of the docstring should be This
            'I202',  # Additional newline in a group of imports
        ],
        max_line_length=200,
        max_complexity=10,
        show_source=True,
    )

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
