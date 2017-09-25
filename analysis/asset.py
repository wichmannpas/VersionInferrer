class Asset:
    """Information about an asset from a website."""
    url: str
    checksum: bytes

    def __init__(self, url: str, checksum: bytes):
        self.url = url
        self.checksum = checksum

    def __eq__(self, other) -> bool:
        return self.url == other.url and \
            self.checksum == other.checksum

    def __hash__(self) -> int:
        return hash(self.url) + hash(self.checksum)

    def __repr__(self) -> str:
        return "<{} '{}'>".format(str(self.__class__.__name__), str(self))

    def __str__(self) -> str:
        return self.url
