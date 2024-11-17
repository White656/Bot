class OpenAIRequestError(Exception):
    def __init__(self, error: str | dict, detail: str | None = None):
        error_str = str(error) if not isinstance(error, str) else error
        detail_str = str(detail) if detail and not isinstance(detail, str) else detail

        description = 'Unsuccessfully request to OpenAI API: {description}'.format(
            description=' - '.join((error_str, detail_str)) if detail_str else error_str
        )
        super().__init__(description)
