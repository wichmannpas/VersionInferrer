import re

from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class Wordpress(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='MediaWiki',
        vendor='Wikimedia Foundation')
    provider = GitTagProvider(
        software_package=software_package,
        url='https://gerrit.wikimedia.org/r/p/mediawiki/core.git',
        version_pattern=re.compile(r'^(?P<version_name>(\d+)\.(\d+)\.(\d+))$')
    )
    path_map = {
        '/': '/',
    }
    ignore_paths = None
