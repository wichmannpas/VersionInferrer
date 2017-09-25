from datetime import datetime

from backends.model import Model
from backends.software_package import SoftwarePackage


class SoftwareVersion(Model):
    """A specific version of a software package."""
    software_package: SoftwarePackage
    name: str
    internal_identifier: str
    release_date: datetime

    def __init__(self, software_package: SoftwarePackage, name: str,
                 internal_identifier: str, release_date: datetime):
        self.software_package = software_package
        self.name = name
        self.internal_identifier = internal_identifier
        self.release_date = release_date

    def __str__(self) -> str:
        return '{} {}'.format(str(self.software_package), self.name)

    def __eq__(self, other) -> bool:
        return (self.software_package == other.software_package and
                self.internal_identifier == other.internal_identifier)

    def __hash__(self) -> int:
        return hash(self.software_package) + hash(self.internal_identifier)
