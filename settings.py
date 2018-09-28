import os
import sys


# General settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CVE_STATISTICS_FILE = os.path.join(BASE_DIR, 'vendor/cve_statistics')

HTTP_TIMEOUT = 3


# Analysis
GUESS_LIMIT = 7
GUESS_IGNORE_DISTANCE = 3  # The minimum distance of the best guess strength to inferior guesses to ignore them
GUESS_IGNORE_MIN_POSITIVE = 2  # The minumum positive count the best guess needs to have in order to ignore guesses at all
GUESS_RELATIVE_IGNORE_DISTANCE = 0.3  # The relative distance of the best guess strength to inferior guesses to ignore them
HTML_PARSER = 'html.parser'
HTML_RELEVANT_ELEMENTS = [
    'a',  # i.e. directory indexes
    'link',
    'script',
    'style',
]
ITERATION_MIN_IMPROVEMENT = 0.5 # The minimum increase in the difference to the best guess required per iteration
MAX_ITERATIONS = 15
MAX_ITERATIONS_WITHOUT_IMPROVEMENT = 3 # The maximum number of consecutive iterations with improvement less than min
MIN_ASSETS_PER_ITERATION = 2
MAX_ASSETS_PER_ITERATION = 8
MIN_ABSOLUTE_SUPPORT = 10
MIN_SUPPORT = 0.2
SUPPORTED_SCHEMES = [
    'http',
    'https',
]
POSITIVE_MATCH_WEIGHT = 1
NEGATIVE_MATCH_WEIGHT = 0.1
FAILED_ASSET_WEIGHT = 1


# Backend
from backends.sqlite import SqliteBackend
BACKEND = SqliteBackend(os.path.join(BASE_DIR, 'db.sqlite3'))


# Cache
CACHE_DIR = os.path.join(BASE_DIR, 'cache')


OVERWRITABLE_SETTINGS = (
    ('GUESS_LIMIT', int),
    ('GUESS_IGNORE_DISTANCE', float),
    ('GUESS_IGNORE_MIN_POSITIVE', float),
    ('GUESS_RELATIVE_IGNORE_DISTANCE', float),
    ('ITERATION_MIN_IMPROVEMENT', float),
    ('MAX_ITERATIONS', int),
    ('MAX_ITERATIONS_WITHOUT_IMPROVEMENT', int),
    ('MIN_ABSOLUTE_SUPPORT', float),
    ('MIN_SUPPORT', float),
    ('POSITIVE_MATCH_WEIGHT', float),
    ('NEGATIVE_MATCH_WEIGHT', float),
    ('FAILED_ASSET_WEIGHT', float),
    ('MIN_ASSETS_PER_ITERATION', int),
)


# import local settings if not in unit test mode
if 'unittest' not in sys.modules:
    try:
        from settings_local import *
    except ImportError as e:
        if e.name != 'settings_local':
            raise

        # local settings are optional
