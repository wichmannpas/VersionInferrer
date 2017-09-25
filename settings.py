import logging
import os


# General settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FORMAT = '%(asctime)-15s: %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)


# Analysis
HTML_PARSER = 'html.parser'
HTML_RELEVANT_ELEMENTS = [
    'a',  # i.e. directory indexes
    'link',
    'script',
    'style',
]
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


# Indexing
MAX_WORKERS = 16
STATIC_FILE_EXTENSIONS = [
    '.css',
    '.gif',
    '.html',
    '.jpeg',
    '.jpg',
    '.js',
    '.json',
    '.png',
    '.scss',
    '.svg',
    '.ttf',
    '.txt',
]
STEP_LIMIT = 1000
