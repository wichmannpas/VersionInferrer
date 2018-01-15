#!/usr/bin/env python3
import sys
from argparse import ArgumentParser, Namespace
from collections import defaultdict
from contextlib import closing
from pprint import pprint
from typing import Dict, Tuple

from tqdm import tqdm

from base.utils import match_str_to_software_version, most_recent_version
from settings import BACKEND


def evaluate(arguments: Namespace):
    """Evaluate the scan results."""
    print('Available results:', len(BACKEND.retrieve_scanned_sites()))

    print('Results with guesses:', result_count())

    print('\nGuess counts:')
    pprint(guess_counts())

    print('\nPackage counts:')
    pprint(package_counts())

    print('\nDistinct packages count:')
    pprint(distinct_packages_count())

    print('\nVulnerable versions:')
    pprint(vulnerable_versions())

    print('\nVulnerable versions by package:')
    pprint(vulnerable_versions_by_package())


def result_count() -> int:
    """
    Number of results containing guesses.
    """
    query = '''
    SELECT
        COUNT(*)
    FROM
        scan_result r
    WHERE
        r.result->>'result' != 'false'
    '''
    return _raw_query(query)[0][0]


def guess_counts() -> Dict[int, int]:
    """
    Get the number of results with specific guess count.
    {
        guess count: number of results with that number of guesses
    }
    """
    query = '''
    SELECT
        0 guesses,
        COUNT(*)
    FROM
        scan_result r
    WHERE
        r.result->>'result' = 'false'
    UNION SELECT
        JSONB_ARRAY_LENGTH(r.result->'result') guesses,
        COUNT(*)
    FROM
        scan_result r
    WHERE
        r.result->>'result' != 'false'
    GROUP BY guesses
    '''
    return {
        guesses: count
        for guesses, count in _raw_query(query)
    }


def package_counts() -> Dict[int, int]:
    """
    Aggregate count of results guessing each package.
    """
    query = '''
    SELECT
        sub.software_package,
        COUNT(*)
    FROM (
        SELECT
            r.url,
            JSONB_ARRAY_ELEMENTS(r.result->'result')->'software_version'->'software_package'->>'name' software_package
        FROM
            scan_result r
        WHERE
            r.result->>'result' != 'false'
        GROUP BY
            url,
            software_package) sub
    GROUP BY
        sub.software_package
    '''
    return {
        software_package: count
        for software_package, count in _raw_query(query)
    }


def distinct_packages_count() -> Dict[int, int]:
    """
    Count how often k different packages were guessed.
    """
    query = '''
    SELECT
        0 package_count,
        COUNT(*)
    FROM
        scan_result r
    WHERE
        r.result->>'result' = 'false'
    UNION SELECT
        sub2.package_count,
        COUNT(*)
    FROM (
        SELECT
            sub.url,
            COUNT(*) package_count
        FROM (
            SELECT
                r.url,
                jsonb_array_elements(r.result->'result')->'software_version'->'software_package'->>'name' software_package
            FROM
                scan_result r
             WHERE
                 r.result->>'result' != 'false'
             GROUP BY
                 url,
                 software_package) sub
         GROUP BY
             sub.url) sub2
     GROUP BY
         sub2.package_count
    '''
    return {
        package_count: count
        for package_count, count in _raw_query(query)
    }


def vulnerable_versions() -> Dict[str, int]:
    """
    Aggregate the number of scan results with detected vulnerable versions:
    * total count (vulnerable and non-vulnerable)
    * total count with guess (vulnerable and non-vulnerable)
    * in the most recent version guessed
    * in all guessed version
    * in any version guessed
    """
    total, total_with_guess, most_recent_vulnerable, all_vulnerable, any_vulnerable = 0, 0, 0, 0, 0

    urls = BACKEND.retrieve_scanned_sites()
    for url in tqdm(urls, leave=False):
        total += 1

        result = BACKEND.retrieve_scan_result(url)['result']
        if not result:
            continue
        versions = {
            version
            for guess in result
            for version in match_str_to_software_version(
                guess['software_version']['software_package']['name'],
                guess['software_version']['name'])
        }

        total_with_guess += 1

        most_recent = most_recent_version(versions)
        if most_recent.vulnerable:
            most_recent_vulnerable += 1

        if all(version.vulnerable for version in versions):
            all_vulnerable += 1

        if any(version.vulnerable for version in versions):
            any_vulnerable += 1

    return {
        'total': total,
        'total_with_guess': total_with_guess,
        'most_recent_vulnerable': most_recent_vulnerable,
        'all_vulnerable': all_vulnerable,
        'any_vulnerable': any_vulnerable,
    }


def vulnerable_versions_by_package() -> Dict[str, Dict[str, int]]:
    """
    Aggregate the number of scan results with detected vulnerable versions
    by package.

    This uses the invariant from the previous results that results have at
    most 1 different package among their guesses.
    """
    agg = defaultdict(lambda: {
        'total': 0,
        'all_vulnerable': 0,
        'any_vulnerable': 0,
        'most_recent_vulnerable': 0,
    })

    urls = BACKEND.retrieve_scanned_sites()
    for url in tqdm(urls, leave=False):
        result = BACKEND.retrieve_scan_result(url)['result']
        if not result:
            continue

        package = result[0]['software_version']['software_package']['name']

        agg[package]['total'] += 1

        versions = {
            version
            for guess in result
            for version in match_str_to_software_version(
                guess['software_version']['software_package']['name'],
                guess['software_version']['name'])
        }

        most_recent = most_recent_version(versions)
        if most_recent.vulnerable:
            agg[package]['most_recent_vulnerable'] += 1

        if all(version.vulnerable for version in versions):
            agg[package]['all_vulnerable'] += 1

        if any(version.vulnerable for version in versions):
            agg[package]['any_vulnerable'] += 1

    return dict(agg)


def _raw_query(query):
    """Run a raw query in the backend."""
    with closing(BACKEND._connection.cursor()) as cursor:
        cursor.execute(query)
        return cursor.fetchall()


if __name__ == '__main__':
    parser = ArgumentParser()
    evaluate(parser.parse_args())
