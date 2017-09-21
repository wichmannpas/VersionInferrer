import sqlite3

from contextlib import closing
from typing import Set, Union

from backends.backend import Backend, BackendException
from backends.model import Model
from backends.software_package import SoftwarePackage
from backends.software_version import SoftwareVersion


class SqliteBackend(Backend):
    """The backend handling the SQLite communication."""
    def __init__(self, path: str):
        self._connection = sqlite3.connect(path)

        # Enable foreign keys
        with closing(self._connection.cursor()) as cursor:
            cursor.execute('PRAGMA foreign_keys = ON')

        # Ensure database is initialized
        self._migrate()

    def __del__(self):
        self._connection.close()

    def retrieve_versions(
            self, software_package: SoftwarePackage) -> Set[SoftwareVersion]:
        """Retrieve all available versions for specified software package. """
        software_package_id = self._get_id(software_package)
        if software_package_id is None:
            raise BackendException('software package not stored')

        with closing(self._connection.cursor()) as cursor:
            # Insert new element
            cursor.execute('''
            SELECT
                identifier
            FROM software_version
            WHERE
                software_package_id=?
            ''', (software_package_id,))

            return set(SoftwareVersion(software_package, row[0])
                    for row in cursor.fetchall())

    def store(self, element: Model) -> bool:
        """
        Insert or update an instance of a Model subclass.

        Returns whether a change has been made.
        """
        if isinstance(element, SoftwarePackage):
            if self._get_id(element) is not None:
                # software package exists already
                return False

            with closing(self._connection.cursor()) as cursor:
                # Insert new element
                cursor.execute('''
                INSERT
                INTO software_package (
                    name,
                    vendor)
                VALUES (
                    ?,
                    ?)
                ''', (element.name, element.vendor))
                return True
        elif isinstance(element, SoftwareVersion):
            software_package_id = self._get_id(element.software_package)
            if software_package_id is None:
                # Software package not yet stored.
                self.store(element.software_package)
                software_package_id = self._get_id(element.software_package)
            with closing(self._connection.cursor()) as cursor:
                # Check whether element exists
                cursor.execute('''
                SELECT
                    COUNT(*)
                FROM software_version
                WHERE
                    software_package_id=? AND
                    identifier=?
                ''', (software_package_id, element.identifier))

                if cursor.fetchone()[0]:
                    # software version exists already
                    return False

                # Insert new element
                cursor.execute('''
                INSERT
                INTO software_version (
                    software_package_id,
                    identifier)
                VALUES (
                    ?,
                    ?)
                ''', (software_package_id, element.identifier))
                return True
        raise BackendException('unsupported model type')

    def _get_id(self, element: Model) -> Union[int, None]:
        """Get the id of a model instance if it exists and has an id field."""
        if isinstance(element, SoftwarePackage):
            with closing(self._connection.cursor()) as cursor:
                cursor.execute('''
                SELECT id
                FROM software_package
                WHERE
                    name=? AND
                    vendor=?
                ''', (element.name, element.vendor))
                row = cursor.fetchone()
                return row[0] if row is not None else None
        raise BackendException('unsupported model type for id lookup')


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
                software_package_id INTEGER NOT NULL,
                identifier TEXT NOT NULL,
                PRIMARY KEY(software_package_id, identifier),
                FOREIGN KEY(software_package_id) REFERENCES software_package(id),
                UNIQUE(software_package_id, identifier)
            )
            ''')
