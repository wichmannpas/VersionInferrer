from abc import abstractmethod, ABCMeta
from typing import Iterable, List, Set, Tuple, Union

from backends.model import Model
from backends.software_package import SoftwarePackage
from backends.software_version import SoftwareVersion
from backends.static_file import StaticFile


class Backend(metaclass=ABCMeta):
    """A base class for database backends."""

    @abstractmethod
    def delete(self, element: Model) -> bool:
        """Delete an instance of a Model subclass."""

    @abstractmethod
    def mark_indexed(self, software_version: SoftwareVersion, indexed: bool = True) -> bool:
        """Update a software version fully indexed flag."""

    @abstractmethod
    def reopen_connection(self):
        """Open a new connection to the backend store."""

    # TODO: Provide a method allowing idf retrieval for several static files at once (db access optimization)
    @abstractmethod
    def retrieve_static_file_idf_weight(
            self, checksum: bytes) -> float:
        """
        Retrieve the IDF weight for a specific static file checksum.
        """

    @abstractmethod
    def retrieve_packages(self) -> Set[SoftwarePackage]:
        """Retrieve all available packages."""

    @abstractmethod
    def retrieve_packages_by_name(
            self, name: str) -> Set[SoftwarePackage]:
        """Retrieve all available packages whose names are likely to name."""

    @abstractmethod
    def retrieve_static_file_users_by_checksum(
            self, checksum: bytes) -> Set[SoftwareVersion]:
        """Retrieve all versions using a static file with a specific checksum."""

    @abstractmethod
    def retrieve_static_file_users_by_webroot_paths(
            self, webroot_path: str) -> Set[SoftwareVersion]:
        """Retrieve all versions providing a static file at the specified path."""

    @abstractmethod
    def retrieve_static_files_almost_unique_to_version(
            self, version: SoftwareVersion,
            max_users: int) -> Set[Tuple[Set[SoftwareVersion], StaticFile]]:
        """
        Get all static files which are used by the specified version and
        in total by max_users versions or less.

        Return a set of using versions for every retrieved static file.
        """

    @abstractmethod
    def retrieve_static_files_popular_to_versions(
            self, versions: Iterable[SoftwareVersion],
            limit: int) -> Set[Tuple[Set[SoftwareVersion], StaticFile]]:
        """
        Get the static files most popular for versions.

        Return a set of using versions (of specified versions) for every
        retrieved static file.
        """

    @abstractmethod
    def retrieve_static_files_unique_to_version(
            self, version: SoftwareVersion) -> Set[StaticFile]:
        """
        Get all static files which are only used by the specified version.
        """

    @abstractmethod
    def retrieve_versions(
            self, software_package: SoftwarePackage,
            indexed_only: bool = True) -> Set[SoftwareVersion]:
        """Retrieve all available versions for specified software package."""

    @abstractmethod
    def retrieve_webroot_paths_with_high_entropy(
            self, software_versions: Iterable[SoftwareVersion],
            limit: int, exclude: Iterable[str] = '') -> List[Tuple[str, int, int]]:
        """
        Retrieve a list of webroot paths which have a high entropy
        among the specified software versions.

        A 3-tuple of the webroot path, the number of users within
        the set of versions, and the number of different checksums
        is returned.
        """

    @abstractmethod
    def static_file_count(self, software_version: SoftwareVersion) -> int:
        """Get the count of static files used by a software version."""

    @abstractmethod
    def store(self, element: Union[Model, List[Model]]):
        """Insert or update an instance of a Model subclass."""

    @abstractmethod
    def version_delta(
            self,
            a: SoftwareVersion,
            b: SoftwareVersion) -> Set[
                Tuple[
                    Union[None, StaticFile],
                    Union[None, StaticFile]]]:
        """
        Get the delta between the static files of two software versions.

        A set of tuples is returned.
        * None, StaticFile means that a static file was added at a path where none was used before
        * StaticFile, None means that a static file was removed from a path
        * StaticFile, StaticFile means that a static file at a specific path was changed
        """


class BackendException(Exception):
    """An exception occuring in a backend."""
