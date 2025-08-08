"""Unit tests for retry logic."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from ukcompanies.exceptions import RateLimitError
from ukcompanies.retry import (
    BackoffStrategy,
    RetryConfig,
    RetryManager,
    exponential_backoff,
    fixed_backoff,
)


class TestRetryConfig:
    """Test RetryConfig class."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        config = RetryConfig()
        assert config.auto_retry is True
        assert config.max_retries == 3
        assert config.backoff_strategy == BackoffStrategy.EXPONENTIAL
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.jitter_range == 1.0
        assert config.on_retry is None

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        callback = MagicMock()
        config = RetryConfig(
            auto_retry=False,
            max_retries=5,
            backoff="fixed",
            base_delay=2.0,
            max_delay=120.0,
            jitter_range=2.0,
            on_retry=callback,
        )
        assert config.auto_retry is False
        assert config.max_retries == 5
        assert config.backoff_strategy == BackoffStrategy.FIXED
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.jitter_range == 2.0
        assert config.on_retry is callback

    def test_invalid_backoff_strategy(self):
        """Test invalid backoff strategy raises ValueError."""
        with pytest.raises(ValueError, match="is not a valid BackoffStrategy"):
            RetryConfig(backoff="invalid")

    def test_negative_max_retries(self):
        """Test negative max_retries raises ValueError."""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            RetryConfig(max_retries=-1)

    def test_non_positive_base_delay(self):
        """Test non-positive base_delay raises ValueError."""
        with pytest.raises(ValueError, match="base_delay must be positive"):
            RetryConfig(base_delay=0)

    def test_non_positive_max_delay(self):
        """Test non-positive max_delay raises ValueError."""
        with pytest.raises(ValueError, match="max_delay must be positive"):
            RetryConfig(max_delay=0)

    def test_max_delay_less_than_base_delay(self):
        """Test max_delay < base_delay raises ValueError."""
        with pytest.raises(ValueError, match="max_delay must be >= base_delay"):
            RetryConfig(base_delay=10.0, max_delay=5.0)

    def test_negative_jitter_range(self):
        """Test negative jitter_range raises ValueError."""
        with pytest.raises(ValueError, match="jitter_range must be non-negative"):
            RetryConfig(jitter_range=-1.0)


class TestBackoffFunctions:
    """Test backoff calculation functions."""

    def test_exponential_backoff_without_jitter(self):
        """Test exponential backoff calculation without jitter."""
        # First attempt (2^0 * 1 = 1)
        delay = exponential_backoff(0, base_delay=1.0, max_delay=60.0, jitter_range=0)
        assert delay == 1.0

        # Second attempt (2^1 * 1 = 2)
        delay = exponential_backoff(1, base_delay=1.0, max_delay=60.0, jitter_range=0)
        assert delay == 2.0

        # Third attempt (2^2 * 1 = 4)
        delay = exponential_backoff(2, base_delay=1.0, max_delay=60.0, jitter_range=0)
        assert delay == 4.0

        # With custom base delay (2^1 * 3 = 6)
        delay = exponential_backoff(1, base_delay=3.0, max_delay=60.0, jitter_range=0)
        assert delay == 6.0

    def test_exponential_backoff_with_jitter(self):
        """Test exponential backoff with jitter."""
        delay = exponential_backoff(1, base_delay=1.0, max_delay=60.0, jitter_range=1.0)
        # 2^1 * 1 = 2, plus 0-1 seconds of jitter
        assert 2.0 <= delay <= 3.0

    def test_exponential_backoff_respects_max_delay(self):
        """Test exponential backoff respects max_delay."""
        # 2^10 * 1 = 1024, but should be capped at 60
        delay = exponential_backoff(10, base_delay=1.0, max_delay=60.0, jitter_range=0)
        assert delay == 60.0

    def test_fixed_backoff_without_jitter(self):
        """Test fixed backoff calculation without jitter."""
        # Attempt number doesn't affect fixed backoff
        delay = fixed_backoff(0, base_delay=5.0, max_delay=60.0, jitter_range=0)
        assert delay == 5.0

        delay = fixed_backoff(5, base_delay=5.0, max_delay=60.0, jitter_range=0)
        assert delay == 5.0

    def test_fixed_backoff_with_jitter(self):
        """Test fixed backoff with jitter."""
        delay = fixed_backoff(1, base_delay=5.0, max_delay=60.0, jitter_range=2.0)
        # 5 plus 0-2 seconds of jitter
        assert 5.0 <= delay <= 7.0


