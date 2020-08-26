import re

from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class Magento(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='Magento Open Source',
        vendor='Magento Inc.',
        alternative_names=[
            'Magento',
        ])
    provider = GitTagProvider(
        software_package=software_package,
        url='https://github.com/magento/magento2.git',
        version_pattern=re.compile(r'^\d+\.\d+\.\d+$'),
    )
    path_map = {
        '/': '/',
    }
    ignore_paths = None
