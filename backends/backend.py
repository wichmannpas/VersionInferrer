from abc import abstractmethod, ABCMeta
from typing import Set

from backends.model import Model
from backends.software_package import SoftwarePackage
from backends.software_version import SoftwareVersion


class Backend(metaclass=ABCMeta):
    """A base class for database backends."""
    @abstractmethod
    def mark_indexed(self, software_version: SoftwareVersion, indexed: bool = True) -> bool:
        """Update a software version fully indexed flag. """

    @abstractmethod
    def retrieve_versions(
            self, software_package: SoftwarePackage,
            indexed_only: bool = True) -> Set[SoftwareVersion]:
        """Retrieve all available versions for specified software package. """

    @abstractmethod
    def static_file_count(self, software_version: SoftwareVersion) -> int:
        """Get the count of static files used by a software version. """

    @abstractmethod
    def store(self, element: Model):
        """Insert or update an instance of a Model subclass. """


class BackendException(Exception):
    """An exception occuring in a backend."""
