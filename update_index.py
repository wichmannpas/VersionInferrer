#!/usr/bin/env python3
import logging

from definitions import definitions
from indexing import indexing
from settings import BACKEND, LOG_FORMAT

logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)


for definition in definitions:
    logging.info('handling software package {}'.format(definition.software_package))
    # Ensure that software package is in the database
    BACKEND.store(definition.software_package)
    
    indexed_versions = BACKEND.retrieve_versions(definition.software_package)
    available_versions = definition.provider.get_versions()

    missing_versions = available_versions - indexed_versions
    logging.info('{} versions not yet indexed'.format(len(missing_versions)))
    for version in missing_versions:
        BACKEND.store(version)
        static_files = indexing.collect_static_files(definition, version)
        logging.info('indexing {} static files'.format(len(static_files)))
        for static_file in static_files:
            BACKEND.store(static_file)
        BACKEND.mark_indexed(version)
