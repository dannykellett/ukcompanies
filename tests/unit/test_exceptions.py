"""Unit tests for exceptions module."""


from ukcompanies.exceptions import (
    AuthenticationError,
    CompaniesHouseError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)


class TestCompaniesHouseError:
    """Test base exception class."""

    def test_base_exception_with_message(self):
        """Test creating base exception with message."""
        error = CompaniesHouseError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.status_code is None

    def test_base_exception_with_status_code(self):
        """Test creating base exception with status code."""
        error = CompaniesHouseError("Test error", status_code=500)
        assert error.message == "Test error"
        assert error.status_code == 500


class TestAuthenticationError:
    """Test authentication error."""

    def test_default_message(self):
        """Test default error message."""
        error = AuthenticationError()
        assert error.message == "Authentication failed"
        assert error.status_code == 401

    def test_custom_message(self):
        """Test custom error message."""
        error = AuthenticationError("Invalid API key")
        assert error.message == "Invalid API key"
        assert error.status_code == 401


class TestRateLimitError:
    """Test rate limit error."""

    def test_default_values(self):
        """Test default error values."""
        error = RateLimitError()
        assert error.message == "Rate limit exceeded"
        assert error.status_code == 429
        assert error.retry_after is None
        assert error.rate_limit_remain is None
        assert error.rate_limit_limit is None
        assert error.rate_limit_reset is None

    def test_with_retry_metadata(self):
        """Test with retry metadata."""
        from datetime import datetime, timezone
        reset_time = datetime.now(timezone.utc)
        error = RateLimitError(
            message="Custom message",
            retry_after=60,
            rate_limit_remain=0,
            rate_limit_limit=600,
            rate_limit_reset=reset_time
        )
        assert error.message == "Custom message (retry after 60.0 seconds)"
        assert error.retry_after == 60
        assert error.rate_limit_remain == 0
        assert error.rate_limit_limit == 600
        assert error.rate_limit_reset == reset_time


class TestNotFoundError:
    """Test not found error."""

    def test_default_message(self):
        """Test default error message."""
        error = NotFoundError()
        assert error.message == "Resource not found"
        assert error.status_code == 404

    def test_custom_message(self):
        """Test custom error message."""
        error = NotFoundError("Company not found")
        assert error.message == "Company not found"
        assert error.status_code == 404


class TestValidationError:
    """Test validation error."""

    def test_default_message(self):
        """Test default error message."""
        error = ValidationError()
        assert error.message == "Validation failed"
        assert error.status_code == 400

    def test_custom_message(self):
        """Test custom error message."""
        error = ValidationError("Invalid company number")
        assert error.message == "Invalid company number"
        assert error.status_code == 400


class TestServerError:
    """Test server error."""

    def test_default_values(self):
        """Test default error values."""
        error = ServerError()
        assert error.message == "Server error"
        assert error.status_code == 500

    def test_custom_status_code(self):
        """Test custom status code."""
        error = ServerError("Gateway timeout", status_code=504)
        assert error.message == "Gateway timeout"
        assert error.status_code == 504


class TestNetworkError:
    """Test network error."""

    def test_default_message(self):
        """Test default error message."""
        error = NetworkError()
        assert error.message == "Network connection failed"
        assert error.status_code is None

    def test_custom_message(self):
        """Test custom error message."""
        error = NetworkError("Connection timeout")
        assert error.message == "Connection timeout"
        assert error.status_code is None
