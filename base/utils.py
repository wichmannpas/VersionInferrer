import os


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
    Join multiple paths using os.path.join, remove leading slashes
    before.
    """
    url = args[0]
    if url.endswith('/'):
        url = url[:-1]
    path = ''
    if len(args) >= 2:
        path = join_paths(*args[1:])
    if path.startswith('/'):
        path = path[1:]
    # TODO: Normalize url before returning?
    return '/'.join([url, path])
