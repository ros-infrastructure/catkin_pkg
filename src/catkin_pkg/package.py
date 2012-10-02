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

"""
Library for parsing package.xml and providing an object
representation.
"""

import os
import re
import xml.dom.minidom as dom


class Package(object):
    """
    Object representation of a ``package.xml`` file
    """
    __slots__ = [
        'package_format',
        'name',
        'version',
        'version_abi',
        'description',
        'maintainers',
        'licenses',
        'urls',
        'authors',
        'build_depends',
        'buildtool_depends',
        'run_depends',
        'test_depends',
        'conflicts',
        'replaces',
        'exports',
        'filename'
    ]

    def __init__(self, filename=None, **kwargs):
        """
        :param filename: location of package.xml.  Necessary if
          converting ``${prefix}`` in ``<export>`` values, ``str``.
        """
        # first make sure all multiple slots have empty list as value
        for attr in self.__slots__:
            if attr.endswith('s'):
                setattr(self, attr, [])
            else:
                setattr(self, attr, None)
        self.filename = filename
        for key, value in kwargs.items():
            if key not in self.__slots__:
                raise TypeError('Unknown Property: %s' % key)
            if key.endswith('s'):
                setattr(self, key, list(value))
            else:
                setattr(self, key, value)

    def __getitem__(self, key):
        if key in self.__slots__:
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

    def validate(self):
        """
        makes sure all standards for packages are met
        :param package: Package to check
        :raises InvalidPackage: in case validation fails
        """
        if not self.name:
            raise InvalidPackage('Package name must not be empty')
        if not re.match('^[a-zA-Z0-9][a-zA-Z0-9_]*$', self.name):
            raise InvalidPackage('Package name %s does not follow naming conventions' %
                             self.name)
        # if not re.match('^[a-z][a-z0-9_]*$', self.name):
        #     sys.stderr.write('WARNING: Package names should be lowercase and start with a letter: %s' % self.name)

        if self.package_format:
            if not re.match('^[0-9]+$', str(self.package_format)):
                raise InvalidPackage('The "format" attribute of the package must contain a positive integer if present')

        if not self.version:
            raise InvalidPackage('Package version must not be empty')
        if not re.match('^[0-9]+\.[0-9_]+\.[0-9_]+$', self.version):
            raise InvalidPackage('Package version %s does not follow version conventions' % self.version)

        if not self.maintainers:
            raise InvalidPackage('Package must declare at least one maintainer')
        for maintainer in self.maintainers:
            maintainer.validate()
            if not maintainer.email:
                raise InvalidPackage('Maintainer must have an email address')

        if not self.licenses:
            raise InvalidPackage('The manifest must contain at least one "license" tag')
        if self.authors is not None:
            for author in self.authors:
                author.validate()

        for dep_type in [self.build_depends,
                         self.buildtool_depends,
                         self.run_depends,
                         self.test_depends,
                         self.conflicts,
                         self.replaces]:
            for depend in dep_type:
                if depend.name == self.name:
                    raise InvalidPackage('The manifest must not depend on a package with the same name as this package')

class Dependency(object):
    __slots__ = ['name', 'version_lt', 'version_lte', 'version_eq', 'version_gte', 'version_gt']

    def __init__(self, name, **kwargs):
        for attr in self.__slots__:
            setattr(self, attr, None)
        self.name = name
        for key, value in kwargs.items():
            if key not in self.__slots__:
                raise TypeError('Unknown Property: %s' % key)
            setattr(self, key, value)

    def __str__(self):
        return self.name


class Export(object):
    __slots__ = ['tagname', 'attributes', 'content']

    def __init__(self, tagname, content=None):
        self.tagname = tagname
        self.attributes = {}
        self.content = content


class Person(object):
    __slots__ = ['name', 'email']

    def __init__(self, name, email=None):
        self.name = name
        self.email = email

    def __str__(self):
        return '%s <%s>' % (self.name, self.email) if self.email is not None else self.name

    def validate(self):
        print(self.email)
        if self.email is None:
            return
        if not re.match('^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+\.[a-zA-Z]{2,6}$',
                        self.email):
            raise InvalidPackage('Invalid email %s %s' %
                                 (self.email, self.name))


class Url(object):
    __slots__ = ['url', 'type']

    def __init__(self, url, type_=None):
        self.url = url
        self.type = type_

    def __str__(self):
        return self.url


def parse_package_for_distutils(path=None):
    """
    Extract the information relevant for distutils from the package
    manifest.  It sets the following keys: name, version, maintainer,
    long_description, license, keywords.

    The following keys depend on information which are
    optional: author, author_email, maintainer_email, url

    :param path: The path of the package.xml file, it may or may not
    include the filename

    :returns: return dict populated with parsed fields
    :raises: :exc:`InvalidPackage`
    :raises: :exc:`IOError`
    """
    if path is None:
        path = '.'
    package = parse_package(path)

    data = {}
    data['name'] = package.name
    data['version'] = package.version

    # either set one author with one email or join all in a single field
    if len(package.authors) == 1 and package.authors[0].email is not None:
        data['author'] = package.authors[0].name
        data['author_email'] = package.authors[0].email
    else:
        data['author'] = ', '.join([('%s <%s>' % (a.name, a.email) if a.email is not None else a.name) for a in package.authors])

    # either set one maintainer with one email or join all in a single field
    if len(package.maintainers) == 1:
        data['maintainer'] = package.maintainers[0].name
        data['maintainer_email'] = package.maintainers[0].email
    else:
        data['maintainer'] = ', '.join(['%s <%s>' % (m.name, m.email) for m in package.maintainers])

    # either set the first URL with the type 'website' or the first URL of any type
    websites = [url.url for url in package.urls if url.type == 'website']
    if websites:
        data['url'] = websites[0]
    elif package.urls:
        data['url'] = package.urls[0].url

    if len(package.description) <= 200:
        data['description'] = package.description
    else:
        data['description'] = package.description[:200]
        data['long_description'] = package.description

    #data['classifiers'] = ['Programming Language :: Python']

    data['license'] = ', '.join(package.licenses)
    data['keywords'] = ['ROS']
    return data


