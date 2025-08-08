"""Core async client for UK Companies API."""

import re
from collections.abc import Callable
from datetime import datetime
from typing import Any

import httpx
import structlog

from .auth import AuthHandler
from .client_endpoints import EndpointMixin
from .config import (
    BASE_DELAY,
    DEFAULT_AUTO_RETRY,
    DEFAULT_BACKOFF_STRATEGY,
    JITTER_RANGE,
    MAX_DELAY,
    Config,
)
from .exceptions import (
    AuthenticationError,
    CompaniesHouseError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .models.rate_limit import RateLimitInfo
from .retry import RetryConfig, RetryManager

logger = structlog.get_logger(__name__)


class AsyncClient(EndpointMixin):
    """Async client for interacting with the Companies House API."""

    # Company number validation patterns
    COMPANY_NUMBER_PATTERN = re.compile(r"^[0-9A-Z]{8}$")
    COMPANY_NUMBER_NUMERIC = re.compile(r"^[0-9]{7,8}$")

    def __init__(
        self,
        api_key: str | None = None,
        config: Config | None = None,
        auto_retry: bool = DEFAULT_AUTO_RETRY,
        max_retries: int | None = None,
        backoff: str = DEFAULT_BACKOFF_STRATEGY,
        on_retry: Callable | None = None,
        **kwargs: Any
    ) -> None:
        """Initialize the async client.

        Args:
            api_key: API key for authentication (overrides config)
            config: Configuration object (uses env if not provided)
            auto_retry: Whether to automatically retry on rate limit
            max_retries: Maximum number of retry attempts
            backoff: Backoff strategy ("exponential" or "fixed")
            on_retry: Optional callback for retry events
            **kwargs: Additional config parameters
        """
        # Build configuration
        if config:
            self.config = config
            # Override API key if provided separately
            if api_key:
                self.config.api_key = api_key
        else:
            # Create config from environment or provided values
            if api_key:
                kwargs["api_key"] = api_key
            self.config = Config.from_env(**kwargs)

        # Set up retry configuration
        self.retry_config = RetryConfig(
            auto_retry=auto_retry,
            max_retries=max_retries if max_retries is not None else self.config.max_retries,
            backoff=backoff,
            base_delay=BASE_DELAY,
            max_delay=MAX_DELAY,
            jitter_range=JITTER_RANGE,
            on_retry=on_retry,
        )
        self.retry_manager = RetryManager(self.retry_config)

        # Initialize authentication
        self.auth = AuthHandler(self.config.api_key)

        # Validate API key format
        if not self.auth.validate_api_key_format():
            logger.warning("API key format appears invalid")

        # HTTP client will be initialized in __aenter__
        self._client: httpx.AsyncClient | None = None
        self._rate_limit_info: RateLimitInfo | None = None

        logger.info(
            "AsyncClient initialized",
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            sandbox=self.config.use_sandbox,
        )

    async def __aenter__(self) -> "AsyncClient":
        """Enter async context manager."""
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers=self.auth.get_headers(),
            follow_redirects=True,
        )
        logger.debug("HTTP client initialized")
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        if self._client:
            await self._client.aclose()
            logger.debug("HTTP client closed")

    @property
    def rate_limit_info(self) -> RateLimitInfo | None:
        """Get the most recent rate limit information.

        Returns:
            Rate limit info from last API response, or None
        """
        return self._rate_limit_info

    def validate_company_number(self, company_number: str) -> str:
        """Validate and normalize a company number.

        Args:
            company_number: Company registration number

        Returns:
            Normalized company number (8 characters, uppercase)

        Raises:
            ValidationError: If company number is invalid
        """
        if not company_number:
            raise ValidationError("Company number cannot be empty")

        # Remove spaces and convert to uppercase
        normalized = company_number.strip().upper().replace(" ", "")

        # Check patterns
        if self.COMPANY_NUMBER_PATTERN.match(normalized):
            return normalized

        # Try numeric pattern with padding
        if self.COMPANY_NUMBER_NUMERIC.match(normalized):
            # Pad with leading zeros to 8 characters
            return normalized.zfill(8)

        raise ValidationError(
            f"Invalid company number format: {company_number}. "
            "Must be 8 characters (alphanumeric) or 7-8 digits."
        )

    def _extract_rate_limit_info(self, response: httpx.Response) -> RateLimitInfo | None:
        """Extract rate limit information from response headers.

        Args:
            response: HTTP response object

        Returns:
            RateLimitInfo if headers present, None otherwise
        """
        headers = response.headers

        # Check for rate limit headers
        remain = headers.get("X-Ratelimit-Remain")
        limit = headers.get("X-Ratelimit-Limit")
        reset = headers.get("X-Ratelimit-Reset")
        retry_after = headers.get("Retry-After")

        if remain and limit and reset:
            try:
                info = RateLimitInfo(
                    remain=int(remain),
                    limit=int(limit),
                    reset=datetime.fromtimestamp(int(reset)),
                    retry_after=int(retry_after) if retry_after else None,
                )

                # Store for later access
                self._rate_limit_info = info

                # Log if getting close to limit
                if info.percent_remaining < 10:
                    logger.warning(
                        "Rate limit warning",
                        remaining=info.remain,
                        limit=info.limit,
                        percent_remaining=info.percent_remaining,
                    )
                else:
                    logger.debug(
                        "Rate limit status",
                        remaining=info.remain,
                        limit=info.limit,
                    )

                return info
            except (ValueError, TypeError) as e:
                logger.error("Failed to parse rate limit headers", error=str(e))

        return None

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the API.

        Args:
            response: HTTP response object

        Raises:
            Appropriate exception based on status code
        """
        status = response.status_code

        # Try to get error message from response
        try:
            error_data = response.json()
            message = error_data.get("error", response.text)
        except Exception:
            message = response.text or f"HTTP {status} error"

        # Map status codes to exceptions
        if status == 401:
            raise AuthenticationError(f"Authentication failed: {message}")
        elif status == 404:
            raise NotFoundError(f"Resource not found: {message}")
        elif status == 429:
            # Use RateLimitError.from_response to extract all headers
            raise RateLimitError.from_response(response)
        elif status == 400:
            raise ValidationError(f"Invalid request: {message}")
        elif 500 <= status < 600:
            raise ServerError(f"Server error: {message}", status_code=status)
        else:
            raise CompaniesHouseError(f"API error: {message}", status_code=status)

    async def _request_without_retry(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            params: Query parameters
            json: JSON body data
            **kwargs: Additional arguments for httpx

        Returns:
            HTTP response object

        Raises:
            NetworkError: On connection failure
            Various API exceptions based on response
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        # Log request
        logger.debug(
            "Making API request",
            method=method,
            path=path,
            params=params,
        )

        try:
            response = await self._client.request(
                method=method, url=path, params=params, json=json, **kwargs
            )

            # Extract rate limit info from all responses
            self._extract_rate_limit_info(response)

            # Handle errors
            if response.status_code >= 400:
                self._handle_error_response(response)

            logger.debug(
                "Request successful",
                status=response.status_code,
                path=path,
            )

            return response

        except httpx.NetworkError as e:
            logger.error("Network error", error=str(e), path=path)
            raise NetworkError(f"Network error: {str(e)}") from e
        except httpx.TimeoutException as e:
            logger.error("Request timeout", error=str(e), path=path)
            raise NetworkError(f"Request timeout: {str(e)}") from e
        except CompaniesHouseError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error("Unexpected error", error=str(e), path=path)
            raise CompaniesHouseError(f"Unexpected error: {str(e)}") from e

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request with optional retry logic.

        Args:
            method: HTTP method
            path: API endpoint path
            params: Query parameters
            json: JSON body data
            **kwargs: Additional arguments

        Returns:
            HTTP response object
        """
        # Use retry logic if configured
        if self.retry_config.auto_retry:
            return await self.retry_manager.execute_with_retry(
                self._request_without_retry, method, path, params=params, json=json, **kwargs
            )
        else:
            return await self._request_without_retry(
                method, path, params=params, json=json, **kwargs
            )

    async def get(
        self, path: str, params: dict[str, Any] | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Make a GET request to the API.

        Args:
            path: API endpoint path
            params: Query parameters
            **kwargs: Additional arguments

        Returns:
            JSON response data
        """
        response = await self._request("GET", path, params=params, **kwargs)
        return response.json()  # type: ignore[no-any-return]

    async def post(
        self, path: str, json: dict[str, Any] | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Make a POST request to the API.

        Args:
            path: API endpoint path
            json: JSON body data
            **kwargs: Additional arguments

        Returns:
            JSON response data
        """
        response = await self._request("POST", path, json=json, **kwargs)
        return response.json()  # type: ignore[no-any-return]
