#!/usr/bin/env python3
from argparse import ArgumentParser, Namespace

from scanning.scanner import Scanner


def scan(arguments: Namespace):
    """Scan sites."""
    scanner = Scanner()
    if arguments.concurrent:
        scanner.concurrent = arguments.concurrent
    if not arguments.skip_existing:
        scanner.skip_existing = False
    scanner.scan_sites(arguments.count)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('count', type=int, default=1000)
    parser.add_argument('--concurrent', '-c', type=int, default=80)
    parser.add_argument('--skip-existing', '-s', type=bool, default=True)
    scan(parser.parse_args())
