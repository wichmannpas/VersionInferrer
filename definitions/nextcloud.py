from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class Nextcloud(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='Nextcloud',
        vendor='NextCloud GmbH')
    provider = GitTagProvider(
        software_package=software_package,
        url='https://github.com/nextcloud/server.git'
    )
    path_map = {
        '/': '/',
    }
    ignore_paths = None
