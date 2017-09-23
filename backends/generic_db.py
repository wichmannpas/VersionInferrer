from abc import abstractmethod
from contextlib import closing
from typing import Set, Union

from backends.backend import Backend, BackendException
from backends.model import Model
from backends.software_package import SoftwarePackage
from backends.software_version import SoftwareVersion
from backends.static_file import StaticFile


def use_id_cache(f):
    def decorated(*args, **kwargs):
        self = args[0]
        element = args[1]
        if element in self._id_cache:
            return self._id_cache[element]
        elem_id = f(*args, **kwargs)
        if elem_id is not None:
            self._id_cache[element] = elem_id
        return elem_id
    return decorated


class GenericDatabaseBackend(Backend):
    """The backend handling the SQLite communication."""
    _operator: str

    def __init__(self, *args, **kwargs):
        self._id_cache = {}

        self._open_connection(*args, **kwargs)

        # Ensure database is initialized
        self._migrate()

    def __del__(self):
        self._connection.close()

    def mark_indexed(self, software_version: SoftwareVersion, indexed: bool = True) -> bool:
        """Mark a software version as fully indexed. """
        software_version_id = self._get_id(software_version)
        if software_version_id is None:
            raise BackendException(
                'software version does not exist in database')
        with closing(self._connection.cursor()) as cursor:
            # Insert new element
            cursor.execute('''
            UPDATE
                software_version
            SET
                indexed=''' + self._operator + '''
            WHERE
                id=''' + self._operator + '''
            ''', (indexed, software_version_id,))

    @abstractmethod
    def _open_connection(self, *args, **kwargs):
        """Open a connection to the database."""

    def retrieve_versions(
            self, software_package: SoftwarePackage,
            indexed_only: bool = True) -> Set[SoftwareVersion]:
        """Retrieve all available versions for specified software package. """
        software_package_id = self._get_id(software_package)
        if software_package_id is None:
            raise BackendException('software package not stored')

        with closing(self._connection.cursor()) as cursor:
            query = '''
            SELECT
                identifier
            FROM software_version
            WHERE
                software_package_id=''' + self._operator + '''
            '''
            if indexed_only:
                query += 'AND indexed=true'
            cursor.execute(query, (software_package_id,))

            return set(SoftwareVersion(software_package, row[0])
                       for row in cursor.fetchall())

    def static_file_count(self, software_version: SoftwareVersion) -> int:
        """Get the count of static files used by a software version. """
        software_version_id = self._get_id(software_version)
        if software_version_id is None:
            raise BackendException('software version not stored')

        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            SELECT
                COUNT(*)
            FROM static_file_use
            WHERE
                software_version_id=''' + self._operator + '''
            ''', (software_version_id,))

            row = cursor.fetchone()
            if row:
                return row[0]
            return 0

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
                    ''' + self._operator + ''',
                    ''' + self._operator + ''')
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
                    software_package_id=''' + self._operator + ''' AND
                    identifier=''' + self._operator + '''
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
                    ''' + self._operator + ''',
                    ''' + self._operator + ''')
                ''', (software_package_id, element.identifier))
                return True
        elif isinstance(element, StaticFile):
            software_version_id = self._get_id(
                element.software_version)
            if software_version_id is None:
                # Software version not yet stored.
                self.store(element.software_version)
                software_version_id = self._get_id(
                    element.software_version)
            static_file_id = self._get_or_create_static_file(element)
            with closing(self._connection.cursor()) as cursor:
                # Check whether element exists
                cursor.execute('''
                SELECT
                    COUNT(*)
                FROM static_file_use
                WHERE
                    software_version_id=''' + self._operator + ''' AND
                    static_file_id=''' + self._operator + '''
                ''', (software_version_id, static_file_id))

                if cursor.fetchone()[0]:
                    # static file use exists already
                    return False

                # Insert new element
                cursor.execute('''
                INSERT
                INTO static_file_use (
                    software_version_id,
                    static_file_id)
                VALUES (
                    ''' + self._operator + ''',
                    ''' + self._operator + ''')
                ''', (
                    software_version_id,
                    static_file_id))
                return True
        raise BackendException('unsupported model type')

    @use_id_cache
    def _get_id(self, element: Model) -> Union[int, None]:
        """Get the id of a model instance if it exists and has an id field."""
        if isinstance(element, SoftwarePackage):
            with closing(self._connection.cursor()) as cursor:
                cursor.execute('''
                SELECT id
                FROM software_package
                WHERE
                    name=''' + self._operator + ''' AND
                    vendor=''' + self._operator + '''
                ''', (element.name, element.vendor))
                row = cursor.fetchone()
                return row[0] if row is not None else None
        elif isinstance(element, SoftwareVersion):
            software_package_id = self._get_id(element.software_package)
            if software_package_id is None:
                return None
            with closing(self._connection.cursor()) as cursor:
                cursor.execute('''
                SELECT id
                FROM software_version
                WHERE
                    software_package_id=''' + self._operator + ''' AND
                    identifier=''' + self._operator + '''
                ''', (software_package_id, element.identifier))
                row = cursor.fetchone()
                return row[0] if row is not None else None
        elif isinstance(element, StaticFile):
            with closing(self._connection.cursor()) as cursor:
                cursor.execute('''
                SELECT id
                FROM static_file
                WHERE
                    src_path=''' + self._operator + ''' AND
                    webroot_path=''' + self._operator + ''' AND
                    checksum=''' + self._operator + '''
                ''', (element.src_path, element.webroot_path, element.checksum))
                row = cursor.fetchone()
                return row[0] if row is not None else None
        raise BackendException(
            'unsupported model type for id lookup: {}'.format(type(element)))

    def _get_or_create_static_file(self, static_file: StaticFile) -> id:
        """Get or create a static file element an return its id."""
        static_file_id = self._get_id(static_file)
        if static_file_id:
            return static_file_id
        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            INSERT
            INTO static_file (
                src_path,
                webroot_path,
                checksum)
            VALUES(
                ''' + self._operator + ''',
                ''' + self._operator + ''',
                ''' + self._operator + ''')
            ''', (
                static_file.src_path,
                static_file.webroot_path,
                static_file.checksum))
        return self._get_id(static_file)
