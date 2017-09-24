import os

from abc import abstractmethod, ABCMeta
from subprocess import call, check_output
from typing import Callable, List, Set, Union

from backends.software_package import SoftwarePackage
from backends.software_version import SoftwareVersion


class Provider(metaclass=ABCMeta):
    """
    The abstract base class for any provider.
    
    A provider exposes functionality to retrieve code and versions.
    """
    def __init__(
            self, software_package: SoftwarePackage,
            version_name_derivator: Union[Callable[[str], str], None] = None):
        self.software_package = software_package
        self.cache_directory = software_package.cache_directory
        self.version_name_derivator = version_name_derivator

    @abstractmethod
    def checkout_version(self, version: SoftwareVersion):
        """Check out specified version into directory."""

    @abstractmethod
    def get_versions(self) -> Set[SoftwareVersion]:
        """Retrieve all available versions and return them as a set."""

    def _call_command(self, command: List[str]) -> int:
        """
        Run a command within the cache directory and return its return code.
        """
        cwd = None
        if os.path.isdir(self.cache_directory):
            cwd = self.cache_directory
        return call(command, cwd=cwd)

    def _check_command(self, command: List[str]) -> str:
        """
        Run a command within the cache directory and return its output as str.
        """
        cwd = None
        if os.path.isdir(self.cache_directory):
            cwd = self.cache_directory
        return check_output(
            command, cwd=cwd).decode()[:-1]

    def _get_software_version(
            self, internal_identifier: str) -> Union[SoftwareVersion, None]:
        """Get a SoftwareVersion object from an internal identifier."""
        name = internal_identifier
        print('foo')
        if self.version_name_derivator is not None:
            name = self.version_name_derivator(internal_identifier)
        print(name)
        return SoftwareVersion(
            software_package=self.software_package,
            name=name,
            internal_identifier=internal_identifier)
