#!/usr/bin/env python3
from argparse import ArgumentParser

from settings import BACKEND


def main():
    parser = ArgumentParser()
    parser.add_argument('package')
    parser.add_argument('versionA')
    parser.add_argument('versionB')
    arguments = parser.parse_args()

    packages = BACKEND.retrieve_packages_by_name(arguments.package)
    if len(packages) != 1:
        print(packages)
        print('Not exactly one match found')
        exit(1)
    package = packages.pop()
    versions = BACKEND.retrieve_versions(package, indexed_only=True)
    version_a = {version for version in versions if version.name == arguments.versionA}
    if len(version_a) != 1:
        print(version_a)
        print('Version A not found')
        exit(1)
    version_a = version_a.pop()
    version_b = {version for version in versions if version.name == arguments.versionB}
    if len(version_b) != 1:
        print(version_b)
        print('Version B not found')
        exit(1)
    version_b = version_b.pop()

    print(package, version_a, version_b)
    delta = BACKEND.version_delta(version_a, version_b)
    print('')
    for old, new in sorted(delta, key=lambda value: (1 if value[0] is None else 2 if value[1] is None else 0, value[0].src_path if value[0] is not None else None, value[1].src_path if value[1] is not None else None)):
        out = ''
        if old is None:
            out += '\033[1;34mnewly created: \033[0m'
        else:
            out += '{} \033[1;36m->\033[0m '.format(old.src_path)
        if new is None:
            out = '\033[1;31mdeleted: \033[0m' + out[:-15]
        else:
            out += new.src_path
        print(out)

    print('')
    print('{} differing static files in total'.format(len(delta)))


if __name__ == '__main__':
    main()
