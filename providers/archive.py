import os
from typing import Callable, Set

from backends.software_package import SoftwarePackage
from backends.software_version import SoftwareVersion
from providers.provider import Provider


class GenericArchiveProvider(Provider):
    """
    This is a generic archive provider. It handles the management of
    archive files.

    As the archive files might be stored arbitrarily, a callable needs
    to be provided which returns a mapping of version identifiers
    to download urls.

    In addition, previously downloaded archives which are not provided
    by that callable anymore are still considered as valid versions.
    """
    def __init__(self, software_package: SoftwarePackage,
                 mapping: Callable[[], dict]):
        super().__init__(software_package)
        self.mapping = mapping
        self._archive_cache_directory = os.path.join(
            self.cache_directory, '.archives-cache')

    def get_versions(self) -> Set[SoftwareVersion]:
        """Retrieve all available versions and return them as a set."""
        return set(self.mapping().keys()) | self._get_cached_version_identifiers()

    def _get_cached_version_identifiers(self) -> Set[str]:
        if not os.path.isdir(self._archive_cache_directory):
            return set()
        return set(os.listdir(self._archive_cache_directory))
