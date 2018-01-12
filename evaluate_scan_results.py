#!/usr/bin/env python3
from argparse import ArgumentParser, Namespace
from contextlib import closing
from typing import Dict

from settings import BACKEND


def evaluate(arguments: Namespace):
    """Evaluate the scan results."""
    #print('Available results:', len(BACKEND.retrieve_scanned_sites()))
    #print('Guess counts:', guess_counts())
    print('Package counts:', package_counts())


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
        guesses: count
        for software_package, count in _raw_query(query)
    }


def _raw_query(query):
    """Run a raw query in the backend."""
    with closing(BACKEND._connection.cursor()) as cursor:
        cursor.execute(query)
        return cursor.fetchall()


if __name__ == '__main__':
    parser = ArgumentParser()
    evaluate(parser.parse_args())
