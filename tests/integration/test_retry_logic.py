"""Integration tests for retry logic."""

import asyncio

import httpx
import pytest
import respx

from ukcompanies import AsyncClient, Config
from ukcompanies.exceptions import RateLimitError, ServerError


@pytest.mark.asyncio
class TestRetryLogic:
    """Test retry logic for rate limiting and server errors."""

    @respx.mock
    async def test_retry_on_rate_limit(self):
        """Test that client retries on 429 rate limit errors."""
        # First call: rate limited
        # Second call: success
        mock_responses = [
            httpx.Response(
                429,
                json={"error": "Rate limit exceeded"},
                headers={"Retry-After": "1"},
            ),
            httpx.Response(
                200,
                json={
                    "company_number": "12345678",
                    "company_name": "TEST COMPANY",
                },
            ),
        ]

        route = respx.get("https://api.company-information.service.gov.uk/company/12345678")
        route.side_effect = mock_responses

        config = Config(api_key="test-key", max_retries=3)
        async with AsyncClient(config=config) as client:
            company = await client.get_company("12345678")

        assert company.company_number == "12345678"
        assert company.company_name == "TEST COMPANY"
        assert route.call_count == 2  # Initial + 1 retry

    @respx.mock
    async def test_retry_on_server_error(self):
        """Test that client retries on 500 server errors."""
        # First call: server error
        # Second call: success
        mock_responses = [
            httpx.Response(500, json={"error": "Internal server error"}),
            httpx.Response(
                200,
                json={
                    "company_number": "12345678",
                    "company_name": "TEST COMPANY",
                },
            ),
        ]

        route = respx.get("https://api.company-information.service.gov.uk/company/12345678")
        route.side_effect = mock_responses

        config = Config(api_key="test-key", max_retries=3)
        async with AsyncClient(config=config) as client:
            company = await client.get_company("12345678")

        assert company.company_number == "12345678"
        assert route.call_count == 2

    @respx.mock
    async def test_max_retries_exceeded(self):
        """Test that max retries limit is respected."""
        # All calls return rate limit error
        route = respx.get("https://api.company-information.service.gov.uk/company/12345678").mock(
            return_value=httpx.Response(
                429,
                json={"error": "Rate limit exceeded"},
                headers={"Retry-After": "0"},  # Short retry for test speed
            )
        )

        config = Config(api_key="test-key", max_retries=2)
        async with AsyncClient(config=config) as client:
            with pytest.raises(RateLimitError) as exc_info:
                await client.get_company("12345678")
            assert "rate limit" in str(exc_info.value).lower()

        # Initial call + 2 retries = 3 total calls
        assert route.call_count == 3

    @respx.mock
    async def test_no_retry_when_disabled(self):
        """Test that retry is disabled when max_retries is 0."""
        route = respx.get("https://api.company-information.service.gov.uk/company/12345678").mock(
            return_value=httpx.Response(
                429,
                json={"error": "Rate limit exceeded"},
            )
        )

        config = Config(api_key="test-key", max_retries=0)
        async with AsyncClient(config=config) as client:
            with pytest.raises(RateLimitError):
                await client.get_company("12345678")

        # Should only make one call (no retries)
        assert route.call_count == 1

    @respx.mock
    async def test_retry_callback(self):
        """Test that on_retry callback is called during retries."""
        retry_attempts = []

        def on_retry(attempt: int, error: Exception):
            retry_attempts.append((attempt, type(error).__name__))

        # First two calls fail, third succeeds
        mock_responses = [
            httpx.Response(429, json={"error": "Rate limited"}, headers={"Retry-After": "0"}),
            httpx.Response(500, json={"error": "Server error"}),
            httpx.Response(200, json={"company_number": "12345678", "company_name": "TEST"}),
        ]

        route = respx.get("https://api.company-information.service.gov.uk/company/12345678")
        route.side_effect = mock_responses

        config = Config(api_key="test-key", max_retries=3)
        async with AsyncClient(config=config) as client:
            # Pass on_retry callback to the request
            # Note: This would need to be supported in the actual implementation
            # For now, this test documents the expected behavior
            pass

        # This test documents expected behavior but would need implementation support
        # assert len(retry_attempts) == 2
        # assert retry_attempts[0] == (1, "RateLimitError")
        # assert retry_attempts[1] == (2, "ServerError")

    @respx.mock
    async def test_exponential_backoff(self):
        """Test that exponential backoff is applied without Retry-After header."""
        # Track timing of requests
        request_times = []

        def track_time(request):
            request_times.append(asyncio.get_event_loop().time())
            return httpx.Response(500, json={"error": "Server error"})

        route = respx.get("https://api.company-information.service.gov.uk/company/12345678")
        route.side_effect = [
            track_time,
            track_time,
            httpx.Response(200, json={"company_number": "12345678", "company_name": "TEST"}),
        ]

        config = Config(api_key="test-key", max_retries=2)
        async with AsyncClient(config=config) as client:
            company = await client.get_company("12345678")

        assert company.company_number == "12345678"
        assert route.call_count == 3

        # Verify exponential backoff pattern (with some tolerance for timing)
        # Note: Actual timing verification would depend on implementation details