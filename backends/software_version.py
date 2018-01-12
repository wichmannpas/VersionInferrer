import os
import pickle
from datetime import datetime
from subprocess import call

from backends.model import Model
from backends.software_package import SoftwarePackage


class SoftwareVersion(Model):
    """A specific version of a software package."""
    # software_package: SoftwarePackage
    # name: str
    # internal_identifier: str
    # release_date: datetime

    def __init__(self, software_package: SoftwarePackage, name: str,
                 internal_identifier: str, release_date: datetime):
        self.software_package = software_package
        self.name = name
        self.internal_identifier = internal_identifier
        self.release_date = release_date

    def __str__(self) -> str:
        return '{} {}'.format(str(self.software_package), self.name)

    def __eq__(self, other) -> bool:
        return (self.software_package == other.software_package and
                self.internal_identifier == other.internal_identifier)

    def __hash__(self) -> int:
        return hash(self.software_package) ^ hash(self.internal_identifier)

    def serialize(self) -> dict:
        """Serialize into a dict."""
        return {
            'software_package': self.software_package.serialize(),
            'name': self.name,
            'internal_identifier': self.internal_identifier,
            'release_date': self.release_date.isoformat(),
        }

    @property
    def vulnerable(self) -> bool:
        """Check whether the version has known vulnerabilities."""
        from settings import CVE_STATISTICS_FILE
        if not os.path.isfile(CVE_STATISTICS_FILE):
            call(['vendor/update'])
        with open(CVE_STATISTICS_FILE, 'rb') as fh:
            cve_statistics = pickle.load(fh)
        return bool(cve_statistics.get(self))
