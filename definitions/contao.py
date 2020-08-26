from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class Contao(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='Contao Open Source CMS',
        vendor='Contao Community',
        alternative_names=[
            'Contao',
        ])
    provider = GitTagProvider(
        software_package=software_package,
        url='https://github.com/contao/core.git'
    )
    path_map = {
        '/': '/',
    }
    ignore_paths = None
