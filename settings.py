import logging
import os


# General settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FORMAT = '%(asctime)-15s: %(message)s'
# TODO: Do not globally set logging format
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)


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
from backends.postgresql import PostgresqlBackend
BACKEND = PostgresqlBackend(host='127.0.0.1', database='ba', user='ba', password='ba')
#from backends.sqlite import SqliteBackend
#BACKEND = SqliteBackend(os.path.join(BASE_DIR, 'db.sqlite3'))


# Cache
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
