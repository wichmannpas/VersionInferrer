#!/usr/bin/env python3
from definitions import definitions
from indexing import indexing
from settings import BACKEND


for definition in definitions:
    # Ensure that software package is in the database
    BACKEND.store(definition.software_package)
    
    indexed_versions = BACKEND.retrieve_versions(definition.software_package)
    available_versions = definition.provider.get_versions()

    missing_versions = available_versions - indexed_versions
    for version in missing_versions:
        static_files = indexing.collect_static_files(definition, version)
        for static_file in static_files:
            BACKEND.store(static_file)
        BACKEND.mark_indexed(version)
