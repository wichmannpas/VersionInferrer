"""
This module is a wrapper of the CVE statistics.
It uses the data from nvd.nist.gov to aggregate vulnerability
counts for software versions.
"""
import json
import logging
import pickle
from collections import defaultdict
from datetime import date
from gzip import decompress
from typing import Dict, Set

import requests

from backends.software_version import SoftwareVersion
from base.utils import match_str_to_software_version
from settings import CVE_STATISTICS_FILE


FIRST_CVE_YEAR = 2002


def affected_versions(cve: dict) -> Set[SoftwareVersion]:
    """Find all versions affected by a cve."""
    result = set()

    affected_products = cve['affects']['vendor']['vendor_data']
    for products in affected_products:
        products = products['product']['product_data']
        for product in products:
            versions = product['version']['version_data']
            product = product['product_name']
            for version in versions:
                version = version['version_value']

                result.update(match_str_to_software_version(product, version))
    return result


def cve_stats_for_year(year: int) -> Dict[SoftwareVersion, Set[str]]:
    url = 'https://static.nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-{}.json.gz'.format(
        year)
    cve_items = json.loads(
        decompress(requests.get(url).content).decode())['CVE_Items']

    statistics = defaultdict(set)
    for cve_item in cve_items:
        cve_id = cve_item['cve']['CVE_data_meta']['ID']
        for version in affected_versions(cve_item['cve']):
            statistics[version].add(cve_id)
    return dict(statistics)


def update_cve_statistics():
    """Update the CVE statistics by fetching CVE data for all years."""
    statistics = {}
    for year in range(FIRST_CVE_YEAR, date.today().year + 1):
        logging.info('fetching CVE statistics for %s', year)
        _join_statistics(
            statistics,
            cve_stats_for_year(year))
    with open(CVE_STATISTICS_FILE, 'wb') as fh:
        pickle.dump(statistics, fh)


def _join_statistics(target: dict, join: dict):
    """Add statistics from join to target in-place."""
    for version, cves in join.items():
        if version not in target:
            target[version] = set()
        target[version].update(cves)
