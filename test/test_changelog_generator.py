# coding=utf-8

from datetime import datetime
import os

from catkin_pkg.changelog import Changelog
from catkin_pkg.changelog import populate_changelog_from_rst
from catkin_pkg.changelog_generator import filter_package_changes
from catkin_pkg.changelog_generator import generate_changelog_file
from catkin_pkg.changelog_generator import generate_changelogs
from catkin_pkg.changelog_generator import generate_version_content
from catkin_pkg.changelog_generator import get_version_section_match
from catkin_pkg.changelog_generator import update_changelog_file
from catkin_pkg.changelog_generator import update_changelogs
from catkin_pkg.changelog_generator_vcs import LogEntry
from catkin_pkg.changelog_generator_vcs import Tag
from catkin_pkg.package import Package

import pytest


@pytest.mark.parametrize(('path', 'expected'), [
    ('sensor', [0, 2]),
    ('sensor_tools', [1, 2]),
    ('.', [0, 1, 2]),
    ('missing', []),
])
def test_filter_package_changes(path, expected):
    entries = [
        LogEntry('Sensor fix', [os.path.join('sensor', 'src', 'sensor.cpp')], 'Ada'),
        LogEntry('Tools fix', [os.path.join('sensor_tools', 'tool.py')], 'Bob'),
        LogEntry('Shared fix', [os.path.join('sensor', 'package.xml'), os.path.join('sensor_tools', 'package.xml')], 'Ada'),
    ]
    forthcoming = Tag(None)
    unchanged = Tag('1.2.0', '2026-01-01')
    changes = {forthcoming: entries, unchanged: None}

    filtered = filter_package_changes(changes, path)

    assert filtered == {forthcoming: [entries[i] for i in expected], unchanged: None}
    assert changes == {forthcoming: entries, unchanged: None}
    assert len(entries) == 3


def test_generate_changelog_file_orders_versions_and_skips_anchors():
    changes = {
        Tag('1.2.9', '2026-01-09'): [LogEntry('Older release', ['a'], 'Bob')],
        Tag('v1.2.10', '2026-01-10'): [LogEntry('Newer release', ['a'], 'Ada')],
        Tag('1.1.0', '2025-12-01'): None,
        Tag(None): [LogEntry('Unreleased change', ['a'], 'Zoë')],
    }

    data = generate_changelog_file('sensor', changes)

    assert data == """\
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package sensor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Forthcoming
-----------
* Unreleased change
* Contributors: Zoë

1.2.10 (2026-01-10)
-------------------
* Newer release
* Contributors: Ada

1.2.9 (2026-01-09)
------------------
* Older release
* Contributors: Bob
"""
    changelog = populate_changelog_from_rst(Changelog('sensor'), data)
    assert [version for version, _, _ in changelog.foreach_version()] == ['1.2.9', '1.2.10']
    assert changelog.get_date_of_version('1.2.10') == datetime(2026, 1, 10)


@pytest.mark.parametrize(('skip_contributors', 'contributors'), [
    (False, '* Contributors: Ada, Zoë\n'),
    (True, ''),
])
def test_generate_version_content(skip_contributors, contributors):
    entries = [
        LogEntry('  Fix driver_\n\n  Keep topic_name and frame_ stable\nSigned-off-by: Example Author', ['a'], 'Zoë'),
        LogEntry('Second fix', ['b'], 'Ada'),
        LogEntry('Third fix', ['c'], 'Zoë'),
    ]

    data = generate_version_content(entries, skip_contributors=skip_contributors)

    assert data == (
        '* Fix driver\\_\n'
        '  Keep topic_name and frame\\_ stable\n'
        '* Second fix\n'
        '* Third fix\n' + contributors)


@pytest.mark.parametrize('newline', ['\n', '\r\n'])
def test_update_changelog_file_prepends_to_existing_section(newline):
    data = (
        'Forthcoming\n'
        '===========\n'
        '* Handwritten note\n\n'
        '1.0.0 (2026-01-01)\n'
        '------------------\n'
        '* Released change\n').replace('\n', newline)
    changes = {
        Tag(None): [LogEntry('New fix', ['a'], 'Ada')],
        Tag('1.0.0', '2026-01-01'): None,
    }

    updated = update_changelog_file(data, changes)

    assert updated.replace('\r\n', '\n') == (
        'Forthcoming\n'
        '===========\n'
        '* New fix\n'
        '* Contributors: Ada\n'
        '\n'
        '* Handwritten note\n\n'
        '1.0.0 (2026-01-01)\n'
        '------------------\n'
        '* Released change\n')
    # A different section is preserved byte-for-byte, including line endings.
    released_section = data[data.index('1.0.0'):]
    assert updated.endswith(released_section)


def test_update_changelog_file_inserts_forthcoming_before_known_release():
    data = '1.0.0 (2026-01-01)\n------------------\n* Released change\n'
    changes = {
        Tag(None): [LogEntry('New fix', ['a'], 'Ada')],
        Tag('1.0.0', '2026-01-01'): None,
    }

    updated = update_changelog_file(data, changes, skip_contributors=True)

    assert updated == 'Forthcoming\n-----------\n* New fix\n\n' + data


def test_duplicate_version_sections_are_rejected():
    data = '1.0.0\n-----\n* First\n\n1.0.0\n=====\n* Second\n'

    with pytest.raises(RuntimeError, match='Found multiple matching sections'):
        get_version_section_match(data, '1.0.0')
    with pytest.raises(RuntimeError, match='Found multiple matching sections'):
        update_changelog_file(data, {Tag('1.0.0'): []})


def test_update_changelog_file_rejects_missing_insertion_point():
    with pytest.raises(RuntimeError, match='Could neither find section'):
        update_changelog_file('Unrelated notes\n', {Tag('1.0.0'): []})


def test_generate_and_update_changelogs_use_package_paths_and_utf8(tmp_path):
    sensor_path = tmp_path / 'sensor'
    tools_path = tmp_path / 'sensor_tools'
    sensor_path.mkdir()
    tools_path.mkdir()
    tools_changelog = tools_path / 'CHANGELOG.rst'
    tools_changelog.write_bytes(b'Keep this manually maintained changelog.\n')
    packages = {'sensor': Package(name='sensor'), 'sensor_tools': Package(name='sensor_tools')}
    changes = {Tag(None): [
        LogEntry('Détecteur fix', [os.path.join('sensor', 'driver.py')], 'Zoë'),
        LogEntry('Tools fix', [os.path.join('sensor_tools', 'tool.py')], 'Bob'),
    ]}

    generate_changelogs(str(tmp_path), packages, changes)

    sensor_changelog = sensor_path / 'CHANGELOG.rst'
    assert sensor_changelog.read_text(encoding='utf-8') == """\
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package sensor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Forthcoming
-----------
* Détecteur fix
* Contributors: Zoë
"""
    assert tools_changelog.read_bytes() == b'Keep this manually maintained changelog.\n'

    update_changelogs(str(tmp_path), {'sensor': packages['sensor']}, {Tag(None): [
        LogEntry('Follow-up fix', [os.path.join('sensor', 'driver.py')], 'Ada'),
        LogEntry('Unrelated change', [os.path.join('sensor_tools', 'tool.py')], 'Bob'),
    ]}, skip_contributors=True)

    data = sensor_changelog.read_text(encoding='utf-8')
    assert '* Follow-up fix\n\n* Détecteur fix\n* Contributors: Zoë\n' in data
    assert 'Unrelated change' not in data
    assert 'Contributors: Ada' not in data
    assert tools_changelog.read_bytes() == b'Keep this manually maintained changelog.\n'
