#!/usr/bin/env python3
import logging
from concurrent.futures import ThreadPoolExecutor
from copy import copy
from traceback import print_exc
from typing import Set, Tuple

from backends.software_version import SoftwareVersion
from backends.model import Model
from definitions.definition import SoftwareDefinition
from definitions import definitions
from indexing import indexing
from settings import BACKEND, LOG_FORMAT, MAX_WORKERS, STEP_LIMIT


logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)


def handle_definition(
        definition: SoftwareDefinition,
        indexed_versions: Set[SoftwareVersion]) -> Tuple[
            Set[Model], Set[SoftwareVersion], bool]:
    store_objects = set()
    versions = set()
    changed = False

    logging.info('handling software package %s', definition.software_package)
    
    available_versions = definition.provider.get_versions()

    missing_versions = available_versions - indexed_versions
    logging.info('%d versions not yet indexed for %s', len(missing_versions), str(definition.software_package))
    for step in range(min(len(missing_versions), STEP_LIMIT)):
        version = missing_versions.pop()
        versions.add(version)

        try:
            BACKEND.store(version)
        except Exception:
            store_objects.add(version)

        static_files = indexing.collect_static_files(definition, version)
        logging.info('indexing %d static files', len(static_files))
        changed = True
        for static_file in static_files:
            try:
                BACKEND.store(static_file)
            except Exception:
                store_objects.add(static_file)

        try:
            BACKEND.mark_indexed(version)
        except Exception:
            pass

    return store_objects, versions, changed


while True:
    changed = False
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = set()
        for definition in definitions:
            # Ensure that software package is in the database
            BACKEND.store(definition.software_package)
            indexed_versions = BACKEND.retrieve_versions(
                definition.software_package)

            futures.add(
                executor.submit(handle_definition, definition, indexed_versions))
        for future in futures:
            store_objects, versions, this_changed = future.result()
            if this_changed:
                changed = True
            if store_objects:
                changed = True
                logging.info('storing %d elements to backend', len(store_objects))
                for element in store_objects:
                    BACKEND.store(element)
            for version in versions:
                BACKEND.mark_indexed(version)
    if not changed:
        break
