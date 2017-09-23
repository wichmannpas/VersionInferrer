from backends.model import Model
from backends.software_version import SoftwareVersion


class StaticFile(Model):
    """A (maybe not so) static file."""
    software_version: SoftwareVersion
    src_path: str
    webroot_path: str
    checksum: str

    def __init__(self, software_version: SoftwareVersion, src_path:
                 str, webroot_path: str, checksum: str):
        self.software_version = software_version
        self.src_path = src_path
        self.webroot_path = webroot_path
        self.checksum = checksum

    def __str__(self) -> str:
        return '{} -> {}'.format(self.webroot_path, self.src_path)

    def __eq__(self, other) -> bool:
        return (self.software_version == other.software_version and
                self.src_path == other.src_path and
                self.webroot_path == other.webroot_path and
                self.checksum == other.checksum)

    def __hash__(self) -> int:
        return hash(self.software_version) + hash(self.src_path) + \
            hash(self.webroot_path) + hash(self.checksum)
