import re

from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider

# TODO: find out path_map
#class Ghost(SoftwareDefinition):
#    software_package = SoftwarePackage(
#        name='Ghost',
#        vendor='Ghost Foundation')
#    provider = GitTagProvider(
#        software_package=software_package,
#        url='https://github.com/TryGhost/Ghost.git',
#        version_pattern=re.compile(r'^(\d+\.){3}.*')
#    )
#    path_map = {
#        '/': '/',
#    }
#    ignore_paths = None
