#!/usr/bin/env python3
from argparse import ArgumentParser, Namespace

from indexing.indexer import Indexer


def index(arguments: Namespace):
    """Index all defined software packages versions."""
    indexer = Indexer()

    if arguments.garbage_collect:
        indexer.gc_all()
        return

    indexer.index_all(
        max_workers=arguments.max_workers)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        '-w', '--max-workers', type=int, default=16,
    )
    parser.add_argument(
        '-g', '--garbage-collect', action='store_true', default=False,
    )

    index(parser.parse_args())

