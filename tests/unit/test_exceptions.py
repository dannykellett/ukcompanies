"""Unit tests for exceptions module."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import httpx
import pytest

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
    
    def test_with_retry_after(self):
        """Test with retry_after value."""
        error = RateLimitError(retry_after=60.5)
        assert "retry after 60.5 seconds" in error.message
        assert error.retry_after == 60.5
    
    def test_with_reset_time(self):
        """Test with rate_limit_reset datetime."""
        from datetime import timedelta
        future_time = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=30)
        error = RateLimitError(rate_limit_reset=future_time)
        assert "resets in" in error.message
        assert error.rate_limit_reset == future_time
    
    def test_with_all_metadata(self):
        """Test with all retry metadata."""
        reset_time = datetime.now(timezone.utc)
        error = RateLimitError(
            message="Custom message",
            retry_after=60.0,
            rate_limit_remain=0,
            rate_limit_limit=600,
            rate_limit_reset=reset_time
        )
        assert "retry after 60.0 seconds" in error.message
        assert error.retry_after == 60.0
        assert error.rate_limit_remain == 0
        assert error.rate_limit_limit == 600
        assert error.rate_limit_reset == reset_time
    
    def test_from_response_with_headers(self):
        """Test creating from response with rate limit headers."""
        future_timestamp = int(datetime.now(timezone.utc).timestamp()) + 60
        response = MagicMock(spec=httpx.Response)
        response.headers = {
            "X-Ratelimit-Remain": "10",
            "X-Ratelimit-Limit": "600",
            "X-Ratelimit-Reset": str(future_timestamp),
        }
        
        error = RateLimitError.from_response(response)
        assert error.rate_limit_remain == 10
        assert error.rate_limit_limit == 600
        assert error.rate_limit_reset is not None
        assert error.retry_after is not None
        assert error.retry_after > 0
    
    def test_from_response_missing_headers(self):
        """Test creating from response without rate limit headers."""
        response = MagicMock(spec=httpx.Response)
        response.headers = {}
        
        error = RateLimitError.from_response(response)
        assert error.message == "Rate limit exceeded"
        assert error.rate_limit_remain is None
        assert error.rate_limit_limit is None
        assert error.rate_limit_reset is None
        assert error.retry_after is None
    
    def test_from_response_invalid_headers(self):
        """Test creating from response with invalid headers."""
        response = MagicMock(spec=httpx.Response)
        response.headers = {
            "X-Ratelimit-Remain": "not-a-number",
            "X-Ratelimit-Limit": "invalid",
            "X-Ratelimit-Reset": "bad-timestamp",
        }
        
        error = RateLimitError.from_response(response)
        assert error.rate_limit_remain is None
        assert error.rate_limit_limit is None
        assert error.rate_limit_reset is None
        assert error.retry_after is None
    
    def test_from_response_past_reset_time(self):
        """Test creating from response with past reset time."""
        past_timestamp = int(datetime.now(timezone.utc).timestamp()) - 60
        response = MagicMock(spec=httpx.Response)
        response.headers = {
            "X-Ratelimit-Reset": str(past_timestamp),
        }
        
        error = RateLimitError.from_response(response)
        assert error.rate_limit_reset is not None
        assert error.retry_after is None  # Past time, no retry_after


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