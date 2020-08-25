from typing import Set

from analysis.resource import Resource, RetrievalFailure
from backends.software_version import SoftwareVersion
from backends.static_file import StaticFile
from base.checksum import calculate_checksum
from settings import BACKEND, FAILED_ASSET_WEIGHT


class Asset(Resource):
    """
    An asset from a website.
    """

    def __eq__(self, other) -> bool:
        if not super().__eq__(other):
            return False
        if self.retrieved and self.success:
            return self.checksum == other.checksum
        return True

    def __hash__(self) -> int:
        base_hash = super().__hash__()
        if self.retrieved and self.success:
            return base_hash ^ hash(self.checksum)
        return base_hash

    @property
    def checksum(self) -> bytes:
        """The checksum of the current assets content."""
        if not self.retrieved:
            self.retrieve()
        if not self._success:
            raise RetrievalFailure

        return self._checksum

    def retrieve(self):
        """Retrieve the asset and calculate its checksum."""
        super().retrieve()

        if self._success:
            self._checksum = calculate_checksum(self.content)

    @property
    def expected_versions(self) -> Set[SoftwareVersion]:
        """
        Retrieve the versions which should provide an asset at this path
        from the backend.
        """
        if not hasattr(self, '_expected_versions'):
            self._expected_versions = BACKEND \
                .retrieve_static_file_users_by_webroot_paths(
                self.webroot_path)
        return self._expected_versions

    @property
    def idf_weight(self):
        """Get the idf weight for this asset."""
        if not self.success:
            return FAILED_ASSET_WEIGHT
        if not hasattr(self, '_idf_weight'):
            # cache in python object
            self._idf_weight = BACKEND.retrieve_static_file_idf_weight(
                self.checksum)
        return self._idf_weight

    def serialize(self) -> dict:
        """Serialize into a dict."""
        base = super().serialize()
        if not self.success:
            base.update({
                'expected_versions': self.expected_versions,
                'using_versions': self.using_versions,
            })
            return base
        base.update({
            'expected_versions': self.expected_versions,
            'using_versions': self.using_versions,
            'checksum': self.checksum.hex(),
        })
        return base

    @property
    def expected_webroot_paths(self) -> Set[str]:
        if not hasattr(self, '_expected_webroot_paths'):
            self._expected_webroot_paths = {
                static_file.webroot_path
                for static_file in self.known_static_files
            }
        return self._expected_webroot_paths

    @property
    def known_static_files(self) -> Set[StaticFile]:
        if not self.success:
            return set()
        if not hasattr(self, '_known_static_files'):
            self._known_static_files = BACKEND.retrieve_static_files_by_checksum(
                self.checksum)
        return self._known_static_files

    @property
    def using_versions(self) -> Set[SoftwareVersion]:
        """
        Retrieve the versions using this asset
        from the backend.
        """
        if not self.success:
            return set()
        if not hasattr(self, '_using_versions'):
            self._using_versions = BACKEND \
                .retrieve_static_file_users_by_checksum(
                self.checksum)
        return self._using_versions
