from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class Wordpress(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='WordPress',
        vendor='WordPress')
    provider = GitTagProvider(
        software_package=software_package,
        url='https://github.com/WordPress/WordPress.git'
    )
    path_map = {
        '/': '/',
        '/': '/',
    }
    ignore_paths = None
