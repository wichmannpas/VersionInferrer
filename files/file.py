from abc import abstractproperty, ABCMeta
from typing import List

from base.checksum import calculate_checksum


class File(metaclass=ABCMeta):
    """
    This is the abstract base class for a static file of a specific type.

    The interface is used to pre- and post-process static files and to
    determine whether a file is a static file (of a specific type).
    """
    USUAL_FILE_NAME_EXTENSIONS: List[str]
    USE_FOR_ANALYSIS: bool
    USE_FOR_INDEX: bool

    file_name: str
    raw_content: bytes

    def __init__(self, file_name: str, raw_content: bytes):
        self.file_name = file_name
        self.raw_content = raw_content

        if not self.matches_file_type:
            raise ValueError(
                'not a static file of type {}'.format(self.__class__.__name__)
            )

    def __repr__(self) -> str:
        return "<{} '{}'>".format(str(self.__class__.__name__), str(self))

    def __str__(self) -> str:
        return self.file_name

    @property
    def checksum(self) -> bytes:
        """
        Calculate the checksum of the normalized content.

        Does not necessarily utilize the same method for all file types.
        """
        return calculate_checksum(self.normalized_content)

    @property
    def has_usual_file_name_extension(self) -> bool:
        """Whether the file has a usual file name extension."""
        return any(
            self.file_name.endswith('.' + extension)
            for extension in self.USUAL_FILE_NAME_EXTENSIONS)

    @abstractproperty
    def matches_file_type(self) -> bool:
        """Whether the current instance is a static file of this type."""

    @abstractproperty
    def normalized_content(self) -> bytes:
        """
        The content of this static file normalized for this file type.
        """
