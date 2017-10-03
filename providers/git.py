import os

from datetime import datetime
from subprocess import CalledProcessError
from typing import Callable, List, Pattern, Set, Union

from providers.provider import Provider
from backends.software_package import SoftwarePackage
from backends.software_version import SoftwareVersion


class GenericGitProvider(Provider):
    """
    This is a generic Git provider. It handles the repository retrieval.
    Version detection is handled in its subclasses.
    """
    def __init__(
            self, software_package: SoftwarePackage, url: str,
            version_name_derivator: Union[Callable[[str], str], None] = None):
        super().__init__(software_package, version_name_derivator)
        self.url = url

    def __str__(self) -> str:
        return 'repository at {}'.format(self.url)

    def __repr__(self) -> str:
        return "<{} '{}'>".format(str(self.__class__.__name__), str(self))

    def _check_cache_directory(self) -> bool:
        """Check whether a valid clone of the provided Git repository."""
        if not os.path.isdir(self.cache_directory):
            return False
        try:
            # origin is the default remote; called 'origin' if cloned by us
            remote_url = self._check_command(
                ['git', 'config', 'remote.origin.url'])
        except CalledProcessError:
            return False
        return remote_url == self.url

    def _checkout(self, git_object: str):
        """Do a git checkout of specified git object."""
        self._refresh_repository()

        # clean all local changes
        code = self._call_command(['git', 'clean', '-xd', '--force', '--quiet'])

        # force-reset to destination commit (unstaging staged changes)
        code = self._call_command(['git', 'reset', '--hard', git_object])
        if code != 0:
            raise GitException('checkout failed')

    def _get_object_datetime(self, git_object: str) -> datetime:
        """Retrieve the age of an object."""
        raw_datetime = self._check_command(
            ['git', 'log', '-1', '--format=%ai', git_object])
        return datetime.strptime(raw_datetime, '%Y-%m-%d %H:%M:%S %z')

    def _init_repository(self):
        if self._check_cache_directory():
            # Nothing to initialize
            return
        if os.path.exists(self.cache_directory):
            raise GitException(
                'cache directory exists and is not a valid repository')
        os.makedirs(
            os.path.dirname(self.cache_directory),
            exist_ok=True)
        code = self._call_command(
            ['git', 'clone', self.url, self.cache_directory])
        if code != 0:
            raise GitException('init failed')

    def _refresh_repository(self):
        if not self._check_cache_directory():
            self._init_repository()
        code = self._call_command(['git', 'fetch', 'origin', '--prune', '--tags', '--force'])
        if code != 0:
            raise GitException('refresh failed')


class GitCommitProvider(GenericGitProvider):
    """A Git provider using commits for versions."""


class GitTagProvider(GenericGitProvider):
    """A Git provider using tags for versions."""
    def __init__(
            self, software_package: SoftwarePackage, url: str,
            version_name_derivator: Union[Callable[[str], str], None] = None,
            version_pattern: Union[Pattern, None] = None,
            exclude_pattern: Union[Pattern, None] = None):
        super().__init__(software_package, url, version_name_derivator)
        self.version_pattern = version_pattern
        self.exclude_pattern = exclude_pattern

    def checkout_version(self, version: SoftwareVersion):
        """Check out specified version."""
        self._checkout(version.internal_identifier)

    def get_versions(self) -> Set[SoftwareVersion]:
        """Retrieve all versions from git tags."""
        self._refresh_repository()

        tags = self._check_command(['git', 'tag']).split('\n')
        # Excluded versions are None and removed after set comprehension
        result = {
            self._get_software_version(tag)
            for tag in tags}
        if None in result:
            result.remove(None)
        return result

    def _get_software_version(
            self, tag: str) -> Union[SoftwareVersion, None]:
        """Get a SoftwareVersion object from a git tag name."""
        internal_identifier = tag
        name = internal_identifier
        if self.version_pattern:
            match = self.version_pattern.match(tag)
            if not match:
                return
            name = match.groupdict().get('version_name', internal_identifier)
        if self.exclude_pattern:
            if self.exclude_pattern.match(tag):
                return

        release_date = self._get_object_datetime(tag)

        # Apply additional name derivation functions from superclasses
        name = super()._get_software_version(name, release_date).name

        return SoftwareVersion(
            software_package=self.software_package,
            name=name,
            internal_identifier=internal_identifier,
            release_date=release_date)


class GitException(Exception):
    """A Git exception."""
