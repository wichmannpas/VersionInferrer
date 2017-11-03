import os
import sys


# General settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Analysis
GUESS_MIN_DIFFERENCE = 5  # The minimum difference of best guess
HTML_PARSER = 'html.parser'
HTML_RELEVANT_ELEMENTS = [
    'a',  # i.e. directory indexes
    'link',
    'script',
    'style',
]
MIN_ABSOLUTE_SUPPORT = 3
MIN_SUPPORT = 0.2
SUPPORTED_SCHEMES = [
    'http',
    'https',
]


# Backend
from backends.sqlite import SqliteBackend
BACKEND = SqliteBackend(os.path.join(BASE_DIR, 'db.sqlite3'))


# Cache
CACHE_DIR = os.path.join(BASE_DIR, 'cache')


# import local settings if not in unit test mode
if 'unittest' not in sys.modules:
    from settings_local import *
