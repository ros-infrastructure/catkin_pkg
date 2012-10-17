from .packages import find_packages


class _PackageDecorator(object):

    def __init__(self, package, path):
        self.package = package
        self.path = path
        self.is_metapackage = 'metapackage' in [e.tagname for e in self.package.exports]
        message_generators = [e.content for e in self.package.exports if e.tagname == 'message_generator']
        self.message_generator = message_generators[0] if message_generators else None
        # full includes direct build depends and recursive run_depends of these build_depends
        self.depends_for_topological_order = None

    def __getattr__(self, name):
        return getattr(self.package, name)

    def calculate_depends_for_topological_order(self, packages):
        """
        Sets self.depends_for_topological_order to the recursive
        dependencies required for topological order. It contains all
        direct build- and buildtool dependencies and their recursive
        runtime dependencies. The set only contains packages which
        are in the passed packages dictionary.

        :param packages: dict of name to ``_PackageDecorator``
        """
        self.depends_for_topological_order = set([])
        # skip external dependencies, meaning names that are not known packages
        for name in [d.name for d in (self.package.build_depends + self.package.buildtool_depends) if d.name in packages.keys()]:
            packages[name]._add_recursive_run_depends(packages, self.depends_for_topological_order)

    def _add_recursive_run_depends(self, packages, depends_for_topological_order):
        """
        Modifies depends_for_topological_order argument by adding
        run_depends of self recursively. Only packages which are in
        the passed packages are added and recursed into.

        :param packages: dict of name to ``_PackageDecorator``
        :param depends_for_topological_order: set to be extended
        """
        depends_for_topological_order.add(self.package.name)
        package_names = packages.keys()
        for name in [d.name for d in self.package.run_depends if d.name in package_names and d.name not in depends_for_topological_order]:
            packages[name]._add_recursive_run_depends(packages, depends_for_topological_order)


def topological_order(root_dir, whitelisted=None, blacklisted=None):
    '''
    Crawls the filesystem to find packages and uses their
    dependencies to return a topologically order list.

    :param root_dir: The path to search in, ``str``
    :param whitelisted: A list of whitelisted package names, ``list``
    :param blacklisted: A list of blacklisted package names, ``list``
    :returns: A list of tuples containining relative paths and ``Package`` objects ``dict``
    '''
    packages = find_packages(root_dir)
    return topological_order_packages(packages, whitelisted, blacklisted)


def topological_order_packages(packages, whitelisted=None, blacklisted=None):
    '''
    Topologically orders packages.
    First returning packages which have message generators and then
    the rest based on direct build-/buildtool_depends and indirect
    recursive run_depends.

    :param packages: A dict mapping relative paths to ``Package`` objects ``dict``
    :param whitelisted: A list of whitelisted package names, ``list``
    :param blacklisted: A list of blacklisted package names, ``list``
    :returns: A list of tuples containining the relative path and a ``Package`` object, ``list``
    '''
    decorators_by_name = {}
    for path, package in packages.items():
        # skip non-whitelisted packages
        if whitelisted and package.name not in whitelisted:
            continue
        # skip blacklisted packages
        if blacklisted and package.name in blacklisted:
            continue
        packages_with_same_name = [p for p in decorators_by_name.values() if p.name == package.name]
        if packages_with_same_name:
            path_with_same_name = [p for p, v in packages.items() if v == packages_with_same_name[0]]
            raise RuntimeError('Two packages with the same name "%s" in the workspace:\n- %s\n- %s' % (package.name, path_with_same_name[0], path))
        decorators_by_name[package.name] = _PackageDecorator(package, path)

    # calculate transitive dependencies
    for decorator in decorators_by_name.values():
        decorator.calculate_depends_for_topological_order(decorators_by_name)

    return _sort_decorated_packages(decorators_by_name)


def _sort_decorated_packages(packages):
    '''
    :param packages: A dict mapping package name to ``_PackageDecorator`` objects ``dict``
    :returns: A List of tuples containing the relative path and a ``Package`` object ``list``
    '''
    ordered_packages = []
    while len(packages) > 0:
        # find all packages without build dependencies
        message_generators = []
        non_message_generators = []
        for name, decorator in packages.items():
            if not decorator.depends_for_topological_order:
                if decorator.message_generator:
                    message_generators.append(name)
                else:
                    non_message_generators.append(name)
        # first choose message generators
        if message_generators:
            names = message_generators
        elif non_message_generators:
            names = non_message_generators
        else:
            # in case of a circular dependency pass the list of remaining package names
            ordered_packages.append([None, ', '.join(sorted(packages.keys()))])
            break

        # alphabetic order only for convenience
        names.sort()

        # add first candidates to ordered list
        # do not add all candidates since removing the depends from the first might affect the next candidates
        name = names[0]
        ordered_packages.append([packages[name].path, packages[name].package])
        # remove package from further processing
        del packages[name]
        for package in packages.values():
            if name in package.depends_for_topological_order:
                package.depends_for_topological_order.remove(name)
    return ordered_packages
