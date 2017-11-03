import os
from typing import List, Union

from backends.model import Model


class SoftwarePackage(Model):
    """A software package."""
    # name: str
    # vendor: str
    # alternative_names: list

    def __init__(self, name: str, vendor: str, alternative_names: Union[List, None] = None):
        self.name = name
        self.vendor = vendor
        self.alternative_names = alternative_names
        if not alternative_names:
            self.alternative_names = []

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other) -> bool:
        return self.name == other.name and self.vendor == other.vendor

    def __hash__(self) -> int:
        return hash(self.name) + hash(self.vendor)

    @property
    def cache_directory(self) -> str:
        """A path to the cache directory."""
        # TODO: Find better solution than local import?
        from settings import CACHE_DIR
        return os.path.join(
            CACHE_DIR,
            self.name.lower())
