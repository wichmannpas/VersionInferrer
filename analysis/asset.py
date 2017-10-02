from typing import Set

from analysis.resource import Resource
from backends.software_version import SoftwareVersion
from base.checksum import calculate_checksum
from settings import BACKEND


class Asset(Resource):
    """
    An asset from a website.
    """
    def __eq__(self, other) -> bool:
        return self.url == other.url and \
            self.checksum == other.checksum

    def __hash__(self) -> int:
        return hash(self.url) + hash(self.checksum)

    @property
    def checksum(self) -> bytes:
        """The checksum of the current assets content."""
        if not self.retrieved:
            self.retrieve()

        return self._checksum

    def retrieve(self):
        """Retrieve the asset and calculate its checksum."""
        super().retrieve()

        self._checksum = calculate_checksum(self.content)

    @property
    def using_versions(self) -> Set[SoftwareVersion]:
        """
        Retrieve the versions using this asset
        from the backend.
        """
        if not hasattr(self, '_using_versions'):
            self._using_versions = BACKEND \
                .retrieve_static_file_users_by_checksum(
                    self.checksum)
        return self._using_versions
