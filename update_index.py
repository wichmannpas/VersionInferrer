#!/usr/bin/env python3
from argparse import ArgumentParser, Namespace
from fnmatch import fnmatch

from definitions import definitions
from indexing.indexer import Indexer


def index(arguments: Namespace):
    """Index all defined software packages versions."""
    indexer = Indexer()

    if arguments.garbage_collect:
        indexer.gc_all()
        return

    limit_definitions = None
    if arguments.limit_definitions:
        limit_definitions = [
            definition
            for definition in definitions
            if fnmatch(
                definition.software_package.name.lower(),
                arguments.limit_definitions.lower())
        ]
        if not limit_definitions:
            print('no definitions match the expression.')
            return
        print(
            'Definitions matching the expression: \n',
            '\n '.join(
                definition.software_package.name
                for definition in limit_definitions))

    indexer.index_all(
        max_workers=arguments.max_workers, limit_definitions=limit_definitions)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        '-w', '--max-workers', type=int, default=16,
    )
    parser.add_argument(
        '-g', '--garbage-collect', action='store_true', default=False,
    )
    parser.add_argument(
        '-l', '--limit-definitions', type=str,
        help='Only index software packages which name matches the given expression',
    )

    index(parser.parse_args())
