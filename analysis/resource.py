import logging
from typing import Set, Union
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from analysis.wappalyzer_apps import wappalyzer_apps
from backends.software_version import SoftwareVersion
from settings import BACKEND, HTML_PARSER


class Resource:
    """
    A resource is any file which can be retrieved from a url.
    """
    # url: str

    def __init__(self, url: str):
        self.url = url

    def __eq__(self, other) -> bool:
        return self.url == other.url

    def __hash__(self) -> int:
        return hash(self.url)

    def __repr__(self) -> str:
        return "<{} '{}'>".format(str(self.__class__.__name__), str(self))

    def __str__(self) -> str:
        return self.url

    @property
    def content(self) -> bytes:
        if not self.retrieved:
            self.retrieve()

        return self._response.content

    def extract_information(self) -> Set[SoftwareVersion]:
        """
        Extract information from resource text source.
        """
        result = set()

        parsed = self._parse()

        # generator tag
        result |= self._extract_generator_tag(parsed)
        result |= self._extract_wappalyzer_information()

        return result

    @property
    def final_url(self) -> str:
        """The final url, i.e., the url of the resource after all redirects."""
        if not self.retrieved:
            self.retrieve()

        return self._response.url

    def retrieve(self):
        """Retrieve the resource from its url."""
        logging.info('Retrieving resource %s', self.url)

        self._response = requests.get(self.url)

        if self._response.status_code != 200:
            logging.info(
                'HTTP %s for %s',
                self._response.status_code,
                self.url)

    @property
    def retrieved(self) -> bool:
        """Whether the resource has already been retrieved."""
        return hasattr(self, '_response')

    @property
    def status_code(self) -> int:
        if not self.retrieved:
            self.retrieve()

        return self._response.status_code

    @property
    def success(self) -> bool:
        return self.status_code == 200

    @property
    def webroot_path(self):
        """Get the webroot path of this asset."""
        # TODO: Add support for subdirs And similar
        url = urlparse(self.url)
        return url.path

    @staticmethod
    def _extract_generator_tag(parsed: BeautifulSoup) -> Set[SoftwareVersion]:
        """Extract information from generator tag."""
        generator_tags = parsed.find_all('meta', {'name': 'generator'})
        if len(generator_tags) != 1:
            # If none or multiple generator tags are found, that is not a
            # reliable source
            return set()

        result = set()

        generator_tag = generator_tags[0].get('content')
        if not generator_tag:
            return set()

        components = generator_tag.split()
        # TODO: Maybe there is already a version in the generator tag ...
        # TODO: Therefore, do not throw non-first components away
        # TODO: Software packages with spaces in name
        matches = BACKEND.retrieve_packages_by_name(components[0])
        for match in matches:
            versions = BACKEND.retrieve_versions(match)
            matching_versions = versions.copy()
            if len(components) > 1:
                # generator tag might contain version information already.
                for version in versions:
                    if components[1].lower().strip() not in version.name.lower().strip():
                        matching_versions.remove(version)
                if not matching_versions:
                    # not a single version matched
                    matching_versions = versions
            result.update(matching_versions)

        logging.info('Generator tag suggests one of: %s', result)

        return result

    def _extract_wappalyzer_information(self) -> Set[SoftwareVersion]:
        """Use wappalyzer wrapper to get version information."""
        # TODO: maybe expansion to version is a bad idea, because packages with a lot of versions get a higher weight than those with only a few releases
        app_matches = set()
        version_matches = set()
        for app in wappalyzer_apps:
            if app.matches(self._response):
                app_matches.add(app)
                version_matches |= BACKEND.retrieve_versions(app.software_package)
        logging.info('wappalyzer suggests on of %s', app_matches)
        return version_matches

    def _parse(self) -> BeautifulSoup:
        return BeautifulSoup(
            self.content,
            HTML_PARSER)
