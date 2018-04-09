#!/usr/bin/env python3
from natsort import natsorted

from settings import BACKEND

packages = BACKEND.retrieve_packages()

for package in packages:
    print(package)

    versions = BACKEND.retrieve_versions(package)
    previous_version = None
    for version in natsorted(versions, key=lambda version: version.name):
        if previous_version is None:
            # nothing to compare to
            previous_version = version
            continue

        delta = BACKEND.version_delta(previous_version, version)
        print(' {:4d} changed static files from {} to {}'.format(
            len(delta),
            previous_version.name,
            version.name,
        ))

        previous_version = version
