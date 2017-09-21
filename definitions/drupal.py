import re

from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider
from backend.software_package import SoftwarePackage


class Drupal(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='Drupal',
        vendor='Drupal')
    provider = GitTagProvider(
        software_package=software_package,
        url='https://github.com/drupal/drupal.git',
        exclude_pattern=re.compile(r'start')
    )
    path_map = {
        '/': '/',
    }
