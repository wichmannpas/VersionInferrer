import os
from typing import Set
from urllib.parse import urlparse

import requests
from requests import Response
from bs4 import BeautifulSoup, SoupStrainer

from analysis.asset import Asset
from backends.software_package import SoftwarePackage
from base.checksum import calculate_checksum
from settings import BACKEND, HTML_PARSER, HTML_RELEVANT_ELEMENTS, \
    STATIC_FILE_EXTENSIONS, SUPPORTED_SCHEMES


def extract_information(html_page: str) -> Set[SoftwarePackage]:
    """Extract information from html source."""
    result = set()

    parsed = BeautifulSoup(
        html_page,
        HTML_PARSER)

    # generator tag
    generator_tags = parsed.find_all('meta', {'name': 'generator'})
    if len(generator_tags) == 1:
        # If none or multiple generator tags are found, that is not a
        # reliable source
        generator_tag = generator_tags[0].get('content')
        if generator_tag:
            components = generator_tag.split()
            # TODO: Maybe there is already a version in the generator tag ...
            # TODO: Therefore, do not throw non-first components away
            # TODO: Software packages with spaces in name
            matches = BACKEND.retrieve_packages_by_name(components[0])
            for match in matches:
                result.add(match)

    return result


def retrieve_included_assets(response: Response) -> Set[Asset]:
    """Fetch included static files from provided html page."""
    main_page = BeautifulSoup(
        response.text,
        HTML_PARSER,
        parse_only=SoupStrainer(
            HTML_RELEVANT_ELEMENTS))

    referenced_urls = set()

    for elem in main_page:
        href = elem.get('href')
        if href:
            referenced_urls.add(href)

        src = elem.get('src')
        if src:
            referenced_urls.add(src)

    assets = set()
    for referenced_url in referenced_urls:
        parsed_url = urlparse(referenced_url)
        if (parsed_url.scheme and
                parsed_url.scheme not in SUPPORTED_SCHEMES) or \
           not any(parsed_url.path.endswith(extension)
                   for extension in STATIC_FILE_EXTENSIONS):
            continue
        if not parsed_url.scheme:
            # url is relative.
            referenced_url = _join_url(response.url, referenced_url)
        assets.add(retrieve_asset(referenced_url))

    return assets


def retrieve_asset(url: str) -> Asset:
    """Retrieve a single asset."""
    asset_content = requests.get(url).content
    return Asset(
        url,
        calculate_checksum(asset_content))


def _join_url(*args) -> str:
    """
    Join multiple paths using os.path.join, remove leading slashes
    before.
    """
    url = args[0]
    if url.endswith('/'):
        url = url[:-1]
    return url + os.path.join(args[1], *(
        arg[1:]
        if arg.startswith('/') else arg
        for arg in args[2:]))
