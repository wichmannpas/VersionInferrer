from concurrent.futures import ProcessPoolExecutor

from analysis.website_analyzer import WebsiteAnalyzer
from base.output import colors, print_info
from scanning import majestic_million


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
        with ProcessPoolExecutor(max_workers=self.concurrent) as executor:
            for site in sites:
                futures.append(executor.submit(
                    self.scan_site, 'http://{}'.format(site.domain)))
            for future in futures:
                # access result to get exceptions etc
                future.result()

    def scan_site(self, url: str):
        """Scan a single site."""
        print_info(
            colors.PURPLE,
            'SCANNING',
            url)
        analyzer = WebsiteAnalyzer(
            primary_url=url)
        analyzer.analyze()
        print_info(
            colors.GREEN,
            'COMPLETED',
            url)
