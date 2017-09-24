import os

from hashlib import blake2b
from typing import List

from backends.software_version import SoftwareVersion
from backends.static_file import StaticFile
from definitions.definition import SoftwareDefinition
from settings import STATIC_FILE_EXTENSIONS


BUFFER_SIZE = 8000000


def collect_static_files(
        definition: SoftwareDefinition, version: SoftwareVersion) -> List[StaticFile]:
    """Index a missing version."""
    definition.provider.checkout_version(version)

    # Generate list of static files
    static_files = []
    for webroot_path, src_path in definition.path_map.items():
        static_files.extend(
            list_static_files(
                version,
                definition.provider.cache_directory,
                webroot_path,
                src_path))
    return [
        static_file
        for static_file in static_files
        if (definition.ignore_paths is None or
            not definition.ignore_paths.match(static_file.src_path))
    ]


def list_static_files(
        software_version: SoftwareVersion, base_dir: str, webroot_path: str,
        src_path: str) -> List[str]:
    """Generate a list of all static files within path."""
    return [
        StaticFile(
            software_version=software_version,
            src_path=_join_paths(
                directory.replace(base_dir, '', 1),
                file_name),
            webroot_path=_join_paths(
                webroot_path,
                directory.replace(_join_paths(base_dir, src_path), '', 1),
                file_name),
            checksum=_calculate_checksum(
                os.path.join(base_dir, directory, file_name)))
        for directory, dirnames, file_names in os.walk(
            _join_paths(base_dir, src_path))
        for file_name in file_names
        if any(
            file_name.lower().endswith(file_extension)
            for file_extension in STATIC_FILE_EXTENSIONS)
    ]


def _calculate_checksum(file_path: str) -> bytes:
    """Calculate a checksum for a file."""
    hasher = blake2b()
    with open(file_path, 'rb') as fh:
        while True:
            buf = fh.read(BUFFER_SIZE)
            if not buf:
                break
            hasher.update(buf)

    return hasher.digest()[:16]


def _join_paths(*args):
    """
    Join multiple paths using os.path.join, remove leading slashes
    before.
    """
    return os.path.join(args[0], *(
        arg[1:]
        if arg.startswith('/') else arg
        for arg in args[1:]))
