#!/usr/bin/env python3
from argparse import ArgumentParser, Namespace

from analysis.website_analyzer import WebsiteAnalyzer
from settings import BACKEND


def analyze(arguments: Namespace):
    """Analyse a site to infer its used software package(s) and versions."""
    analyzer = WebsiteAnalyzer(arguments.primary_url)
    analyzer.analyze()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('primary_url')

    analyze(parser.parse_args())
