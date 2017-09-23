from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


class TYPO3(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='TYPO3',
        vendor='TYPO3 GmbH')
    provider = GitTagProvider(
        software_package=software_package,
        url='git://git.typo3.org/Packages/TYPO3.CMS.git'
    )
    path_map = {
        '/': '/',
    }
    ignore_paths = None