class TestRetryManager:
    """Test RetryManager class."""

    @pytest.fixture
    def config(self):
        """Create a default retry config."""
        return RetryConfig()

    @pytest.fixture
    def manager(self, config):
        """Create a retry manager."""
        return RetryManager(config)

    def test_get_backoff_delay_exponential(self, manager):
        """Test getting exponential backoff delay."""
        manager.config.backoff_strategy = BackoffStrategy.EXPONENTIAL
        manager.config.jitter_range = 0  # No jitter for predictable testing

        assert manager._get_backoff_delay(0) == 1.0
        assert manager._get_backoff_delay(1) == 2.0
        assert manager._get_backoff_delay(2) == 4.0

    def test_get_backoff_delay_fixed(self, manager):
        """Test getting fixed backoff delay."""
        manager.config.backoff_strategy = BackoffStrategy.FIXED
        manager.config.base_delay = 3.0
        manager.config.jitter_range = 0  # No jitter for predictable testing

        assert manager._get_backoff_delay(0) == 3.0
        assert manager._get_backoff_delay(1) == 3.0
        assert manager._get_backoff_delay(2) == 3.0

    def test_extract_reset_time_valid_header(self, manager):
        """Test extracting reset time from valid header."""
        # Create a timestamp 10 seconds in the future
        future_time = datetime.now(timezone.utc).timestamp() + 10
        response = MagicMock(spec=httpx.Response)
        response.headers = {"X-Ratelimit-Reset": str(int(future_time))}

        wait_time = manager._extract_reset_time(response)
        assert wait_time is not None
        assert 9 <= wait_time <= 11  # Allow for small timing differences

    def test_extract_reset_time_past_timestamp(self, manager):
        """Test extracting reset time with past timestamp returns None."""
        # Create a timestamp 10 seconds in the past
        past_time = datetime.now(timezone.utc).timestamp() - 10
        response = MagicMock(spec=httpx.Response)
        response.headers = {"X-Ratelimit-Reset": str(int(past_time))}

        wait_time = manager._extract_reset_time(response)
        assert wait_time is None

    def test_extract_reset_time_missing_header(self, manager):
        """Test extracting reset time with missing header returns None."""
        response = MagicMock(spec=httpx.Response)
        response.headers = {}

        wait_time = manager._extract_reset_time(response)
        assert wait_time is None

    def test_extract_reset_time_invalid_header(self, manager):
        """Test extracting reset time with invalid header returns None."""
        response = MagicMock(spec=httpx.Response)
        response.headers = {"X-Ratelimit-Reset": "not-a-number"}

        wait_time = manager._extract_reset_time(response)
        assert wait_time is None

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_attempt(self, manager):
        """Test successful request on first attempt."""
        request_func = AsyncMock(return_value=MagicMock(status_code=200))

        response = await manager.execute_with_retry(request_func, "arg1", kwarg1="value1")

        assert response.status_code == 200
        request_func.assert_called_once_with("arg1", kwarg1="value1")

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_after_retry(self, manager):
        """Test successful request after retry."""
        # First call raises RateLimitError, second succeeds
        request_func = AsyncMock(side_effect=[
            RateLimitError("Rate limited"),
            MagicMock(status_code=200),
        ])
        manager.config.jitter_range = 0  # No jitter for faster test
        manager.config.base_delay = 0.01  # Short delay for faster test

        response = await manager.execute_with_retry(request_func)

        assert response.status_code == 200
        assert request_func.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_max_retries_exceeded(self, manager):
        """Test max retries exceeded raises RateLimitError."""
        # Always raises RateLimitError
        request_func = AsyncMock(side_effect=RateLimitError("Rate limited"))
        manager.config.max_retries = 2
        manager.config.jitter_range = 0
        manager.config.base_delay = 0.01

        with pytest.raises(RateLimitError):
            await manager.execute_with_retry(request_func)

        assert request_func.call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_execute_with_retry_auto_retry_disabled(self, manager):
        """Test auto_retry disabled raises immediately."""
        manager.config.auto_retry = False
        request_func = AsyncMock(side_effect=RateLimitError("Rate limited"))

        with pytest.raises(RateLimitError):
            await manager.execute_with_retry(request_func)

        request_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_retry_uses_reset_header(self, manager):
        """Test retry uses X-Ratelimit-Reset header when available."""
        # Use a future timestamp 2 seconds from now
        future_timestamp = int(datetime.now(timezone.utc).timestamp()) + 2
        reset_time = datetime.fromtimestamp(future_timestamp, tz=timezone.utc)
        # First call raises RateLimitError with reset time, second succeeds
        request_func = AsyncMock(side_effect=[
            RateLimitError("Rate limited", retry_after=2.0, rate_limit_reset=reset_time),
            MagicMock(status_code=200),
        ])
        manager.config.max_delay = 1.0  # Cap at 1 second for test

        start_time = asyncio.get_event_loop().time()
        response = await manager.execute_with_retry(request_func)
        elapsed = asyncio.get_event_loop().time() - start_time

        assert response.status_code == 200
        # Should use the reset header time, but capped at max_delay (1.0)
        assert 0.9 <= elapsed <= 1.1  # Should wait approximately 1.0 seconds (capped)

    @pytest.mark.asyncio
    async def test_execute_with_retry_callback_invoked(self, manager):
        """Test on_retry callback is invoked."""
        callback = AsyncMock()
        manager.config.on_retry = callback
        manager.config.jitter_range = 0
        manager.config.base_delay = 0.01

        # First call raises RateLimitError, second succeeds
        request_func = AsyncMock(side_effect=[
            RateLimitError("Rate limited"),
            MagicMock(status_code=200),
        ])

        await manager.execute_with_retry(request_func)

        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] == 1  # Attempt number
        assert isinstance(args[1], float)  # Wait time
        assert hasattr(args[2], 'status_code')  # Mock response object
        assert args[2].status_code == 429  # Response status

    @pytest.mark.asyncio
    async def test_execute_with_retry_sync_callback(self, manager):
        """Test synchronous on_retry callback."""
        callback = MagicMock()
        manager.config.on_retry = callback
        manager.config.jitter_range = 0
        manager.config.base_delay = 0.01

        # First call raises RateLimitError, second succeeds
        request_func = AsyncMock(side_effect=[
            RateLimitError("Rate limited"),
            MagicMock(status_code=200),
        ])

        await manager.execute_with_retry(request_func)

        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_retry_callback_exception_handled(self, manager):
        """Test callback exceptions are handled gracefully."""
        callback = AsyncMock(side_effect=Exception("Callback error"))
        manager.config.on_retry = callback
        manager.config.jitter_range = 0
        manager.config.base_delay = 0.01

        # First call raises RateLimitError, second succeeds
        request_func = AsyncMock(side_effect=[
            RateLimitError("Rate limited"),
            MagicMock(status_code=200),
        ])

        # Should not raise the callback exception
        response = await manager.execute_with_retry(request_func)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_execute_with_retry_network_error_retried(self, manager):
        """Test network errors are retried."""
        manager.config.jitter_range = 0
        manager.config.base_delay = 0.01

        request_func = AsyncMock(
            side_effect=[
                httpx.ConnectError("Connection failed"),
                MagicMock(status_code=200),
            ]
        )

        response = await manager.execute_with_retry(request_func)
        assert response.status_code == 200
        assert request_func.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_network_error_max_retries(self, manager):
        """Test network errors respect max retries."""
        manager.config.max_retries = 1
        request_func = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))

        with pytest.raises(httpx.ConnectError):
            await manager.execute_with_retry(request_func)

        assert request_func.call_count == 2  # Initial + 1 retry
