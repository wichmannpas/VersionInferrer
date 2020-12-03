#!/usr/bin/env python3
import pickle
from argparse import ArgumentParser
from datetime import datetime

from tqdm import tqdm

from settings import BACKEND, CACHE_DIR


def main():
    parser = ArgumentParser(description='a')
    parser.add_argument('--limit-per-package', type=int, default=25)
    arguments = parser.parse_args()

    cache_file_path = CACHE_DIR / 'popular_files.pickle'

    refresh = datetime.now()

    packages = BACKEND.retrieve_packages()
    progress_packages = tqdm(packages)
    result = {}
    for software_package in progress_packages:
        progress_packages.set_description('{:>15s}'.format(software_package.name[:15]))
        result[software_package] = BACKEND.retrieve_static_files_popular_for_software_package(
            software_package, limit=arguments.limit_per_package)

    with cache_file_path.open('wb') as cache_file:
        pickle.dump({
            'refresh': refresh,
            'data': result,
        }, cache_file)


if __name__ == '__main__':
    main()
