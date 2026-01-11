from app.domain.errors.domain_errors import Error
from app.domain.errors.error_codes import ErrorCode


class HighlightNotFoundError(Error):
    def __init__(self, highlight_id: str):
        super().__init__(
            f"Highlight with ID {highlight_id} not found", ErrorCode.NOT_FOUND
        )
