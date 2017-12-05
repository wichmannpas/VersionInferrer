import os
import pickle
from concurrent.futures import ProcessPoolExecutor
from urllib.parse import urlparse

from analysis.website_analyzer import WebsiteAnalyzer
from base.output import colors, print_info
from scanning import majestic_million
from settings import BACKEND, SCAN_DIR


class Scanner:
    """
    The scanner handles the automated scanning of multiple (many)
    sites.
    """
    concurrent = 80
    skip_existing = True

    def scan_sites(self, count: int):
        """Scan first count sites of majestic top million."""
        if not os.path.isdir(SCAN_DIR):
            os.makedirs(SCAN_DIR, exist_ok=True)

        sites = majestic_million.get_sites(1, count)
        futures = []
        with ProcessPoolExecutor(max_workers=self.concurrent) as executor:
            for site in sites:
                futures.append(executor.submit(
                    self.scan_site, 'http://{}'.format(site.domain)))
            for future in futures:
                # access result to get exceptions etc
                future.result()

    def scan_site(self, url: str):
        """Scan a single site."""
        domain = urlparse(url).hostname
        if self.skip_existing and os.path.isfile(os.path.join(SCAN_DIR, domain)):
            print_info(
                colors.YELLOW,
                'SKIPPING',
                url)
            return
        print_info(
            colors.PURPLE,
            'SCANNING',
            url)
        BACKEND.reopen_connection()
        analyzer = WebsiteAnalyzer(
            primary_url=url)
        best_guess = analyzer.analyze()
        with open(os.path.join(SCAN_DIR, domain), 'wb') as fdes:
            pickle.dump(best_guess, fdes)
        print_info(
            colors.GREEN,
            'COMPLETED',
            url)
