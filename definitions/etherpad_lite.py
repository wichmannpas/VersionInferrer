from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class EtherpadLite(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='Etherpad Lite',
        vendor='Ether')
    provider = GitTagProvider(
        software_package=software_package,
        url='https://github.com/ether/etherpad-lite.git'
    )
    path_map = {
        '/static/': '/src/static/',
    }
    ignore_paths = None
