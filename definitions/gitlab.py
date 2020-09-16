from backends.software_package import SoftwarePackage
from definitions.definition import SoftwareDefinition
from providers.DebRepositoryProvider import DebRepositoryProvider


class GitlabEnterpriseEdition(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='Gitlab Enterprise Edition',
        vendor='Gitlab Inc.')
    provider = DebRepositoryProvider(
        software_package=software_package,
        repo_base_url='https://packages.gitlab.com/gitlab/gitlab-ee/ubuntu/',
        repo_packages_path='dists/xenial/main/binary-amd64/Packages',
        repo_package='gitlab-ee'
    )
    path_map = {
        '/': '/opt/gitlab/embedded/service/gitlab-rails/public/',
    }
    ignore_paths = None

class GitlabCommunityEdition(SoftwareDefinition):
    software_package = SoftwarePackage(
        name='Gitlab Community Edition',
        vendor='Gitlab Inc.')
    provider = DebRepositoryProvider(
        software_package=software_package,
        repo_base_url='https://packages.gitlab.com/gitlab/gitlab-ce/ubuntu/',
        repo_packages_path='dists/xenial/main/binary-amd64/Packages',
        repo_package='gitlab-ce'
    )
    path_map = {
        '/': '/opt/gitlab/embedded/service/gitlab-rails/public/',
    }
    ignore_paths = None
