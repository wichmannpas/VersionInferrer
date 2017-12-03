import json
from typing import Union

from base.utils import normalize_data
from files.file import File


class JsonFile(File):
    """
    A JSON file.
    """
    USUAL_FILE_NAME_EXTENSIONS = [
        'json',
    ]
    USE_FOR_ANALYSIS = True
    USE_FOR_INDEX = True

    @property
    def matches_file_type(self) -> bool:
        """Whether the current instance is a static file of this type."""
        if self.raw_content is not None and self.normalized_content is None:
            # normalization fails
            return False
        return self.has_usual_file_name_extension

    @property
    def normalized_content(self) -> Union[bytes, None]:
        """
        The content of this static file normalized for this file type.
        """
        try:
            data = json.loads(self.raw_content.decode())
            return normalize_data(data)
        except (TypeError, ValueError):
            return None
