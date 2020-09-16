from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Callable, Set, Union

from backends.software_package import SoftwarePackage
from backends.software_version import SoftwareVersion


class Provider(metaclass=ABCMeta):
    """
    The abstract base class for any provider.

    A provider exposes functionality to retrieve code and versions.
    """
    cache_directory: str

    def __init__(
            self, software_package: SoftwarePackage,
            version_name_derivator: Union[Callable[[str], str], None] = None):
        self.software_package = software_package
        self.cache_directory = software_package.cache_directory
        self.version_name_derivator = version_name_derivator

    @abstractmethod
    def get_versions(self) -> Set[SoftwareVersion]:
        """Retrieve all available versions and return them as a set."""

    @abstractmethod
    def list_files(self, version: SoftwareVersion):
        """List all files available within version."""

    @abstractmethod
    def get_file_data(self, version: SoftwareVersion, path: str):
        """Get stream of file data at path as contained within version.."""

    def _get_software_version(
            self, internal_identifier: str, name: str,
            release_date: datetime) -> Union[SoftwareVersion, None]:
        """Get a SoftwareVersion object from an internal identifier."""
        if self.version_name_derivator is not None:
            name = self.version_name_derivator(internal_identifier)
        return SoftwareVersion(
            software_package=self.software_package,
            name=name,
            internal_identifier=internal_identifier,
            release_date=release_date)
