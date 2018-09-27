import os
import re

from datetime import datetime, timezone, timedelta
from subprocess import CalledProcessError
from typing import Callable, List, Pattern, Set, Union

from pygit2 import clone_repository, Commit, GIT_FETCH_PRUNE, Index, Tag
from pygit2.repository import Repository

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

    def list_files(self, version: SoftwareVersion):
        """List all files available within version."""
        commit = self._get_commit(version)
        index = Index()
        index.read_tree(commit.tree)
        return [
            entry.path
            for entry in index
        ]

    def get_file_data(self, version: SoftwareVersion, path: str):
        """Get data of file at path as contained within version.."""
        commit = self._get_commit(version)
        file_blob = self.repository.revparse_single('{}:{}'.format(
            commit.hex,
            path))
        return file_blob.data

    @property
    def repository(self):
        if hasattr(self, '_repository'):
            return self._repository

        return Repository(self.cache_directory)

    def _check_cache_directory(self) -> bool:
        """Check whether a valid clone of the provided Git repository."""
        if not os.path.isdir(self.cache_directory):
            return False
        try:
            remote_url = self.repository.remotes['origin'].url
        except (CalledProcessError, ValueError):
            return False
        return remote_url == self.url

    def _get_commit(self, version: SoftwareVersion) -> Commit:
        return self.commit[version.internal_identifier]

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
        self._repository = clone_repository(self.url, self.cache_directory, bare=True)

    def _refresh_repository(self):
        if not self._check_cache_directory():
            self._init_repository()
        remote = self.repository.remotes['origin']
        assert remote.refspec_count
        assert remote.get_refspec(0).force
        remote.fetch(prune=GIT_FETCH_PRUNE)


class GitCommitProvider(GenericGitProvider):
    """A Git provider using commits for versions."""


class GitTagProvider(GenericGitProvider):
    """A Git provider using tags for versions."""
    TAG_PATTERN = re.compile(r'^refs/tags/(.*)$')

    def __init__(
            self, software_package: SoftwarePackage, url: str,
            version_name_derivator: Union[Callable[[str], str], None] = None,
            version_pattern: Union[Pattern, None] = None,
            exclude_pattern: Union[Pattern, None] = None):
        super().__init__(software_package, url, version_name_derivator)
        self.version_pattern = version_pattern
        self.exclude_pattern = exclude_pattern

    def get_versions(self) -> Set[SoftwareVersion]:
        """Retrieve all versions from git tags."""
        self._refresh_repository()

        tags = [
            matched_ref.group(1)
            for matched_ref in (
                self.TAG_PATTERN.match(ref)
                for ref in self.repository.listall_references())
            if matched_ref
        ]
        # Excluded versions are None and removed after set comprehension
        result = {
            self._get_software_version(tag)
            for tag in tags}
        if None in result:
            result.remove(None)
        return result

    def _get_commit(self, version: SoftwareVersion) -> Commit:
        return self._get_commit_from_tag_name(version.internal_identifier)

    def _get_commit_from_tag_name(self, tag_name: str) -> Commit:
        rev = self.repository.revparse_single(tag_name)

        if isinstance(rev, Tag):
            # this is a tag object
            return rev.get_object()

        return rev

    def _get_software_version(
            self, tag: str) -> Union[SoftwareVersion, None]:
        """Derive a SoftwareVersion object from a git tag name."""
        internal_identifier = tag
        if self.version_pattern:
            match = self.version_pattern.match(internal_identifier)
            if not match:
                return
            name = match.groupdict().get('version_name', internal_identifier)
        if self.exclude_pattern:
            if self.exclude_pattern.match(internal_identifier):
                return

        commit = self._get_commit_from_tag_name(internal_identifier)
        tzinfo  = timezone(timedelta(minutes=commit.author.offset))
        release_date = datetime.fromtimestamp(float(commit.author.time), tzinfo)

        # Apply additional name derivation functions from superclasses
        name = super()._get_software_version(internal_identifier, release_date).name

        return SoftwareVersion(
            software_package=self.software_package,
            name=name,
            internal_identifier=internal_identifier,
            release_date=release_date)


class GitException(Exception):
    """A Git exception."""
