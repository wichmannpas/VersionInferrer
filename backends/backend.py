from abc import abstractmethod, ABCMeta
from typing import Set

from backends.model import Model
from backends.software_package import SoftwarePackage
from backends.software_version import SoftwareVersion
from backends.static_file import StaticFile


class Backend(metaclass=ABCMeta):
    """A base class for database backends."""
    @abstractmethod
    def mark_indexed(self, software_version: SoftwareVersion, indexed: bool = True) -> bool:
        """Update a software version fully indexed flag."""

    @abstractmethod
    def retrieve_static_file_users_by_checksum(
            self, checksum: bytes) -> Set[SoftwareVersion]:
        """Retrieve all versions using a static file with a specific checksum."""

    @abstractmethod
    def retrieve_packages_by_name(
            self, name: str) -> Set[SoftwarePackage]:
        """Retrieve all available packages whose names are likely to name."""

    @abstractmethod
    def retrieve_versions(
            self, software_package: SoftwarePackage,
            indexed_only: bool = True) -> Set[SoftwareVersion]:
        """Retrieve all available versions for specified software package."""

    @abstractmethod
    def static_file_count(self, software_version: SoftwareVersion) -> int:
        """Get the count of static files used by a software version."""

    @abstractmethod
    def store(self, element: Model):
        """Insert or update an instance of a Model subclass."""


class BackendException(Exception):
    """An exception occuring in a backend."""
