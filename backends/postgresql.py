import psycopg2

from contextlib import closing

from backends.backend import Backend
from backends.generic_db import use_cache, GenericDatabaseBackend
from backends.model import Model
from backends.software_package import SoftwarePackage
from backends.software_version import SoftwareVersion
from backends.static_file import StaticFile


class PostgresqlBackend(GenericDatabaseBackend):
    """The backend handling the SQLite communication."""
    _operator = '%s'
    _true_value = 'true'

    def store(self, element: Model) -> bool:
        """
        Insert or update an instance of a Model subclass.

        Returns whether a change has been made.
        For postgres, return value is not always accurate.
        """
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
                vendor)
            VALUES (
                %s,
                %s)
            ON CONFLICT (name, vendor) DO UPDATE
                SET vendor=software_package.vendor
            RETURNING id
            ''', (software_package.name, software_package.vendor))
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
                indexed BOOLEAN DEFAULT 'f',
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
