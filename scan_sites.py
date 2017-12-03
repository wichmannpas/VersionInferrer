#!/usr/bin/env python3
from argparse import ArgumentParser, Namespace

from scanning.scanner import Scanner


def scan(arguments: Namespace):
    """Scan sites."""
    scanner = Scanner()
    if arguments.threads:
        scanner.threads = arguments.threads
    scanner.scan_sites(arguments.count)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('count', type=int, default=1000)
    parser.add_argument('--threads', type=int, default=80)
    scan(parser.parse_args())
