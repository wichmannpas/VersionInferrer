from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class PhpBB(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='phpBB',
        vendor='phpBB Limited')
    provider = GitTagProvider(
        software_package=software_package,
        url='https://github.com/phpbb/phpbb.git'
    )
    path_map = {
        '/': '/',
    }
    ignore_paths = None
