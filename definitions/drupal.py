import re

from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class Drupal(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='Drupal',
        vendor='Drupal')
    provider = GitTagProvider(
        software_package=software_package,
        url='https://github.com/drupal/drupal.git',
        version_pattern=re.compile(r'\d\..*')
    )
    path_map = {
        '/': '/',
    }
    ignore_paths = None
