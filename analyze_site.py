#!/usr/bin/env python3
import json
import logging
import sys
from argparse import ArgumentParser, Namespace

from analysis.website_analyzer import WebsiteAnalyzer
from base.json import CustomJSONEncoder


def analyze(arguments: Namespace):
    """Analyse a site to infer its used software package(s) and versions."""
    analyzer = WebsiteAnalyzer(
        primary_url=arguments.primary_url)

    if arguments.json_only:
        logging.disable(logging.CRITICAL)

    if arguments.max_iterations:
        analyzer.max_iterations = arguments.max_iterations
    if arguments.guess_limit:
        analyzer.guess_limit = arguments.guess_limit
    if arguments.min_assets_per_iteration:
        analyzer.min_assets_per_iteration = arguments.min_assets_per_iteration,
    if arguments.max_assets_per_iteration:
        analyzer.max_assets_per_iteration = arguments.max_assets_per_iteration,

    result = analyzer.analyze()

    if not arguments.json_only:
        print(analyzer.get_statistics())

    json_file = sys.stdout
    if arguments.json_file:
        # TODO: make sure file is closed again
        json_file = open(arguments.json_file, 'w')

    if not result:
        json.dump({}, json_file)
        return

    if not arguments.json_only:
        print(result)

    more_recent = analyzer.more_recent_version(
        guess.software_version for guess in result)

    if more_recent and not arguments.json_only:
        print(
            'More recent version {} released, possibly outdated!'.format(
                more_recent))

    json.dump({
        'result': result,
        'more_recent': more_recent,
    }, json_file, cls=CustomJSONEncoder)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('primary_url')

    parser.add_argument('-i', '--max-iterations', type=int)
    parser.add_argument('-l', '--guess-limit', type=int)
    parser.add_argument('--min-assets-per-iteration', type=int)
    parser.add_argument('--max-assets-per-iteration', type=int)

    parser.add_argument(
        '--json-only', action='store_true',
        help='Only output json data to stdout.')
    parser.add_argument(
        '--json-file',
        help='Write JSON output to file instead of stdout.')

    analyze(parser.parse_args())
