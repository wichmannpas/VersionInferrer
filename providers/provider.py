from abc import abstractmethod, ABCMeta
from typing import List

from software_package import SoftwarePackage, SoftwareVersion


class Provider(metaclass=ABCMeta):
    """
    The abstract base class for any provider.
    
    A provider exposes functionality to retrieve code and versions.
    """
    def __init__(self, software_package: SoftwarePackage):
        self.software_package = software_package
        self.cache_directory = software_package.cache_directory

    @abstractmethod
    def checkout_version(self, version: SoftwareVersion):
        """Check out specified version into directory."""

    @abstractmethod
    def get_versions(self) -> List[SoftwareVersion]:
        """Retrieve all available versions and return them as a list."""
