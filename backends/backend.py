from abc import abstractmethod, ABCMeta
from typing import List

from backends.model import Model
from backends.software_package import SoftwarePackage
from backends.software_version import SoftwareVersion


class Backend(metaclass=ABCMeta):
    """A base class for database backends."""
    @abstractmethod
    def retrieve_versions(
            self, software_package: SoftwarePackage) -> List[SoftwareVersion]:
        """Retrieve all available versions for specified software package. """

    @abstractmethod
    def store(self, element: Model) -> bool:
        """
        Insert or update an instance of a Model subclass.

        Returns whether a change has been made.
        """


class BackendException(Exception):
    """An exception occuring in a backend."""
