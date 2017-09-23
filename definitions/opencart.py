from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class OpenCart(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='OpenCart',
        vendor='OpenCart Limited')
    provider = GitTagProvider(
        software_package=software_package,
        url='https://github.com/opencart/opencart.git'
    )
    path_map = {
        '/': '/upload/',
    }
    ignore_paths = None
