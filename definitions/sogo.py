from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class SOGo(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='SOGo',
        vendor='Inverse Inc')
    provider = GitTagProvider(
        software_package=software_package,
        url='https://github.com/inverse-inc/sogo.git'
    )
    path_map = {
        '/SOGo/SOGo.woa/': '/UI/',
    }
    ignore_paths = None
