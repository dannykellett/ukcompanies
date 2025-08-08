"""Unit tests for configuration module."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError as PydanticValidationError

from ukcompanies.config import (
    BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    SANDBOX_URL,
    Config,
)


class TestConfig:
    """Test configuration class."""

    def test_minimal_config(self):
        """Test creating config with minimal required fields."""
        config = Config(api_key="test-api-key-12345678901234567890")
        assert config.api_key == "test-api-key-12345678901234567890"
        assert config.base_url == BASE_URL
        assert config.timeout == DEFAULT_TIMEOUT
        assert config.max_retries == DEFAULT_MAX_RETRIES
        assert config.use_sandbox is False

    def test_full_config(self):
        """Test creating config with all fields."""
        config = Config(
            api_key="test-api-key-12345678901234567890",
            base_url="https://custom.api.com",
            timeout=60.0,
            max_retries=5,
            use_sandbox=False
        )
        assert config.api_key == "test-api-key-12345678901234567890"
        assert config.base_url == "https://custom.api.com"
        assert config.timeout == 60.0
        assert config.max_retries == 5

    def test_sandbox_mode(self):
        """Test sandbox mode overrides base URL."""
        config = Config(
            api_key="test-api-key-12345678901234567890",
            use_sandbox=True
        )
        assert config.base_url == SANDBOX_URL

    def test_api_key_validation(self):
        """Test API key validation."""
        # Empty API key
        with pytest.raises(PydanticValidationError) as exc_info:
            Config(api_key="")
        assert "API key cannot be empty" in str(exc_info.value)

        # Whitespace-only API key
        with pytest.raises(PydanticValidationError) as exc_info:
            Config(api_key="   ")
        assert "API key cannot be empty" in str(exc_info.value)

        # API key with whitespace is trimmed
        config = Config(api_key="  test-key-12345678901234567890  ")
        assert config.api_key == "test-key-12345678901234567890"

    def test_timeout_validation(self):
        """Test timeout validation."""
        # Negative timeout
        with pytest.raises(PydanticValidationError) as exc_info:
            Config(api_key="test-key", timeout=-1)
        assert "Timeout must be positive" in str(exc_info.value)

        # Zero timeout
        with pytest.raises(PydanticValidationError) as exc_info:
            Config(api_key="test-key", timeout=0)
        assert "Timeout must be positive" in str(exc_info.value)

        # Timeout too large
        with pytest.raises(PydanticValidationError) as exc_info:
            Config(api_key="test-key", timeout=301)
        assert "Timeout cannot exceed 300 seconds" in str(exc_info.value)

    def test_max_retries_validation(self):
        """Test max retries validation."""
        # Negative retries
        with pytest.raises(PydanticValidationError) as exc_info:
            Config(api_key="test-key", max_retries=-1)
        assert "Max retries cannot be negative" in str(exc_info.value)

        # Too many retries
        with pytest.raises(PydanticValidationError) as exc_info:
            Config(api_key="test-key", max_retries=11)
        assert "Max retries cannot exceed 10" in str(exc_info.value)

    def test_base_url_trailing_slash_removal(self):
        """Test that trailing slashes are removed from base URL."""
        config = Config(
            api_key="test-key",
            base_url="https://api.example.com/"
        )
        assert config.base_url == "https://api.example.com"

    def test_from_env_with_all_vars(self):
        """Test creating config from environment variables."""
        env_vars = {
            "COMPANIES_HOUSE_API_KEY": "env-api-key-12345678901234567890",
            "COMPANIES_HOUSE_BASE_URL": "https://env.api.com",
            "COMPANIES_HOUSE_USE_SANDBOX": "true",
            "COMPANIES_HOUSE_TIMEOUT": "45.5",
            "COMPANIES_HOUSE_MAX_RETRIES": "7"
        }

        with patch.dict(os.environ, env_vars):
            config = Config.from_env()

        assert config.api_key == "env-api-key-12345678901234567890"
        assert config.base_url == SANDBOX_URL  # Sandbox overrides base URL
        assert config.use_sandbox is True
        assert config.timeout == 45.5
        assert config.max_retries == 7

    def test_from_env_with_partial_vars(self):
        """Test creating config from partial environment variables."""
        env_vars = {
            "COMPANIES_HOUSE_API_KEY": "env-api-key-12345678901234567890",
            "COMPANIES_HOUSE_USE_SANDBOX": "false"
        }

        with patch.dict(os.environ, env_vars):
            config = Config.from_env()

        assert config.api_key == "env-api-key-12345678901234567890"
        assert config.base_url == BASE_URL
        assert config.use_sandbox is False
        assert config.timeout == DEFAULT_TIMEOUT
        assert config.max_retries == DEFAULT_MAX_RETRIES

    def test_from_env_with_invalid_values(self):
        """Test that invalid env values are ignored."""
        env_vars = {
            "COMPANIES_HOUSE_API_KEY": "env-api-key-12345678901234567890",
            "COMPANIES_HOUSE_TIMEOUT": "invalid",
            "COMPANIES_HOUSE_MAX_RETRIES": "not-a-number"
        }

        with patch.dict(os.environ, env_vars):
            config = Config.from_env()

        # Invalid values should be ignored, defaults used
        assert config.timeout == DEFAULT_TIMEOUT
        assert config.max_retries == DEFAULT_MAX_RETRIES

    def test_from_env_with_kwargs_override(self):
        """Test that kwargs override environment variables."""
        env_vars = {
            "COMPANIES_HOUSE_API_KEY": "env-api-key",
            "COMPANIES_HOUSE_TIMEOUT": "30"
        }

        with patch.dict(os.environ, env_vars):
            config = Config.from_env(
                api_key="override-key-12345678901234567890",
                timeout=90.0
            )

        assert config.api_key == "override-key-12345678901234567890"
        assert config.timeout == 90.0

    def test_from_env_without_api_key(self):
        """Test that missing API key raises error."""
        # Clear any existing env var
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(PydanticValidationError) as exc_info:
                Config.from_env()
            assert "api_key" in str(exc_info.value).lower()
