from __future__ import print_function

from .packages import find_packages


class _PackageDecorator(object):

    def __init__(self, package):
        self.package = package
        self.is_metapackage = 'metapackage' in [e.tagname for e in self.package.exports]
        message_generators = [e.content for e in self.package.exports if e.tagname == 'message_generator']
        self.message_generator = message_generators[0] if message_generators else None
        # full includes direct build depends and recursive run_depends of these build_depends
        self.full_depends = None

    def __getattr__(self, name):
        return getattr(self.package, name)

    def calculate_full_depends(self, packages):
        self.full_depends = set([])
        package_names = packages.keys()
        for name in [d.name for d in self.build_depends if d.name in package_names]:
            self.full_depends.add(name)
            packages[name]._add_recursive_run_depends(packages, self.full_depends)

    def _add_recursive_run_depends(self, packages, full_depends):
        package_names = packages.keys()
        for name in [d.name for d in self.run_depends if d.name in package_names and d.name not in full_depends]:
            full_depends.add(name)
            packages[name]._add_recursive_run_depends(packages, full_depends)


def topological_order(root_dir, whitelisted=None, blacklisted=None):
    packages = find_packages(root_dir)
    decorators = {}
    for name, package in packages.items():
        decorators[name] = _PackageDecorator(package)
    decorators = topological_order_packages(decorators, whitelisted, blacklisted)
    packages = []
    for name, decorator in decorators:
        packages.append([name, decorator.package])
    return packages


def topological_order_packages(packages, whitelisted=None, blacklisted=None):
    selected = {}
    for path, package in packages.items():
        # skip non-whitelisted packages
        if whitelisted and package.name not in whitelisted:
            continue
        # skip blacklisted packages
        if blacklisted and package.name in blacklisted:
            continue
        packages_with_same_name = {k: v for k, v in selected.items() if v.name == package.name}
        if packages_with_same_name:
            raise RuntimeError('Two packages with the same name "%s" in the workspace:\n- %s\n- %s' % (package.name, selected[path].path, package.path))
        selected[path] = package

    # calculate transitive dependencies
    for package in selected.values():
        package.calculate_full_depends(selected)

    return _sort_packages(selected)


def _sort_packages(packages):
    '''
    First returning packages which have message generators and then the rest based on direct build_depends and indirect recursive run_depends.
    '''

    ordered_packages = []
    while len(packages) > 0:
        # find all packages without build dependencies
        message_generators = []
        non_message_generators = []
        for name, data in packages.items():
            if not data.full_depends:
                if data.message_generator:
                    message_generators.append(name)
                else:
                    non_message_generators.append(name)
        # first choose message generators
        if message_generators:
            names = message_generators
        elif non_message_generators:
            names = non_message_generators
        else:
            # in case of a circular dependency pass the list of remaining packages
            ordered_packages.append([None, ', '.join(sorted(packages.keys()))])
            break

        # alphabetic order only for convenience
        names.sort()

        # add first candidates to ordered list
        # do not add all candidates since removing the depends from the first might affect the next candidates
        name = names[0]
        ordered_packages.append([name, packages[name]])
        # remove package from further processing
        del packages[name]
        for package in packages.values():
            if name in package.full_depends:
                package.full_depends.remove(name)
    return ordered_packages


def get_message_generators(ordered_packages):
    return [name for (name, data) in ordered_packages if hasattr(data, 'message_generator') and data.message_generator]
