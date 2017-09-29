from analysis.resource import Resource
from base.checksum import calculate_checksum


class Asset(Resource):
    """
    An asset from a website.
    """
    def __init__(self, url: str):
        super().__init__(url)

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
