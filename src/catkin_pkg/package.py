# Software License Agreement (BSD License)
#
# Copyright (c) 2012, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""Library for parsing package.xml and providing an object representation."""

from __future__ import print_function

from copy import deepcopy
import os
import re
import sys
import xml.dom.minidom as dom

from catkin_pkg.condition import evaluate_condition

PACKAGE_MANIFEST_FILENAME = 'package.xml'
PACKAGE_MANIFEST_SCHEMA_URLS = [
    'http://download.ros.org/schema/package_format1.xsd',
    'http://download.ros.org/schema/package_format2.xsd',
    'http://download.ros.org/schema/package_format3.xsd',
]


class Package(object):
    """Object representation of a package manifest file."""

    __slots__ = [
        'package_format',
        'name',
        'version',
        'version_compatibility',
        'description',
        'maintainers',
        'licenses',
        'urls',
        'authors',
        'build_depends',
        'buildtool_depends',
        'build_export_depends',
        'buildtool_export_depends',
        'exec_depends',
        'test_depends',
        'doc_depends',
        'conflicts',
        'replaces',
        'group_depends',
        'member_of_groups',
        'exports',
        'filename'
    ]

    def __init__(self, filename=None, **kwargs):
        """
        Initialize Package.

        :param filename: location of package.xml.  Necessary if
          converting ``${prefix}`` in ``<export>`` values, ``str``.
        """
        # initialize all slots ending with "s" with lists, all other with plain values
        for attr in self.__slots__:
            if attr.endswith('s'):
                value = list(kwargs[attr]) if attr in kwargs else []
                setattr(self, attr, value)
            else:
                value = kwargs[attr] if attr in kwargs else None
                setattr(self, attr, value)
        if 'depends' in kwargs:
            for d in kwargs['depends']:
                for slot in [self.build_depends, self.build_export_depends, self.exec_depends]:
                    if d not in slot:
                        slot.append(deepcopy(d))
            del kwargs['depends']
        if 'run_depends' in kwargs:
            for d in kwargs['run_depends']:
                for slot in [self.build_export_depends, self.exec_depends]:
                    if d not in slot:
                        slot.append(deepcopy(d))
            del kwargs['run_depends']
        self.filename = filename
        self.licenses = [license_ if isinstance(license_, License) else License(license_) for license_ in self.licenses]
        # verify that no unknown keywords are passed
        unknown = set(kwargs.keys()).difference(self.__slots__)
        if unknown:
            raise TypeError('Unknown properties: %s' % ', '.join(unknown))

    def __getattr__(self, name):
        if name == 'run_depends':
            # merge different dependencies if they are not exactly equal
            # potentially having the same dependency name multiple times with different attributes
            run_depends = []
            [run_depends.append(deepcopy(d)) for d in self.exec_depends + self.build_export_depends if d not in run_depends]
            return run_depends
        raise AttributeError(name)

    def __getitem__(self, key):
        if key in self.__slots__ + ['run_depends']:
            return getattr(self, key)
        raise KeyError('Unknown key "%s"' % key)

    def __iter__(self):
        for slot in self.__slots__:
            yield slot

    def __str__(self):
        data = {}
        for attr in self.__slots__:
            data[attr] = getattr(self, attr)
        return str(data)

    def has_buildtool_depend_on_catkin(self):
        """
        Return True if this Package buildtool depends on catkin, otherwise False.

        :returns: True if the given package buildtool depends on catkin
        :rtype: bool
        """
        return 'catkin' in (d.name for d in self.buildtool_depends)

    def get_build_type(self):
        """
        Return value of export/build_type element, or 'catkin' if unspecified.

        :returns: package build type
        :rtype: str
        :raises: :exc:`InvalidPackage`
        """
        # for backward compatibility a build type without an evaluated
        # condition is still being considered (i.e. evaluated_condition is None)
        build_type_exports = [
            e.content for e in self.exports
            if e.tagname == 'build_type' and e.evaluated_condition is not False]
        if not build_type_exports:
            return 'catkin'
        if len(build_type_exports) == 1:
            return build_type_exports[0]
        raise InvalidPackage('Only one <build_type> element is permitted.', self.filename)

    def has_invalid_metapackage_dependencies(self):
        """
        Return True if this package has invalid dependencies for a metapackage.

        This is defined by REP-0127 as any non-run_depends dependencies other then a buildtool_depend on catkin.

        :returns: True if the given package has any invalid dependencies, otherwise False
        :rtype: bool
        """
        buildtool_depends = [d.name for d in self.buildtool_depends if d.name != 'catkin']
        return len(self.build_depends + buildtool_depends + self.test_depends) > 0

    def is_metapackage(self):
        """
        Return True if this pacakge is a metapackage, otherwise False.

        :returns: True if metapackage, else False
        :rtype: bool
        """
        return 'metapackage' in (e.tagname for e in self.exports)

    def evaluate_conditions(self, context):
        """
        Evaluate the conditions of all dependencies and memberships.

        :param context: A dictionary with key value pairs to replace variables
          starting with $ in the condition.
        :raises: :exc:`ValueError` if any condition fails to parse
        """
        for attr in (
            'build_depends',
            'buildtool_depends',
            'build_export_depends',
            'buildtool_export_depends',
            'exec_depends',
            'test_depends',
            'doc_depends',
            'conflicts',
            'replaces',
            'group_depends',
            'member_of_groups',
            'exports',
        ):
            conditionals = getattr(self, attr)
            for conditional in conditionals:
                conditional.evaluate_condition(context)

    def validate(self, warnings=None):
        """
        Make sure all standards for packages are met.

        :param package: Package to check
        :param warnings: Print warnings if None or return them in the given list
        :raises InvalidPackage: in case validation fails
        """
        errors = []
        new_warnings = []

        def is_valid_spdx_identifier(lic):
            """
            Check if the license is already one of valid SPDX Identifiers.

            The list was created from https://spdx.org/licenses/ with:
            cat doc/spdx-3.10-2020-08-03.csv | cut -f 2 | grep -v ^Identifier$
            """
            return lic in ['0BSD', 'AAL', 'Abstyles', 'Adobe-2006', 'Adobe-Glyph', 'ADSL', 'AFL-1.1', 'AFL-1.2', 'AFL-2.0', 'AFL-2.1', 'AFL-3.0', 'Afmparse', 'AGPL-1.0-only', 'AGPL-1.0-or-later',
                           'AGPL-3.0-only', 'AGPL-3.0-or-later', 'Aladdin', 'AMDPLPA', 'AML', 'AMPAS', 'ANTLR-PD', 'Apache-1.0', 'Apache-1.1', 'Apache-2.0', 'APAFML', 'APL-1.0', 'APSL-1.0',
                           'APSL-1.1', 'APSL-1.2', 'APSL-2.0', 'Artistic-1.0', 'Artistic-1.0-cl8', 'Artistic-1.0-Perl', 'Artistic-2.0', 'Bahyph', 'Barr', 'Beerware', 'BitTorrent-1.0',
                           'BitTorrent-1.1', 'blessing', 'BlueOak-1.0.0', 'Borceux', 'BSD-1-Clause', 'BSD-2-Clause', 'BSD-2-Clause-Patent', 'BSD-2-Clause-Views', 'BSD-3-Clause',
                           'BSD-3-Clause-Attribution', 'BSD-3-Clause-Clear', 'BSD-3-Clause-LBNL', 'BSD-3-Clause-No-Nuclear-License', 'BSD-3-Clause-No-Nuclear-License-2014',
                           'BSD-3-Clause-No-Nuclear-Warranty', 'BSD-3-Clause-Open-MPI', 'BSD-4-Clause', 'BSD-4-Clause-UC', 'BSD-Protection', 'BSD-Source-Code', 'BSL-1.0', 'bzip2-1.0.5',
                           'bzip2-1.0.6', 'CAL-1.0', 'CAL-1.0-Combined-Work-Exception', 'Caldera', 'CATOSL-1.1', 'CC-BY-1.0', 'CC-BY-2.0', 'CC-BY-2.5', 'CC-BY-3.0', 'CC-BY-3.0-AT', 'CC-BY-4.0',
                           'CC-BY-NC-1.0', 'CC-BY-NC-2.0', 'CC-BY-NC-2.5', 'CC-BY-NC-3.0', 'CC-BY-NC-4.0', 'CC-BY-NC-ND-1.0', 'CC-BY-NC-ND-2.0', 'CC-BY-NC-ND-2.5', 'CC-BY-NC-ND-3.0',
                           'CC-BY-NC-ND-3.0-IGO', 'CC-BY-NC-ND-4.0', 'CC-BY-NC-SA-1.0', 'CC-BY-NC-SA-2.0', 'CC-BY-NC-SA-2.5', 'CC-BY-NC-SA-3.0', 'CC-BY-NC-SA-4.0', 'CC-BY-ND-1.0', 'CC-BY-ND-2.0',
                           'CC-BY-ND-2.5', 'CC-BY-ND-3.0', 'CC-BY-ND-4.0', 'CC-BY-SA-1.0', 'CC-BY-SA-2.0', 'CC-BY-SA-2.5', 'CC-BY-SA-3.0', 'CC-BY-SA-3.0-AT', 'CC-BY-SA-4.0', 'CC-PDDC', 'CC0-1.0',
                           'CDDL-1.0', 'CDDL-1.1', 'CDLA-Permissive-1.0', 'CDLA-Sharing-1.0', 'CECILL-1.0', 'CECILL-1.1', 'CECILL-2.0', 'CECILL-2.1', 'CECILL-B', 'CECILL-C', 'CERN-OHL-1.1',
                           'CERN-OHL-1.2', 'CERN-OHL-P-2.0', 'CERN-OHL-S-2.0', 'CERN-OHL-W-2.0', 'ClArtistic', 'CNRI-Jython', 'CNRI-Python', 'CNRI-Python-GPL-Compatible', 'Condor-1.1',
                           'copyleft-next-0.3.0', 'copyleft-next-0.3.1', 'CPAL-1.0', 'CPL-1.0', 'CPOL-1.02', 'Crossword', 'CrystalStacker', 'CUA-OPL-1.0', 'Cube', 'curl', 'D-FSL-1.0', 'diffmark',
                           'DOC', 'Dotseqn', 'DSDP', 'dvipdfm', 'ECL-1.0', 'ECL-2.0', 'EFL-1.0', 'EFL-2.0', 'eGenix', 'Entessa', 'EPICS', 'EPL-1.0', 'EPL-2.0', 'ErlPL-1.1', 'etalab-2.0',
                           'EUDatagrid', 'EUPL-1.0', 'EUPL-1.1', 'EUPL-1.2', 'Eurosym', 'Fair', 'Frameworx-1.0', 'FreeImage', 'FSFAP', 'FSFUL', 'FSFULLR', 'FTL', 'GFDL-1.1-invariants-only',
                           'GFDL-1.1-invariants-or-later', 'GFDL-1.1-no-invariants-only', 'GFDL-1.1-no-invariants-or-later', 'GFDL-1.1-only', 'GFDL-1.1-or-later', 'GFDL-1.2-invariants-only',
                           'GFDL-1.2-invariants-or-later', 'GFDL-1.2-no-invariants-only', 'GFDL-1.2-no-invariants-or-later', 'GFDL-1.2-only', 'GFDL-1.2-or-later', 'GFDL-1.3-invariants-only',
                           'GFDL-1.3-invariants-or-later', 'GFDL-1.3-no-invariants-only', 'GFDL-1.3-no-invariants-or-later', 'GFDL-1.3-only', 'GFDL-1.3-or-later', 'Giftware', 'GL2PS', 'Glide',
                           'Glulxe', 'GLWTPL', 'gnuplot', 'GPL-1.0-only', 'GPL-1.0-or-later', 'GPL-2.0-only', 'GPL-2.0-or-later', 'GPL-3.0-only', 'GPL-3.0-or-later', 'gSOAP-1.3b', 'HaskellReport',
                           'Hippocratic-2.1', 'HPND', 'HPND-sell-variant', 'IBM-pibs', 'ICU', 'IJG', 'ImageMagick', 'iMatix', 'Imlib2', 'Info-ZIP', 'Intel', 'Intel-ACPI', 'Interbase-1.0', 'IPA',
                           'IPL-1.0', 'ISC', 'JasPer-2.0', 'JPNIC', 'JSON', 'LAL-1.2', 'LAL-1.3', 'Latex2e', 'Leptonica', 'LGPL-2.0-only', 'LGPL-2.0-or-later', 'LGPL-2.1-only', 'LGPL-2.1-or-later',
                           'LGPL-3.0-only', 'LGPL-3.0-or-later', 'LGPLLR', 'Libpng', 'libpng-2.0', 'libselinux-1.0', 'libtiff', 'LiLiQ-P-1.1', 'LiLiQ-R-1.1', 'LiLiQ-Rplus-1.1', 'Linux-OpenIB',
                           'LPL-1.0', 'LPL-1.02', 'LPPL-1.0', 'LPPL-1.1', 'LPPL-1.2', 'LPPL-1.3a', 'LPPL-1.3c', 'MakeIndex', 'MirOS', 'MIT', 'MIT-0', 'MIT-advertising', 'MIT-CMU', 'MIT-enna',
                           'MIT-feh', 'MITNFA', 'Motosoto', 'mpich2', 'MPL-1.0', 'MPL-1.1', 'MPL-2.0', 'MPL-2.0-no-copyleft-exception', 'MS-PL', 'MS-RL', 'MTLL', 'MulanPSL-1.0', 'MulanPSL-2.0',
                           'Multics', 'Mup', 'NASA-1.3', 'Naumen', 'NBPL-1.0', 'NCGL-UK-2.0', 'NCSA', 'Net-SNMP', 'NetCDF', 'Newsletr', 'NGPL', 'NIST-PD', 'NIST-PD-fallback', 'NLOD-1.0', 'NLPL',
                           'Nokia', 'NOSL', 'Noweb', 'NPL-1.0', 'NPL-1.1', 'NPOSL-3.0', 'NRL', 'NTP', 'NTP-0', 'O-UDA-1.0', 'OCCT-PL', 'OCLC-2.0', 'ODbL-1.0', 'ODC-By-1.0', 'OFL-1.0',
                           'OFL-1.0-no-RFN', 'OFL-1.0-RFN', 'OFL-1.1', 'OFL-1.1-no-RFN', 'OFL-1.1-RFN', 'OGC-1.0', 'OGL-Canada-2.0', 'OGL-UK-1.0', 'OGL-UK-2.0', 'OGL-UK-3.0', 'OGTSL', 'OLDAP-1.1',
                           'OLDAP-1.2', 'OLDAP-1.3', 'OLDAP-1.4', 'OLDAP-2.0', 'OLDAP-2.0.1', 'OLDAP-2.1', 'OLDAP-2.2', 'OLDAP-2.2.1', 'OLDAP-2.2.2', 'OLDAP-2.3', 'OLDAP-2.4', 'OLDAP-2.5',
                           'OLDAP-2.6', 'OLDAP-2.7', 'OLDAP-2.8', 'OML', 'OpenSSL', 'OPL-1.0', 'OSET-PL-2.1', 'OSL-1.0', 'OSL-1.1', 'OSL-2.0', 'OSL-2.1', 'OSL-3.0', 'Parity-6.0.0', 'Parity-7.0.0',
                           'PDDL-1.0', 'PHP-3.0', 'PHP-3.01', 'Plexus', 'PolyForm-Noncommercial-1.0.0', 'PolyForm-Small-Business-1.0.0', 'PostgreSQL', 'PSF-2.0', 'psfrag', 'psutils', 'Python-2.0',
                           'Qhull', 'QPL-1.0', 'Rdisc', 'RHeCos-1.1', 'RPL-1.1', 'RPL-1.5', 'RPSL-1.0', 'RSA-MD', 'RSCPL', 'Ruby', 'SAX-PD', 'Saxpath', 'SCEA', 'Sendmail', 'Sendmail-8.23',
                           'SGI-B-1.0', 'SGI-B-1.1', 'SGI-B-2.0', 'SHL-0.5', 'SHL-0.51', 'SimPL-2.0', 'SISSL', 'SISSL-1.2', 'Sleepycat', 'SMLNJ', 'SMPPL', 'SNIA', 'Spencer-86', 'Spencer-94',
                           'Spencer-99', 'SPL-1.0', 'SSH-OpenSSH', 'SSH-short', 'SSPL-1.0', 'SugarCRM-1.1.3', 'SWL', 'TAPR-OHL-1.0', 'TCL', 'TCP-wrappers', 'TMate', 'TORQUE-1.1', 'TOSL',
                           'TU-Berlin-1.0', 'TU-Berlin-2.0', 'UCL-1.0', 'Unicode-DFS-2015', 'Unicode-DFS-2016', 'Unicode-TOU', 'Unlicense', 'UPL-1.0', 'Vim', 'VOSTROM', 'VSL-1.0', 'W3C',
                           'W3C-19980720', 'W3C-20150513', 'Watcom-1.0', 'Wsuipa', 'WTFPL', 'X11', 'Xerox', 'XFree86-1.1', 'xinetd', 'Xnet', 'xpp', 'XSkat', 'YPL-1.0', 'YPL-1.1', 'Zed', 'Zend-2.0',
                           'Zimbra-1.3', 'Zimbra-1.4', 'Zlib', 'zlib-acknowledgement', 'ZPL-1.1', 'ZPL-2.0', 'ZPL-2.1']

        def map_license_to_spdx(lic):
            """
            Map some commonly used license values to one of valid SPDX Identifiers.

            This is mapping only whatever value is listed in package.xml without any
            knowledge about the actual license used in the source files - it can map
            only the clear unambiguous cases (while triggering an warning) - the rest
            needs to be fixed in package.xml, so it will trigger an error

            This is similar to what e.g. Openembedded is doing in:
            http://git.openembedded.org/openembedded-core/tree/meta/conf/licenses.conf
            """
            return {
                'Apache License Version 2.0': 'Apache-2.0',
                'Apachi 2': 'Apache-2.0',
                'Apache License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0)': 'Apache-2.0',
                'Apache v2': 'Apache-2.0',
                'Apache v2.0': 'Apache-2.0',
                'Apache2.0': 'Apache-2.0',
                'APACHE2.0': 'Apache-2.0',
                'Apache2': 'Apache-2.0',
                'Apache License, Version 2.0': 'Apache-2.0',
                'Apache 2': 'Apache-2.0',
                'Apache 2.0': 'Apache-2.0',
                'Apache License 2.0': 'Apache-2.0',
                'LGPL v2': 'LGPL-2.0-only',
                'LGPL v2.1 or later': 'LGPL-2.1-or-later',
                'LGPL v2.1': 'LGPL-2.1-only',
                'LGPL-2.1': 'LGPL-2.1-only',
                'LGPLv2.1': 'LGPL-2.1-only',
                'GNU Lesser Public License 2.1': 'LGPL-2.1-only',
                'LGPL3': 'LGPL-3.0-only',
                'LGPLv3': 'LGPL-3.0-only',
                'GPL-2.0': 'GPL-2.0-only',
                'GPLv2': 'GPL-2.0-only',
                'GNU General Public License v2.0': 'GPL-2.0-only',
                'GNU GPL v3.0': 'GPL-3.0-only',
                'GPL v3': 'GPL-3.0-only',
                'GPLv3': 'GPL-3.0-only',
                'ECL2.0': 'EPL-2.0',
                'Eclipse Public License 2.0': 'EPL-2.0',
                'Mozilla Public License Version 1.1': 'MPL-1.1',
                'Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International Public License': 'CC-BY-NC-ND-4.0',
                'CreativeCommons-Attribution-NonCommercial-NoDerivatives-4.0': 'CC-BY-NC-ND-4.0',
                'CreativeCommons-Attribution-NonCommercial-ShareAlike-4.0-International': 'CC-BY-NC-SA-4.0',
                'CC BY-NC-SA 4.0': 'CC-BY-NC-SA-4.0',
                'CreativeCommons-by-nc-4.0': 'CC-BY-NC-4.0',
                'CreativeCommons-by-nc-sa-2.0': 'CC-BY-NC-SA-2.0',
                'Creative Commons BY-NC-ND 3.0': 'CC-BY-NC-ND-3.0',
                'BSD 3-clause Clear License': 'BSD-2-Clause',
                'BSD 3-clause. See license attached': 'BSD-2-Clause',
                'BSD 2-Clause License': 'BSD-2-Clause',
                'BSD2': 'BSD-2-Clause',
                'BSD-3': 'BSD-3-Clause',
                'BSD 3-Clause': 'BSD-3-Clause',
                'Boost Software License 1.0': 'BSL-1.0',
                'Boost': 'BSL-1.0',
                'Boost Software License, Version 1.0': 'BSL-1.0',
                'Boost Software License': 'BSL-1.0',
                'BSL1.0': 'BSL-1.0',
                'MIT License': 'MIT',
                'zlib License': 'Zlib',
                'zlib': 'Zlib'
            }.get(lic, None)

        def map_license_to_more_common_format(lic):
            """
            Map license value to more common format.

            These aren't SPDX Identifiers, but lets unify them at least.
            """
            return {
                "Check-author's-website": 'Check-authors-website',
                'proprietary': 'Proprietary',
                'Public Domain': 'PD',
                'Public domain': 'PD',
                'TODO': 'TODO-CATKIN-PACKAGE-LICENSE'
            }.get(lic, None)

        def validate_licenses(licenses, warnings):
            for lic in licenses:
                if is_valid_spdx_identifier(lic):
                    continue

                common = map_license_to_more_common_format(lic)
                if common:
                    lic = common
                    warnings.append('The license value "%s" is not valid SPDX identifier, and it is usually used as "%s"' % (lic, common))

                if license == 'TODO-CATKIN-PACKAGE-LICENSE':
                    warnings.append('The license value "%s" is only temporary from the template, replace it with correct value' % (lic))
                    continue

                spdx = map_license_to_spdx(lic)
                if not spdx:
                    warnings.append('The license value "%s" cannot be mapped to valid SPDX identifier' % (lic))
                elif spdx != lic:
                    # double check that what we mapped it to, is one of valid SPDX identifiers
                    if not is_valid_spdx_identifier(spdx):
                        warnings.append('The license value "%s" was mapped to "%s", but that is not listed as valid identifier' % (lic, spdx))
                    else:
                        warnings.append('The license value "%s" is not valid SPDX identifier, please use "%s" instead' % (lic, spdx))

        if self.package_format:
            if not re.match('^[1-9][0-9]*$', str(self.package_format)):
                errors.append('The "format" attribute of the package must contain a positive integer if present')

        if not self.name:
            errors.append('Package name must not be empty')
        # accepting upper case letters and hyphens only for backward compatibility
        if not re.match('^[a-zA-Z0-9][a-zA-Z0-9_-]*$', self.name):
            errors.append('Package name "%s" does not follow naming conventions' % self.name)
        else:
            if not re.match('^[a-z][a-z0-9_-]*$', self.name):
                new_warnings.append(
                    'Package name "%s" does not follow the naming conventions. It should start with '
                    'a lower case letter and only contain lower case letters, digits, underscores, and dashes.' % self.name)

        version_regexp = r'^[0-9]+\.[0-9]+\.[0-9]+$'
        if not self.version:
            errors.append('Package version must not be empty')
        elif not re.match(version_regexp, self.version):
            errors.append('Package version "%s" does not follow version conventions' % self.version)
        elif not re.match(r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$', self.version):
            new_warnings.append('Package "%s" does not follow the version conventions. It should not contain leading zeros (unless the number is 0).' % self.name)
        if self.version_compatibility:
            if not re.match(version_regexp, self.version_compatibility):
                errors.append(
                    "Package compatibility version '%s' does not follow "
                    'version conventions' % self.version_compatibility)

        if not self.description:
            errors.append('Package description must not be empty')

        if not self.maintainers:
            errors.append("Package '{0}' must declare at least one maintainer".format(self.name))
        for maintainer in self.maintainers:
            try:
                maintainer.validate()
            except InvalidPackage as e:
                errors.append(e.msg)
            if not maintainer.email:
                errors.append('Maintainers must have an email address')

        if not self.licenses:
            errors.append('The package node must contain at least one "license" tag')
        if [license_ for license_ in self.licenses if not license_.strip()]:
            errors.append('The license tag must neither be empty nor only contain whitespaces')

        validate_licenses(self.licenses, new_warnings)

        if self.authors is not None:
            for author in self.authors:
                try:
                    author.validate()
                except InvalidPackage as e:
                    errors.append(e.msg)

        dep_types = {
            'build': self.build_depends,
            'buildtool': self.buildtool_depends,
            'build_export': self.build_export_depends,
            'buildtool_export': self.buildtool_export_depends,
            'exec': self.exec_depends,
            'test': self.test_depends,
            'doc': self.doc_depends
        }
        for dep_type, depends in dep_types.items():
            for depend in depends:
                if depend.name == self.name:
                    errors.append('The package "%s" must not "%s_depend" on a package with the same name as this package' % (self.name, dep_type))

        if (
            set([d.name for d in self.group_depends]) &
            set([g.name for g in self.member_of_groups])
        ):
            errors.append(
                "The package must not 'group_depend' on a package which it "
                'also declares to be a member of')

        if self.is_metapackage():
            if not self.has_buildtool_depend_on_catkin():
                # TODO escalate to error in the future, or use metapackage.validate_metapackage
                new_warnings.append('Metapackage "%s" must buildtool_depend on catkin.' % self.name)
            if self.has_invalid_metapackage_dependencies():
                new_warnings.append('Metapackage "%s" should not have other dependencies besides a '
                                    'buildtool_depend on catkin and %s.' %
                                    (self.name, 'run_depends' if self.package_format == 1 else 'exec_depends'))

        for warning in new_warnings:
            if warnings is None:
                print('WARNING: ' + warning, file=sys.stderr)
            elif warning not in warnings:
                warnings.append(warning)

        if errors:
            raise InvalidPackage('\n'.join(errors), self.filename)


class Dependency(object):
    __slots__ = [
        'name',
        'version_lt', 'version_lte', 'version_eq', 'version_gte', 'version_gt',
        'condition',
        'evaluated_condition',
    ]

    def __init__(self, name, **kwargs):
        self.evaluated_condition = None
        for attr in self.__slots__:
            value = kwargs[attr] if attr in kwargs else None
            setattr(self, attr, value)
        self.name = name
        # verify that no unknown keywords are passed
        unknown = set(kwargs.keys()).difference(self.__slots__)
        if unknown:
            raise TypeError('Unknown properties: %s' % ', '.join(unknown))

    def __eq__(self, other):
        if not isinstance(other, Dependency):
            return False
        return all(getattr(self, attr) == getattr(other, attr) for attr in self.__slots__ if attr != 'evaluated_condition')

    def __hash__(self):
        return hash(tuple(getattr(self, slot) for slot in self.__slots__))

    def __str__(self):
        return self.name

    def __repr__(self):
        kv = []
        for slot in self.__slots__:
            attr = getattr(self, slot, None)
            if attr is not None:
                kv.append('{}={!r}'.format(slot, attr))
        return '{}({})'.format(self.__class__.__name__, ', '.join(kv))

    def evaluate_condition(self, context):
        """
        Evaluate the condition.

        The result is also stored in the member variable `evaluated_condition`.

        :param context: A dictionary with key value pairs to replace variables
          starting with $ in the condition.

        :returns: True if the condition evaluates to True, else False
        :raises: :exc:`ValueError` if the condition fails to parse
        """
        self.evaluated_condition = evaluate_condition(self.condition, context)
        return self.evaluated_condition


class Export(object):
    __slots__ = ['tagname', 'attributes', 'content', 'evaluated_condition']

    def __init__(self, tagname, content=None):
        self.tagname = tagname
        self.attributes = {}
        self.content = content
        self.evaluated_condition = None

    def __str__(self):
        txt = '<%s' % self.tagname
        for key in sorted(self.attributes.keys()):
            txt += ' %s="%s"' % (key, self.attributes[key])
        if self.content:
            txt += '>%s</%s>' % (self.content, self.tagname)
        else:
            txt += '/>'
        return txt

    def evaluate_condition(self, context):
        """
        Evaluate the condition.

        The result is also stored in the member variable `evaluated_condition`.

        :param context: A dictionary with key value pairs to replace variables
          starting with $ in the condition.

        :returns: True if the condition evaluates to True, else False
        :raises: :exc:`ValueError` if the condition fails to parse
        """
        self.evaluated_condition = evaluate_condition(self.attributes.get('condition'), context)
        return self.evaluated_condition


# Subclassing ``str`` to keep backward compatibility.
class License(str):

    def __new__(cls, value, file_=None):
        obj = str.__new__(cls, str(value))
        obj.file = file_
        return obj


class Person(object):
    __slots__ = ['name', 'email']

    def __init__(self, name, email=None):
        self.name = name
        self.email = email

    def __str__(self):
        name = self.name
        if not isinstance(name, str):
            name = name.encode('utf-8')
        if self.email is not None:
            return '%s <%s>' % (name, self.email)
        else:
            return '%s' % name

    def validate(self):
        if self.email is None:
            return
        if not re.match(r'^[-a-zA-Z0-9_%+]+(\.[-a-zA-Z0-9_%+]+)*@[-a-zA-Z0-9%]+(\.[-a-zA-Z0-9%]+)*\.[a-zA-Z]{2,}$', self.email):
            raise InvalidPackage('Invalid email "%s" for person "%s"' % (self.email, self.name))


class Url(object):
    __slots__ = ['url', 'type']

    def __init__(self, url, type_=None):
        self.url = url
        self.type = type_

    def __str__(self):
        return self.url


def parse_package_for_distutils(path=None):
    print('WARNING: %s/setup.py: catkin_pkg.package.parse_package_for_distutils() is deprecated. Please use catkin_pkg.python_setup.generate_distutils_setup(**kwargs) instead.' %
          os.path.basename(os.path.abspath('.')))
    from .python_setup import generate_distutils_setup
    data = {}
    if path is not None:
        data['package_xml_path'] = path
    return generate_distutils_setup(**data)


class InvalidPackage(Exception):

    def __init__(self, msg, package_path=None):
        self.msg = msg
        self.package_path = package_path
        Exception.__init__(self, self.msg)

    def __str__(self):
        result = '' if not self.package_path else "Error(s) in package '%s':\n" % self.package_path
        return result + Exception.__str__(self)


def package_exists_at(path):
    """
    Check that a package exists at the given path.

    :param path: path to a package
    :type path: str
    :returns: True if package exists in given path, else False
    :rtype: bool
    """
    return os.path.isdir(path) and os.path.isfile(os.path.join(path, PACKAGE_MANIFEST_FILENAME))


def _get_package_xml(path):
    """
    Get xml of package manifest.

    :param path: The path of the package.xml file, it may or may not
        include the filename

    :returns: a tuple with the xml as well as the path of the read file
    :raises: :exc:`IOError`
    """
    if os.path.isfile(path):
        filename = path
    elif package_exists_at(path):
        filename = os.path.join(path, PACKAGE_MANIFEST_FILENAME)
        if not os.path.isfile(filename):
            raise IOError('Directory "%s" does not contain a "%s"' % (path, PACKAGE_MANIFEST_FILENAME))
    else:
        raise IOError('Path "%s" is neither a directory containing a "%s" file nor a file' % (path, PACKAGE_MANIFEST_FILENAME))

    # Force utf8 encoding for python3.
    # This way unicode files can still be processed on non-unicode locales.
    kwargs = {}
    if sys.version_info[0] >= 3:
        kwargs['encoding'] = 'utf8'

    with open(filename, 'r', **kwargs) as f:
        return f.read(), filename


def has_ros_schema_reference(path):
    """
    Check if the XML file contains a processing instruction referencing a ROS package manifest schema.

    :param path: The path of the package.xml file, it may or may not
        include the filename
    :type path: str
    :returns: True if it contains the known reference, else False
    :rtype: bool
    :raises: :exc:`IOError`
    """
    xml, _ = _get_package_xml(path)
    return has_ros_schema_reference_string(xml)


def has_ros_schema_reference_string(data):
    """
    Check if the XML data contains a processing instruction referencing a ROS package manifest schema.

    :param data: package.xml contents
    :type data: str
    :returns: True if it contains the known reference, else False
    :rtype: bool
    """
    if sys.version_info[0] == 2 and not isinstance(data, str):
        data = data.encode('utf-8')
    try:
        root = dom.parseString(data)
    except Exception:
        # invalid XML
        return False

    for child in root.childNodes:
        if child.nodeType == child.PROCESSING_INSTRUCTION_NODE:
            if child.target == 'xml-model':
                # extract schema url from "xml-model" processing instruction
                schema_url = re.search(r'href="([A-Za-z0-9\._/:]*)"', child.data).group(1)
                if schema_url in PACKAGE_MANIFEST_SCHEMA_URLS:
                    return True

    return False


def parse_package(path, warnings=None):
    """
    Parse package manifest.

    :param path: The path of the package.xml file, it may or may not
        include the filename
    :param warnings: Print warnings if None or return them in the given list

    :returns: return :class:`Package` instance, populated with parsed fields
    :raises: :exc:`InvalidPackage`
    :raises: :exc:`IOError`
    """
    xml, filename = _get_package_xml(path)
    return parse_package_string(xml, filename, warnings=warnings)


def _check_known_attributes(node, known):
    if node.hasAttributes():
        attrs = map(str, node.attributes.keys())
        # colon is the namespace separator in attributes, xmlns can be added to any tag
        unknown_attrs = [attr for attr in attrs if not (attr in known or attr == 'xmlns' or ':' in attr)]
        if unknown_attrs:
            return ['The "%s" tag must not have the following attributes: %s' % (node.tagName, ', '.join(unknown_attrs))]
    return []


def parse_package_string(data, filename=None, warnings=None):
    """
    Parse package.xml string contents.

    :param data: package.xml contents, ``str``
    :param filename: full file path for debugging, ``str``
    :param warnings: Print warnings if None or return them in the given list
    :returns: return parsed :class:`Package`
    :raises: :exc:`InvalidPackage`
    """
    if sys.version_info[0] == 2 and not isinstance(data, str):
        data = data.encode('utf-8')
    try:
        root = dom.parseString(data)
    except Exception as ex:
        raise InvalidPackage('The manifest contains invalid XML:\n%s' % ex, filename)

    pkg = Package(filename)

    # verify unique root node
    nodes = _get_nodes(root, 'package')
    if len(nodes) != 1:
        raise InvalidPackage('The manifest must contain a single "package" root tag', filename)
    root = nodes[0]

    # format attribute
    value = _get_node_attr(root, 'format', default=1)
    pkg.package_format = int(value)
    assert pkg.package_format in (1, 2, 3), \
        "Unable to handle package.xml format version '%d', please update catkin_pkg " \
        '(e.g. on Ubuntu/Debian use: sudo apt-get update && sudo apt-get install --only-upgrade python-catkin-pkg)' % pkg.package_format

    # name
    pkg.name = _get_node_value(_get_node(root, 'name', filename))

    # version and optional compatibility
    version_node = _get_node(root, 'version', filename)
    pkg.version = _get_node_value(version_node)
    pkg.version_compatibility = _get_node_attr(
        version_node, 'compatibility', default=None)

    # description
    pkg.description = _get_node_value(_get_node(root, 'description', filename), allow_xml=True, apply_str=False)

    # at least one maintainer, all must have email
    maintainers = _get_nodes(root, 'maintainer')
    for node in maintainers:
        pkg.maintainers.append(Person(
            _get_node_value(node, apply_str=False),
            _get_node_attr(node, 'email')
        ))

    # urls with optional type
    urls = _get_nodes(root, 'url')
    for node in urls:
        pkg.urls.append(Url(
            _get_node_value(node),
            _get_node_attr(node, 'type', default='website')
        ))

    # authors with optional email
    authors = _get_nodes(root, 'author')
    for node in authors:
        pkg.authors.append(Person(
            _get_node_value(node, apply_str=False),
            _get_node_attr(node, 'email', default=None)
        ))

    # at least one license
    licenses = _get_nodes(root, 'license')
    for node in licenses:
        pkg.licenses.append(License(
            _get_node_value(node),
            _get_node_attr(node, 'file', default=None)
        ))

    errors = []
    # dependencies and relationships
    pkg.build_depends = _get_dependencies(root, 'build_depend')
    pkg.buildtool_depends = _get_dependencies(root, 'buildtool_depend')
    if pkg.package_format == 1:
        run_depends = _get_dependencies(root, 'run_depend')
        for d in run_depends:
            pkg.build_export_depends.append(deepcopy(d))
            pkg.exec_depends.append(deepcopy(d))
    if pkg.package_format != 1:
        pkg.build_export_depends = _get_dependencies(root, 'build_export_depend')
        pkg.buildtool_export_depends = _get_dependencies(root, 'buildtool_export_depend')
        pkg.exec_depends = _get_dependencies(root, 'exec_depend')
        depends = _get_dependencies(root, 'depend')
        for dep in depends:
            # check for collisions with specific dependencies
            same_build_depends = ['build_depend' for d in pkg.build_depends if d == dep]
            same_build_export_depends = ['build_export_depend' for d in pkg.build_export_depends if d == dep]
            same_exec_depends = ['exec_depend' for d in pkg.exec_depends if d == dep]
            if same_build_depends or same_build_export_depends or same_exec_depends:
                errors.append("The generic dependency on '%s' is redundant with: %s" % (dep.name, ', '.join(same_build_depends + same_build_export_depends + same_exec_depends)))
            # only append non-duplicates
            if not same_build_depends:
                pkg.build_depends.append(deepcopy(dep))
            if not same_build_export_depends:
                pkg.build_export_depends.append(deepcopy(dep))
            if not same_exec_depends:
                pkg.exec_depends.append(deepcopy(dep))
        pkg.doc_depends = _get_dependencies(root, 'doc_depend')
    pkg.test_depends = _get_dependencies(root, 'test_depend')
    pkg.conflicts = _get_dependencies(root, 'conflict')
    pkg.replaces = _get_dependencies(root, 'replace')

    # group dependencies and memberships
    pkg.group_depends = _get_group_dependencies(root, 'group_depend')
    pkg.member_of_groups = _get_group_memberships(root, 'member_of_group')

    if pkg.package_format == 1:
        for test_depend in pkg.test_depends:
            same_build_depends = ['build_depend' for d in pkg.build_depends if d == test_depend]
            same_run_depends = ['run_depend' for d in pkg.run_depends if d == test_depend]
            if same_build_depends or same_run_depends:
                errors.append('The test dependency on "%s" is redundant with: %s' % (test_depend.name, ', '.join(same_build_depends + same_run_depends)))

    # exports
    export_node = _get_optional_node(root, 'export', filename)
    if export_node is not None:
        exports = []
        for node in [n for n in export_node.childNodes if n.nodeType == n.ELEMENT_NODE]:
            export = Export(str(node.tagName), _get_node_value(node, allow_xml=True))
            for key, value in node.attributes.items():
                export.attributes[str(key)] = str(value)
            exports.append(export)
        pkg.exports = exports

    # verify that no unsupported tags and attributes are present
    errors += _check_known_attributes(root, ['format'])
    depend_attributes = ['version_lt', 'version_lte', 'version_eq', 'version_gte', 'version_gt']
    if pkg.package_format > 2:
        depend_attributes.append('condition')
    known = {
        'name': [],
        'version': ['compatibility'],
        'description': [],
        'maintainer': ['email'],
        'license': [],
        'url': ['type'],
        'author': ['email'],
        'build_depend': depend_attributes,
        'buildtool_depend': depend_attributes,
        'test_depend': depend_attributes,
        'conflict': depend_attributes,
        'replace': depend_attributes,
        'export': [],
    }
    if pkg.package_format == 1:
        known.update({
            'run_depend': depend_attributes,
        })
    if pkg.package_format != 1:
        known.update({
            'build_export_depend': depend_attributes,
            'buildtool_export_depend': depend_attributes,
            'depend': depend_attributes,
            'exec_depend': depend_attributes,
            'doc_depend': depend_attributes,
        })
    if pkg.package_format > 2:
        known.update({
            'group_depend': ['condition'],
            'member_of_group': ['condition']
        })
    if pkg.package_format > 2:
        known.update({
            'license': ['file'],
        })
    nodes = [n for n in root.childNodes if n.nodeType == n.ELEMENT_NODE]
    unknown_tags = set([n.tagName for n in nodes if n.tagName not in known.keys()])
    if unknown_tags:
        errors.append('The manifest of package "%s" (with format version %d) must not contain the following tags: %s' % (pkg.name, pkg.package_format, ', '.join(unknown_tags)))
    if 'run_depend' in unknown_tags and pkg.package_format >= 2:
        errors.append('Please replace <run_depend> tags with <exec_depend> tags.')
    elif 'exec_depend' in unknown_tags and pkg.package_format < 2:
        errors.append('Either update to a newer format or replace <exec_depend> tags with <run_depend> tags.')
    for node in [n for n in nodes if n.tagName in known.keys()]:
        errors += _check_known_attributes(node, known[node.tagName])
        if node.tagName not in ['description', 'export']:
            subnodes = [n for n in node.childNodes if n.nodeType == n.ELEMENT_NODE]
            if subnodes:
                errors.append('The "%s" tag must not contain the following children: %s' % (node.tagName, ', '.join([n.tagName for n in subnodes])))

    if errors:
        raise InvalidPackage('Error(s):%s' % (''.join(['\n- %s' % e for e in errors])), filename)

    pkg.validate(warnings=warnings)

    return pkg


def _get_nodes(parent, tagname):
    return [n for n in parent.childNodes if n.nodeType == n.ELEMENT_NODE and n.tagName == tagname]


def _get_node(parent, tagname, filename):
    nodes = _get_nodes(parent, tagname)
    if len(nodes) != 1:
        raise InvalidPackage('The manifest must contain exactly one "%s" tag' % tagname, filename)
    return nodes[0]


def _get_optional_node(parent, tagname, filename):
    nodes = _get_nodes(parent, tagname)
    if len(nodes) > 1:
        raise InvalidPackage('The manifest must not contain more than one "%s" tags' % tagname, filename)
    return nodes[0] if nodes else None


def _get_node_value(node, allow_xml=False, apply_str=True):
    if allow_xml:
        value = (''.join([n.toxml() for n in node.childNodes])).strip(' \n\r\t')
    else:
        value = (''.join([n.data for n in node.childNodes if n.nodeType == n.TEXT_NODE])).strip(' \n\r\t')
    if apply_str:
        value = str(value)
    return value


def _get_node_attr(node, attr, default=False):
    """:param default: False means value is required."""
    if node.hasAttribute(attr):
        return str(node.getAttribute(attr))
    if default is False:
        raise InvalidPackage('The "%s" tag must have the attribute "%s"' % (node.tagName, attr))
    return default


def _get_dependencies(parent, tagname):
    depends = []
    for node in _get_nodes(parent, tagname):
        depend = Dependency(_get_node_value(node))
        for attr in ('version_lt', 'version_lte', 'version_eq', 'version_gte', 'version_gt', 'condition'):
            setattr(depend, attr, _get_node_attr(node, attr, None))
        depends.append(depend)
    return depends


def _get_group_dependencies(parent, tagname):
    from .group_dependency import GroupDependency
    depends = []
    for node in _get_nodes(parent, tagname):
        depends.append(
            GroupDependency(
                _get_node_value(node),
                condition=_get_node_attr(node, 'condition', default=None)))
    return depends


def _get_group_memberships(parent, tagname):
    from .group_membership import GroupMembership
    memberships = []
    for node in _get_nodes(parent, tagname):
        memberships.append(
            GroupMembership(
                _get_node_value(node),
                condition=_get_node_attr(node, 'condition', default=None)))
    return memberships
