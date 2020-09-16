import os
import re
import tarfile
from datetime import datetime
from pathlib import Path
from subprocess import check_call
from typing import Callable, Set, Union

import requests

from backends.software_package import SoftwarePackage
from backends.software_version import SoftwareVersion
from providers.provider import Provider

PACKAGE_PATTERN = re.compile(
    r'Package:\s*(?P<name>[\w-]+).*?Version:\s*(?P<version>.*?)\n.*?\s*Filename:\s*(?P<filename>.*?)\n',
    re.DOTALL)


class DebRepositoryProvider(Provider):
    """
    A provider for a DEB (debian) repository.
    """

    def __init__(self, software_package: SoftwarePackage,
                 repo_base_url: str, repo_packages_path: str, repo_package: str,
                 version_name_derivator: Union[Callable[[str], str], None] = None):
        super().__init__(software_package, version_name_derivator)
        self.repo_base_url = repo_base_url
        self.repo_packages_path = repo_packages_path
        self.repo_package = repo_package

    def get_versions(self) -> Set[SoftwareVersion]:
        packages = self._read_packages()
        return {
            SoftwareVersion(
                software_package=self.software_package,
                name=version,
                internal_identifier=version,
                # TODO: release date not contained within PACKAGES file!
                release_date=datetime.min)
            for version in packages.keys()
        }

    def list_files(self, version: SoftwareVersion):
        self._download_deb_data(version)

        with tarfile.open(self._cache_data_path(version)) as data_file:
            return [
                Path(member.name).as_posix()
                for member in data_file.getmembers()
                if member.isfile()
            ]

    def get_file_data(self, version: SoftwareVersion, path: str):
        self._download_deb_data(version)

        with tarfile.open(self._cache_data_path(version)) as data_file:
            return data_file.extractfile('./' + path).read()

    def _read_packages(self) -> dict:
        if not hasattr(self, '_cached_packages'):
            response = requests.get(self.repo_packages_url)
            self._cached_packages = {}
            for package in PACKAGE_PATTERN.finditer(response.text):
                package = package.groupdict()
                if package['name'] != self.repo_package:
                    continue
                self._cached_packages[package['version']] = package['filename']
        return self._cached_packages

    @property
    def repo_packages_url(self):
        return os.path.join(self.repo_base_url + self.repo_packages_path)

    def _download_deb_data(self, version: SoftwareVersion):
        """
        Download version's DEB file and extract data.tar.gz if it does not exist in cache.
        """
        cache_deb_path = self._cache_deb_path(version)
        cache_data_path = self._cache_data_path(version)

        if cache_data_path.exists():
            return

        if not cache_deb_path.exists():
            packages = self._read_packages()
            deb_path = packages.get(version.internal_identifier)
            assert deb_path, 'version %s not known in repo PACKAGES file' % version.internal_identifier
            deb_url = self.repo_base_url + deb_path
            cache_deb_path.parent.mkdir(parents=True, exist_ok=True)
            with cache_deb_path.open('wb') as deb_file, requests.get(deb_url, stream=True) as deb_stream:
                deb_stream.raise_for_status()
                for chunk in deb_stream.iter_content(chunk_size=10000):
                    deb_file.write(chunk)

        with cache_data_path.open('wb') as data_file:
            check_call((
                'ar',
                'p',
                cache_deb_path.as_posix(),
                'data.tar.gz',
            ), stdout=data_file)

        # remove deb file
        cache_deb_path.unlink()

    def _cache_deb_path(self, version) -> Path:
        # TODO: remove unsafe characters from internal identifier
        return Path(self.cache_directory) / (version.internal_identifier + '.deb')

    def _cache_data_path(self, version) -> Path:
        # TODO: remove unsafe characters from internal identifier
        return Path(self.cache_directory) / (version.internal_identifier + '.tar.gz')
