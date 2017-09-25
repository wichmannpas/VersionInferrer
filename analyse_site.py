#!/usr/bin/env python3
from argparse import ArgumentParser, Namespace

import requests

from analysis.analysis import extract_information, retrieve_included_assets
from settings import BACKEND


def analyse(arguments: Namespace):
    """Analyse a site to infer its used software package(s) and versions."""
    main_page_response = requests.get(arguments.url)

    first_estimates = extract_information(main_page_response.text)
    print(first_estimates)

    main_assets = retrieve_included_assets(main_page_response)
    for asset in main_assets:
        print(asset)
        print(BACKEND.retrieve_static_file_users_by_checksum(asset.checksum))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('url')

    analyse(parser.parse_args())
