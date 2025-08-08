"""Custom exception hierarchy for UK Companies API client.

This module defines custom exceptions for handling various error scenarios
when interacting with the Companies House API.
"""

import contextlib
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


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
        retry_after: float | None = None,
        rate_limit_remain: int | None = None,
        rate_limit_limit: int | None = None,
        rate_limit_reset: datetime | None = None,
    ) -> None:
        """Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            rate_limit_remain: Remaining requests in current window
            rate_limit_limit: Total request limit for the window
            rate_limit_reset: Datetime when rate limit resets
        """
        # Include retry info in message if available
        if retry_after is not None:
            message = f"{message} (retry after {retry_after:.1f} seconds)"
        elif rate_limit_reset is not None:
            wait_seconds = (rate_limit_reset - datetime.now(timezone.utc)).total_seconds()
            if wait_seconds > 0:
                message = f"{message} (resets in {wait_seconds:.1f} seconds)"

        super().__init__(message, status_code=429)
        self.retry_after = retry_after
        self.rate_limit_remain = rate_limit_remain
        self.rate_limit_limit = rate_limit_limit
        self.rate_limit_reset = rate_limit_reset

    @classmethod
    def from_response(cls, response: "httpx.Response") -> "RateLimitError":
        """Create RateLimitError from HTTP response.

        Args:
            response: HTTP response with 429 status

        Returns:
            RateLimitError with rate limit information
        """
        headers = response.headers

        # Extract rate limit information from headers
        rate_limit_remain = None
        if "X-Ratelimit-Remain" in headers:
            with contextlib.suppress(ValueError, TypeError):
                rate_limit_remain = int(headers["X-Ratelimit-Remain"])

        rate_limit_limit = None
        if "X-Ratelimit-Limit" in headers:
            with contextlib.suppress(ValueError, TypeError):
                rate_limit_limit = int(headers["X-Ratelimit-Limit"])

        rate_limit_reset = None
        retry_after = None
        if "X-Ratelimit-Reset" in headers:
            try:
                reset_timestamp = int(headers["X-Ratelimit-Reset"])
                rate_limit_reset = datetime.fromtimestamp(reset_timestamp, tz=timezone.utc)
                # Calculate retry_after from reset time
                current_time = datetime.now(timezone.utc)
                wait_seconds = (rate_limit_reset - current_time).total_seconds()
                if wait_seconds > 0:
                    retry_after = wait_seconds
            except (ValueError, TypeError):
                pass

        return cls(
            message="Rate limit exceeded",
            retry_after=retry_after,
            rate_limit_remain=rate_limit_remain,
            rate_limit_limit=rate_limit_limit,
            rate_limit_reset=rate_limit_reset,
        )


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
