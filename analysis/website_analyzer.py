import logging
from typing import FrozenSet, Set
from urllib.parse import urlparse

from bs4 import BeautifulSoup, SoupStrainer

from analysis.asset import Asset
from analysis.resource import Resource
from base.utils import join_url
from settings import BACKEND, HTML_PARSER, HTML_RELEVANT_ELEMENTS, \
    STATIC_FILE_EXTENSIONS, SUPPORTED_SCHEMES

class WebsiteAnalyzer:
    """
    This class provides the website analyzer. It is used to analyze a
    single website to detect software packages and versions.
    """
    primary_url: str
    retrieved_assets: FrozenSet[Asset]
    retrieved_resources: Set[Resource]

    def __init__(self, primary_url: str):
        self.primary_url = primary_url
        self.retrieved_resources = set()

    def analyze(self):
        """Analyze the website."""
        main_page = Resource(self.primary_url)
        self.retrieved_resources.add(main_page)

        first_estimates = main_page.extract_information()

        main_assets = self.retrieve_included_assets(main_page)
        candidates = set()
        for asset in main_assets:
            candidates.update(
                BACKEND.retrieve_static_file_users_by_checksum(asset.checksum))

        logging.info('assets from primary page lead to candidates: %s', candidates)

        # TODO: do not just throw all of them together
        candidates |= first_estimates

        # TODO: make sure that no assets are fetched multiple times
        assets_with_entropy = BACKEND.retrieve_webroot_paths_with_high_entropy(
            candidates, 5)
        print(assets_with_entropy)
        for webroot_path, using_versions, different_cheksums in assets_with_entropy:
            url = join_url(self.primary_url, webroot_path)
            logging.info(
                'Regarding path %s used by %s versions with '
                '%s different revisions', webroot_path, using_versions,
                different_cheksums)
            self.retrieved_resources.add(Asset(url))


        """
        print('using popular static files to reduce number of candidates')
        while True:
            popular = BACKEND.retrieve_static_files_popular_to_versions(
                candidates, limit=5)

            # TODO: Do not assume that there are static files

            changed = False
            for using_versions, static_file in popular:
                if static_file in loaded_static_files:
                    continue
                changed = True
                loaded_static_files.add(static_file)
                asset_url = join_url(self.primary_url, static_file.webroot_path)
                print('retrieving {}'.format(asset_url))
                asset = Asset(asset_url)

                users = BACKEND.retrieve_static_file_users_by_checksum(
                    asset.checksum)
                print(users)

                candidates &= users

                print(candidates)

            if not changed:
                break
        """

    def retrieve_included_assets(self, resource: Resource) -> Set[Asset]:
        """Retrieve the assets referenced from resource."""
        parsed = BeautifulSoup(
            resource.content,
            HTML_PARSER,
            parse_only=SoupStrainer(
                HTML_RELEVANT_ELEMENTS))

        referenced_urls = set()

        for elem in parsed:
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
                # TODO: relative to webroot?
                referenced_url = join_url(resource.url, referenced_url)
            assets.add(Asset(referenced_url))

        return assets

    @property
    def retrieved_assets(self) -> FrozenSet[Asset]:
        """Filter the retrieved resources for assets."""
        return frozenset(
            asset
            for asset in self.retrieved_resources
            if isinstance(asset, Asset))
