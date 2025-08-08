"""Integration tests for retry logic and rate limiting."""

import asyncio
from datetime import datetime, timezone

import httpx
import pytest
import respx

from ukcompanies import AsyncClient
from ukcompanies.exceptions import RateLimitError


class TestRetryIntegration:
    """Integration tests for retry logic with mocked API responses."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_successful_retry_after_429(self):
        """Test successful retry after receiving 429 response."""
        # First request returns 429, second returns success
        route = respx.get("https://api.company-information.service.gov.uk/company/12345678")
        route.side_effect = [
            httpx.Response(
                429,
                headers={
                    "X-Ratelimit-Remain": "0",
                    "X-Ratelimit-Limit": "600",
                    "X-Ratelimit-Reset": str(int(datetime.now(timezone.utc).timestamp()) + 1),
                },
            ),
            httpx.Response(
                200,
                json={
                    "company_number": "12345678",
                    "company_name": "TEST COMPANY LIMITED",
                    "company_status": "active",
                    "type": "ltd",
                },
                headers={
                    "X-Ratelimit-Remain": "599",
                    "X-Ratelimit-Limit": "600",
                    "X-Ratelimit-Reset": str(int(datetime.now(timezone.utc).timestamp()) + 300),
                },
            ),
        ]

        async with AsyncClient(
            api_key="test-key",
            auto_retry=True,
            max_retries=3,
            backoff="exponential",
        ) as client:
            # Short delays for testing
            client.retry_config.base_delay = 0.01
            client.retry_config.max_delay = 0.5

            # Should retry and succeed
            company = await client.get_company("12345678")
            assert company.company_number == "12345678"
            assert company.company_name == "TEST COMPANY LIMITED"

        # Verify both requests were made
        assert route.call_count == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_max_retries_exceeded(self):
        """Test that RateLimitError is raised after max retries."""
        # All requests return 429
        route = respx.get("https://api.company-information.service.gov.uk/company/12345678")
        route.return_value = httpx.Response(
            429,
            headers={
                "X-Ratelimit-Remain": "0",
                "X-Ratelimit-Limit": "600",
                "X-Ratelimit-Reset": str(int(datetime.now(timezone.utc).timestamp()) + 10),
            },
        )

        async with AsyncClient(
            api_key="test-key",
            auto_retry=True,
            max_retries=2,
            backoff="fixed",
        ) as client:
            # Configure short delays for testing
            client.retry_config.base_delay = 0.01
            client.retry_config.jitter_range = 0

            # Should raise RateLimitError after retries
            with pytest.raises(RateLimitError) as exc_info:
                await client.get_company("12345678")

            assert exc_info.value.rate_limit_remain == 0
            assert exc_info.value.rate_limit_limit == 600

        # Initial request + 2 retries = 3 total
        assert route.call_count == 3

    @pytest.mark.asyncio
    @respx.mock
    async def test_respect_rate_limit_reset_header(self):
        """Test that retry respects X-Ratelimit-Reset header."""
        # Mock responses with rate limit reset header
        reset_time = int(datetime.now(timezone.utc).timestamp()) + 1

        route = respx.get("https://api.company-information.service.gov.uk/company/12345678")
        route.side_effect = [
            httpx.Response(
                429,
                headers={
                    "X-Ratelimit-Remain": "0",
                    "X-Ratelimit-Limit": "600",
                    "X-Ratelimit-Reset": str(reset_time),
                },
            ),
            httpx.Response(
                200,
                json={
                    "company_number": "12345678",
                    "company_name": "TEST COMPANY LIMITED",
                    "company_status": "active",
                    "type": "ltd",
                },
            ),
        ]

        async with AsyncClient(
            api_key="test-key",
            auto_retry=True,
            max_retries=3,
        ) as client:
            # Configure max delay to cap wait time
            client.retry_config.max_delay = 0.5

            start = asyncio.get_event_loop().time()
            company = await client.get_company("12345678")
            elapsed = asyncio.get_event_loop().time() - start

            assert company.company_number == "12345678"
            # Should have waited approximately the capped time
            assert 0.4 <= elapsed <= 0.6

    @pytest.mark.asyncio
    @respx.mock
    async def test_on_retry_callback_invoked(self):
        """Test that on_retry callback is invoked during retries."""
        retry_attempts = []

        async def on_retry(attempt: int, wait: float, response: httpx.Response) -> None:
            """Track retry attempts."""
            retry_attempts.append({
                "attempt": attempt,
                "wait": wait,
                "status": response.status_code,
            })

        # Setup responses
        route = respx.get("https://api.company-information.service.gov.uk/company/12345678")
        route.side_effect = [
            httpx.Response(429, headers={"X-Ratelimit-Remain": "0"}),
            httpx.Response(429, headers={"X-Ratelimit-Remain": "0"}),
            httpx.Response(
                200,
                json={
                    "company_number": "12345678",
                    "company_name": "TEST COMPANY LIMITED",
                    "company_status": "active",
                    "type": "ltd",
                },
            ),
        ]

        async with AsyncClient(
            api_key="test-key",
            auto_retry=True,
            max_retries=3,
            on_retry=on_retry,
        ) as client:
            # Configure short delays for testing
            client.retry_config.base_delay = 0.01
            client.retry_config.jitter_range = 0

            company = await client.get_company("12345678")
            assert company.company_number == "12345678"

        # Callback should have been called twice (for 2 retries)
        assert len(retry_attempts) == 2
        assert retry_attempts[0]["attempt"] == 1
        assert retry_attempts[0]["status"] == 429
        assert retry_attempts[1]["attempt"] == 2
        assert retry_attempts[1]["status"] == 429

    @pytest.mark.asyncio
    @respx.mock
    async def test_exponential_backoff_strategy(self):
        """Test exponential backoff strategy."""
        route = respx.get("https://api.company-information.service.gov.uk/company/12345678")
        route.side_effect = [
            httpx.Response(429),
            httpx.Response(429),
            httpx.Response(
                200,
                json={
                    "company_number": "12345678",
                    "company_name": "TEST COMPANY LIMITED",
                    "company_status": "active",
                    "type": "ltd",
                },
            ),
        ]

        wait_times = []

        async def track_wait(attempt: int, wait: float, response: httpx.Response) -> None:
            wait_times.append(wait)

        async with AsyncClient(
            api_key="test-key",
            auto_retry=True,
            max_retries=3,
            backoff="exponential",
            on_retry=track_wait,
        ) as client:
            # No jitter for predictable testing
            client.retry_config.jitter_range = 0
            client.retry_config.base_delay = 0.1

            company = await client.get_company("12345678")
            assert company.company_number == "12345678"

        # Check exponential backoff pattern (2^0 * 0.1, 2^1 * 0.1)
        assert len(wait_times) == 2
        assert wait_times[0] == 0.1  # 2^0 * 0.1
        assert wait_times[1] == 0.2  # 2^1 * 0.1

    @pytest.mark.asyncio
    @respx.mock
    async def test_fixed_backoff_strategy(self):
        """Test fixed backoff strategy."""
        route = respx.get("https://api.company-information.service.gov.uk/company/12345678")
        route.side_effect = [
            httpx.Response(429),
            httpx.Response(429),
            httpx.Response(
                200,
                json={
                    "company_number": "12345678",
                    "company_name": "TEST COMPANY LIMITED",
                    "company_status": "active",
                    "type": "ltd",
                },
            ),
        ]

        wait_times = []

        async def track_wait(attempt: int, wait: float, response: httpx.Response) -> None:
            wait_times.append(wait)

        async with AsyncClient(
            api_key="test-key",
            auto_retry=True,
            max_retries=3,
            backoff="fixed",
            on_retry=track_wait,
        ) as client:
            # No jitter for predictable testing
            client.retry_config.jitter_range = 0
            client.retry_config.base_delay = 0.15

            company = await client.get_company("12345678")
            assert company.company_number == "12345678"

        # Check fixed backoff pattern
        assert len(wait_times) == 2
        assert wait_times[0] == 0.15  # Fixed delay
        assert wait_times[1] == 0.15  # Fixed delay

    @pytest.mark.asyncio
    @respx.mock
    async def test_auto_retry_disabled(self):
        """Test that auto_retry=False disables retry logic."""
        route = respx.get("https://api.company-information.service.gov.uk/company/12345678")
        route.return_value = httpx.Response(
            429,
            headers={
                "X-Ratelimit-Remain": "0",
                "X-Ratelimit-Limit": "600",
            },
        )

        async with AsyncClient(
            api_key="test-key",
            auto_retry=False,  # Disable auto retry
        ) as client:
            # Should raise immediately without retry
            with pytest.raises(RateLimitError):
                await client.get_company("12345678")

        # Only one request should have been made
        assert route.call_count == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_async_behavior_maintained(self):
        """Test that retry logic maintains async behavior."""
        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0

        async def slow_response(request=None):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.05)
            concurrent_count -= 1
            return httpx.Response(
                200,
                json={
                    "company_number": "12345678",
                    "company_name": "TEST COMPANY LIMITED",
                    "company_status": "active",
                    "type": "ltd",
                },
            )

        route1 = respx.get("https://api.company-information.service.gov.uk/company/12345678")
        route1.side_effect = [
            httpx.Response(429),
            httpx.Response(429),
            slow_response,
        ]

        route2 = respx.get("https://api.company-information.service.gov.uk/company/87654321")
        route2.side_effect = [
            httpx.Response(429),
            slow_response,
        ]

        async with AsyncClient(
            api_key="test-key",
            auto_retry=True,
            max_retries=3,
        ) as client:
            # Short delays for testing
            client.retry_config.base_delay = 0.01
            client.retry_config.jitter_range = 0

            # Make concurrent requests
            results = await asyncio.gather(
                client.get_company("12345678"),
                client.get_company("87654321"),
            )

            assert len(results) == 2
            assert results[0].company_number == "12345678"
            assert results[1].company_number == "12345678"  # Both return same mock data

        # Should have had concurrent executions
        assert max_concurrent >= 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_network_error_retry(self):
        """Test retry on network errors."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.ConnectError("Connection failed")
            return httpx.Response(
                200,
                json={
                    "company_number": "12345678",
                    "company_name": "TEST COMPANY LIMITED",
                    "company_status": "active",
                    "type": "ltd",
                },
            )

        route = respx.get("https://api.company-information.service.gov.uk/company/12345678")
        route.mock(side_effect=side_effect)

        async with AsyncClient(
            api_key="test-key",
            auto_retry=True,
            max_retries=3,
        ) as client:
            # Short delays for testing
            client.retry_config.base_delay = 0.01
            client.retry_config.jitter_range = 0

            company = await client.get_company("12345678")
            assert company.company_number == "12345678"

        # Should have retried after network error
        assert call_count == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_missing_rate_limit_headers(self):
        """Test handling of 429 responses without rate limit headers."""
        route = respx.get("https://api.company-information.service.gov.uk/company/12345678")
        route.side_effect = [
            httpx.Response(429),  # No headers
            httpx.Response(
                200,
                json={
                    "company_number": "12345678",
                    "company_name": "TEST COMPANY LIMITED",
                    "company_status": "active",
                    "type": "ltd",
                },
            ),
        ]

        async with AsyncClient(
            api_key="test-key",
            auto_retry=True,
            max_retries=3,
        ) as client:
            # Short delays for testing
            client.retry_config.base_delay = 0.01
            client.retry_config.jitter_range = 0

            # Should use exponential backoff when headers missing
            company = await client.get_company("12345678")
            assert company.company_number == "12345678"

        assert route.call_count == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_rate_limit_info_extraction(self):
        """Test that rate limit info is extracted and stored."""
        route = respx.get("https://api.company-information.service.gov.uk/company/12345678")
        reset_time = int(datetime.now(timezone.utc).timestamp()) + 300

        route.return_value = httpx.Response(
            200,
            json={
                "company_number": "12345678",
                "company_name": "TEST COMPANY LIMITED",
                "company_status": "active",
                "type": "ltd",
            },
            headers={
                "X-Ratelimit-Remain": "450",
                "X-Ratelimit-Limit": "600",
                "X-Ratelimit-Reset": str(reset_time),
            },
        )

        async with AsyncClient(api_key="test-key") as client:
            company = await client.get_company("12345678")
            assert company.company_number == "12345678"

            # Check rate limit info was extracted
            rate_info = client.rate_limit_info
            assert rate_info is not None
            assert rate_info.remain == 450
            assert rate_info.limit == 600
            assert rate_info.percent_remaining == 75.0

    @pytest.mark.asyncio
    @respx.mock
    async def test_100_percent_coverage_scenarios(self):
        """Test edge cases for 100% code coverage."""
        # Test with real rate limit headers
        route = respx.get("https://api.company-information.service.gov.uk/company/12345678")
        future_time = int(datetime.now(timezone.utc).timestamp()) + 5

        route.side_effect = [
            httpx.Response(
                429,
                headers={
                    "X-Ratelimit-Remain": "0",
                    "X-Ratelimit-Limit": "600",
                    "X-Ratelimit-Reset": str(future_time),
                },
            ),
            httpx.Response(
                200,
                json={
                    "company_number": "12345678",
                    "company_name": "TEST COMPANY LIMITED",
                    "company_status": "active",
                    "type": "ltd",
                },
            ),
        ]

        async with AsyncClient(
            api_key="test-key",
            auto_retry=True,
            max_retries=3,
        ) as client:
            # Configure for fast testing
            client.retry_config.max_delay = 0.1

            company = await client.get_company("12345678")
            assert company.company_number == "12345678"

        assert route.call_count == 2
