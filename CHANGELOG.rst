1.1.0 (2025-09-09)
==================

- Declare dependency on setuptools in stdeb. `#360 <https://github.com/ros-infrastructure/catkin_pkg/pull/360>`_
- Update Ubuntu and Debian platforms supported by catkin_pkg. `#359 <https://github.com/ros-infrastructure/catkin_pkg/pull/359>`_
- Move flake8 import into test. `#361 <https://github.com/ros-infrastructure/catkin_pkg/pull/361>`_
- Switch to a raw string for the prepare_release cli. `#362 <https://github.com/ros-infrastructure/catkin_pkg/pull/362>`_
- Switch to ros-infrastructure centralized CI. `#363 <https://github.com/ros-infrastructure/catkin_pkg/pull/363>`_
- Support PEP 338 invocation of catkin_pkg modules. `#367 <https://github.com/ros-infrastructure/catkin_pkg/pull/367>`_
- Use platform-agnostic path manipulation in test_packages.py. `#366 <https://github.com/ros-infrastructure/catkin_pkg/pull/366>`_
- Deprecate the bare catkin_* scripts. `#368 <https://github.com/ros-infrastructure/catkin_pkg/pull/368>`_
- Fix symlink resolution on Windows w/short filenames. `#365 <https://github.com/ros-infrastructure/catkin_pkg/pull/365>`_
- Enable tests on Windows. `#364 <https://github.com/ros-infrastructure/catkin_pkg/pull/364>`_
- Fix AttributeError with docutils >= 0.18. `#352 <https://github.com/ros-infrastructure/catkin_pkg/pull/352>`_
- Remove spurious global declaration. `#375 <https://github.com/ros-infrastructure/catkin_pkg/pull/375>`_
- Replace pkg_resources usage with packaging. `#374 <https://github.com/ros-infrastructure/catkin_pkg/pull/374>`_

Contributors
------------

- Chris Lalancette
- Johannes Rothe
- Scott K Logan
- Steven! Ragnarök

1.0.0 (2023-09-12)
==================

- List 'ROS Infrastructure Team' as the package maintainer. `#328 <https://github.com/ros-infrastructure/catkin_pkg/pull/328>`_
- Drop support for Python 2. `#354 <https://github.com/ros-infrastructure/catkin_pkg/pull/354>`_
- Move flake8 config to setup.cfg, address flake8 v6 violations. `#356 <https://github.com/ros-infrastructure/catkin_pkg/pull/356>`_

Contributors
------------

- Scott K Logan
- Steven! Ragnarök

0.5.2 (2022-05-27)
==================

- Use renamed function for getting multiple build types. `#342 <https://github.com/ros-infrastructure/catkin_pkg/pull/342>`_
  - Resolves `#341 <https://github.com/ros-infrastructure/catkin_pkg/pull/341>`_

Contributors
------------

- Steven! Ragnarök

0.5.1 (2022-05-10)
==================

- Add API method for getting all build types regardless of conditions. `#337 <https://github.com/ros-infrastructure/catkin_pkg/pull/337>`_
- Pass all string format arguments as a tuple. `#339 <https://github.com/ros-infrastructure/catkin_pkg/pull/339>`_
  - Resolves `#338 <https://github.com/ros-infrastructure/catkin_pkg/pull/338>`_
- Consider all build types when updating package versions. `#340 <https://github.com/ros-infrastructure/catkin_pkg/pull/340>`_
  - Resolves `#336 <https://github.com/ros-infrastructure/catkin_pkg/pull/336>`_

Contributors
------------

- Scott K Logan
- Steven! Ragnarök

0.5.0 (2022-05-10)
==================

- Remove references to Travis CI. `#314 <https://github.com/ros-infrastructure/catkin_pkg/pull/314>`_
- Drop python 2.7 on macOS. `#318 <https://github.com/ros-infrastructure/catkin_pkg/pull/318>`_
- Update release suites. `#317 <https://github.com/ros-infrastructure/catkin_pkg/pull/317>`_
- Use unittest.mock where possible. `#321 <https://github.com/ros-infrastructure/catkin_pkg/pull/321>`_
- Declare test dependencies in extras_require.test. `#323 <https://github.com/ros-infrastructure/catkin_pkg/pull/323>`_
- Drop support for Python < 2.7 (2.7 itself is still supported). `#322 <https://github.com/ros-infrastructure/catkin_pkg/pull/322>`_
- Run tests with pytest instead of nose. `#324 <https://github.com/ros-infrastructure/catkin_pkg/pull/324>`_
- Enable Python 3.10 tests, bump actions/setup-python. `#325 <https://github.com/ros-infrastructure/catkin_pkg/pull/325>`_
- Mark linter test and declare cov/junit module name. `#327 <https://github.com/ros-infrastructure/catkin_pkg/pull/327>`_
- Add plaintext_description field to Package. `#305 <https://github.com/ros-infrastructure/catkin_pkg/pull/305>`_
- Use only first line of plaintext description in distutils setup generation. `#326 <https://github.com/ros-infrastructure/catkin_pkg/pull/326>`_
- Update catkin_prepare_release to support setup.py files in ament_python packages. `#331 <https://github.com/ros-infrastructure/catkin_pkg/pull/331>`_
  - This pull requests introduces an API change!
    ``catkin_pkg.package_version.update_packages`` now takes the full dict of package Paths: Package objects instead of just the paths.
- Make filenames to be used as ignore markers configurable. `#307 <https://github.com/ros-infrastructure/catkin_pkg/pull/307>`_
- Fix catkin_package_version after API change. `#333 <https://github.com/ros-infrastructure/catkin_pkg/pull/333>`_

Contributors
------------

- Jan Strohbeck
- Scott K Logan
- Steven! Ragnarök
- Tomáš Hrnčiar
- William Woodall
