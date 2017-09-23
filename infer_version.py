#!/usr/bin/env python3
from argparse import ArgumentParser


def main(arguments):
    


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('url')

    args = parser.parse_args()
    print(args.url)
