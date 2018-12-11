#!/usr/bin/env python3
import logging
import os
from argparse import ArgumentParser, Namespace

from base.utils import clean_path_name
from scanning.scanner import Scanner


def scan(arguments: Namespace):
    """Scan sites."""
    scanner = Scanner(arguments.identifier)
    if arguments.concurrent:
        scanner.concurrent = arguments.concurrent

    if arguments.log_dir:
        os.makedirs(arguments.log_dir, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(arguments.log_dir, clean_path_name(arguments.identifier)),
            format='%(asctime)-15s: %(message)s',
            level=logging.INFO)

    if arguments.persist_resources:
        # must not exist or be an existing *directory*
        assert os.path.isdir(arguments.persist_resources) or \
            not os.path.exists(arguments.persist_resources), 'invalid persist path'

        scanner.persist_resources = arguments.persist_resources

    urls = None
    if arguments.urls_from_file:
        with open(arguments.urls_from_file, 'r') as fh:
            urls = fh.read().splitlines()

    scanner.scan_sites(arguments.count, urls=urls, skip=arguments.skip)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('count', type=int, default=1000)
    parser.add_argument('--concurrent', '-c', type=int, default=80)
    parser.add_argument('--skip', '-s', type=int, default=0)
    parser.add_argument('--urls-from-file', type=str, help='Read newline-separated URLs from file instead of majestic million')
    parser.add_argument('--identifier', '-i', type=str, help='An identifier for this scan.', required=True)
    parser.add_argument(
        '--persist-resources',
        '-p',
        help='Persist retrieved resources within the specified path for debugging purposes.')
    parser.add_argument(
        '--log-dir',
        '-l',
        help='Write log file with identifier as name within directory.')
    scan(parser.parse_args())
