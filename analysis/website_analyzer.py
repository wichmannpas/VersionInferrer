import logging
import os
from collections import defaultdict
from typing import Dict, FrozenSet, List, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup, SoupStrainer

from analysis.asset import Asset
from analysis.resource import Resource
from backends.software_version import SoftwareVersion
from base.utils import join_url
from files import file_types_for_analysis
from settings import BACKEND, GUESS_MIN_DIFFERENCE, HTML_PARSER, \
    HTML_RELEVANT_ELEMENTS, ITERATION_MIN_IMPROVEMENT, \
    MAX_ITERATIONS_WITHOUT_IMPROVEMENT, MIN_ABSOLUTE_SUPPORT, \
    MIN_SUPPORT, SUPPORTED_SCHEMES


class WebsiteAnalyzer:
    """
    This class provides the website analyzer. It is used to analyze a
    single website to detect software packages and versions.
    """
    # primary_url: str
    # retrieved_resources: Set[Resource]

    def __init__(self, primary_url: str):
        self.primary_url = primary_url
        self.retrieved_resources = set()

    def analyze(
            self,
            max_iterations: int = 15,
            guess_limit: int = 7,
            min_assets_per_iteration: int = 2,
            max_assets_per_iteration: int = 8):
        """Analyze the website."""
        main_page = Resource(self.primary_url)
        self.retrieved_resources.add(main_page)
        if main_page.final_url != self.primary_url:
            logging.info('updating primary url to %s', main_page.final_url)
            self.primary_url = main_page.final_url

        first_estimates = main_page.extract_information()

        self.retrieve_included_assets(main_page)
        # regard favicon
        self.retrieved_resources.add(Asset(
            join_url(self.primary_url, 'favicon.ico')))

        # First iteration uses all first estimates as well as best
        # guesses from main assets
        guesses = [(estimate, 0) for estimate in first_estimates] + \
            self.get_best_guesses(guess_limit)
        logging.info('assets from primary page and first estimates lead to guesses: %s', guesses)

        useless_iteration_count = 0
        for iteration in range(max_iterations):
            logging.info('starting iteration %s', iteration)
            useless = False

            if not guesses:
                logging.error('no guesses left. Cannot continue.')
                return None

            # TODO: make sure that no assets are fetched multiple times
            assets_with_entropy = BACKEND.retrieve_webroot_paths_with_high_entropy(
                software_versions=(guess[0] for guess in guesses),
                limit=max_assets_per_iteration,
                exclude=(
                    asset.webroot_path
                    for asset in self.retrieved_assets))
            status_codes = defaultdict(int)
            iteration_matching_assets = 0
            for webroot_path, using_versions, different_cheksums in assets_with_entropy:
                if iteration_matching_assets >= min_assets_per_iteration:
                    logging.info(
                        'Reached min iteration assets count. Stop iteration.')
                    break
                url = join_url(self.primary_url, webroot_path)
                logging.info(
                    'Regarding path %s used by %s versions with '
                    '%s different revisions', webroot_path, using_versions,
                    different_cheksums)
                asset = Asset(url)
                if asset in self.retrieved_resources:
                    logging.info('asset already known, skipping')
                    continue
                status_codes[asset.status_code] += 1
                if asset.using_versions:
                    iteration_matching_assets += 1
                self.retrieved_resources.add(asset)
            if 200 not in status_codes:
                logging.info('no asset could be retrieved in this iteration.')
                useless = True

            previous_decisiveness = self._guess_decisiveness(guesses)
            guesses = self.get_best_guesses(guess_limit)
            logging.info('new guesses are %s', guesses)

            new_decisiveness = self._guess_decisiveness(guesses)
            gain = new_decisiveness - previous_decisiveness
            if gain < ITERATION_MIN_IMPROVEMENT:
                logging.info(
                    'decisiveness gain (%s) is less than minimum required',
                    gain)
                useless = True

            if useless:
                logging.info('iteration was useless.')
                useless_iteration_count += 1
                if useless_iteration_count >= MAX_ITERATIONS_WITHOUT_IMPROVEMENT:
                    logging.info(
                        'Reached max number of iterations without improvement (%s)',
                        useless_iteration_count)
                    break
            else:
                useless_iteration_count = 0

            if (len(guesses) <= 1 or
                    guesses[0][1] - guesses[1][1] >= GUESS_MIN_DIFFERENCE):
                logging.info('stopping iterations early.')
                break

        if not guesses:
            logging.warning('no guesses found')
            return None

        best_guess, matches = guesses[0]
        support = matches / len(self.matchable_retrieved_assets)
        logging.info('Best guess is %s (support %s)', best_guess, support)

        if support < MIN_SUPPORT or matches < MIN_ABSOLUTE_SUPPORT:
            logging.warning('Support is too low. No usable result available.')
            return None

        # TODO: Return something (define interface)

    def get_best_guesses(self, limit: int) -> List[Tuple[SoftwareVersion, int]]:
        """
        Extract the best guesses using the retrieved assets.
        """
        guesses = sorted((
            (version, count)
            for version, count
            in self.map_retrieved_assets_to_versions().items()
            if version is not None), key=lambda i: -i[1])

        if not guesses:
            return []

        best_guess_count = guesses[0][1]
        min_count = 0.7 * best_guess_count
        return [
            guess
            for guess in guesses[:limit]
            if guess[1] >= min_count
        ]

    def get_statistics(self) -> dict:
        """Get statistics about the current analyzer instance."""
        return {
            'retrieved_assets_total': len(self.retrieved_assets),
            'retrieved_resources_total': len(self.retrieved_resources),
            'retrieved_resources_successful': sum(1 for res in self.retrieved_resources if res.success),
        }

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

    @property
    def matchable_retrieved_assets(self) -> FrozenSet[Asset]:
        """Filter the retrieved resources for matchable assets."""
        return frozenset(
            asset
            for asset in self.retrieved_resources
            if isinstance(asset, Asset) and asset.using_versions)

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
                    parsed_url.scheme not in SUPPORTED_SCHEMES):
                continue
            file_name = os.path.basename(referenced_url)
            file = None
            for file_type in file_types_for_analysis:
                try:
                    file = file_type(file_name, None)
                    break
                except ValueError:
                    pass
            if file is None:
                # not a static file
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

    @staticmethod
    def _guess_decisiveness(guesses: List[Tuple[SoftwareVersion, int]]) -> int:
        """Calculate the difference from the best guess to other guesses."""
        if len(guesses) < 2:
            return 0
        best_guess_count = guesses[0][1]
        return sum(
            best_guess_count - count
            for guess, count in guesses[1:]) / len(guesses)
