from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class Ghost(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='Ghost',
        vendor='Ghost Foundation')
    provider = GitTagProvider(
        software_package=software_package,
        url='https://github.com/TryGhost/Ghost.git'
    )
    path_map = {
        '/': '/',
    }
    ignore_paths = None
