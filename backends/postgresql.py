import json
from contextlib import closing
from datetime import datetime
from string import ascii_letters, digits
from typing import Iterable, List, Optional, Tuple, Union

import psycopg2

from backends.backend import BackendException
from backends.generic_db import GenericDatabaseBackend, use_cache
from backends.model import Model
from backends.software_package import SoftwarePackage
from backends.software_version import SoftwareVersion
from backends.static_file import StaticFile
from base.json import CustomJSONEncoder


class PostgresqlBackend(GenericDatabaseBackend):
    """The backend handling the SQLite communication."""
    _operator = '%s'
    _true_value = 'true'

    def initialize_scan_results(self, scan_identifier: str):
        """
        Prepare the backend to store scan results.

        This only supports postgresql.
        """
        self._assert_valid_scan_identifier(scan_identifier)

        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            CREATE SEQUENCE IF NOT EXISTS scan_result_{}_id_seq;
            '''.format(scan_identifier))
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_result_{identifier} (
                id INTEGER PRIMARY KEY DEFAULT NEXTVAL('scan_result_{identifier}_id_seq') NOT NULL,
                url TEXT NOT NULL UNIQUE,
                scan_time TIMESTAMP NOT NULL,
                result JSONB
            )
            '''.format(identifier= scan_identifier))
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS
                scan_result_{identifier}_url
            ON scan_result_{identifier}(url)
            '''.format(identifier=scan_identifier))

    def retrieve_scan_result(self, url: str, scan_identifier: str) -> Union[object, None]:
        """
        Retrieve a scan result from the backend.
        """
        self._assert_valid_scan_identifier(scan_identifier)

        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            SELECT
                r.result
            FROM
                scan_result_{} r
            WHERE
                r.url = %s
            '''.format(scan_identifier), (url,))
            result = cursor.fetchone()
            if result:
                return result[0]

    def retrieve_scan_results(self, urls: Iterable[str], scan_identifier: str) -> List[Tuple[str, object]]:
        """
        Bulk retrieve scan results from the backend.
        """
        self._assert_valid_scan_identifier(scan_identifier)

        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            SELECT
                r.url,
                r.result
            FROM
                scan_result_{} r
            WHERE
                r.url IN %s
            '''.format(scan_identifier), (tuple(urls),))
            return cursor.fetchall()

    def retrieve_scanned_sites(self, scan_identifier: str) -> List[str]:
        """
        Retrieve a list of the site URLs that have an existing scan result.
        """
        self._assert_valid_scan_identifier(scan_identifier)

        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            SELECT
                r.url
            FROM
                scan_result_{} r
            '''.format(scan_identifier))
            return [r[0] for r in cursor.fetchall()]

    def store_scan_result(self, url: str, result: object, scan_identifier: str):
        """
        Store a scan result to the backend.
        """
        self._assert_valid_scan_identifier(scan_identifier)

        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            INSERT
            INTO scan_result_{} (
                url,
                scan_time,
                result
            )
            VALUES (
                %s,
                %s,
                %s
            )
            '''.format(scan_identifier), (url, datetime.now(), json.dumps(result, cls=CustomJSONEncoder)))

    def store(self, element: Union[Model, List[Model]]) -> Union[bool, List[bool]]:
        """
        Insert or update an instance of a Model subclass.

        Returns whether a change has been made.
        For postgres, return value is not always accurate.
        """
        if isinstance(element, list):
            return self._store_many(element)

        if isinstance(element, SoftwarePackage):
            self._insert_software_package(element)
            return True
        elif isinstance(element, SoftwareVersion):
            self._insert_software_version(element)
            return True
        elif isinstance(element, StaticFile):
            software_version_id = self._insert_software_version(
                element.software_version)
            static_file_id = self._get_or_create_static_file(element)
            with closing(self._connection.cursor()) as cursor:
                cursor.execute('''
                INSERT
                INTO static_file_use (
                    software_version_id,
                    static_file_id)
                VALUES (
                    %s,
                    %s)
                ON CONFLICT DO NOTHING
                ''', (
                    software_version_id,
                    static_file_id))
            return True
        raise BackendException('unsupported model type')

    @use_cache
    def _insert_software_package(self, software_package: SoftwarePackage) -> int:
        """Insert a software package and return its id."""
        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            INSERT
            INTO software_package (
                name,
                vendor,
                alternative_names)
            VALUES (
                %(name)s,
                %(vendor)s,
                %(alternative_names)s)
            ON CONFLICT (name, vendor) DO UPDATE
                SET alternative_names=%(alternative_names)s
            RETURNING id
            ''', {
                'name': software_package.name,
                'vendor': software_package.vendor,
                'alternative_names': self._pack_list(software_package.alternative_names),
            })
            return cursor.fetchone()[0]

    @use_cache
    def _insert_software_version(self, software_version: SoftwareVersion) -> int:
        """Insert a software version and return its id."""
        software_package_id = self._insert_software_package(
            software_version.software_package)
        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            INSERT
            INTO software_version (
                software_package_id,
                name,
                internal_identifier,
                release_date)
            VALUES (
                %(software_package_id)s,
                %(name)s,
                %(internal_identifier)s,
                %(release_date)s)
            ON CONFLICT (software_package_id, internal_identifier) DO UPDATE
                SET
                    name=%(name)s,
                    release_date=%(release_date)s
            RETURNING id
            ''', {
                'software_package_id': software_package_id,
                'name': software_version.name,
                'internal_identifier': software_version.internal_identifier,
                'release_date': software_version.release_date})
            return cursor.fetchone()[0]

    def _get_or_create_static_file(self, static_file: StaticFile) -> int:
        """Get or create a static file element an return its id."""
        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            INSERT
            INTO static_file (
                src_path,
                webroot_path,
                checksum)
            VALUES(
                %s,
                %s,
                %s)
            ON CONFLICT
                (src_path, webroot_path, checksum)
                DO UPDATE
                SET "src_path"="static_file"."src_path"
            RETURNING id
            ''', (
                static_file.src_path,
                static_file.webroot_path,
                static_file.checksum))
            return cursor.fetchone()[0]

    def _open_connection(self, *args, **kwargs):
        """Open a connection to the database."""
        self._connection = psycopg2.connect(*args, **kwargs)
        self._connection.set_session(autocommit=True)

    def _migrate(self):
        """Create the database tables if they do not exist."""
        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            CREATE SEQUENCE IF NOT EXISTS software_package_id_seq;
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS software_package (
                id INTEGER PRIMARY KEY DEFAULT NEXTVAL('software_package_id_seq') NOT NULL,
                name TEXT NOT NULL,
                vendor TEXT NOT NULL,
                alternative_names TEXT[] DEFAULT '{}',
                UNIQUE(name, vendor)
            )
            ''')
            cursor.execute('''
            CREATE SEQUENCE IF NOT EXISTS software_version_id_seq;
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS software_version (
                id INTEGER PRIMARY KEY DEFAULT NEXTVAL('software_version_id_seq') NOT NULL,
                software_package_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                internal_identifier TEXT NOT NULL,
                release_date TIMESTAMP NOT NULL,
                indexed TIMESTAMP,
                FOREIGN KEY(software_package_id) REFERENCES software_package(id) ON DELETE CASCADE,
                UNIQUE(software_package_id, internal_identifier)
            )
            ''')
            cursor.execute('''
            CREATE SEQUENCE IF NOT EXISTS static_file_id_seq;
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS static_file (
                id INTEGER PRIMARY KEY DEFAULT NEXTVAL('static_file_id_seq') NOT NULL,
                src_path TEXT NOT NULL,
                webroot_path TEXT NOT NULL,
                checksum BYTEA NOT NULL,
                UNIQUE(src_path, webroot_path, checksum)
            )
            ''')
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS
                static_file_webroot_path
            ON static_file(webroot_path)
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS static_file_use (
                software_version_id INTEGER NOT NULL,
                static_file_id INTEGER NOT NULL,
                FOREIGN KEY(software_version_id) REFERENCES software_version(id) ON DELETE CASCADE,
                FOREIGN KEY(static_file_id) REFERENCES static_file(id) ON DELETE CASCADE,
                PRIMARY KEY(software_version_id, static_file_id)
            )
            ''')
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS
                static_file_use_static_file_id
            ON static_file_use(static_file_id)
            ''')

    def _store_many(self, elements: List[Model]) -> Optional[List[bool]]:
        if not elements:
            return None
        model = type(elements[0])
        for elem in elements:
            if type(elem) != model:
                raise BackendException(
                    'bulk insertion is only supported for objects of the '
                    'same type')
        if model == SoftwareVersion:
            # inspection does not notice that this is indeed a List[SoftwareVersion]
            # noinspection PyTypeChecker
            self._store_many_software_versions(elements)
        elif model == StaticFile:
            # inspection does not notice that this is indeed a List[StaticFile]
            # noinspection PyTypeChecker
            self._store_many_static_files(elements)
        else:
            # implement actual bulk insertion for other model types
            return [
                self.store(elem)
                for elem in elements
            ]

    def _store_many_software_versions(self, versions: List[SoftwareVersion]):
        with closing(self._connection.cursor()) as cursor:
            query_values = []
            for software_version in versions:
                software_package_id = self._insert_software_package(
                    software_version.software_package)
                query_values.append(cursor.mogrify('''(
                        %(software_package_id)s,
                        %(name)s,
                        %(internal_identifier)s,
                        %(release_date)s
                    )''', {
                    'software_package_id': software_package_id,
                    'name': software_version.name,
                    'internal_identifier': software_version.internal_identifier,
                    'release_date': software_version.release_date
                }))
            cursor.execute(b'''
                INSERT
                INTO software_version (
                    software_package_id,
                    name,
                    internal_identifier,
                    release_date)
                VALUES ''' + b','.join(query_values) + b'''
                ON CONFLICT (software_package_id, internal_identifier) DO UPDATE
                    SET
                        name=EXCLUDED.name
                RETURNING id
                ''')
            for software_package, id in zip(versions, cursor.fetchall()):
                self._cache[software_package] = id

    def _store_many_static_files(self, static_files: List[StaticFile]):
        with closing(self._connection.cursor()) as cursor:
            query_values = []

            # add all static file objects to cache
            self._insert_raw_static_files(static_files)

            for static_file in static_files:
                software_version_id = self._insert_software_version(
                    static_file.software_version)
                static_file_id = self._get_or_create_static_file(static_file)
                query_values.append(
                    cursor.mogrify('(%s, %s)',
                                   (software_version_id, static_file_id)))
            cursor.execute(b'''
                INSERT
                INTO static_file_use (
                    software_version_id,
                    static_file_id)
                VALUES ''' + b','.join(query_values) + b'''
                ON CONFLICT DO NOTHING
                ''')

    def _insert_raw_static_files(self, static_files: List[StaticFile]) -> List[int]:
        """Get or insert multiple static files and get their ids."""
        with closing(self._connection.cursor()) as cursor:
            query_values = []
            for static_file in static_files:
                query_values.append(cursor.mogrify('(%s, %s, %s)', (
                    static_file.src_path,
                    static_file.webroot_path,
                    static_file.checksum)))
            cursor.execute(b'''
            INSERT
            INTO static_file (
                src_path,
                webroot_path,
                checksum)
            VALUES ''' + b','.join(query_values) + b'''
            ON CONFLICT
                (src_path, webroot_path, checksum)
                DO UPDATE
                SET "src_path"="static_file"."src_path"
            RETURNING id
            ''')
            result = []
            for static_file, id in zip(static_files, cursor.fetchall()):
                self._cache[static_file] = id
                result.append(id)
            return result

    @staticmethod
    def _pack_list(unpacked: list) -> object:
        # postgres has native list support
        return unpacked

    @staticmethod
    def _unpack_list(raw: Iterable) -> Iterable:
        # postgres has native list support
        return raw

    @staticmethod
    def _assert_valid_scan_identifier(identifier: str):
        assert all(
            c in ascii_letters + digits + '_' for c in identifier
        ), 'invalid identifier'
