"""Custom exception hierarchy for UK Companies API client.

This module defines custom exceptions for handling various error scenarios
when interacting with the Companies House API.
"""


class CompaniesHouseError(Exception):
    """Base exception for all Companies House API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            status_code: HTTP status code if applicable
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(CompaniesHouseError):
    """Raised when authentication fails (401 status)."""

    def __init__(self, message: str = "Authentication failed") -> None:
        """Initialize authentication error."""
        super().__init__(message, status_code=401)


class RateLimitError(CompaniesHouseError):
    """Raised when rate limit is exceeded (429 status)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        remaining: int | None = None,
        limit: int | None = None,
    ) -> None:
        """Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            remaining: Remaining requests in current window
            limit: Total request limit for the window
        """
        super().__init__(message, status_code=429)
        self.retry_after = retry_after
        self.remaining = remaining
        self.limit = limit


class NotFoundError(CompaniesHouseError):
    """Raised when a resource is not found (404 status)."""

    def __init__(self, message: str = "Resource not found") -> None:
        """Initialize not found error."""
        super().__init__(message, status_code=404)


class ValidationError(CompaniesHouseError):
    """Raised when data validation fails."""

    def __init__(self, message: str = "Validation failed") -> None:
        """Initialize validation error."""
        super().__init__(message, status_code=400)


class ServerError(CompaniesHouseError):
    """Raised when server returns 5xx status."""

    def __init__(self, message: str = "Server error", status_code: int = 500) -> None:
        """Initialize server error."""
        super().__init__(message, status_code=status_code)


class NetworkError(CompaniesHouseError):
    """Raised when network connection fails."""

    def __init__(self, message: str = "Network connection failed") -> None:
        """Initialize network error."""
        super().__init__(message, status_code=None)
