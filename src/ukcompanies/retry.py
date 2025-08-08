"""Retry logic and rate limiting implementation."""

import asyncio
import random
from collections.abc import Callable
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


class BackoffStrategy(Enum):
    """Backoff strategy for retry logic."""

    EXPONENTIAL = "exponential"
    FIXED = "fixed"


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        auto_retry: bool = True,
        max_retries: int = 3,
        backoff: str = "exponential",
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter_range: float = 1.0,
        on_retry: Callable | None = None,
    ) -> None:
        """Initialize retry configuration.

        Args:
            auto_retry: Whether to automatically retry on rate limit
            max_retries: Maximum number of retry attempts
            backoff: Backoff strategy ("exponential" or "fixed")
            base_delay: Base delay in seconds for backoff calculation
            max_delay: Maximum delay in seconds between retries
            jitter_range: Maximum jitter to add to delay in seconds
            on_retry: Optional callback before each retry
        """
        self.auto_retry = auto_retry
        self.max_retries = max_retries
        self.backoff_strategy = BackoffStrategy(backoff)
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter_range = jitter_range
        self.on_retry = on_retry

        self._validate()

    def _validate(self) -> None:
        """Validate configuration parameters."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if self.max_delay <= 0:
            raise ValueError("max_delay must be positive")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.jitter_range < 0:
            raise ValueError("jitter_range must be non-negative")


def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter_range: float = 1.0,
) -> float:
    """Calculate exponential backoff with jitter.

    Args:
        attempt: Retry attempt number (0-based)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter_range: Maximum jitter to add in seconds

    Returns:
        Delay in seconds before next retry
    """
    delay = min(2**attempt * base_delay, max_delay)
    jitter = random.uniform(0, jitter_range)
    return delay + jitter


def fixed_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter_range: float = 1.0,
) -> float:
    """Calculate fixed backoff with optional jitter.

    Args:
        attempt: Retry attempt number (0-based, unused for fixed)
        base_delay: Fixed delay in seconds
        max_delay: Maximum delay in seconds (unused for fixed)
        jitter_range: Maximum jitter to add in seconds

    Returns:
        Delay in seconds before next retry
    """
    jitter = random.uniform(0, jitter_range)
    return base_delay + jitter


class RetryManager:
    """Manages retry logic for rate-limited requests."""

    def __init__(self, config: RetryConfig) -> None:
        """Initialize retry manager.

        Args:
            config: Retry configuration
        """
        self.config = config

    def _get_backoff_delay(self, attempt: int) -> float:
        """Get backoff delay for given attempt.

        Args:
            attempt: Retry attempt number (0-based)

        Returns:
            Delay in seconds
        """
        if self.config.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            return exponential_backoff(
                attempt,
                self.config.base_delay,
                self.config.max_delay,
                self.config.jitter_range,
            )
        else:
            return fixed_backoff(
                attempt,
                self.config.base_delay,
                self.config.max_delay,
                self.config.jitter_range,
            )

    def _extract_reset_time(self, response: httpx.Response) -> float | None:
        """Extract rate limit reset time from response headers.

        Args:
            response: HTTP response

        Returns:
            Seconds to wait until reset, or None if not available
        """
        reset_header = response.headers.get("X-Ratelimit-Reset")
        if not reset_header:
            return None

        try:
            reset_timestamp = int(reset_header)
            reset_time = datetime.fromtimestamp(reset_timestamp, tz=timezone.utc)
            current_time = datetime.now(timezone.utc)
            wait_seconds = (reset_time - current_time).total_seconds()

            if wait_seconds > 0:
                logger.debug(
                    "Rate limit reset time extracted",
                    reset_time=reset_time.isoformat(),
                    wait_seconds=wait_seconds,
                )
                return wait_seconds
            return None
        except (ValueError, TypeError) as e:
            logger.warning(
                "Failed to parse rate limit reset header",
                header_value=reset_header,
                error=str(e),
            )
            return None

    @staticmethod
    def _create_mock_429_response() -> Any:
        """Create a mock 429 response object for callbacks.

        This maintains backward compatibility with callback signatures
        that expect an HTTP response object.

        Returns:
            Mock response object with status_code and headers attributes
        """
        return type('Response', (), {
            'status_code': 429,
            'headers': {}
        })()

    async def execute_with_retry(
        self,
        request_func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> httpx.Response:
        """Execute request with retry logic.

        Args:
            request_func: Async function to execute
            *args: Positional arguments for request_func
            **kwargs: Keyword arguments for request_func

        Returns:
            HTTP response

        Raises:
            RateLimitError: When max retries exceeded
        """
        from .exceptions import NetworkError, RateLimitError

        attempt = 0

        while attempt <= self.config.max_retries:
            try:
                response = await request_func(*args, **kwargs)

                # If we get a response without exception, return it
                return response

            except RateLimitError as e:
                # Handle rate limit errors
                if not self.config.auto_retry or attempt >= self.config.max_retries:
                    raise

                # Calculate wait time from exception
                if e.retry_after is not None:
                    wait_time = min(e.retry_after, self.config.max_delay)
                else:
                    wait_time = self._get_backoff_delay(attempt)

                # Call retry callback if provided
                if self.config.on_retry:
                    try:
                        mock_response = self._create_mock_429_response()
                        if asyncio.iscoroutinefunction(self.config.on_retry):
                            await self.config.on_retry(attempt + 1, wait_time, mock_response)
                        else:
                            self.config.on_retry(attempt + 1, wait_time, mock_response)
                    except Exception as exc:
                        logger.warning(
                            "Retry callback raised exception",
                            error=str(exc),
                            attempt=attempt + 1,
                        )

                logger.info(
                    "Rate limited, retrying request",
                    attempt=attempt + 1,
                    max_retries=self.config.max_retries,
                    wait_seconds=wait_time,
                )

                # Non-blocking async sleep
                await asyncio.sleep(wait_time)
                attempt += 1

            except (httpx.HTTPError, NetworkError) as exc:
                # Network errors during retry
                if attempt >= self.config.max_retries:
                    raise
                logger.warning(
                    "Network error during request, retrying",
                    error=str(exc),
                    attempt=attempt + 1,
                )
                wait_time = self._get_backoff_delay(attempt)
                await asyncio.sleep(wait_time)
                attempt += 1

        # Max retries exceeded (shouldn't normally reach here)
        raise RateLimitError("Max retries exceeded")

