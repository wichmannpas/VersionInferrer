import os

from subprocess import call, check_output, CalledProcessError
from typing import List, Pattern, Union

from providers.provider import Provider
from software_package import SoftwarePackage, SoftwareVersion


class GenericGitProvider(Provider):
    """
    This is a generic Git provider. It handles the repository retrieval.
    Version detection is handled in its subclasses.
    """
    def __init__(self, software_package: SoftwarePackage, url: str):
        super().__init__(software_package)
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

    def _check_command(self, command: List[str]) -> str:
        """
        Run a command within the cache directory and return its output as str.
        """
        cwd = None
        if os.path.isdir(self.cache_directory):
            cwd = self.cache_directory
        return check_output(
            command, cwd=cwd).decode()[:-1]

    def _checkout(self, git_object: str):
        """Do a git checkout of specified git object."""
        self._refresh_repository()

        code = self._call_command(['git', 'checkout', git_object])
        if code != 0:
            raise GitException('checkout failed')

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
        code = self._call_command(['git', 'pull'])
        if code != 0:
            raise GitException('refresh failed')

    def _call_command(self, command: List[str]) -> int:
        """
        Run a command within the cache directory and return its return code.
        """
        cwd = None
        if os.path.isdir(self.cache_directory):
            cwd = self.cache_directory
        return call(command, cwd=cwd)


class GitCommitProvider(GenericGitProvider):
    """A Git provider using commits for versions."""


class GitTagProvider(GenericGitProvider):
    """A Git provider using tags for versions."""
    def __init__(self, software_package: SoftwarePackage, url: str,
                 version_pattern: Union[Pattern, None] = None):
        super().__init__(software_package, url)
        self.version_pattern = version_pattern

    def checkout_version(self, version: SoftwareVersion):
        """Check out specified version."""
        self._checkout(version.identifier)

    def get_versions(self) -> List[SoftwareVersion]:
        """Retrieve all versions from git tags."""
        tags = self._check_command(['git', 'tag']).split('\n')
        return [
            SoftwareVersion(self.software_package, tag)
            for tag in tags
            if not self.version_pattern or self.version_pattern.match(tag)]


class GitException(Exception):
    """A Git exception."""
