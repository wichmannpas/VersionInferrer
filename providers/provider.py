import os

from abc import abstractmethod, ABCMeta
from subprocess import call, check_output
from typing import List

from backend.software_package import SoftwarePackage
from backend.software_version import SoftwareVersion


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
