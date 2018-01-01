import logging
from typing import Union

import pyjsparser
from pyjsparser import JsSyntaxError

from base.utils import normalize_data
from files.file import File


class JavascriptFile(File):
    """
    A JavaScript file.
    """
    USUAL_FILE_NAME_EXTENSIONS = [
        'js',
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
            content = self.raw_content.decode()
        except UnicodeDecodeError:
            return None

        if not self.has_usual_file_name_extension:
            # skip parsing if file extension does not indicate javascript
            return None

        try:
            parsed = pyjsparser.parse(content)

            return normalize_data(parsed)
        except (JsSyntaxError, TypeError, ValueError):
            logging.warning(
                'failed to parse javascript file %s. Skipping abstract syntax tree construction',
                self.file_name)
            parsed = content
        try:
            return normalize_data(parsed)
        except (TypeError, ValueError):
            return None
