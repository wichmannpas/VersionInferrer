from typing import Union

from files.file import File


class ExtensionlessFile(File):
    """
    A file without an extension (README, CHANGES, Jenkinsfile)
    """

    USE_FOR_ANALYSIS = True
    USE_FOR_INDEX = True

    @property
    def matches_file_type(self) -> bool:
        """Whether the current instance is a static file of this type."""
        return '.' not in self.file_name

    @property
    def normalized_content(self) -> Union[bytes, None]:
        """
        The content of this static file normalized for this file type.
        """
        # TODO: do actual normalization
        return self.raw_content
