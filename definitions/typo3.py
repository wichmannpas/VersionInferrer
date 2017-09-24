import re

from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.git import GitTagProvider


def version_name_derivator(internal_identifier):
    replaced = re.sub(
        r'(\d+)-(\d+)-(\d+)(.*)', 
        r'\1.\2.\3-\4',
        internal_identifier).lower()
    if replaced[-1] == '-':
        return replaced[:-1]
    return replaced



class TYPO3(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='TYPO3',
        vendor='TYPO3 GmbH')
    provider = GitTagProvider(
        software_package=software_package,
        url='git://git.typo3.org/Packages/TYPO3.CMS.git',
        version_pattern=re.compile(r'^TYPO3_(?P<version_name>.*)'),
        version_name_derivator=version_name_derivator)
    path_map = {
        '/': '/',
    }
    ignore_paths = None
