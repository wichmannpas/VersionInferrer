from typing import Set
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, SoupStrainer

from analysis.asset import Asset
from base.checksum import calculate_checksum
from settings import HTML_PARSER, HTML_RELEVANT_ELEMENTS, \
    STATIC_FILE_EXTENSIONS, SUPPORTED_SCHEMAS


def retrieve_included_assets(url: str) -> Set[Asset]:
    """Retrieve specified url and fetch included static files."""
    main_page = requests.get(url).text
    main_page = BeautifulSoup(
        main_page,
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
        if not any(referenced_url.startswith(schema)
                   for schema in SUPPORTED_SCHEMAS) or \
            not any(parsed_url.path.endswith(extension)
                    for extension in STATIC_FILE_EXTENSIONS):
            continue
        assets.add(retrieve_asset(referenced_url))

    return assets


def retrieve_asset(url: str) -> Asset:
    """Retrieve a single asset."""
    asset_content = requests.get(url).content
    return Asset(
        url,
        calculate_checksum(asset_content))
