from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class Joomla(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='Joomla! CMS™',
        vendor='Open Source Matters')
    provider = GitTagProvider(
        software_package=software_package,
        url='https://github.com/joomla/joomla-cms.git'
    )
    path_map = {
        '/': '/',
    }
    ignore_paths = None
