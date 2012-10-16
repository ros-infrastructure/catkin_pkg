# Software License Agreement (BSD License)
#
# Copyright (c) 2008, Willow Garage, Inc.
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

from __future__ import print_function

import sys
import os
from string import Template

from catkin_pkg.package import Package


class PackageTemplate(Package):

    def __init__(self, components=None, **kwargs):
        super(PackageTemplate, self).__init__(**kwargs)
        self.components = components or []
        self.validate()


def create_files(newfiles, target_dir):
    """
    writes file contents to target_dir/filepath for all entries of newfiles.
    Aborts early if files exist in places for new files or directories

    :param newfiles: a dict {filepath: contents}
    :param target_dir: a string
    """
    # first check no filename conflict exists
    for filename in newfiles:
        target_file = os.path.join(target_dir, filename)
        if os.path.exists(target_file):
            raise ValueError('File exists: %s' % target_file)
        dirname = os.path.dirname(target_file)
        while(dirname != target_dir):
            if os.path.isfile(dirname):
                raise ValueError('Cannot create directory, file exists: %s' %
                                 dirname)
            dirname = os.path.dirname(dirname)

    for filename, content in newfiles.items():
        target_file = os.path.join(target_dir, filename)
        dirname = os.path.dirname(target_file)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        # print(target_file, content)
        with open(target_file, 'ab') as fhand:
            fhand.write(content)


def create_package_files(target_path, package_template, newfiles):
    """
    creates given newfiles and a package.xml from package template.

    :param target_path: parent folder where to create the package
    :param package_template: contains the required information
    :param newfiles: dict {filepath: file_contents_str}
    """
    newfiles[os.path.join(target_path, 'package.xml')] = create_package_xml(package_template)
    create_files(newfiles, target_path)


class CatkinTemplate(Template):
    """subclass to use @ instead of $ as markers"""
    delimiter = '@'
    escape = '@'


def _create_depend_tag(dep_type,
                      name,
                      version_eq=None,
                      version_lt=None,
                      version_lte=None,
                      version_gt=None,
                      version_gte=None):
    """
    Helper to create xml snippet for package.xml
    """

    version_string = []
    for key, var in {'version_eq': version_eq,
                     'version_lt': version_lt,
                     'version_lte': version_lte,
                     'version_gt': version_gt,
                     'version_gte': version_gte}.items():
        if var is not None:
            version_string.append(' %s="%s"' % (key, var))
    result = '  <%s%s>%s</%s>\n' % (dep_type,
                                  ''.join(version_string),
                                  name,
                                  dep_type)
    return result


def create_package_xml(package_template):
    """
    :param package_template: contains the required information
    :returns: file contents as string
    """
    with open(os.path.join(os.path.dirname(__file__), 'templates', 'package.xml.in'), 'r') as fhand:
        package_xml_template = fhand.read()
    ctemp = CatkinTemplate(package_xml_template)
    temp_dict = {}
    for key in package_template.__slots__:
        temp_dict[key] = getattr(package_template, key)

    if package_template.version_abi:
        temp_dict['version_abi'] = ' abi="%s"' % package_template.version_abi
    else:
        temp_dict['version_abi'] = ''

    if not package_template.description:
        temp_dict['description'] = 'The %s package ...' % package_template.name

    licenses = []
    for plicense in package_template.licenses:
        licenses.append('  <license>%s</license>\n' % plicense)
    temp_dict['licenses'] = ''.join(licenses)

    def get_person_tag(tagname, person):
        email_string = (""
                        if person.email is None
                        else 'email="%s"' % person.email)
        return '  <%s %s>%s</%s>\n' % (tagname, email_string, person.name, tagname)

    maintainers = []
    for maintainer in package_template.maintainers:
        maintainers.append(get_person_tag('maintainer', maintainer))
    temp_dict['maintainers'] = ''.join(maintainers)

    urls = []
    for url in package_template.urls:
        type_string = ("" if url.type is None
                       else 'type="%s"' % url.type)
        urls.append('    <url %s >%s</url>\n' % (type_string, url.url))
    temp_dict['urls'] = ''.join(urls)

    authors = []
    for author in package_template.authors:
        authors.append(get_person_tag('author', author))
    temp_dict['authors'] = ''.join(authors)

    dependencies = []
    for dep_type, dep_list in {'build_depend': package_template.build_depends,
                               'buildtool_depend': package_template.buildtool_depends,
                               'run_depend': package_template.run_depends,
                               'test_depend': package_template.test_depends,
                               'conflict': package_template.conflicts,
                               'replace': package_template.replaces}.items():
        for dep in dep_list:
            if 'depend' in dep_type:
                dependencies.append(_create_depend_tag(dep_type,
                                                       dep.name,
                                                       dep.version_eq,
                                                       dep.version_lt,
                                                       dep.version_lte,
                                                       dep.version_gt,
                                                       dep.version_gte))
            else:
                dependencies.append(_create_depend_tag(dep_type,
                                                       dep.name))
    temp_dict['dependencies'] = ''.join(dependencies)

    exports = []
    if package_template.exports is not None:
        for export in package_template.exports:
            if export.content is not None:
                sys.stderr.write('WARNING: Create package does not know how to serialize exports with content: %s, %s, %s' % (export.tagname, export.attributes, export.content))
            else:
                attribs = ['%s="%s"' % (k, v) for (k, v) in export.attributes]
                exports.append('    <%s%s/>\n' % (export.tagname, ''.join(attribs)))
    temp_dict['exports'] = ''.join(exports)

    temp_dict['components'] = package_template.components

    return ctemp.substitute(temp_dict)
