import psycopg2

from contextlib import closing

from backends.backend import Backend
from backends.generic_db import GenericDatabaseBackend


class PostgresqlBackend(GenericDatabaseBackend):
    """The backend handling the SQLite communication."""
    _operator = '%s'

    def _open_connection(self, *args, **kwargs):
        """Open a connection to the database."""
        self._connection = psycopg2.connect(*args, **kwargs)

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
                identifier TEXT NOT NULL,
                indexed BOOLEAN DEFAULT 'f',
                FOREIGN KEY(software_package_id) REFERENCES software_package(id),
                UNIQUE(software_package_id, identifier)
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
                checksum TEXT NOT NULL
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS static_file_use (
                software_version_id INTEGER NOT NULL,
                static_file_id INTEGER NOT NULL,
                FOREIGN KEY(software_version_id) REFERENCES software_version(id),
                FOREIGN KEY(static_file_id) REFERENCES static_file(id),
                PRIMARY KEY(software_version_id, static_file_id)
            )
            ''')
