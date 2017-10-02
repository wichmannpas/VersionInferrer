import os
from urllib.parse import urljoin

from url_normalize import url_normalize


def join_paths(*args):
    """
    Join multiple paths using os.path.join, remove leading slashes
    before.
    """
    return os.path.join(args[0], *(
        arg[1:]
        if arg.startswith('/') else arg
        for arg in args[1:]))


def join_url(*args) -> str:
    """
    Join a base url and paths.
    """
    base_url = args[0]
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    path = ''
    if len(args) >= 2:
        path = join_paths(*args[1:])

    return url_normalize(urljoin(base_url, path))
