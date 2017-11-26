import re

from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class Wordpress(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='Moodle',
        vendor='Moodle HQ')
    provider = GitTagProvider(
        software_package=software_package,
        url='git://git.moodle.org/moodle.git',
        version_pattern=re.compile(r'^v(?P<version_name>\d+\.\d+\.\d+)'),
    )
    path_map = {
        '/': '/',
    }
    ignore_paths = None
