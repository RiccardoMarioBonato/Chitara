from typing import Optional


class APIError(Exception):
    """Raised when the Suno API returns an error or is unreachable."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
