#!/usr/bin/env python3
from argparse import ArgumentParser, Namespace

from analysis.website_analyzer import WebsiteAnalyzer
from settings import BACKEND


def analyze(arguments: Namespace):
    """Analyse a site to infer its used software package(s) and versions."""
    analyzer = WebsiteAnalyzer(
        primary_url=arguments.primary_url)
    analyzer.analyze(
        max_iterations=arguments.max_iterations,
        guess_limit=arguments.guess_limit,
        min_assets_per_iteration=arguments.min_assets_per_iteration,
        max_assets_per_iteration=arguments.max_assets_per_iteration)

    print(analyzer.get_statistics())


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('primary_url')

    parser.add_argument('-i', '--max-iterations', type=int, default=15)
    parser.add_argument('-l', '--guess-limit', type=int, default=7)
    parser.add_argument('--min-assets-per-iteration', type=int, default=2)
    parser.add_argument('--max-assets-per-iteration', type=int, default=8)

    analyze(parser.parse_args())
