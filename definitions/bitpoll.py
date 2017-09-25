from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class Bitpoll(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='Bitpoll',
        vendor='Bitpoll Maintainers')
    provider = GitTagProvider(
        software_package=software_package,
        url='https://github.com/fsinfuhh/Bitpoll.git'
    )
    path_map = {
        '/static/': '/bitpoll/base/static/',
    }
    ignore_paths = None