class InvalidPackage(Exception):
    pass


def parse_package(path):
    """
    Parse package manifest.

    :param path: The path of the package.xml file, it may or may not
    include the filename

    :returns: return :class:`Package` instance, populated with parsed fields
    :raises: :exc:`InvalidPackage`
    :raises: :exc:`IOError`
    """
    if os.path.isfile(path):
        filename = path
    elif os.path.isdir(path):
        filename = os.path.join(path, 'package.xml')
        if not os.path.isfile(filename):
            raise IOError('Directory "%s" does not contain a "package.xml"' % (path))
    else:
        raise IOError('Path "%s" is neither a directory containing a "package.xml" file nor a file' % (path))

    with open(filename, 'r') as f:
        try:
            return parse_package_string(f.read(), filename)
        except InvalidPackage as e:
            e.args = ['Invalid package manifest "%s": %s' % (filename, e.message)]
            raise


def parse_package_string(data, filename=None):
    """
    Parse package.xml string contents.

    :param data: package.xml contents, ``str``
    :param filename: full file path for debugging, ``str``
    :returns: return parsed :class:`Package`
    :raises: :exc:`InvalidPackage`
    """
    try:
        d = dom.parseString(data)
    except Exception as e:
        raise InvalidPackage('The manifest contains invalid XML:\n%s' % e)

    pkg = Package(filename)

    # verify unique root node
    nodes = _get_nodes(d, 'package')
    if len(nodes) != 1:
        raise InvalidPackage('The manifest must contain a single "package" root tag')
    root = nodes[0]

    # format attribute
    value = _get_node_attr(root, 'format', default=1)
    pkg.package_format = int(value)

    # name
    pkg.name = _get_node_value(_get_node(root, 'name'))

    # version and optional abi
    version_node = _get_node(root, 'version')
    pkg.version = _get_node_value(version_node)
    pkg.version_abi = _get_node_attr(version_node, 'abi', default=None)

    # description
    pkg.description = _get_node_value(_get_node(root, 'description'), allow_xml=True)

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
        pkg.licenses.append(_get_node_value(node))

    # dependencies and relationships
    pkg.build_depends = _get_dependencies(root, 'build_depend')
    pkg.buildtool_depends = _get_dependencies(root, 'buildtool_depend')
    pkg.run_depends = _get_dependencies(root, 'run_depend')
    pkg.test_depends = _get_dependencies(root, 'test_depend')
    pkg.conflicts = _get_dependencies(root, 'conflict')
    pkg.replaces = _get_dependencies(root, 'replace')

    # exports
    export_node = _get_optional_node(root, 'export')
    if export_node is not None:
        exports = []
        for node in [n for n in export_node.childNodes if n.nodeType == n.ELEMENT_NODE]:
            export = Export(str(node.tagName), _get_node_value(node, allow_xml=True))
            for key, value in node.attributes.items():
                export.attributes[str(key)] = str(value)
            exports.append(export)
        pkg.exports = exports
    pkg.validate()
    return pkg


def _get_nodes(parent, tagname):
    return [n for n in parent.childNodes if n.nodeType == n.ELEMENT_NODE and n.tagName == tagname]


def _get_node(parent, tagname):
    nodes = _get_nodes(parent, tagname)
    if len(nodes) != 1:
        raise InvalidPackage('The manifest must contain exactly one "%s" tags' % tagname)
    return nodes[0]


def _get_optional_node(parent, tagname):
    nodes = _get_nodes(parent, tagname)
    if len(nodes) > 1:
        raise InvalidPackage('The manifest must not contain more than one "%s" tags' % tagname)
    return nodes[0] if nodes else None


def _get_node_value(node, allow_xml=False, apply_str=True):
    if allow_xml:
        value = (''.join([n.toxml() for n in node.childNodes])).strip(' \n\r\t')
    else:
        value = (''.join([n.data for n in node.childNodes if n.nodeType == n.TEXT_NODE])).strip(' \n\r\t')
    if apply_str:
        value = str(value)
    return value


def _get_optional_node_value(parent, tagname, default=None):
    node = _get_optional_node(parent, tagname)
    if node is None:
        return default
    return _get_node_value(node)


def _get_node_attr(node, attr, default=False):
    """
    :param default: False means value required required
    """
    if node.hasAttribute(attr):
        return str(node.getAttribute(attr))
    if default is False:
        raise InvalidPackage('The "%s" tag must have the attribute "%s"' % (node.tagName, attr))
    return default


def _get_dependencies(parent, tagname):
    depends = []
    for node in _get_nodes(parent, tagname):
        depend = Dependency(_get_node_value(node))
        for attr in ['version_lt', 'version_lte', 'version_eq', 'version_gte', 'version_gt']:
            setattr(depend, attr, _get_node_attr(node, attr, None))
        depends.append(depend)
    return depends
