import os

from backends.model import Model


class SoftwarePackage(Model):
    """A software package."""
    name: str
    vendor: str

    def __init__(self, name: str, vendor: str):
        self.name = name
        self.vendor = vendor

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
