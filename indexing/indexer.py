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
        Garbace collect a specific definition, deleting versions
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

    def index_all(self, max_workers: int = 16):
        """Index for all definitions."""
        while True:
            changed = False
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = set()
                for definition in definitions:
                    # Ensure that software package is in the database
                    self._store_to_backend(definition.software_package)
                    indexed_versions = BACKEND.retrieve_versions(
                        definition.software_package)

                    worker = deepcopy(self)
                    futures.add(
                        executor.submit(
                            worker.index_definition, definition, indexed_versions))
                for future in futures:
                    this_changed = future.result()
                    if this_changed:
                        changed = True
            if not changed:
                break

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

        return changed

    def index_version(
            self, definition: SoftwareDefinition,
            version: SoftwareVersion) -> List[StaticFile]:
        """Index a missing version."""
        definition.provider.checkout_version(version)

        # Generate list of static files
        static_files = []
        for webroot_path, src_path in definition.path_map.items():
            static_files.extend(
                self.iterate_static_file_paths(
                    version,
                    definition.provider.cache_directory,
                    webroot_path,
                    src_path))
        return [
            static_file
            for static_file in static_files
            if (definition.ignore_paths is None or
                not definition.ignore_paths.match(static_file.src_path))
        ]


    def iterate_static_file_paths(
            self, software_version: SoftwareVersion, base_dir: str,
            webroot_path: str, src_path: str) -> Iterable[str]:
        """
        Get the paths of all static files within base_dir using
        src_path and webroot_path mapping.
        """
        for directory, file_name in (
                (directory, file_name)
                for directory, dir_names, file_names in os.walk(join_paths(
                        base_dir, src_path))
                for file_name in file_names):
            full_path = os.path.join(base_dir, directory, file_name)
            if not os.path.isfile(full_path) or os.path.islink(full_path):
                # do not index non-regular files
                continue
            with open(full_path, 'rb') as fdes:
                raw_content = fdes.read()

            file = None
            for file_type in file_types_for_index:
                try:
                    file = file_type(file_name, raw_content)
                except ValueError:
                    continue
            if file is None:
                # Not a file of any matching type.
                continue

            yield StaticFile(
                software_version=software_version,
                src_path=join_paths(
                    directory.replace(base_dir, '', 1),
                    file_name),
                webroot_path=join_paths(
                    webroot_path,
                    directory.replace(join_paths(base_dir, src_path), '', 1),
                    file_name),
                checksum=file.checksum)

    def _delete_from_backend(self, obj: Model):
        """Store an object to the database."""
        # TODO: re-implement fallback for backends not capable of multi-threading
        #       (i.e., using mark_indexed as hoook or similar)

        BACKEND.delete(obj)

    def _store_to_backend(self, obj: Union[Model, List[Model]]):
        """Store an object to the database."""
        # TODO: re-implement fallback for backends not capable of multi-threading
        #       (i.e., using mark_indexed as hoook or similar)

        BACKEND.store(obj)

    def _mark_version_indexed(self, version: SoftwareVersion):
        """Store an object to the database."""
        # TODO: re-implement fallback for backends not capable of multi-threading

        BACKEND.mark_indexed(version)
