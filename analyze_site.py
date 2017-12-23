#!/usr/bin/env python3
from argparse import ArgumentParser, Namespace

from analysis.website_analyzer import WebsiteAnalyzer


def analyze(arguments: Namespace):
    """Analyse a site to infer its used software package(s) and versions."""
    analyzer = WebsiteAnalyzer(
        primary_url=arguments.primary_url)

    if arguments.max_iterations:
        analyzer.max_iterations = arguments.max_iterations
    if arguments.guess_limit:
        analyzer.guess_limit = arguments.guess_limit
    if arguments.min_assets_per_iteration:
        analyzer.min_assets_per_iteration = arguments.min_assets_per_iteration,
    if arguments.max_assets_per_iteration:
        analyzer.max_assets_per_iteration = arguments.max_assets_per_iteration,

    result = analyzer.analyze()

    print(analyzer.get_statistics())

    if not result:
        return

    print(result)

    more_recent = analyzer.more_recent_version(
        guess.software_version for guess in result)

    if more_recent:
        print(
            'More recent version {} released, possibly outdated!'.format(
                more_recent))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('primary_url')

    parser.add_argument('-i', '--max-iterations', type=int)
    parser.add_argument('-l', '--guess-limit', type=int)
    parser.add_argument('--min-assets-per-iteration', type=int)
    parser.add_argument('--max-assets-per-iteration', type=int)

    analyze(parser.parse_args())
