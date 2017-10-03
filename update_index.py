#!/usr/bin/env python3
from argparse import ArgumentParser, Namespace

from indexing.indexer import Indexer


def index(arguments: Namespace):
    """Index all defined software packages versions."""
    indexer = Indexer()
    indexer.index_all(
        max_workers=arguments.max_workers)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        '-w', '--max-workers', type=int, default=16)

    index(parser.parse_args())

