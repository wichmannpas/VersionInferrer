import re

from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class OwnCloud(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='ownCloud',
        vendor='ownCloud')
    provider = GitTagProvider(
        software_package=software_package,
        url='https://github.com/owncloud/core.git',
        version_pattern=re.compile(r'v(?P<version_name>.*)')
    )
    path_map = {
        '/': '/',
    }
    ignore_paths = None
