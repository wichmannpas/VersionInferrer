import logging
from typing import Union

from slimit import ast
from slimit.parser import Parser

from base.utils import normalize_data
from files.file import File


parser = Parser()


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
            parsed = parser.parse(content)
            parsed = ast_to_builtin(parsed)

            return normalize_data(parsed)
        except (SyntaxError, TypeError, ValueError):
            logging.warning(
                'failed to parse javascript file %s. Skipping abstract syntax tree construction',
                self.file_name)
            parsed = content
        try:
            return normalize_data(parsed)
        except (TypeError, ValueError):
            return None


def ast_to_builtin(data: object) -> object:
    """
    Model slimit.ast objects using only  built-in types.

    This makes use of the __dict__ attribute of the python objects.
    """
    if isinstance(data, ast.Node):
        return ast_to_builtin(data.__dict__)

    if isinstance(data, dict):
        return {
            key: ast_to_builtin(value)
            for key, value in data.items()
        }
    elif isinstance(data, (list, set, tuple)):
        return [
            ast_to_builtin(item)
            for item in data
        ]
    return data
