from abc import abstractproperty, ABCMeta
from typing import List


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
