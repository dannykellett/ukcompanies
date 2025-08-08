"""Unit tests for authentication module."""

import base64

import pytest

from ukcompanies.auth import AuthHandler
from ukcompanies.exceptions import AuthenticationError


class TestAuthHandler:
    """Test authentication handler."""

    def test_init_with_valid_api_key(self):
        """Test initialization with valid API key."""
        handler = AuthHandler("test-api-key-12345678901234567890")
        assert handler.api_key == "test-api-key-12345678901234567890"

    def test_init_with_whitespace_api_key(self):
        """Test that API key whitespace is stripped."""
        handler = AuthHandler("  test-api-key-12345678901234567890  ")
        assert handler.api_key == "test-api-key-12345678901234567890"

    def test_init_with_empty_api_key(self):
        """Test that empty API key raises error."""
        with pytest.raises(AuthenticationError) as exc_info:
            AuthHandler("")
        assert "API key is required" in str(exc_info.value)

    def test_init_with_whitespace_only_api_key(self):
        """Test that whitespace-only API key raises error."""
        with pytest.raises(AuthenticationError) as exc_info:
            AuthHandler("   ")
        assert "API key is required" in str(exc_info.value)

    def test_init_with_none_api_key(self):
        """Test that None API key raises error."""
        with pytest.raises(AuthenticationError) as exc_info:
            AuthHandler(None)
        assert "API key is required" in str(exc_info.value)

    def test_generate_auth_header(self):
        """Test HTTP Basic Auth header generation."""
        handler = AuthHandler("test-api-key-12345678901234567890")

        # The header should be "Basic <base64(api_key:)>"
        expected_auth = base64.b64encode(b"test-api-key-12345678901234567890:").decode("ascii")
        expected_header = f"Basic {expected_auth}"

        headers = handler.get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == expected_header

    def test_get_headers(self):
        """Test getting authentication headers."""
        handler = AuthHandler("my-api-key-12345678901234567890")
        headers = handler.get_headers()

        assert isinstance(headers, dict)
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")

        # Verify the encoded value
        auth_value = headers["Authorization"].replace("Basic ", "")
        decoded = base64.b64decode(auth_value).decode("utf-8")
        assert decoded == "my-api-key-12345678901234567890:"

    def test_validate_api_key_format_valid(self):
        """Test API key format validation with valid keys."""
        # Valid long key
        handler = AuthHandler("valid-api-key-that-is-long-enough-12345")
        assert handler.validate_api_key_format() is True

        # Minimum length key (20 chars)
        handler = AuthHandler("12345678901234567890")
        assert handler.validate_api_key_format() is True

    def test_validate_api_key_format_invalid(self):
        """Test API key format validation with invalid keys."""
        # Too short
        handler = AuthHandler("short-key")
        assert handler.validate_api_key_format() is False

        # Common test values
        test_values = ["test", "demo", "example", "your-api-key", "TEST", "DEMO"]
        for test_val in test_values:
            # Need to pad to avoid init error
            padded = test_val + "x" * (20 - len(test_val))
            handler = AuthHandler(padded)
            # But check with original value
            handler.api_key = test_val
            assert handler.validate_api_key_format() is False

    def test_auth_header_persistence(self):
        """Test that auth header is generated once and persisted."""
        handler = AuthHandler("test-api-key-12345678901234567890")

        # Get headers multiple times
        headers1 = handler.get_headers()
        headers2 = handler.get_headers()

        # Should be the same object/value
        assert headers1["Authorization"] == headers2["Authorization"]
