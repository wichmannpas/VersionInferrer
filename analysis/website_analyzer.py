import logging
import pickle
import os
from collections import defaultdict
from typing import Dict, FrozenSet, Iterable, List, Optional, Tuple, Union
from urllib.parse import urlparse

from bs4 import BeautifulSoup, SoupStrainer

import settings
from analysis.asset import Asset
from analysis.guess import Guess
from analysis.resource import Resource
from backends.software_package import SoftwarePackage
from backends.software_version import SoftwareVersion
from base.utils import join_url, most_recent_version
from files import file_types_for_analysis
from settings import BACKEND, HTML_PARSER, HTML_RELEVANT_ELEMENTS, \
    SUPPORTED_SCHEMES


class WebsiteAnalyzer:
    """
    This class provides the website analyzer. It is used to analyze a
    single website to detect software packages and versions.
    """
    # primary_url: str
    # retrieved_resources: Set[Resource]
    # _cache: dict
    _cache_file = None
    debug_info = None
    persist_resources = None

    def __init__(self, primary_url: str, cache_file: Optional[str] = None):
        self.complete_retrieval = False
        self.dry_run = False
        self.retrieved_resources = set()
        self._cache = {}
        if cache_file:
            self._load_cache(cache_file)
        if not primary_url.startswith(('http://', 'https://')):
            logging.warning('No scheme was given for the primary URL. Falling back to \'http://\' as scheme.')
            self.primary_url = 'http://{}'.format(primary_url)
        else:
            self.primary_url = primary_url

    def __del__(self):
        if self._cache_file:
            self._persist_cache()
        if self.persist_resources:
            self._persist_resources()

    def perform_complete_index_retrieval_for(
            self, packages: List[SoftwarePackage],
            dry_run=False):
        self.software_packages = packages
        self.dry_run = dry_run
        self.complete_retrieval = True

        self._init_debug_info()

        estimates = set()

        for package in packages:
            estimates |= BACKEND.retrieve_versions(package)

        guesses = [Guess(estimate) for estimate in estimates]
        self.iteration = 0
        self._useless_iteration_count = 0
        self._iterate(guesses)

    def analyze(self) -> Union[List[Guess], None]:
        """Analyze the website."""
        self._init_debug_info()

        main_page = Resource(self.primary_url, self._cache)
        if not main_page.success:
            logging.info('failed to retrieve main resource. Stopping')
            return None
        self.retrieved_resources.add(main_page)
        if main_page.final_url != self.primary_url:
            logging.info('updating primary url to %s', main_page.final_url)
            self.primary_url = main_page.final_url

        first_estimates = main_page.extract_information()

        self._retrieve_included_assets(main_page)
        # regard favicon
        self.retrieved_resources.add(Asset(
            join_url(self.primary_url, 'favicon.ico'), self._cache))

        # First iteration uses all first estimates as well as best
        # guesses from main assets
        guesses = [Guess(estimate) for estimate in first_estimates] + \
            self._get_best_guesses(settings.GUESS_LIMIT)
        logging.info('assets from primary page and first estimates lead to guesses: %s', guesses)

        self.debug_info['initial_guesses'] = [guess.debug_serialize() for guess in guesses]

        self._useless_iteration_count = 0
        for iteration in range(settings.MAX_ITERATIONS):
            if not guesses:
                logging.error('no guesses left. Cannot continue.')
                return None

            self.iteration = iteration
            guesses = self._iterate(guesses)
            if self._useless_iteration_count >= settings.MAX_ITERATIONS_WITHOUT_IMPROVEMENT:
                logging.info(
                    'Reached max number of iterations without improvement (%s)',
                    self._useless_iteration_count)
                break

            if len(guesses) == 1 and self._has_enough_support(guesses):
                logging.info('no guesses to distinguish and support is high enough. Stopping.')
                break

        if not guesses:
            logging.warning('no guesses found')
            return None

        best_guess, support = self._calculate_support(guesses)
        logging.info('Best guess is %s (support %s)', best_guess, support)
        enough_support = self._has_enough_support(guesses)

        self.debug_info['result'] = {
            'best_guess': [guess.debug_serialize() for guess in best_guess],
            'support': support,
            'enough_support': enough_support,
        }

        if not enough_support:
            logging.warning('Support is too low. No usable result available.')
            return None

        return best_guess

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

    @staticmethod
    def more_recent_version(
                version: Union[SoftwareVersion, Iterable[SoftwareVersion]]
            ) -> Union[None, SoftwareVersion]:
        """
        Check whether version is the most recent release of its
        software package.
        Returns None if it is most recent (compared to index), the
        most recent version otherwise.

        version can be an interable of multiple versions (i.e., a result
        from analyze). In that case the
        most recent version of those versions is regarded.
        """
        if not isinstance(version, SoftwareVersion):
            # TODO: find a better way than casting to list
            version = list(version)
            assert all(
                v.software_package == version[0].software_package
                for v in version[1:]), 'the iterable contains versions of different software packages'
            version = most_recent_version(version)

        package = version.software_package
        most_recent = most_recent_version(
            BACKEND.retrieve_versions(package, indexed_only=False))

        if most_recent == version:
            return None
        return most_recent

    def _calculate_support(self, guesses: List[Guess]) -> Tuple[List[Guess], float]:
        """Calculate the support of guesses and get the best guess(es)."""
        # TODO: be a bit more academical in support/confidence determination
        best_guess = guesses[0]
        best_strength = best_guess.strength
        support = best_strength / len(self.retrieved_assets)
        best_guess = [best_guess]
        for guess in guesses[1:]:
            if guess.strength != best_strength:
                break
            best_guess.append(guess)

        return best_guess, support

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
        min_strength = min(
            (1 - settings.GUESS_RELATIVE_IGNORE_DISTANCE) * best_guess_strength,
            best_guess_strength - settings.GUESS_IGNORE_DISTANCE)
        if guesses[0].positive_strength < settings.GUESS_IGNORE_MIN_POSITIVE:
            min_strength = float('-inf')
        return [
            guess
            for guess in guesses[:limit]
            if guess.strength >= min_strength
        ]

    def _has_enough_support(self, guesses: List[Guess]) -> bool:
        """Check whether the support of best_guess is high enough."""
        best_guess, support = self._calculate_support(guesses)
        return support >= settings.MIN_SUPPORT and best_guess[0].strength >= settings.MIN_ABSOLUTE_SUPPORT

    def _init_debug_info(self):
        self.debug_info = {
            'parameters': {},
            'primary_url': self.primary_url,
            'initial_guesses': [],
            'iterations': [],
        }

        for setting, typ in settings.OVERWRITABLE_SETTINGS:
            self.debug_info['parameters'][setting.lower()] = getattr(settings, setting)

        self.debug_info['parameters']['complete_retrieval'] = self.complete_retrieval
        self.debug_info['parameters']['dry_run'] = self.dry_run

    def _iterate(
                self, guesses: List[Tuple[SoftwareVersion, int]]
            ) -> List[Tuple[SoftwareVersion, int]]:
        """Do an iteration."""
        logging.info('starting iteration %s', self.iteration)
        useless = False

        debug_info = {}
        self.debug_info['iterations'].append(debug_info)

        debug_info['iteration'] = self.iteration
        debug_info['retrieved_assets'] = []

        # TODO: make sure that no assets are fetched multiple times
        limit = settings.MAX_ASSETS_PER_ITERATION
        if self.complete_retrieval:
            limit = None
        assets_with_entropy = BACKEND.retrieve_webroot_paths_with_high_entropy(
            software_versions=(guess.software_version for guess in guesses),
            limit=limit,
            exclude=(
                asset.webroot_path
                for asset in self.retrieved_assets))
        status_codes = defaultdict(int)
        iteration_matching_assets = 0
        for webroot_path, using_versions, different_cheksums in assets_with_entropy:
            if not self.complete_retrieval and \
                    iteration_matching_assets >= settings.MIN_ASSETS_PER_ITERATION:
                logging.info(
                    'Reached min iteration assets count. Stop iteration.')
                debug_info['finish_reason'] = 'min count reached'
                break
            url = join_url(self.primary_url, webroot_path)
            logging.info(
                'Regarding path %s used by %s versions with '
                '%s different revisions', webroot_path, using_versions,
                different_cheksums)
            asset_debug_info = {
                'url': url,
                'webroot_path': webroot_path,
                'using_versions': using_versions,
                'different_checksums': different_cheksums,
            }
            if not self.dry_run:
                asset = Asset(url, self._cache)
                if asset in self.retrieved_resources:
                    logging.info('asset already known, skipping')
                    continue
                success = False
                if asset.success:
                    status_codes[asset.status_code] += 1
                    success = True
                found_in_index = False
                if asset.using_versions:
                    iteration_matching_assets += 1
                    found_in_index = True
                self.retrieved_resources.add(asset)
                asset_debug_info['success'] = success
                asset_debug_info['found_in_index'] = found_in_index
            debug_info['retrieved_assets'].append(asset_debug_info)

        debug_info['asset_count'] = len(debug_info['retrieved_assets'])

        if 200 not in status_codes:
            logging.info('no asset could be retrieved in this iteration.')
            useless = True
            debug_info['useless_reason'] = 'no asset successfully retrieved'

        previous_decisiveness = self._guess_decisiveness(guesses)
        guesses = self._get_best_guesses(settings.GUESS_LIMIT)
        logging.info('new guesses are %s', guesses)

        new_decisiveness = self._guess_decisiveness(guesses)
        gain = new_decisiveness - previous_decisiveness
        if gain < settings.ITERATION_MIN_IMPROVEMENT:
            logging.info(
                'decisiveness gain (%s) is less than minimum required',
                gain)
            useless = True
            debug_info['useless_reason'] = 'gain less than required'

        debug_info['new_guesses'] = [guess.debug_serialize() for guess in guesses]
        debug_info['new_decisiveness'] = new_decisiveness
        debug_info['gain'] = gain

        if useless:
            logging.info('iteration was useless.')
            self._useless_iteration_count += 1
        else:
            self._useless_iteration_count = 0

        debug_info['useless'] = useless

        return guesses

    def _load_cache(self, cache_file: str):
        self._cache_file = cache_file
        if not os.path.isfile(self._cache_file):
            return
        with open(cache_file, 'rb') as ca:
            self._cache = pickle.load(ca)
            assert isinstance(self._cache, dict), 'invalid cache file'

    def _map_retrieved_assets_to_versions(
            self) -> Dict[SoftwareVersion, Tuple[int, int]]:
        """
        Create a dictionary mapping from every software version to the number
        of retrieved assets which are in use and which are expected but not in
        use by it.
        """
        # TODO: not only bare counts are interesting, but mutual matches etc.
        # Therefore, find a better modeling strategy
        result = defaultdict(lambda: [set(), set()])
        for asset in self.retrieved_assets:
            for version in asset.expected_versions | asset.using_versions:
                if version in asset.using_versions:
                    result[version][0].add(asset)
                else:
                    # not actually using it but expected it
                    result[version][1].add(asset)
        return dict(result)

    @property
    def _matchable_retrieved_assets(self) -> FrozenSet[Asset]:
        """Filter the retrieved resources for matchable assets."""
        return frozenset(
            asset
            for asset in self.retrieved_resources
            if isinstance(asset, Asset) and asset.using_versions)

    def _persist_cache(self):
        with open(self._cache_file, 'wb') as ca:
            pickle.dump(self._cache, ca)

    def _persist_resources(self):
        os.makedirs(self.persist_resources, exist_ok=True)
        for resource in self.retrieved_resources:
            resource.persist(self.persist_resources)

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
            try:
                parsed_url = urlparse(referenced_url)
            except ValueError:
                # invalid URL
                continue
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
            asset = Asset(referenced_url, self._cache)
            self.retrieved_resources.add(asset)

    @staticmethod
    def _guess_decisiveness(guesses: List[Guess]) -> int:
        """Calculate the difference from the best guess to other guesses."""
        if not guesses:
            return 0
        if len(guesses) == 1:
            return guesses[0].strength
        best_guess_strength = guesses[0].strength
        return sum(
            best_guess_strength - guess.strength
            for guess in guesses[1:]) / len(guesses)
