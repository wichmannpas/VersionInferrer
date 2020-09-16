from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.DebRepositoryProvider import DebRepositoryProvider


class GitlabEnterpriseEdition(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='Jitsi Meet',
        vendor='8x8')
    provider = DebRepositoryProvider(
        software_package=software_package,
        repo_base_url='https://download.jitsi.org/',
        repo_packages_path='stable/Packages',
        repo_package='jitsi-meet-web'
    )
    path_map = {
        '/': '/usr/share/jitsi-meet/',
    }
    ignore_paths = None
