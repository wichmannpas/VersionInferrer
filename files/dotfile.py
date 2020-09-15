from typing import Union

from files.file import File


class DotFile(File):
    """
    A dotfile (e.g., .eslintrc)
    """

    USE_FOR_ANALYSIS = True
    USE_FOR_INDEX = True

    @property
    def matches_file_type(self) -> bool:
        """Whether the current instance is a static file of this type."""
        return self.file_name.startswith('.')

    @property
    def normalized_content(self) -> Union[bytes, None]:
        """
        The content of this static file normalized for this file type.
        """
        # TODO: do actual normalization
        return self.raw_content
