from staticfiles.static_file import StaticFile


class CssFile(StaticFile):
    """
    A CSS file.
    """
    USUAL_FILE_NAME_EXTENSIONS = [
        'css',
        'less',
        'scss',
    ]
    USE_FOR_ANALYSIS = True
    USE_FOR_INDEX = True

    @property
    def matches_file_type(self) -> bool:
        """Whether the current instance is a static file of this type."""
        return self.has_usual_file_name_extension

    @property
    def normalized_content(self) -> bytes:
        """
        The content of this static file normalized for this file type.
        """
        # TODO: do actual normalization
        return self.raw_content
