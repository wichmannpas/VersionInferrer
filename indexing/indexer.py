import logging
import os
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from typing import Iterable, List, Set, Union

from backends.model import Model
from backends.software_version import SoftwareVersion
from backends.static_file import StaticFile
from base.utils import join_paths
from definitions.definition import SoftwareDefinition
from definitions import definitions
from files import file_types_for_index
from providers.provider import Provider
from settings import BACKEND


class Indexer:
    """
    This class handles the indexing process.
    """

    def gc_all(self):
        """Garbace collect all definitions."""
        logging.info('Garbage collecting all definitions.')
        for definition in definitions:
            indexed_versions = BACKEND.retrieve_versions(
                definition.software_package)
            self.gc_definition(definition, indexed_versions)

    def gc_definition(
            self, definition: SoftwareDefinition,
            indexed_versions: Set[SoftwareVersion]) -> bool:
        """
        Garbage collect a specific definition, deleting versions
        not available through provider.
        Returns whether at least one version was deleted.
        """
        changed = False

        logging.info(
            'handling gc for software package %s', definition.software_package)

        available_versions = definition.provider.get_versions()

        gone_versions = indexed_versions - available_versions
        if not gone_versions:
            return False
        logging.info(
            '%d indexed versions not available anymore for %s',
            len(gone_versions),
            str(definition.software_package))
        for version in gone_versions:
            logging.info(
                'deleting version %s of %s',
                str(version),
                str(definition.software_package))
            self._delete_from_backend(version)
        return True

    def index_all(self, max_workers: int = 16,
            limit_definitions: Union[None, List[str]] = None):
        """Index for all definitions."""
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = set()
            tasks = []
            for definition in definitions:
                if limit_definitions is not None and definition not in limit_definitions:
                    # this definition is to be skipped
                    continue
                # Ensure that software package is in the database
                self._store_to_backend(definition.software_package)
                indexed_versions = BACKEND.retrieve_versions(
                    definition.software_package)

                worker = deepcopy(self)
                tasks.append((worker.index_definition, definition, indexed_versions))
            for task in tasks:
                futures.add(
                    executor.submit(*task))
            for future in futures:
                # await all the futures
                future.result()

    def index_definition(
            self, definition: SoftwareDefinition,
            indexed_versions: Set[SoftwareVersion]) -> bool:
        """
        Index a specific definition.
        Returns whether at least one new was indexed.
        """
        BACKEND.reopen_connection()

        changed = False

        logging.info('handling software package %s', definition.software_package)

        available_versions = definition.provider.get_versions()

        missing_versions = available_versions - indexed_versions
        self._store_to_backend(list(missing_versions))

        logging.info(
            '%d versions not yet indexed for %s',
            len(missing_versions),
            str(definition.software_package))
        for version in missing_versions:
            static_files = self.index_version(definition, version)
            logging.info('indexing %d static files', len(static_files))
            changed = True
            self._store_to_backend(static_files)

            self._mark_version_indexed(version)
            logging.info('indexed %d static files', len(static_files))

        return changed

    def index_version(
            self, definition: SoftwareDefinition,
            version: SoftwareVersion) -> List[StaticFile]:
        """Index a missing version."""
        file_paths = definition.provider.list_files(version)

        # Generate list of static files
        static_files = []
        for webroot_path, src_path in definition.path_map.items():
            static_files.extend(
                self.iterate_static_file_paths(
                    definition.provider,
                    version,
                    file_paths,
                    webroot_path,
                    src_path))
        return [
            static_file
            for static_file in static_files
            if (definition.ignore_paths is None or
                not definition.ignore_paths.match(static_file.src_path))
        ]


    def iterate_static_file_paths(
            self, provider: Provider, version: SoftwareVersion,
            file_paths: list, webroot_path: str, src_path: str
    ) -> Iterable[str]:
        """
        Add all static files underneath src_path and resolve their
        webroot path.
        """
        if src_path.startswith('/'):
            # remove leading slash
            src_path = src_path[1:]
        if webroot_path.startswith('/'):
            # remove leading slash
            webroot_path = webroot_path[1:]

        for full_path in file_paths:
            if not full_path.startswith(src_path):
                # file path is not relevant
                continue
            raw_content = provider.get_file_data(version, full_path)
            path = full_path.replace(src_path, '', 1)

            file = None
            for file_type in file_types_for_index:
                try:
                    file = file_type(os.path.basename(path), raw_content)
                except ValueError:
                    continue
            if file is None:
                # Not a file of any matching type.
                continue

            yield StaticFile(
                software_version=version,
                src_path=full_path,
                webroot_path=join_paths(
                    webroot_path,
                    path),
                checksum=file.checksum)

    def _delete_from_backend(self, obj: Model):
        """Store an object to the database."""
        # TODO: re-implement fallback for backends not capable of multi-threading
        #       (i.e., using mark_indexed as hook or similar)

        BACKEND.delete(obj)

    def _store_to_backend(self, obj: Union[Model, List[Model]]):
        """Store an object to the database."""
        # TODO: re-implement fallback for backends not capable of multi-threading
        #       (i.e., using mark_indexed as hook or similar)

        BACKEND.store(obj)

    def _mark_version_indexed(self, version: SoftwareVersion):
        """Store an object to the database."""
        # TODO: re-implement fallback for backends not capable of multi-threading

        BACKEND.mark_indexed(version)
