from concurrent.futures import ThreadPoolExecutor

from analysis.website_analyzer import WebsiteAnalyzer
from base.output import colors, print_info
from scanning import majestic_million


class Scanner:
    """
    The scanner handles the automated scanning of multiple (many)
    sites.
    """
    threads = 80

    def scan_sites(self, count: int):
        """Scan first count sites of majestic top million."""
        sites = majestic_million.get_sites(1, count)
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for site in sites:
                executor.submit(
                    self.scan_site, 'http://{}'.format(site.domain))

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
