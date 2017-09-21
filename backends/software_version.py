from backends.model import Model
from backends.software_package import SoftwarePackage


class SoftwareVersion(Model):
    """A specific version of a software package."""
    software_package: SoftwarePackage
    identifier: str

    def __init__(self, software_package: SoftwarePackage, identifier: str):
        self.software_package = software_package
        self.identifier = identifier

    def __repr__(self) -> str:
        return "<{} '{}'>".format(str(self.__class__.__name__), str(self))

    def __str__(self) -> str:
        return '{} {}'.format(str(self.software_package), self.identifier)
