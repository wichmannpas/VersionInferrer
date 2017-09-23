import os


# General settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Backend
from backends.sqlite import SqliteBackend
BACKEND = SqliteBackend(os.path.join(BASE_DIR, 'db.sqlite3'))


# Cache
CACHE_DIR = os.path.join(BASE_DIR, 'cache')


# Indexing
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
