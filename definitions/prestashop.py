from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class PrestaShop(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='PrestaShop',
        vendor='PrestaShop')
    provider = GitTagProvider(
        software_package=software_package,
        url='https://github.com/PrestaShop/PrestaShop.git'
    )
    path_map = {
        '/': '/',
    }
    ignore_paths = None
