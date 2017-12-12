import re

from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class OwnCloud(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='DokuWiki',
        vendor='Andreas Gohr, et al.')
    provider = GitTagProvider(
        software_package=software_package,
        url='git://github.com/splitbrain/dokuwiki.git',
        version_pattern=re.compile(r'^release_stable_(?P<version_name>[0-9a-z-]+)$')
    )
    path_map = {
        '/': '/',
    }
    ignore_paths = None
