import sqlite3

from contextlib import closing

from backends.backend import Backend
from backends.generic_db import GenericDatabaseBackend


class SqliteBackend(GenericDatabaseBackend):
    """The backend handling the SQLite communication."""
    _operator = '?'
    _true_value = '1'

    def _open_connection(self, *args, **kwargs):
        """Open a connection to the database."""
        self._connection = sqlite3.connect(*args, **kwargs)

        # Enable foreign keys
        with closing(self._connection.cursor()) as cursor:
            cursor.execute('PRAGMA foreign_keys = ON')

    def _migrate(self):
        """Create the database tables if they do not exist."""
        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS software_package (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                name TEXT NOT NULL,
                vendor TEXT NOT NULL,
                UNIQUE(name, vendor)
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS software_version (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                software_package_id INTEGER NOT NULL,
                identifier TEXT NOT NULL,
                indexed BOOLEAN DEFAULT 0,
                FOREIGN KEY(software_package_id) REFERENCES software_package(id),
                UNIQUE(software_package_id, identifier)
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS static_file (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
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
