import json
import sqlite3

from contextlib import closing
from typing import Iterable, Tuple

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
                alternative_names TEXT DEFAULT '[]',
                UNIQUE(name, vendor)
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS software_version (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                software_package_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                internal_identifier TEXT NOT NULL,
                release_date DATETIME,
                indexed BOOLEAN DEFAULT 0,
                FOREIGN KEY(software_package_id) REFERENCES software_package(id),
                UNIQUE(software_package_id, internal_identifier)
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS static_file (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                src_path TEXT NOT NULL,
                webroot_path TEXT NOT NULL,
                checksum BINARY NOT NULL
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
                FOREIGN KEY(software_version_id) REFERENCES software_version(id),
                FOREIGN KEY(static_file_id) REFERENCES static_file(id),
                PRIMARY KEY(software_version_id, static_file_id)
            )
            ''')
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS
                static_file_use_static_file_id
            ON static_file_use(static_file_id)
            ''')

    @staticmethod
    def _pack_list(unpacked: list) -> object:
        return json.dumps(unpacked)

    @staticmethod
    def _unpack_list(raw: object) -> list:
        return json.loads(raw)

    def _expand_list_operators(self, params: Iterable) -> Tuple[str, list]:
        """
        Generate operator string and parameter list for a sql list.
        Sqlite requires many single parameters.
        """
        params = list(params)
        operators = ', '.join([self._operator] * len(params))
        return '(' + operators + ')', list(params)
