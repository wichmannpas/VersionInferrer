import logging
import os
from collections import defaultdict
from typing import Dict, FrozenSet, List, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup, SoupStrainer

from analysis.asset import Asset
from analysis.guess import Guess
from analysis.resource import Resource
from backends.software_version import SoftwareVersion
from base.utils import join_url
from files import file_types_for_analysis
from settings import BACKEND, GUESS_IGNORE_DISTANCE, \
    GUESS_IGNORE_MIN_POSITIVE, GUESS_RELATIVE_IGNORE_DISTANCE, \
    HTML_PARSER, HTML_RELEVANT_ELEMENTS, ITERATION_MIN_IMPROVEMENT, \
    MAX_ITERATIONS_WITHOUT_IMPROVEMENT, MIN_ABSOLUTE_SUPPORT, MIN_SUPPORT, \
    SUPPORTED_SCHEMES


class WebsiteAnalyzer:
    """
    This class provides the website analyzer. It is used to analyze a
    single website to detect software packages and versions.
    """
    # primary_url: str
    # retrieved_resources: Set[Resource]
    max_iterations = 15
    guess_limit = 7
    min_assets_per_iteration = 2
    max_assets_per_iteration = 8

    def __init__(self, primary_url: str):
        self.primary_url = primary_url
        self.retrieved_resources = set()

    def analyze(self):
        """Analyze the website."""
        main_page = Resource(self.primary_url)
        self.retrieved_resources.add(main_page)
        if main_page.final_url != self.primary_url:
            logging.info('updating primary url to %s', main_page.final_url)
            self.primary_url = main_page.final_url

        first_estimates = main_page.extract_information()

        self._retrieve_included_assets(main_page)
        # regard favicon
        self.retrieved_resources.add(Asset(
            join_url(self.primary_url, 'favicon.ico')))

        # First iteration uses all first estimates as well as best
        # guesses from main assets
        guesses = [Guess(estimate) for estimate in first_estimates] + \
            self._get_best_guesses(self.guess_limit)
        logging.info('assets from primary page and first estimates lead to guesses: %s', guesses)

        self._useless_iteration_count = 0
        for iteration in range(self.max_iterations):
            if not guesses:
                logging.error('no guesses left. Cannot continue.')
                return None

            self.iteration = iteration
            guesses = self._iterate(guesses)
            if self._useless_iteration_count >= MAX_ITERATIONS_WITHOUT_IMPROVEMENT:
                logging.info(
                    'Reached max number of iterations without improvement (%s)',
                    self._useless_iteration_count)
                break

            if len(guesses) <= 1:
                logging.info('no guesses to distinguish. stopping iterations early.')
                break

        if not guesses:
            logging.warning('no guesses found')
            return None

        best_guess = guesses[0]
        best_strength = best_guess.strength
        support = best_strength / len(self.retrieved_assets)
        other_best_guesses = []
        for guess in guesses[1:]:
            if guess.strength != best_strength:
                break
            other_best_guesses.append(guess)
        if other_best_guesses:
            best_guess = [best_guess] + other_best_guesses
        logging.info('Best guess is %s (support %s)', best_guess, support)

        if support < MIN_SUPPORT or best_strength < MIN_ABSOLUTE_SUPPORT:
            logging.warning('Support is too low. No usable result available.')
            return None

        # TODO: Return something (define interface)

    def get_statistics(self) -> dict:
        """Get statistics about the current analyzer instance."""
        return {
            'retrieved_assets_total': len(self.retrieved_assets),
            'retrieved_resources_total': len(self.retrieved_resources),
            'retrieved_resources_successful': sum(
                1 for res in self.retrieved_resources if res.retrieved and res.success),
        }

    @property
    def retrieved_assets(self) -> FrozenSet[Asset]:
        """Filter the retrieved resources for assets."""
        return frozenset(
            asset
            for asset in self.retrieved_resources
            if isinstance(asset, Asset))


        # TODO: Return something (define interface)

    def _get_best_guesses(self, limit: int) -> List[Guess]:
        """
        Extract the best guesses using the retrieved assets.
        """
        guesses = sorted((
            Guess(version, count[0], count[1])
            for version, count
            in self._map_retrieved_assets_to_versions().items()
            if version is not None), reverse=True)

        if not guesses:
            return []

        best_guess_strength = guesses[0].strength
        min_strength = max(
            (1 - GUESS_RELATIVE_IGNORE_DISTANCE) * best_guess_strength,
            best_guess_strength - GUESS_IGNORE_DISTANCE)
        if guesses[0].positive_matches < GUESS_IGNORE_MIN_POSITIVE:
            min_strength = float('-inf')
        return [
            guess
            for guess in guesses[:limit]
            if guess.strength >= min_strength
        ]

    def _iterate(
            self, guesses: List[Tuple[SoftwareVersion, int]]
        ) -> List[Tuple[SoftwareVersion, int]]:
        """Do an iteration."""
        logging.info('starting iteration %s', self.iteration)
        useless = False

        # TODO: make sure that no assets are fetched multiple times
        assets_with_entropy = BACKEND.retrieve_webroot_paths_with_high_entropy(
            software_versions=(guess.software_version for guess in guesses),
            limit=self.max_assets_per_iteration,
            exclude=(
                asset.webroot_path
                for asset in self.retrieved_assets))
        status_codes = defaultdict(int)
        iteration_matching_assets = 0
        for webroot_path, using_versions, different_cheksums in assets_with_entropy:
            if iteration_matching_assets >= self.min_assets_per_iteration:
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
        guesses = self._get_best_guesses(self.guess_limit)
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
            self._useless_iteration_count += 1
        else:
            self._useless_iteration_count = 0

        return guesses

    def _map_retrieved_assets_to_versions(
            self) -> Dict[SoftwareVersion, Tuple[int, int]]:
        """
        Create a dictionary mapping from every software version to the number
        of retrieved assets which are in use and which are expected but not in
        us by it.
        """
        # TODO: not only bare counts are interesting, but mutual matches etc.
        # Therefore, find a better modeling strategy
        result = defaultdict(lambda: [0, 0])
        for asset in self.retrieved_assets:
            for version in asset.expected_versions | asset.using_versions:
                if version in asset.using_versions:
                    result[version][0] += 1
                else:
                    # not actually using it but expected it
                    result[version][1] += 1
        return dict(result)

    @property
    def _matchable_retrieved_assets(self) -> FrozenSet[Asset]:
        """Filter the retrieved resources for matchable assets."""
        return frozenset(
            asset
            for asset in self.retrieved_resources
            if isinstance(asset, Asset) and asset.using_versions)

    def _retrieve_included_assets(self, resource: Resource):
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

    @staticmethod
    def _guess_decisiveness(guesses: List[Tuple[SoftwareVersion, int]]) -> int:
        """Calculate the difference from the best guess to other guesses."""
        if len(guesses) < 2:
            return 0
        best_guess_strength = guesses[0].strength
        return sum(
            best_guess_strength - guess.strength
            for guess in guesses[1:]) / len(guesses)
