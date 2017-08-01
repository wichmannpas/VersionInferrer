import os

from settings import CACHE_DIR


class SoftwarePackage:
    """A software package."""
    name: str
    vendor: str

    def __init__(self, name: str, vendor: str):
        self.name = name
        self.vendor = vendor

    def __repr__(self) -> str:
        return "<{} '{}'>".format(str(self.__class__.__name__), str(self))

    def __str__(self) -> str:
        return self.name

    @property
    def cache_directory(self) -> str:
        """A path to the cache directory."""
        return os.path.join(
            CACHE_DIR,
            self.name.lower())


class SoftwareVersion:
    """A specific version of a software package."""
    software: SoftwarePackage
    identifier: str

    def __init__(self, software: SoftwarePackage, identifier: str):
        self.software = software
        self.identifier = identifier

    def __repr__(self) -> str:
        return "<{} '{}'>".format(str(self.__class__.__name__), str(self))

    def __str__(self) -> str:
        return '{} {}'.format(str(self.software), self.identifier)
