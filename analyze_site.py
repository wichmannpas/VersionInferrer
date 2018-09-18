#!/usr/bin/env python3
import json
import logging
import sys
from argparse import ArgumentParser, Namespace
from fnmatch import fnmatch

from analysis.website_analyzer import WebsiteAnalyzer
from base.json import CustomJSONEncoder
from definitions import definitions
import settings


def analyze(arguments: Namespace):
    """Analyse a site to infer its used software package(s) and versions."""
    analyzer = WebsiteAnalyzer(
        primary_url=arguments.primary_url)

    if arguments.json_only:
        logging.disable(logging.CRITICAL)

    for setting, typ in settings.OVERWRITABLE_SETTINGS:
        val = getattr(arguments, setting.lower(), None)
        if val is not None:
            setattr(settings, setting, val)

    if arguments.complete_index_retrieval_for:
        packages = [
            definition.software_package
            for definition in definitions
            if fnmatch(
                definition.software_package.name.lower(),
                arguments.complete_index_retrieval_for.lower())
        ]
        result = analyzer.perform_complete_index_retrieval_for(packages, arguments.dry_run)
    else:
        result = analyzer.analyze()

    if not arguments.json_only:
        print(analyzer.get_statistics())

    if arguments.debug_json_file:
        with open(arguments.debug_json_file, 'w') as debug_file:
            json.dump(analyzer.debug_info, debug_file, cls=CustomJSONEncoder)

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

    for setting, typ in settings.OVERWRITABLE_SETTINGS:
        parser.add_argument('--{}'.format(
            setting.lower().replace('_', '-')),
            type=typ)

    parser.add_argument(
        '--complete-index-retrieval-for', '-c',
        help='Retrieve all assets from the index for software packages that match this pattern')
    parser.add_argument(
        '--dry-run', '-n', action='store_true', default=False,
        help='Only determine which assets to retrieve')

    parser.add_argument(
        '--json-only', action='store_true',
        help='Only output json data to stdout.')
    parser.add_argument(
        '--json-file',
        help='Write JSON output to file instead of stdout.')

    parser.add_argument(
        '--debug-json-file',
        '-d',
        help='Write JSON debug output to this specified file')

    arguments = parser.parse_args()

    if arguments.dry_run and not arguments.complete_index_retrieval_for:
        raise ValueError('dry run is only valid for complete index retrieval!')

    analyze(arguments)
