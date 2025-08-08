"""Configuration module for UK Companies API client.

This module handles client configuration, API endpoints, and constants.
"""

import contextlib
import os
from typing import Any

from pydantic import BaseModel, Field, field_validator

# API Endpoints
BASE_URL = "https://api.company-information.service.gov.uk"
SANDBOX_URL = "https://api-sandbox.company-information.service.gov.uk"

# Default settings
DEFAULT_TIMEOUT = 30.0  # seconds
DEFAULT_MAX_RETRIES = 3
RATE_LIMIT_WINDOW = 300  # 5 minutes in seconds
RATE_LIMIT_MAX_REQUESTS = 600  # Max requests per window

# Retry configuration defaults
DEFAULT_AUTO_RETRY = True
DEFAULT_BACKOFF_STRATEGY = "exponential"
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 60.0  # seconds
JITTER_RANGE = 1.0  # seconds


class Config(BaseModel):
    """Configuration for the Companies House API client."""

    api_key: str = Field(..., description="API key for authentication")
    base_url: str = Field(default=BASE_URL, description="Base URL for API")
    timeout: float = Field(default=DEFAULT_TIMEOUT, description="Request timeout in seconds")
    max_retries: int = Field(default=DEFAULT_MAX_RETRIES, description="Maximum retry attempts")
    use_sandbox: bool = Field(default=False, description="Use sandbox environment")

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key format."""
        if not v or not v.strip():
            raise ValueError("API key cannot be empty")
        return v.strip()

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: float) -> float:
        """Validate timeout value."""
        if v <= 0:
            raise ValueError("Timeout must be positive")
        if v > 300:
            raise ValueError("Timeout cannot exceed 300 seconds")
        return v

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v: int) -> int:
        """Validate max retries."""
        if v < 0:
            raise ValueError("Max retries cannot be negative")
        if v > 10:
            raise ValueError("Max retries cannot exceed 10")
        return v

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate and clean base URL."""
        # Remove trailing slash if present
        return v.rstrip("/")

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization processing."""
        # Override base_url if use_sandbox is True
        if self.use_sandbox:
            self.base_url = SANDBOX_URL

    @classmethod
    def from_env(cls, **kwargs: Any) -> "Config":
        """Create config from environment variables.

        Environment variables:
        - COMPANIES_HOUSE_API_KEY: API key for authentication
        - COMPANIES_HOUSE_BASE_URL: Optional custom base URL
        - COMPANIES_HOUSE_USE_SANDBOX: Set to 'true' for sandbox mode
        - COMPANIES_HOUSE_TIMEOUT: Request timeout in seconds
        - COMPANIES_HOUSE_MAX_RETRIES: Maximum retry attempts

        Args:
            **kwargs: Additional config values to override environment

        Returns:
            Config instance
        """
        env_config: dict[str, Any] = {}

        # Get API key from environment
        api_key = os.getenv("COMPANIES_HOUSE_API_KEY")
        if api_key:
            env_config["api_key"] = api_key

        # Get optional settings from environment
        base_url = os.getenv("COMPANIES_HOUSE_BASE_URL")
        if base_url:
            env_config["base_url"] = base_url

        use_sandbox = os.getenv("COMPANIES_HOUSE_USE_SANDBOX", "").lower() == "true"
        env_config["use_sandbox"] = use_sandbox

        timeout = os.getenv("COMPANIES_HOUSE_TIMEOUT")
        if timeout:
            with contextlib.suppress(ValueError):
                env_config["timeout"] = float(timeout)

        max_retries = os.getenv("COMPANIES_HOUSE_MAX_RETRIES")
        if max_retries:
            with contextlib.suppress(ValueError):
                env_config["max_retries"] = int(max_retries)

        # Override with any provided kwargs
        env_config.update(kwargs)

        return cls(**env_config)
