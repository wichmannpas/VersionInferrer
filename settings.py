import os


# General settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FORMAT = '%(asctime)-15s: %(message)s'


# Backend
from backends.postgresql import PostgresqlBackend
BACKEND = PostgresqlBackend(database='ba', user='ba', password='ba')
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
    '.png',
    '.scss',
    '.svg',
    '.ttf',
    '.txt',
]
STEP_LIMIT = 3
