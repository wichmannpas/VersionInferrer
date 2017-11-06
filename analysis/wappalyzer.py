"""
This is a wrapper module around Wappalyzer
(https://github.com/AliasIO/Wappalyzer).
It uses the apps.json provided by the wappalyzer project in order to
get first estimates for a website.
The specification of the apps.json file can be found at
https://wappalyzer.com/docs.
"""

import re
from typing import List

from bs4 import BeautifulSoup
from requests import Response

from backends.software_package import SoftwarePackage
from settings import HTML_PARSER


class WappalyzerApp:
    """
    This represents a wappalyzer-supported app.
    """
    def __init__(self, software_package: SoftwarePackage, raw_data: dict):
        self.software_package = software_package
        self._raw_data = raw_data

    def _eq__(self, other) -> bool:
        return self.software_package == other.software_package

    def __hash__(self) -> int:
        return hash(self.software_package)

    def __str__(self) -> str:
        return str(self.software_package)

    def __repr__(self) -> str:
        return "<{} '{}'>".format(str(self.__class__.__name__), str(self))

    def matches(self, response: Response) -> bool:
        """Check whether response possibly matches this app."""
        return (
            self._check_headers(response) or
            self._check_meta(response) or
            self._check_html(response) or
            self._check_scripts(response)
        )

    def _check_headers(self, response: Response) -> bool:
        header_patterns = self._raw_data.get('headers', {}).items()
        return any(
            re.match(pat_value, value, re.IGNORECASE)
            for pat_name, pat_value in header_patterns
            for name, value in response.headers.items()
            if pat_name.lower() == name.lower())

    def _check_html(self, response: Response) -> bool:
        html_patterns = self._get_category('html')
        return any(
            re.search(pattern, response.text, re.IGNORECASE)
            for pattern in html_patterns)

    def _check_meta(self, response: Response) -> bool:
        meta_patterns = self._raw_data.get('meta', {}).items()
        meta_tags = self._parse(response).find_all('meta')
        return any(
            re.match(
                pat_content,
                tag.get('content', ''),
                re.IGNORECASE)
            for pat_name, pat_content in meta_patterns
            for tag in meta_tags
            if pat_name.lower() == tag.get('name', '').lower())

    def _check_scripts(self, response: Response) -> bool:
        script_patterns = self._get_category('script')
        script_urls = self._parse(response).find_all('script')
        return any(
            re.search(
                pattern,
                script_tag.get('src', ''),
                re.IGNORECASE)
            for pattern in script_patterns
            for script_tag in script_urls)

    def _get_category(self, category: str) -> List[str]:
        """
        The apps.json contains strings for single-element values and list
        of strings for multi-element values. This returns a list for all.
        """
        data = self._raw_data.get(category)
        if not data:
            return []
        if isinstance(data, List):
            return data
        return [data]

    @staticmethod
    def _parse(response: Response) -> BeautifulSoup:
        return BeautifulSoup(
            response.text,
            HTML_PARSER)
