import logging
import os
import pickle
from concurrent.futures import ProcessPoolExecutor
from traceback import format_exc, print_exc
from urllib.parse import urlparse

from analysis.website_analyzer import WebsiteAnalyzer
from backends.postgresql import PostgresqlBackend
from base.output import colors, print_info
from scanning import majestic_million
from settings import BACKEND


class Scanner:
    """
    The scanner handles the automated scanning of multiple (many)
    sites.
    """
    concurrent = 80

    def scan_sites(self, count: int):
        """Scan first count sites of majestic top million."""
        sites = majestic_million.get_sites(1, count)
        futures = []
        assert isinstance(
            BACKEND, PostgresqlBackend), 'postgresql backend required for scanning'
        BACKEND.initialize_scan_results()
        with ProcessPoolExecutor(max_workers=self.concurrent) as executor:
            for site in sites:
                futures.append(executor.submit(
                    self._monitor_scan_site, 'http://{}'.format(site.domain)))
            for future in futures:
                # access result to get exceptions etc
                future.result()

    def scan_site(self, url: str):
        """Scan a single site."""
        BACKEND.reopen_connection()

        domain = urlparse(url).hostname

        result = BACKEND.retrieve_scan_result(url)
        if result is not None:
            print_info(
                colors.YELLOW,
                'SKIPPING',
                url)
            return
        print_info(
            colors.PURPLE,
            'SCANNING',
            url)
        analyzer = WebsiteAnalyzer(
            primary_url=url)
        result = analyzer.analyze()
        if not result:
            result = False
        more_recent = None
        if result:
            more_recent = analyzer.more_recent_version(
                guess.software_version for guess in result)
        BACKEND.store_scan_result(url, {
            'result': result,
            'more_recent': more_recent,
        })
        print_info(
            colors.GREEN,
            'COMPLETED',
            url)

    def _monitor_scan_site(self, *args, **kwargs):
        """
        Execute the scan_site method and catch and print all exceptions.
        """
        try:
            self.scan_site(*args, **kwargs)
        except Exception as e:
            print('failure for', args, kwargs)
            print_exc()
            logging.error(format_exc())
