import os
from urllib.parse import urljoin

import msgpack
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


def normalize_data(data: object) -> bytes:
    """
    Normalize Python data into a bytes string.

    The purpose of the normalization is to transform data into
    its canonical form, thus making similar data which
    is supposed to be identical actually identical.
    """
    if isinstance(data, bytes):
        return data.strip()
    if isinstance(data, str):
        return data.strip().encode()
    if isinstance(data, dict):
        return msgpack.dumps(sorted([
            (normalize_data(key), normalize_data(value))
            for key, value in data.items()
        ]))
    if isinstance(data, (list, set, tuple)):
        return msgpack.dumps(sorted([
            normalize_data(item)
            for item in data
        ]))

    # use msgpack without further normalization. Might raise TypeError
    return msgpack.dumps(data)
