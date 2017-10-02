import logging
from collections import defaultdict
from typing import Dict, FrozenSet, List, Set
from urllib.parse import urlparse

from bs4 import BeautifulSoup, SoupStrainer

from analysis.asset import Asset
from analysis.resource import Resource
from backends.software_version import SoftwareVersion
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

    def analyze(
            self,
            max_iterations: int = 15,
            guess_limit: int = 10,
            assets_per_iteration: int = 8):
        """Analyze the website."""
        main_page = Resource(self.primary_url)
        self.retrieved_resources.add(main_page)

        first_estimates = main_page.extract_information()

        self.retrieve_included_assets(main_page)

        # First iteration uses all first estimates as well as best
        # guesses from main assets
        guesses = [(estimate, 0) for estimate in first_estimates] + \
            self.get_best_guesses(guess_limit)
        logging.info('assets from primary page and first estimates lead to guesses: %s', guesses)

        for iteration in range(max_iterations):
            logging.info('starting iteration %s', iteration)

            # TODO: make sure that no assets are fetched multiple times
            # TODO: find some exclude mechanism for previous iteration's webroot paths
            assets_with_entropy = BACKEND.retrieve_webroot_paths_with_high_entropy(
                (guess[0] for guess in guesses), assets_per_iteration)
            for webroot_path, using_versions, different_cheksums in assets_with_entropy:
                url = join_url(self.primary_url, webroot_path)
                logging.info(
                    'Regarding path %s used by %s versions with '
                    '%s different revisions', webroot_path, using_versions,
                    different_cheksums)
                self.retrieved_resources.add(Asset(url))

            # TODO: stop if guess is clear enough
            guesses = self.get_best_guesses(guess_limit)
            logging.info('new guesses are %s', guesses)

        if not guesses:
            logging.warning('no guesses found')
            return None

        best_guess = guesses[0][0]
        logging.info('Best guess is %s', best_guess)

        # TODO: Return something (define interface)

    def get_best_guesses(self, limit: int) -> List[SoftwareVersion]:
        """
        Extract the best guesses using the retrieved assets.
        """
        guesses = sorted(
            self.map_retrieved_assets_to_versions().items(),
            key=lambda i: -i[1])
        return [
            guess
            for guess in guesses[:limit]
            if guess[0] is not None
        ]

    def map_retrieved_assets_to_versions(self) -> Dict[SoftwareVersion, int]:
        """
        Create a dictionary mapping from every software version to the number
        of retrieved assets which are in use by it.
        """
        # TODO: not only bare counts are interesting, but mutual matches etc.
        # Therefore, find a better modeling strategy
        result = defaultdict(int)
        for asset in self.retrieved_assets:
            if not asset.using_versions:
                result[None] += 1
                continue
            for version in asset.using_versions:
                result[version] += 1
        return dict(result)

    def retrieve_included_assets(self, resource: Resource):
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
            asset = Asset(referenced_url)
            self.retrieved_resources.add(asset)

    @property
    def retrieved_assets(self) -> FrozenSet[Asset]:
        """Filter the retrieved resources for assets."""
        return frozenset(
            asset
            for asset in self.retrieved_resources
            if isinstance(asset, Asset))
