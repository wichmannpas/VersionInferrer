from abc import abstractmethod, abstractstaticmethod
from contextlib import closing
from typing import Iterable, List, Set, Tuple, Union

from backends.backend import Backend, BackendException
from backends.model import Model
from backends.software_package import SoftwarePackage
from backends.software_version import SoftwareVersion
from backends.static_file import StaticFile


def use_cache(f):
    def decorated(*args, **kwargs):
        self = args[0]
        element = args[1]
        if element in self._cache:
            return self._cache[element]
        elem_id = f(*args, **kwargs)
        if elem_id is not None:
            self._cache[element] = elem_id
        return elem_id
    return decorated


class GenericDatabaseBackend(Backend):
    """The backend handling the SQLite communication."""
    # _operator: str
    # _true_value: str

    def __init__(self, *args, **kwargs):
        self._cache = {}

        self._open_connection(*args, **kwargs)

        # Ensure database is initialized
        self._migrate()

    def __del__(self):
        self._connection.close()

    def delete(self, element: Model) -> bool:
        """Delete an instance of a Model subclass."""
        if isinstance(element, SoftwareVersion):
            id = self._get_id(element)
            if id is None:
                return False
            with closing(self._connection.cursor()) as cursor:
                # Check whether element exists
                cursor.execute('''
                DELETE
                FROM software_version
                WHERE
                    id = ''' + self._operator + '''
                ''', (id,))
                return True
        raise BackendException('unsupported model type for deletion')

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

    def retrieve_packages(self) -> Set[SoftwarePackage]:
        """Retrieve all available packages."""
        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            SELECT
                name,
                vendor,
                alternative_names
            FROM
                software_package
            ''', ())
            return {
                SoftwarePackage(
                    name=name, vendor=vendor,
                    alternative_names=self._unpack_list(alternative_names))
                for name, vendor, alternative_names in cursor.fetchall()}

    def retrieve_packages_by_name(
            self, name: str) -> Set[SoftwarePackage]:
        """Retrieve all available packages whose names are likely to name."""
        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            SELECT
                name,
                vendor,
                alternative_names
            FROM
                software_package
            WHERE
                LOWER(name) LIKE LOWER(''' + self._operator + ''')
            ''', (name,))
            return {
                SoftwarePackage(
                    name=name, vendor=vendor,
                    alternative_names=self._unpack_list(alternative_names))
                for name, vendor, alternative_names in cursor.fetchall()}

    def retrieve_static_files_almost_unique_to_version(
            self, version: SoftwareVersion,
            max_users: int) -> Set[Tuple[Set[SoftwareVersion], StaticFile]]:
        """
        Get all static files which are used by the specified version and
        in total by max_users versions or less.

        Return a set of using versions for every retrieved static file.
        """
        return {
            (frozenset(self._retrieve_static_file_users(static_file_id)),
             StaticFile(
                 version,
                 src_path,
                 webroot_path,
                 self._unpack_binary(checksum)))
            for static_file_id, src_path, webroot_path, checksum
            in self._retrieve_static_files_by_version(version, max_users)}

    def retrieve_static_files_popular_to_versions(
            self, versions: Iterable[SoftwareVersion],
            limit: int) -> Set[Tuple[Set[SoftwareVersion], StaticFile]]:
        """
        Get the static files most popular for versions.

        Return a set of using versions (of specified versions) for every
        retrieved static file.
        """
        with closing(self._connection.cursor()) as cursor:
            operators, list_params = self._expand_list_operators(self._get_id(version) for version in versions)
            cursor.execute('''
            SELECT
                sf.id,
                sf.src_path,
                sf.webroot_path,
                sf.checksum,
                (SELECT
                    COUNT(us.software_version_id)
                 FROM
                     static_file_use us
                 WHERE
                     us.static_file_id=sf.id AND
                     us.software_version_id IN ''' +
                     operators +
                     ''') vu
                 FROM
                     static_file sf
                 WHERE
                     EXISTS (
                         SELECT
                             1
                         FROM
                             static_file_use us
                         WHERE
                             us.static_file_id=sf.id)
                 ORDER BY
                     vu DESC
                 LIMIT ''' + self._operator + '''
            ''', tuple(list_params + [limit]))
            return {
                (frozenset(user
                           for user
                           in self._retrieve_static_file_users(static_file_id)
                           if user in versions),
                 StaticFile(
                     None,
                     src_path,
                     webroot_path,
                     self._unpack_binary(checksum)))
                for static_file_id, src_path, webroot_path, checksum, users
                in cursor.fetchall()}

    def retrieve_static_files_unique_to_version(
            self, version: SoftwareVersion) -> Set[StaticFile]:
        """
        Get all static files which are only used by the specified version.
        """
        return {
            StaticFile(
                version,
                src_path,
                webroot_path,
                self._unpack_binary(checksum))
            for static_file_id, src_path, webroot_path, checksum
            in self._retrieve_static_files_by_version(version)}

    def retrieve_static_file_users_by_checksum(
            self, checksum: bytes) -> Set[SoftwareVersion]:
        """Retrieve all versions using a static file with a specific checksum."""
        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            SELECT
                p.name,
                p.vendor,
                p.alternative_names,
                v.name,
                v.internal_identifier,
                v.release_date
            FROM
                software_package p,
                software_version v
            WHERE
                v.software_package_id = p.id AND
                v.id IN
                    (SELECT
                         software_version_id
                     FROM
                         static_file_use
                     WHERE
                         static_file_id IN
                             (SELECT
                                  id
                              FROM
                                  static_file sf
                              WHERE
                                  sf.checksum=''' + self._operator + '''))
            ''', (checksum,))
            return self._get_software_versions_from_raw(cursor.fetchall())

    def retrieve_static_file_users_by_webroot_paths(
            self, webroot_path: str) -> Set[SoftwareVersion]:
        """Retrieve all versions providing a static file at the specified path."""
        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            SELECT
                p.name,
                p.vendor,
                p.alternative_names,
                v.name,
                v.internal_identifier,
                v.release_date
            FROM
                software_package p,
                software_version v
            WHERE
                v.software_package_id = p.id AND
                v.id IN
                    (SELECT
                         software_version_id
                     FROM
                         static_file_use
                     WHERE
                         static_file_id IN
                             (SELECT
                                  id
                              FROM
                                  static_file sf
                              WHERE
                                  sf.webroot_path=''' + self._operator + '''))
            ''', (webroot_path,))
            return self._get_software_versions_from_raw(cursor.fetchall())

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
                name,
                internal_identifier,
                release_date
            FROM software_version
            WHERE
                software_package_id=''' + self._operator + '''
            '''
            if indexed_only:
                query += 'AND indexed=' + self._true_value
            cursor.execute(query, (software_package_id,))

            return {
                SoftwareVersion(
                    software_package,
                    name=name,
                    internal_identifier=internal_identifier,
                    release_date=release_date)
                for name, internal_identifier, release_date in cursor.fetchall()}

    def retrieve_webroot_paths_with_high_entropy(
            self, software_versions: Iterable[SoftwareVersion],
            limit: int, exclude: Iterable[str] = '') -> List[Tuple[str, int, int]]:
        """
        Retrieve a list of webroot paths which have a high entropy
        among the specified software versions.

        A 3-tuple of the webroot path, the number of users within
        the set of versions, and the number of different checksums
        is returned.
        """
        software_version_ids = set()
        for version in software_versions:
            version_id = self._get_id(version)
            if version_id is None:
                raise BackendException('software version not found')
            software_version_ids.add(version_id)

        if not software_version_ids:
            # no versions to check.
            return []

        with closing(self._connection.cursor()) as cursor:
            software_version_ids = tuple(software_version_ids)
            list_operators, params = self._expand_list_operators(software_version_ids)
            query = '''
            SELECT
                subquery.webroot_path,
                subquery.version_count,
                subquery.checksum_count
            FROM (
                SELECT
                    sf.webroot_path,
                    COUNT(DISTINCT us.software_version_id) version_count,
                    COUNT(DISTINCT sf.checksum) checksum_count
                FROM
                    static_file sf
                JOIN
                    static_file_use us
                ON
                    us.static_file_id=sf.id
                WHERE
                    us.software_version_id IN ''' + list_operators
            exclude = tuple(exclude)
            if exclude:
                operators, new_params = self._expand_list_operators(exclude)
                query += 'AND sf.webroot_path NOT IN ' + operators
                params.extend(new_params)
            query += '''
                GROUP BY
                    sf.webroot_path) subquery
            WHERE
                NOT (
                    subquery.version_count = ''' + str(int(len(software_version_ids))) + ''' AND
                    subquery.checksum_count = 1)
            ORDER BY
                (subquery.version_count + subquery.checksum_count) DESC
            LIMIT ''' + str(int(limit)) + '''
            '''
            cursor.execute(query, tuple(params))

            return cursor.fetchall()

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

    def store(self, element: Union[Model, List[Model]]) -> bool:
        """
        Insert or update an instance or multiple instances of a Model
        subclass.

        Returns whether a change has been made.
        """
        if isinstance(element, list):
            # TODO: use actual bulk insert on database level
            return [
                self.store(elem)
                for elem in element
            ]
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
                    vendor,
                    alternative_names)
                VALUES (
                    ''' + self._operator + ''',
                    ''' + self._operator + ''',
                    ''' + self._operator + ''')
                ''', (element.name,
                      element.vendor,
                      self._pack_list(element.alternative_names)))
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
                    internal_identifier=''' + self._operator + '''
                ''', (software_package_id, element.internal_identifier))

                if cursor.fetchone()[0]:
                    # software version exists already
                    return False

                # Insert new element
                cursor.execute('''
                INSERT
                INTO software_version (
                    software_package_id,
                    name,
                    internal_identifier,
                    release_date)
                VALUES (
                    ''' + self._operator + ''',
                    ''' + self._operator + ''',
                    ''' + self._operator + ''',
                    ''' + self._operator + ''')
                ''', (software_package_id, element.name,
                      element.internal_identifier, element.release_date))
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

    @use_cache
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
                    internal_identifier=''' + self._operator + '''
                ''', (software_package_id, element.internal_identifier))
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

    def _retrieve_static_file_users(
            self, static_file_id: int) -> Set[SoftwareVersion]:
        """Retrieve all versions using a static file."""
        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            SELECT
                p.name,
                p.vendor,
                p.alternative_names,
                v.name,
                v.internal_identifier,
                v.release_date
            FROM
                software_package p,
                software_version v
            WHERE
                v.software_package_id = p.id AND
                v.id IN
                    (SELECT
                         software_version_id
                     FROM
                         static_file_use
                     WHERE
                         static_file_id=''' + self._operator + ''')
            ''', (static_file_id,))
            return self._get_software_versions_from_raw(cursor.fetchall())

    def _retrieve_static_files_by_version(self, version: SoftwareVersion,
                                          max_users: int = 1):
        with closing(self._connection.cursor()) as cursor:
            cursor.execute('''
            SELECT
                sf.id,
                sf.src_path,
                sf.webroot_path,
                sf.checksum
            FROM
                static_file sf
            WHERE
                EXISTS
                (
                    SELECT
                        1
                    FROM
                        static_file_use us
                    WHERE
                        us.static_file_id=sf.id AND
                        us.software_version_id=''' + self._operator + ''') AND
                (
                    SELECT
                        COUNT(us.software_version_id)
                    FROM
                        static_file_use us
                    WHERE
                        us.static_file_id=sf.id)<=''' + self._operator + '''
            ''', (self._get_id(version), max_users))
            return cursor.fetchall()

    @staticmethod
    def _get_software_versions_from_raw(
            raw: Iterable) -> Set[SoftwareVersion]:
        return {
            SoftwareVersion(
                software_package=SoftwarePackage(
                    name=p_name,
                    vendor=p_vendor,
                    alternative_names=GenericDatabaseBackend._unpack_list(p_alternative_names)),
                name=v_name,
                internal_identifier=v_internal_identifier,
                release_date=v_release_date)
            for p_name, p_vendor, p_alternative_names, v_name, \
                v_internal_identifier, v_release_date
            in raw
        }

    @abstractmethod
    def _open_connection(self, *args, **kwargs):
        """Open a connection to the database."""

    @staticmethod
    def _unpack_binary(obj) -> bytes:
        """
        Unpack binary object and return bytes.

        It is bytes for sqlite and memoryview for psycopg2, for example.
        """
        if isinstance(obj, memoryview):
            return obj.tobytes()
        return obj

    @abstractstaticmethod
    def _pack_list(unpacked: list) -> object:
        """Pack a list for the database."""

    @abstractstaticmethod
    def _unpack_list(raw: object) -> list:
        """Unpack a list from the database."""

    def _expand_list_operators(self, params: Iterable) -> Tuple[str, list]:
        """Generate operator string and parameter list for a sql list."""
        return self._operator, [tuple(params)]
