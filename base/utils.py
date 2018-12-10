import os
from string import ascii_letters, digits
from urllib.parse import urljoin, urlparse
from typing import Iterable, Set

import msgpack
from url_normalize import url_normalize

from backends.software_version import SoftwareVersion

from settings import BACKEND


def join_paths(*args):
    """
    Join multiple paths using os.path.join, remove leading slashes
    before.
    """
    return os.path.join(args[0], *(
        arg[1:]
        if arg.startswith('/') else arg
        for arg in args[1:]))


def join_url(*args) -> str:
    """
    Join a base url and paths.
    """
    base_url = args[0]
    base_path = urlparse(base_url).path[1:]
    base_url = base_url.replace(base_path, '', 1)
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    path = ''
    if len(args) >= 2:
        join_args = args[1:]
        if base_path:
            join_args = (base_path,) + join_args
        path = join_paths(*join_args)

    return url_normalize(urljoin(base_url, path))


def normalize_data(data: object) -> bytes:
    """
    Normalize Python data into a bytes string.

    The purpose of the normalization is to transform data into
    its canonical form, thus making similar data which
    is supposed to be identical actually identical.
    """
    if isinstance(data, bytes):
        return data.strip()
    if isinstance(data, str):
        return data.strip().encode()
    if isinstance(data, dict):
        return msgpack.dumps(sorted([
            (normalize_data(key), normalize_data(value))
            for key, value in data.items()
        ]))
    if isinstance(data, (list, set, tuple)):
        return msgpack.dumps(sorted([
            normalize_data(item)
            for item in data
        ]))

    # use msgpack without further normalization. Might raise TypeError
    return msgpack.dumps(data)


def match_str_to_software_version(package_name: str, version_name: str) -> Set[SoftwareVersion]:
    """Match strings to all software versions matching that name."""
    matches = set()
    for package in BACKEND.retrieve_packages():
        if (package.name.lower() == package_name.lower() or
                any(name.lower() == package_name.lower()
                    for name in package.alternative_names)):
            for version in BACKEND.retrieve_versions(package):
                if version.name.lower() == version_name.lower():
                    matches.add(version)
    return matches


def most_recent_version(versions: Iterable[SoftwareVersion]) -> SoftwareVersion:
    """
    Get the most recent version (based on its release date) from an
    iterable of versions.
    """
    return max(versions, key=lambda v: v.release_date)


def clean_path_name(name: str) -> str:
    VALID_NAME_CHARS = ascii_letters + digits + '-_.()=[]{}\\'
    return ''.join(
        ch for ch in name.replace('/', '_')
        if ch in VALID_NAME_CHARS)
