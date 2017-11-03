try:
    from hashlib import blake2b
except ImportError:
    # support for older python versions
    from pyblake2 import blake2b


BUFFER_SIZE = 8000000


def calculate_checksum(data: bytes) -> bytes:
    """Calculate a checksum for raw data."""
    hasher = blake2b()
    hasher.update(data)
    return hasher.digest()[:16]


def calculate_file_checksum(file_path: str) -> bytes:
    """Calculate a checksum for a file."""
    hasher = blake2b()
    with open(file_path, 'rb') as fdes:
        while True:
            buf = fdes.read(BUFFER_SIZE)
            if not buf:
                break
            hasher.update(buf)

    return hasher.digest()[:16]
