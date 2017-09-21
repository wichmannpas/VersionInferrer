import os

from backend.model import Model


class SoftwarePackage(Model):
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
        # TODO: Find better solution than local import?
        from settings import CACHE_DIR
        return os.path.join(
            CACHE_DIR,
            self.name.lower())
