from backends.model import Model
from backends.software_version import SoftwareVersion


class StaticFile(Model):
    """A (maybe not so) static file."""
    software_version: SoftwareVersion
    src_path: str
    webroot_path: str
    checksum: str

    def __init__(self, software_version: SoftwareVersion, src_path: str, webroot_path: str, checksum: str):
        self.software_version = software_version
        self.src_path = src_path
        self.webroot_path = webroot_path
        self.checksum = checksum

    def __str__(self) -> str:
        return '{} -> {}'.format(self.webroot_path, self.src_path)
