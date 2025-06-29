"""Custom exceptions for the Codegen SDK."""

from typing import Any


class CodegenError(Exception):
    """Base exception for all Codegen SDK errors."""

    def __init__(self, message: str, status_code: int | None = None, response_data: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}


class AuthenticationError(CodegenError):
    """Raised when authentication fails."""

    pass


class AuthorizationError(CodegenError):
    """Raised when the user lacks permission for the requested operation."""

    pass


class NotFoundError(CodegenError):
    """Raised when a requested resource is not found."""

    pass


class ValidationError(CodegenError):
    """Raised when request validation fails."""

    pass


class RateLimitError(CodegenError):
    """Raised when rate limits are exceeded."""

    pass


class ServerError(CodegenError):
    """Raised when the server encounters an error."""

    pass


class APIError(CodegenError):
    """Generic API error for unexpected responses."""

    pass


def handle_api_error(status_code: int | None, message: str, response_data: dict[str, Any] | None = None) -> CodegenError:
    """Convert HTTP status codes to appropriate exception types."""
    if status_code is None:
        return APIError(message, status_code, response_data)
    elif status_code == 401:
        return AuthenticationError(message, status_code, response_data)
    elif status_code == 403:
        return AuthorizationError(message, status_code, response_data)
    elif status_code == 404:
        return NotFoundError(message, status_code, response_data)
    elif status_code == 422:
        return ValidationError(message, status_code, response_data)
    elif status_code == 429:
        return RateLimitError(message, status_code, response_data)
    elif status_code is not None and 500 <= status_code < 600:
        return ServerError(message, status_code, response_data)
    else:
        return APIError(message, status_code, response_data)
